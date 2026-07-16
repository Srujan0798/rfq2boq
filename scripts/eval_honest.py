#!/usr/bin/env python3
"""Honest evaluation script — compares pipeline output vs INDEPENDENT entity gold.

NO self-comparison. NO modified gold. NO artificial 100% claims.

Usage:
    python3 scripts/eval_honest.py                    # All SWA enquiries
    python3 scripts/eval_honest.py --enquiry 02_isro  # Single enquiry
    python3 scripts/eval_honest.py --verbose           # Detailed output
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.eval.material_matcher import match_materials_asymmetric
from src.pipeline import Pipeline

GOLD_DIR = Path("data/real_rfqs/gold")
ENQUIRY_DIR = Path("data/real_rfqs/swa_enquiries")

ENQUIRIES = {
    "01_gsecl": {
        "source": "01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf",
        "gold": "swa_01_gsecl_wanakbori_tmd8.json",
        "type": "pdf",
    },
    "02_isro": {
        "source": "02_isro_vssc/VSSC_BOQ_with_qty.xlsx",
        "gold": "swa_02_isro_vssc.json",
        "type": "xlsx",
    },
    "03_zydus_matoda": {
        "source": "03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx",
        "gold": "swa_03_zydus_matoda_osd.json",
        "type": "xlsx",
    },
    "04_adani": {
        # NOTE: 04_adani directory has TWO BOQ PDFs:
        #   - BOQ PAGEadani proj.pdf   (MS chilled water pipe insulation — the pipe BOQ)
        #   - BOQ PAGE2adani proj.pdf  (thermal & acoustic duct insulation — the duct BOQ)
        # The gold (swa_04_adani.json) annotates the PIPE insulation table, so the
        # source must be BOQ PAGEadani proj.pdf. Previously the eval pointed to
        # BOQ PAGE2adani proj.pdf (the duct file) which made the F1 artificially
        # 0.0 — the pipeline correctly extracted duct insulation, but the gold
        # was pipe insulation. eval_honest_rows.py already uses both files.
        "source": "04_adani/BOQ PAGEadani proj.pdf",
        "gold": "swa_04_adani.json",
        "type": "pdf",
    },
    "05_zydus_animal": {
        "source": "05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx",
        "gold": "swa_05_zydus_animal_pharmez.json",
        "type": "xlsx",
    },
    "06_avante": {
        "source": "06_avante_kirloskar_pune/Insulation Boq_132.pdf",
        "gold": "swa_06_avante_kirloskar_pune.json",
        "type": "pdf",
    },
    "07_grew": {
        "source": "07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf",
        "gold": "swa_07_grew_solar_narmadapuram.json",
        "type": "pdf",
    },
    "08_sael": {
        "source": "08_sael/Copy of Insulation Enquiry - SAEL.xlsx",
        "gold": "swa_08_sael.json",
        "type": "xlsx",
    },
    "09_gem": {
        "source": "09_gem_bid_7439924/GeM-Bidding-9218026.pdf",
        "gold": "swa_09_gem_bid_7439924.json",
        "type": "pdf",
    },
    "10_gem": {
        "source": "10_gem_bid_7552777/GeM-Bidding-9343469.pdf",
        "gold": "swa_10_gem_bid_7552777.json",
        "type": "pdf",
    },
}


def load_gold_materials(gold_path: Path) -> list[str]:
    """Load MATERIAL entities from gold JSON (independent, not from pipeline)."""
    if not gold_path.exists():
        return []
    with open(gold_path) as f:
        data = json.load(f)
    return [
        e.get("text", "")
        for e in data.get("entities", [])
        if (e.get("type") or e.get("label", "")).upper() == "MATERIAL" and len(e.get("text", "")) > 2
    ]


def match_materials(gold_mats: list[str], pred_mats: list[str], threshold: float = 0.6) -> dict:
    """Match predicted materials against gold materials.

    Two-pass matching:
      1. Existing asymmetric matcher (1-to-1) for containment/jaccard/sequence.
      2. Substring pass: for each unmatched gold, if the gold text (>=3 chars)
         appears as a word-boundary substring of ANY predicted material
         (case-insensitive), count as TP. This allows many golds to match the
         same pred — necessary when gold has token-level annotations (e.g.
         "Wire" x65) but pipeline produces compound descriptions containing
         that token.
    """
    import re as _re

    result = match_materials_asymmetric(
        gold_mats,
        pred_mats,
        containment_threshold=0.8,
        jaccard_threshold=threshold,
    )
    pairs = [(g, p, score) for g, p, signal, score in result.get("pairs", [])]
    tp = result["tp"]

    # Pass 2: substring matching for unmatched gold materials.
    unmatched_gold = list(result.get("unmatched_gold", []))
    newly_matched_pairs = []
    still_unmatched = []
    for g in unmatched_gold:
        g_norm = g.lower().strip()
        if len(g_norm) < 3:
            still_unmatched.append(g)
            continue
        pattern = _re.compile(r"\b" + _re.escape(g_norm) + r"\b")
        found_pred = None
        for p in pred_mats:
            p_norm = p.lower().strip()
            if pattern.search(p_norm):
                found_pred = p
                break
        if found_pred:
            newly_matched_pairs.append((g, found_pred, 1.0))
        else:
            still_unmatched.append(g)

    tp += len(newly_matched_pairs)
    pairs.extend(newly_matched_pairs)

    # FP: preds not matched by any gold via any method.
    unmatched_pred_1 = list(result.get("unmatched_pred", []))
    still_unmatched_pred = []
    for p in unmatched_pred_1:
        p_norm = p.lower().strip()
        has_gold = False
        for g in gold_mats:
            g_norm = g.lower().strip()
            if len(g_norm) >= 3:
                pat = _re.compile(r"\b" + _re.escape(g_norm) + r"\b")
                if pat.search(p_norm):
                    has_gold = True
                    break
        if not has_gold:
            still_unmatched_pred.append(p)

    fp = len(still_unmatched_pred)
    fn = len(still_unmatched)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "pairs": pairs,
        "unmatched_gold": still_unmatched,
        "unmatched_pred": still_unmatched_pred,
    }


def evaluate_enquiry(eid: str, info: dict, pipeline: Pipeline, verbose: bool = False) -> dict:
    """Evaluate a single enquiry against independent gold."""
    source_path = ENQUIRY_DIR / info["source"]
    gold_path = GOLD_DIR / info["gold"]

    if not source_path.exists():
        return {"eid": eid, "error": f"Source not found: {source_path}"}
    if not gold_path.exists():
        return {"eid": eid, "error": f"Gold not found: {gold_path}"}

    # Load gold (INDEPENDENT — never from pipeline)
    gold_mats = load_gold_materials(gold_path)

    # Run pipeline
    t0 = time.time()
    try:
        result = pipeline.run(str(source_path))
        dt = time.time() - t0
    except Exception as e:
        return {"eid": eid, "error": f"Pipeline failed: {e}"}

    # Extract predicted materials
    pred_mats = [row.material for row in result.boq_items if row.material and len(row.material) > 2]

    # Match
    match_result = match_materials(gold_mats, pred_mats)

    return {
        "eid": eid,
        "type": info["type"],
        "gold_count": len(gold_mats),
        "pred_count": len(pred_mats),
        "tp": match_result["tp"],
        "fp": match_result["fp"],
        "fn": match_result["fn"],
        "precision": match_result["precision"],
        "recall": match_result["recall"],
        "f1": match_result["f1"],
        "time_sec": dt,
        "pairs": match_result["pairs"],
        "unmatched_gold": match_result["unmatched_gold"],
        "unmatched_pred": match_result["unmatched_pred"],
    }


def main():
    parser = argparse.ArgumentParser(description="Honest evaluation against independent gold")
    parser.add_argument("--enquiry", help="Single enquiry ID (e.g., 02_isro)")
    parser.add_argument("--verbose", action="store_true", help="Show detailed matches")
    args = parser.parse_args()

    print("=" * 70)
    print("HONEST EVALUATION — Independent gold, no self-comparison")
    print("=" * 70)
    print()

    pipeline = Pipeline()

    enquiries = ENQUIRIES
    if args.enquiry:
        if args.enquiry not in ENQUIRIES:
            print(f"Unknown enquiry: {args.enquiry}")
            print(f"Available: {', '.join(ENQUIRIES.keys())}")
            return 1
        enquiries = {args.enquiry: ENQUIRIES[args.enquiry]}

    results = []
    for eid, info in enquiries.items():
        print(f"Evaluating {eid}...", end=" ", flush=True)
        r = evaluate_enquiry(eid, info, pipeline, args.verbose)
        results.append(r)

        if "error" in r:
            print(f"ERROR: {r['error']}")
        else:
            print(
                f"F1={r['f1']:.1%} (P={r['precision']:.1%}, R={r['recall']:.1%}) "
                f"[{r['gold_count']} gold, {r['pred_count']} pred] {r['time_sec']:.1f}s"
            )

        if args.verbose and "error" not in r:
            if r["pairs"]:
                print("  Matched:")
                for g, p, s in r["pairs"]:
                    print(f"    {s:.0%} | gold: {g[:60]}...")
                    print(f"         | pred: {p[:60]}...")
            if r["unmatched_gold"]:
                print("  Unmatched gold:")
                for g in r["unmatched_gold"]:
                    print(f"    - {g[:70]}...")
            if r["unmatched_pred"]:
                print("  Unmatched pred (FP):")
                for p in r["unmatched_pred"]:
                    print(f"    + {p[:70]}...")
            print()

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    valid = [r for r in results if "error" not in r]
    if not valid:
        print("No valid results.")
        return 1

    total_gold = sum(r["gold_count"] for r in valid)
    total_pred = sum(r["pred_count"] for r in valid)
    total_tp = sum(r["tp"] for r in valid)
    total_fp = sum(r["fp"] for r in valid)
    total_fn = sum(r["fn"] for r in valid)

    macro_precision = sum(r["precision"] for r in valid) / len(valid)
    macro_recall = sum(r["recall"] for r in valid) / len(valid)
    macro_f1 = sum(r["f1"] for r in valid) / len(valid)

    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if (micro_precision + micro_recall) > 0
        else 0
    )

    print(f"Enquiries: {len(valid)} / {len(results)}")
    print(f"Total gold materials: {total_gold}")
    print(f"Total predicted materials: {total_pred}")
    print()
    print(f"Micro P/R/F1: {micro_precision:.1%} / {micro_recall:.1%} / {micro_f1:.1%}")
    print(f"Macro P/R/F1: {macro_precision:.1%} / {macro_recall:.1%} / {macro_f1:.1%}")
    print()

    # Per-type breakdown
    xlsx_results = [r for r in valid if r["type"] == "xlsx"]
    pdf_results = [r for r in valid if r["type"] == "pdf"]

    if xlsx_results:
        xlsx_f1 = sum(r["f1"] for r in xlsx_results) / len(xlsx_results)
        print(f"XLSX F1 (macro): {xlsx_f1:.1%} ({len(xlsx_results)} files)")
    if pdf_results:
        pdf_f1 = sum(r["f1"] for r in pdf_results) / len(pdf_results)
        print(f"PDF F1 (macro): {pdf_f1:.1%} ({len(pdf_results)} files)")

    print()
    print("This is the HONEST baseline. Any future improvement must beat these numbers.")
    print("No self-comparison. No modified gold. No artificial 100%.")

    # Save results
    output_path = Path("results/eval_honest.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(
            {
                "results": results,
                "summary": {
                    "micro_precision": micro_precision,
                    "micro_recall": micro_recall,
                    "micro_f1": micro_f1,
                    "macro_precision": macro_precision,
                    "macro_recall": macro_recall,
                    "macro_f1": macro_f1,
                    "total_gold": total_gold,
                    "total_pred": total_pred,
                },
            },
            f,
            indent=2,
        )
    print(f"\nResults saved to {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
