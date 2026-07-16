#!/usr/bin/env python3
"""Generalization harness: run pipeline on unseen RFQs and report results.

Usage:
    python scripts/generalization_harness.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import Pipeline

UNSEEN_DIR = Path("data/real_rfqs/additional_real")
RESULTS_DIR = Path("results/generalization")


def run_harness() -> None:
    if not UNSEEN_DIR.exists():
        print(f"Unseen RFQ directory not found: {UNSEEN_DIR}")
        sys.exit(1)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(UNSEEN_DIR.rglob("*.pdf"))
    xlsx_files = sorted(UNSEEN_DIR.rglob("*.xlsx")) + sorted(UNSEEN_DIR.rglob("*.xls"))
    all_files = pdf_files + xlsx_files

    print(f"Found {len(pdf_files)} PDFs, {len(xlsx_files)} XLSX files")
    print(f"Total: {len(all_files)} files to process\n")

    pipeline = Pipeline()
    results: list[dict] = []
    total_items = 0
    total_errors = 0

    for i, file_path in enumerate(all_files, 1):
        rel_path = file_path.relative_to(UNSEEN_DIR)
        print(f"[{i}/{len(all_files)}] {rel_path} ... ", end="", flush=True)
        start = time.time()
        try:
            result = pipeline.run(str(file_path))
            elapsed = time.time() - start
            item_count = len(result.boq_items)
            avg_conf = result.metadata.avg_confidence if result.metadata else 0.0
            total_items += item_count
            print(f"{item_count} items, avg_conf={avg_conf:.2f}, {elapsed:.1f}s")
            results.append(
                {
                    "file": str(rel_path),
                    "items": item_count,
                    "avg_confidence": round(avg_conf, 3),
                    "time_sec": round(elapsed, 2),
                    "error": None,
                    "boq_items": [
                        {
                            "material": b.material,
                            "quantity": float(b.quantity) if b.quantity is not None else 0,
                            "unit": b.unit,
                            "confidence": round(b.confidence, 3),
                        }
                        for b in result.boq_items
                    ],
                }
            )
        except Exception as e:
            elapsed = time.time() - start
            total_errors += 1
            print(f"ERROR: {e}")
            results.append(
                {
                    "file": str(rel_path),
                    "items": 0,
                    "avg_confidence": 0.0,
                    "time_sec": round(elapsed, 2),
                    "error": f"{type(e).__name__}: {e}",
                    "boq_items": [],
                }
            )

    # Summary statistics
    success_count = len(all_files) - total_errors
    files_with_items = sum(1 for r in results if r["items"] > 0)
    files_empty = sum(1 for r in results if r["items"] == 0 and r["error"] is None)
    avg_items_per_file = total_items / success_count if success_count > 0 else 0

    summary = {
        "run_date": datetime.now(UTC).isoformat(),
        "total_files": len(all_files),
        "successful": success_count,
        "errors": total_errors,
        "files_with_items": files_with_items,
        "files_empty": files_empty,
        "total_items_extracted": total_items,
        "avg_items_per_file": round(avg_items_per_file, 2),
        "results": results,
    }

    summary_path = RESULTS_DIR / "generalization_report.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{'='*60}")
    print("GENERALIZATION HARNESS COMPLETE")
    print(f"{'='*60}")
    print(f"Total files:      {len(all_files)}")
    print(f"Successful:       {success_count}")
    print(f"Errors:           {total_errors}")
    print(f"Files with items: {files_with_items}")
    print(f"Files empty:      {files_empty}")
    print(f"Total items:      {total_items}")
    print(f"Avg items/file:   {avg_items_per_file:.1f}")
    print(f"Report saved:     {summary_path}")

    # Write a human-readable markdown summary
    md_path = RESULTS_DIR / "generalization_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Generalization Harness Report\n\n")
        f.write(f"**Run date:** {datetime.now(UTC).isoformat()}\n\n")
        f.write("## Summary\n\n")
        f.write("| Metric | Value |\n|---|---|\n")
        f.write(f"| Total files | {len(all_files)} |\n")
        f.write(f"| Successful | {success_count} |\n")
        f.write(f"| Errors | {total_errors} |\n")
        f.write(f"| Files with items | {files_with_items} |\n")
        f.write(f"| Files empty | {files_empty} |\n")
        f.write(f"| Total items extracted | {total_items} |\n")
        f.write(f"| Avg items per file | {avg_items_per_file:.1f} |\n\n")
        f.write("## Per-File Results\n\n")
        f.write("| File | Items | Avg Conf | Time | Error |\n")
        f.write("|---|---|---|---|---|\n")
        for r in results:
            err = r["error"] or "—"
            f.write(f"| {r['file']} | {r['items']} | {r['avg_confidence']:.2f} | {r['time_sec']:.1f}s | {err} |\n")

    print(f"Markdown saved:   {md_path}")


if __name__ == "__main__":
    run_harness()
