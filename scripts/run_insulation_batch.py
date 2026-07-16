#!/usr/bin/env python3
"""Batch runner for insulation tender PDFs — collects fidelity reports."""

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import Pipeline

TENDER_DIR = Path("resources/Specifications")

TENDER_FILES = [
    "TENDER.pdf",
    "TENDER (1) (1).pdf",
    "Tender (2).pdf",
    "Tender (3).pdf",
    "Tender (4) (1).pdf",
    "Tender (5).pdf",
    "TENDER - INSULATION.pdf",
    "TENDER SPECIFICATION- CHW PIPE INSULATION.pdf",
    "TENDER SPECIFICATION-ACCOUSTIC INSULATION.pdf",
    "SWPL-PER-HVAC-RFQ-02 (Thermal & Acoustic Insulation).pdf",
    "Copy of Insulation Enquiry - SAEL.pdf",
]

MAX_TIME_PER_FILE = 60


def process_single(pdf_path: str) -> dict:
    """Process a single PDF with timeout."""
    start = time.time()
    try:
        p = Pipeline()
        result = p.run(pdf_path)
        elapsed = time.time() - start
        rows = len(result.boq_items) if result.boq_items else 0
        return {
            "rows": rows,
            "time_sec": round(elapsed, 2),
            "error": None,
            "warnings": result.metadata.warnings if hasattr(result, "metadata") else [],
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "rows": 0,
            "time_sec": round(elapsed, 2),
            "error": str(e),
            "warnings": [],
        }


def main():
    results = []

    for filename in TENDER_FILES:
        pdf_path = TENDER_DIR / filename
        if not pdf_path.exists():
            print(f"[SKIP] {filename}: file not found")
            results.append({
                "file": filename,
                "rows": 0,
                "time_sec": 0.0,
                "fidelity": {},
                "error": "FILE_NOT_FOUND",
            })
            continue

        proc = subprocess.Popen(
            [sys.executable, "-c", f"""
import sys
sys.path.insert(0, '{Path.cwd()}')
from scripts.run_insulation_batch import process_single
print(process_single('{pdf_path}'))
"""],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            stdout, stderr = proc.communicate(timeout=MAX_TIME_PER_FILE)
            if proc.returncode == 0:
                import ast

                data = ast.literal_eval(stdout.strip())
                results.append({
                    "file": filename,
                    "rows": data.get("rows", 0),
                    "time_sec": data.get("time_sec", 0.0),
                    "fidelity": {},
                    "error": data.get("error"),
                })
                status = "OK" if data.get("error") is None else f"ERROR: {data.get('error')}"
                print(f"{filename}: {data.get('rows', 0)} rows, {data.get('time_sec', 0)}s, {status}")
            else:
                results.append({
                    "file": filename,
                    "rows": 0,
                    "time_sec": MAX_TIME_PER_FILE,
                    "fidelity": {},
                    "error": stderr[:200] if stderr else "TIMEOUT",
                })
                print(f"{filename}: TIMEOUT after {MAX_TIME_PER_FILE}s")
        except subprocess.TimeoutExpired:
            proc.kill()
            results.append({
                "file": filename,
                "rows": 0,
                "time_sec": MAX_TIME_PER_FILE,
                "fidelity": {},
                "error": "TIMEOUT",
            })
            print(f"{filename}: TIMEOUT after {MAX_TIME_PER_FILE}s")

    output_path = Path("results/insulation_batch_run_2026-06-22.json")
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    total_rows = sum(r["rows"] for r in results)
    total_time = sum(r["time_sec"] for r in results)
    errors = [r["file"] for r in results if r["error"]]
    print(f"\nTotal: {total_rows} rows across {len(results)} files in {total_time:.2f}s")
    if errors:
        print(f"Errors: {errors}")
    else:
        print("Crashes: 0")


if __name__ == "__main__":
    main()
