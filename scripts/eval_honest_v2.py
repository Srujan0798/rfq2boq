#!/usr/bin/env python3
"""Z1 honest evaluation script — entity-level, with asymmetric matcher.

Compares pipeline output vs INDEPENDENT entity gold, but uses:
  1. Phrase extraction on predictions (strip action prefix / spec / suffix).
  2. Asymmetric material matcher (containment + substring + 0.6 Jaccard
     fallback) so that short human gold can match long pipeline sentences.

Gold loading is reused from `scripts/eval_honest.py` (no duplication).
The frozen baseline script `scripts/eval_honest.py` is not modified.

Usage:
    python3 scripts/eval_honest_v2.py                    # All SWA enquiries
    python3 scripts/eval_honest_v2.py --enquiry 01_gsecl # Single enquiry
    python3 scripts/eval_honest_v2.py --no-phrase-extract  # matcher only
    python3 scripts/eval_honest_v2.py --held-out path/to/file.pdf
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Reuse the frozen gold loader and ENQUIRIES map from the baseline script.
from scripts.eval_honest import ENQUIRIES, GOLD_DIR, load_gold_materials  # noqa: E402
from src.eval.matchers import match_materials_asymmetric
from src.nlp.patterns.material_phrases import extract_canonical_material
from src.pipeline import Pipeline

ENQUIRY_DIR = Path("data/real_rfqs/swa_enquiries")
OUTPUT_PATH = Path("results/eval_honest_v2.json")


def evaluate_enquiry_v2(
    eid: str,
    info: dict,
    pipeline: Pipeline,
    use_phrase_extract: bool = True,
    containment_threshold: float = 0.8,
    jaccard_threshold: float = 0.6,
    verbose: bool = False,
) -> dict:
    """Run pipeline + asymmetric matcher on one enquiry."""
    source_path = ENQUIRY_DIR / info["source"]
    gold_path = GOLD_DIR / info["gold"]

    if not source_path.exists():
        return {"eid": eid, "error": f"Source not found: {source_path}"}
    if not gold_path.exists():
        return {"eid": eid, "error": f"Gold not found: {gold_path}"}

    gold_mats = load_gold_materials(gold_path)

    t0 = time.time()
    try:
        result = pipeline.run(str(source_path))
        dt = time.time() - t0
    except Exception as e:
        return {"eid": eid, "error": f"Pipeline failed: {e}"}

    pred_mats_raw = [row.material for row in result.boq_items if row.material and len(row.material) > 2]
    pred_mats = [extract_canonical_material(m) for m in pred_mats_raw] if use_phrase_extract else pred_mats_raw

    match_result = match_materials_asymmetric(
        gold_mats,
        pred_mats,
        containment_threshold=containment_threshold,
        jaccard_threshold=jaccard_threshold,
    )

    return {
        "eid": eid,
        "type": info["type"],
        "gold_count": len(gold_mats),
        "pred_count": len(pred_mats),
        "pred_count_raw": len(pred_mats_raw),
        "tp": match_result["tp"],
        "fp": match_result["fp"],
        "fn": match_result["fn"],
        "precision": match_result["precision"],
        "recall": match_result["recall"],
        "f1": match_result["f1"],
        "time_sec": dt,
        "pairs": match_result["pairs"],
        "signals": match_result["signals"],
        "unmatched_gold": match_result["unmatched_gold"],
        "unmatched_pred": match_result["unmatched_pred"],
        "phrase_extract": use_phrase_extract,
    }


def evaluate_held_out(
    file_path: str,
    pipeline: Pipeline,
    use_phrase_extract: bool = True,
) -> dict:
    """Run pipeline on a file outside the SWA set. For freshness audit."""
    fp = Path(file_path)
    if not fp.exists():
        return {"error": f"Held-out file not found: {fp}"}
    t0 = time.time()
    try:
        result = pipeline.run(str(fp))
        dt = time.time() - t0
    except Exception as e:
        return {"error": f"Pipeline failed: {e}"}

    pred_mats_raw = [row.material for row in result.boq_items if row.material and len(row.material) > 2]
    pred_mats = [extract_canonical_material(m) for m in pred_mats_raw] if use_phrase_extract else pred_mats_raw

    return {
        "file": str(fp),
        "file_size_bytes": fp.stat().st_size,
        "item_count": len(pred_mats),
        "item_count_raw": len(pred_mats_raw),
        "time_sec": dt,
        "project_name": result.project_name,
        "doc_id": result.doc_id,
        "first_5_items": pred_mats[:5],
    }


def _summarize(results: list[dict]) -> dict:
    valid = [r for r in results if "error" not in r]
    if not valid:
        return {"error": "no valid results"}
    total_gold = sum(r["gold_count"] for r in valid)
    total_pred = sum(r["pred_count"] for r in valid)
    total_tp = sum(r["tp"] for r in valid)
    total_fp = sum(r["fp"] for r in valid)
    total_fn = sum(r["fn"] for r in valid)
    macro_p = sum(r["precision"] for r in valid) / len(valid)
    macro_r = sum(r["recall"] for r in valid) / len(valid)
    macro_f1 = sum(r["f1"] for r in valid) / len(valid)
    micro_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    micro_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) else 0.0
    return {
        "n_files": len(valid),
        "total_gold": total_gold,
        "total_pred": total_pred,
        "macro_precision": macro_p,
        "macro_recall": macro_r,
        "macro_f1": macro_f1,
        "micro_precision": micro_p,
        "micro_recall": micro_r,
        "micro_f1": micro_f1,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Z1 honest eval with phrase extraction + asymmetric matcher")
    parser.add_argument("--enquiry", help="Single enquiry ID")
    parser.add_argument("--no-phrase-extract", action="store_true", help="Disable phrase extraction")
    parser.add_argument("--held-out", help="Path to a held-out RFQ (must not be in swa_enquiries/)")
    parser.add_argument("--containment-threshold", type=float, default=0.8, help="Containment threshold (default 0.8)")
    parser.add_argument(
        "--jaccard-threshold", type=float, default=0.6, help="Jaccard threshold (default 0.6, never <0.6)"
    )
    parser.add_argument("--verbose", action="store_true", help="Detailed per-file output")
    parser.add_argument("--output", default=str(OUTPUT_PATH), help="Output JSON path")
    args = parser.parse_args()

    if args.jaccard_threshold < 0.6:
        print(f"ERROR: jaccard-threshold must be >= 0.6 (Z1 constraint). Got {args.jaccard_threshold}.")
        return 2

    print("=" * 70)
    print("Z1 HONEST EVAL — Phrase extraction + asymmetric matcher")
    print("=" * 70)
    print(f"  phrase_extract: {not args.no_phrase_extract}")
    print(f"  containment_threshold: {args.containment_threshold}")
    print(f"  jaccard_threshold: {args.jaccard_threshold} (frozen >= 0.6)")
    print()

    pipeline = Pipeline()
    enquiries = ENQUIRIES
    if args.enquiry:
        if args.enquiry not in ENQUIRIES:
            print(f"Unknown enquiry: {args.enquiry}")
            return 1
        enquiries = {args.enquiry: ENQUIRIES[args.enquiry]}

    results: list[dict] = []
    for eid, info in enquiries.items():
        print(f"  {eid}...", end=" ", flush=True)
        r = evaluate_enquiry_v2(
            eid,
            info,
            pipeline,
            use_phrase_extract=not args.no_phrase_extract,
            containment_threshold=args.containment_threshold,
            jaccard_threshold=args.jaccard_threshold,
            verbose=args.verbose,
        )
        results.append(r)
        if "error" in r:
            print(f"ERROR: {r['error']}")
        else:
            print(
                f"F1={r['f1']:.1%} (P={r['precision']:.1%}, R={r['recall']:.1%}) "
                f"[{r['gold_count']} gold, {r['pred_count']} pred] {r['time_sec']:.1f}s"
            )

    summary = _summarize(results)
    print()
    print("=" * 70)
    print("SUMMARY (Z1)")
    print("=" * 70)
    if "error" not in summary:
        print(f"Files: {summary['n_files']}")
        print(
            f"Micro P/R/F1: {summary['micro_precision']:.1%} / {summary['micro_recall']:.1%} / {summary['micro_f1']:.1%}"
        )
        print(
            f"Macro P/R/F1: {summary['macro_precision']:.1%} / {summary['macro_recall']:.1%} / {summary['macro_f1']:.1%}"
        )
        pdf = [r for r in results if r.get("type") == "pdf" and "error" not in r]
        xlsx = [r for r in results if r.get("type") == "xlsx" and "error" not in r]
        if pdf:
            print(f"PDF F1 (macro):  {sum(r['f1'] for r in pdf) / len(pdf):.1%} ({len(pdf)} files)")
        if xlsx:
            print(f"XLSX F1 (macro): {sum(r['f1'] for r in xlsx) / len(xlsx):.1%} ({len(xlsx)} files)")

    held_out_result: dict | None = None
    if args.held_out:
        print()
        print("=" * 70)
        print(f"HELD-OUT: {args.held_out}")
        print("=" * 70)
        held_out_result = evaluate_held_out(args.held_out, pipeline, use_phrase_extract=not args.no_phrase_extract)
        if "error" in held_out_result:
            print(f"ERROR: {held_out_result['error']}")
        else:
            print(f"  size: {held_out_result['file_size_bytes']:,} bytes")
            print(f"  items: {held_out_result['item_count']} (raw: {held_out_result['item_count_raw']})")
            print(f"  time: {held_out_result['time_sec']:.1f}s")
            print(f"  project_name: {held_out_result['project_name']}")
            print(f"  doc_id: {held_out_result['doc_id']}")
            for it in held_out_result["first_5_items"]:
                print(f"    - {it[:100]}")

    out = {
        "results": results,
        "summary": summary,
        "held_out": held_out_result,
        "config": {
            "phrase_extract": not args.no_phrase_extract,
            "containment_threshold": args.containment_threshold,
            "jaccard_threshold": args.jaccard_threshold,
        },
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out, indent=2, default=str))
    print()
    print(f"Saved: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
