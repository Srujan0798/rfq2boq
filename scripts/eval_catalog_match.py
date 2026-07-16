#!/usr/bin/env python3
"""Evaluate the catalog matcher against gold annotations for all 10 SWA enquiries.

Reads gold annotations (MATERIAL entities) and compares against:
  1. Catalog matcher output (GeM catalog matching)
  2. Pipeline BOQ materials (full extraction pipeline)

Reports per-file and overall precision/recall/F1 for catalog matching.

Usage:
    python3 scripts/eval_catalog_match.py
    python3 scripts/eval_catalog_match.py --enquiry 02_isro
    python3 scripts/eval_catalog_match.py --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nlp.catalog_matcher import CatalogMatcher

GOLD_DIR = Path("data/real_rfqs/gold")
ENQUIRY_DIR = Path("data/real_rfqs/swa_enquiries")
OUTPUT_DIR = Path("results")

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


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def load_gold_materials(gold_path: Path) -> list[str]:
    """Load MATERIAL entities from gold JSON."""
    if not gold_path.exists():
        return []
    with open(gold_path) as f:
        data = json.load(f)
    return [
        e.get("text", "")
        for e in data.get("entities", [])
        if (e.get("type") or e.get("label", "")).upper() == "MATERIAL"
        and len(e.get("text", "")) > 2
    ]


def match_materials(
    gold_mats: list[str],
    pred_mats: list[str],
    threshold: float = 0.6,
) -> dict:
    """Match predicted materials against gold materials. Returns TP/FP/FN + P/R/F1."""
    matched_gold: set[int] = set()
    matched_pred: set[int] = set()
    pairs = []

    for i, g in enumerate(gold_mats):
        best_j = -1
        best_score = 0.0
        for j, p in enumerate(pred_mats):
            if j in matched_pred:
                continue
            score = similarity(g, p)
            if score > best_score:
                best_score = score
                best_j = j
        if best_j >= 0 and best_score >= threshold:
            matched_gold.add(i)
            matched_pred.add(best_j)
            pairs.append((g, pred_mats[best_j], best_score))

    tp = len(matched_gold)
    fp = len(pred_mats) - len(matched_pred)
    fn = len(gold_mats) - len(matched_gold)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "pairs": pairs,
        "unmatched_gold": [g for i, g in enumerate(gold_mats) if i not in matched_gold],
        "unmatched_pred": [p for j, p in enumerate(pred_mats) if j not in matched_pred],
    }


def evaluate_enquiry(
    eid: str,
    info: dict,
    matcher: CatalogMatcher,
    verbose: bool = False,
) -> dict:
    """Evaluate a single enquiry: gold MATERIAL entities vs catalog matcher output."""
    source_path = ENQUIRY_DIR / info["source"]
    gold_path = GOLD_DIR / info["gold"]

    if not gold_path.exists():
        return {"eid": eid, "error": f"Gold not found: {gold_path}"}

    gold_mats = load_gold_materials(gold_path)
    if not gold_mats:
        return {"eid": eid, "error": "No gold MATERIAL entities"}

    # Extract materials from source — for XLSX use pipeline, for PDF use text extraction
    pipeline_mats: list[str] = []
    if not source_path.exists():
        return {"eid": eid, "error": f"Source not found: {source_path}"}

    if info["type"] == "xlsx":
        try:
            from src.pipeline_xlsx import XLSXRowPipeline

            xlsx_pipe = XLSXRowPipeline()
            boq_rows = xlsx_pipe.run(str(source_path))
            pipeline_mats = [r.material for r in boq_rows if r.material and len(r.material) > 2]
        except Exception as e:
            return {"eid": eid, "error": f"XLSX pipeline failed: {e}"}
    else:
        try:
            from src.pipeline import Pipeline

            pipeline = Pipeline()
            result = pipeline.run(str(source_path))
            pipeline_mats = [r.material for r in result.boq_items if r.material and len(r.material) > 2]
        except Exception as e:
            return {"eid": eid, "error": f"Pipeline failed: {e}"}

    # Run catalog matcher on pipeline materials
    t0 = time.time()
    catalog_matches = matcher.match_batch(pipeline_mats)
    dt = time.time() - t0

    matched_catalog = [m for m in catalog_matches if not m.is_unmatched]
    unmatched_catalog = [m for m in catalog_matches if m.is_unmatched]

    # Match pipeline materials against gold (full pipeline P/R/F1)
    pipeline_match = match_materials(gold_mats, pipeline_mats)

    # Match catalog-matched materials against gold (what the catalog catches)
    # Also include unmatched items that are pipeline materials (not silently dropped)
    all_catalog_output = [m.input_text for m in catalog_matches]
    catalog_match_result = match_materials(gold_mats, all_catalog_output)

    # Catalog precision: of items the catalog matched, how many are in gold?
    # (Uses the matched alias as the "predicted" material for comparison)
    catalog_pred_texts = [m.gem_name or m.input_text for m in catalog_matches]
    catalog_pr = match_materials(gold_mats, catalog_pred_texts)

    return {
        "eid": eid,
        "type": info["type"],
        "source": str(source_path),
        "gold_count": len(gold_mats),
        "pipeline_materials_count": len(pipeline_mats),
        "catalog_matched_count": len(matched_catalog),
        "catalog_unmatched_count": len(unmatched_catalog),
        # Pipeline full extraction metrics
        "pipeline": {
            "tp": pipeline_match["tp"],
            "fp": pipeline_match["fp"],
            "fn": pipeline_match["fn"],
            "precision": pipeline_match["precision"],
            "recall": pipeline_match["recall"],
            "f1": pipeline_match["f1"],
        },
        # Catalog matcher: all items (matched + unmatched) vs gold
        "catalog_all": {
            "tp": catalog_match_result["tp"],
            "fp": catalog_match_result["fp"],
            "fn": catalog_match_result["fn"],
            "precision": catalog_match_result["precision"],
            "recall": catalog_match_result["recall"],
            "f1": catalog_match_result["f1"],
        },
        # Catalog matcher: using gem_name as prediction
        "catalog_gem_names": {
            "tp": catalog_pr["tp"],
            "fp": catalog_pr["fp"],
            "fn": catalog_pr["fn"],
            "precision": catalog_pr["precision"],
            "recall": catalog_pr["recall"],
            "f1": catalog_pr["f1"],
        },
        "time_sec": round(dt, 3),
        "unmatched_items": [m.to_dict() for m in unmatched_catalog[:20]],
        "unmatched_gold": catalog_match_result.get("unmatched_gold", []),
    }


def compute_overall(results: list[dict]) -> dict:
    """Compute micro-averaged metrics across all enquiries."""
    total_tp = {"pipeline": 0, "catalog_all": 0, "catalog_gem_names": 0}
    total_fp = {"pipeline": 0, "catalog_all": 0, "catalog_gem_names": 0}
    total_fn = {"pipeline": 0, "catalog_all": 0, "catalog_gem_names": 0}
    total_gold = 0
    total_pipeline_pred = 0
    total_catalog_matched = 0
    n_files = 0

    for r in results:
        if "error" in r:
            continue
        n_files += 1
        total_gold += r["gold_count"]
        total_pipeline_pred += r["pipeline_materials_count"]
        total_catalog_matched += r["catalog_matched_count"]
        for key in ("pipeline", "catalog_all", "catalog_gem_names"):
            total_tp[key] += r[key]["tp"]
            total_fp[key] += r[key]["fp"]
            total_fn[key] += r[key]["fn"]

    def _prf1(tp: int, fp: int, fn: int) -> dict:
        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
        return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4)}

    return {
        "n_files": n_files,
        "total_gold_materials": total_gold,
        "total_pipeline_predictions": total_pipeline_pred,
        "total_catalog_matched": total_catalog_matched,
        "pipeline_overall": _prf1(total_tp["pipeline"], total_fp["pipeline"], total_fn["pipeline"]),
        "catalog_all_overall": _prf1(total_tp["catalog_all"], total_fp["catalog_all"], total_fn["catalog_all"]),
        "catalog_gem_names_overall": _prf1(
            total_tp["catalog_gem_names"], total_fp["catalog_gem_names"], total_fn["catalog_gem_names"]
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate catalog matcher against gold annotations")
    parser.add_argument("--enquiry", "-e", help="Single enquiry ID (e.g. 02_isro)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    try:
        matcher = CatalogMatcher()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Catalog loaded: {matcher.catalog_size} products, {matcher.unique_products} unique")
    print()

    enquiry_ids = [args.enquiry] if args.enquiry else sorted(ENQUIRIES.keys())
    results = []

    for eid in enquiry_ids:
        if eid not in ENQUIRIES:
            print(f"Unknown enquiry: {eid}")
            continue
        info = ENQUIRIES[eid]
        print(f"[*] {eid}: {info['source']}")
        result = evaluate_enquiry(eid, info, matcher, verbose=args.verbose)
        results.append(result)
        if "error" in result:
            print(f"    ERROR: {result['error']}")
        else:
            print(f"    Gold: {result['gold_count']} materials")
            print(f"    Pipeline: {result['pipeline_materials_count']} materials")
            print(f"    Catalog matched: {result['catalog_matched_count']}, unmatched: {result['catalog_unmatched_count']}")
            p = result["pipeline"]
            c = result["catalog_all"]
            print(f"    Pipeline  P={p['precision']:.3f} R={p['recall']:.3f} F1={p['f1']:.3f}")
            print(f"    Catalog   P={c['precision']:.3f} R={c['recall']:.3f} F1={c['f1']:.3f}")
            if args.verbose and result["unmatched_items"]:
                print("    Unmatched items:")
                for item in result["unmatched_items"][:5]:
                    print(f"      - {item['input_text'][:80]}")
        print()

    # Overall
    overall = compute_overall(results)
    print("=" * 60)
    print("OVERALL (micro-averaged)")
    print(f"  Files evaluated: {overall['n_files']}")
    print(f"  Total gold materials: {overall['total_gold_materials']}")
    print(f"  Total pipeline predictions: {overall['total_pipeline_predictions']}")
    print(f"  Total catalog matched: {overall['total_catalog_matched']}")
    print()
    for key, label in [
        ("pipeline_overall", "Pipeline (full extraction)"),
        ("catalog_all_overall", "Catalog (all items vs gold)"),
        ("catalog_gem_names_overall", "Catalog (gem names vs gold)"),
    ]:
        m = overall[key]
        print(f"  {label}: P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f}")
    print("=" * 60)

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "eval_catalog_match.json"
    report = {
        "overall": overall,
        "per_file": results,
        "catalog_summary": matcher.get_catalog_summary(),
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
