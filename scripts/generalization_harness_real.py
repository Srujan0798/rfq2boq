#!/usr/bin/env python3
"""Generalization harness: run pipeline on REAL unseen RFQs only (skip empty placeholders)."""

from __future__ import annotations

import json
import signal
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import Pipeline

UNSEEN_DIR = Path("data/real_rfqs/additional_real")
RESULTS_DIR = Path("results/generalization")
MIN_SIZE = 1000  # Skip empty placeholder PDFs
MAX_SIZE = 10_000_000  # Skip very large PDFs (>10MB)
PER_FILE_TIMEOUT = 120  # Max seconds per file


class TimeoutError(Exception):
    pass


def _timeout_handler(signum, frame):
    raise TimeoutError(f"File processing exceeded {PER_FILE_TIMEOUT}s")


def run_harness() -> None:
    if not UNSEEN_DIR.exists():
        print(f"Unseen RFQ directory not found: {UNSEEN_DIR}")
        sys.exit(1)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Only real PDFs (1KB < size < 10MB)
    all_files = sorted([f for f in UNSEEN_DIR.rglob("*.pdf") if MIN_SIZE < f.stat().st_size < MAX_SIZE])
    print(f"Found {len(all_files)} real PDFs ({MIN_SIZE/1024:.0f}KB < size < {MAX_SIZE/1024/1024:.0f}MB)")
    print()

    pipeline = Pipeline()
    results: list[dict] = []
    total_items = 0
    total_errors = 0
    timeouts = 0

    for i, file_path in enumerate(all_files, 1):
        rel_path = file_path.relative_to(UNSEEN_DIR)
        print(f"[{i}/{len(all_files)}] {rel_path} ... ", end="", flush=True)
        start = time.time()

        # Set per-file timeout
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(PER_FILE_TIMEOUT)

        try:
            result = pipeline.run(str(file_path))
            signal.alarm(0)
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
                        {"material": b.material, "quantity": float(b.quantity), "unit": b.unit}
                        for b in result.boq_items
                    ],
                }
            )
        except TimeoutError:
            signal.alarm(0)
            timeouts += 1
            elapsed = time.time() - start
            print(f"TIMEOUT after {PER_FILE_TIMEOUT}s")
            results.append(
                {
                    "file": str(rel_path),
                    "items": 0,
                    "avg_confidence": 0.0,
                    "time_sec": round(elapsed, 2),
                    "error": "TIMEOUT",
                    "boq_items": [],
                }
            )
        except Exception as e:
            signal.alarm(0)
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
        finally:
            signal.signal(signal.SIGALRM, old_handler)

    success_count = len(all_files) - total_errors - timeouts
    files_with_items = sum(1 for r in results if r["items"] > 0)
    files_empty = sum(1 for r in results if r["items"] == 0 and r["error"] is None)
    avg_items = total_items / success_count if success_count > 0 else 0

    summary = {
        "run_date": datetime.now(UTC).isoformat(),
        "total_files": len(all_files),
        "successful": success_count,
        "errors": total_errors,
        "timeouts": timeouts,
        "files_with_items": files_with_items,
        "files_empty": files_empty,
        "total_items_extracted": total_items,
        "avg_items_per_file": round(avg_items, 2),
        "results": results,
    }

    summary_path = RESULTS_DIR / "generalization_real_report.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{'='*60}")
    print("GENERALIZATION HARNESS (REAL PDFs ONLY)")
    print(f"{'='*60}")
    print(f"Total real PDFs:  {len(all_files)}")
    print(f"Successful:       {success_count}")
    print(f"Errors:           {total_errors}")
    print(f"Timeouts:         {timeouts}")
    print(f"Files with items: {files_with_items}")
    print(f"Files empty:      {files_empty}")
    print(f"Total items:      {total_items}")
    print(f"Avg items/file:   {avg_items:.1f}")
    print(f"Report saved:     {summary_path}")


if __name__ == "__main__":
    run_harness()
