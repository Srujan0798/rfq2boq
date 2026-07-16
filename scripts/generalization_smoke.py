#!/usr/bin/env python3
"""
Generalization smoke harness.

Run the pipeline on unseen real tenders (additional_real/ or any new files you provide)
and produce honest, reproducible output.

Usage:
  python3 scripts/generalization_smoke.py --dir data/real_rfqs/additional_real --limit 5 --out results/generalization_smoke.md
  python3 scripts/generalization_smoke.py --files data/real_rfqs/additional_real/rfq_bridge_RFQ1900_045.pdf data/real_rfqs/additional_real/some_other.pdf

This is the tool for "prove it works on new PDFs" without ever tuning to the 10 SWA sacred files.
It reports counts, timings, sample rows, and flags obvious junk (empty material, 0 qty, etc).

Never use this to chase % on the 10. The 10 are only for final held-out reporting via validate_product.py.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

# Allow running as `python3 scripts/generalization_smoke.py` without install
sys.path.insert(0, str(Path(__file__).parent.parent))

# Robust direct load of the Pipeline class (avoids any package/attribute lookup issues
# seen in some run environments; the module source defines `class Pipeline`).
import types

_pipeline_mod = types.ModuleType("pipeline")
exec((Path(__file__).parent.parent / "src" / "pipeline.py").read_text(), _pipeline_mod.__dict__)
Pipeline = _pipeline_mod.Pipeline


def run_on_file(pipeline: Pipeline, path: Path) -> dict[str, Any]:
    start = time.time()
    try:
        result = pipeline.run(str(path))
        dt = time.time() - start
        items = result.boq_items
        sample = []
        for r in items[:5]:
            sample.append(
                {
                    "item_no": r.item_no,
                    "material": r.material[:80] if r.material else "",
                    "quantity": float(r.quantity),
                    "unit": r.unit,
                }
            )
        bad_count = sum(
            1 for r in items if (not r.material or not r.material.strip()) or (r.quantity <= 0 and not r.rate_only)
        )
        return {
            "file": path.name,
            "full_path": str(path),
            "items": len(items),
            "time_sec": round(dt, 1),
            "sample": sample,
            "bad_rows": bad_count,
            "error": None,
        }
    except Exception as e:
        dt = time.time() - start
        return {
            "file": path.name,
            "full_path": str(path),
            "items": 0,
            "time_sec": round(dt, 1),
            "sample": [],
            "bad_rows": 0,
            "error": str(e),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generalization smoke on unseen real tenders")
    parser.add_argument(
        "--dir", type=str, default=None, help="Directory of PDFs/XLSX to run (will pick .pdf and .xlsx)"
    )
    parser.add_argument("--files", nargs="*", default=None, help="Explicit list of files")
    parser.add_argument("--limit", type=int, default=5, help="Max files from --dir")
    parser.add_argument("--out", type=str, default="results/generalization_smoke.md", help="Output markdown report")
    args = parser.parse_args()

    files: list[Path] = []
    if args.files:
        files = [Path(f) for f in args.files if Path(f).exists()]
    elif args.dir:
        d = Path(args.dir)
        cands = sorted(list(d.glob("*.pdf")) + list(d.glob("*.xlsx")) + list(d.glob("*.xls")))
        files = cands[: args.limit]
    else:
        parser.error("Provide --dir or --files")

    if not files:
        print("No files found.")
        return

    print(f"Generalization smoke on {len(files)} unseen file(s)...")
    p = Pipeline()

    results = []
    for f in files:
        print(f"  Running {f.name} ...")
        res = run_on_file(p, f)
        results.append(res)
        print(f"    -> {res['items']} items in {res['time_sec']}s (bad={res['bad_rows']})")

    # Write JSON
    out_json = Path("results/generalization_smoke.json")
    out_json.parent.mkdir(exist_ok=True)
    out_json.write_text(json.dumps({"date": str(date.today()), "results": results}, indent=2))

    # Write MD
    lines = [
        "# Generalization Smoke Report",
        "",
        f"**Date:** {date.today().isoformat()}",
        "**Purpose:** Honest run on files the pipeline was never tuned or given gold for.",
        "**Rule:** These files are *not* the 10 SWA sacred. Improvements must help here before claiming progress.",
        "",
        "## Summary",
        "",
        f"- Files run: {len(results)}",
        f"- Total items across all: {sum(r['items'] for r in results)}",
        f"- Files with errors: {sum(1 for r in results if r['error'])}",
        "",
        "## Per-file",
        "",
    ]
    for r in results:
        lines.append(f"### {r['file']}")
        lines.append(f"- Items: {r['items']}")
        lines.append(f"- Time: {r['time_sec']}s")
        lines.append(f"- Bad rows (empty material or invalid qty): {r['bad_rows']}")
        if r["error"]:
            lines.append(f"- **ERROR:** {r['error']}")
        else:
            lines.append("- Sample rows:")
            for s in r["sample"]:
                lines.append(f"  - {s['item_no']}. {s['material']} | {s['quantity']} {s['unit']}")
        lines.append("")

    lines.append("## Notes for next steps")
    lines.append(
        "- If a file produces 0 or very few usable rows: investigate page classification, table detection (pdfplumber fallback), or NER recall on that vocabulary."
    )
    lines.append("- Never add special cases for particular filenames. Fix the general layers.")
    lines.append(
        "- After owner 09/10 sign-off + retrain, re-run this smoke on a fresh batch of additional_real to measure real improvement on unseen."
    )
    lines.append("")

    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {args.out} and results/generalization_smoke.json")
    print("Use this to drive fixes on real new tenders.")


if __name__ == "__main__":
    main()
