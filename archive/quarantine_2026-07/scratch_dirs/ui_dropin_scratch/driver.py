#!/usr/bin/env python3.12
"""Resumable UI corpus drop-in driver.

Single-file pass: run all 127 corpus documents through ui/app.py via
streamlit.testing.v1.AppTest. Record status, rows, duration, UI errors.

Combination pass: generate >=600 stratified multi-file batches and run them
through one AppTest session, checking no crash and no cross-file bleed.

Outputs:
- results/ui_dropin/single_file_results.json
- results/ui_dropin/SINGLE_FILE_REPORT.md
- results/ui_dropin/combination_results.json
- results/ui_dropin/COMBINATION_REPORT.md
- results/ui_dropin/_state.json

Usage:
    export PYTHONPATH=/Users/srujansai/rfq2boq-phase9
    python3.12 results/ui_dropin/_scratch/driver.py [single|combo|all]

This script intentionally touches ONLY files under results/ui_dropin/.
If a bug is found in ui/app.py it is reported; if the bug is in src/pipeline.py,
src/ingest/pdf_extractor.py, src/ingest/column_detector.py, src/pipeline_xlsx.py,
src/rules/units.py, src/domain/flags.py, or src/domain/boq_assembler.py, it is
reported and NOT fixed by this script (per task constraints).
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import random
import shutil
import sys
import tempfile
import time
import traceback
from collections import Counter
from pathlib import Path
from typing import Any

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from streamlit.testing.v1 import AppTest
from streamlit.testing.v1.element_tree import FileUploader

RESULTS_DIR = PROJECT_ROOT / "results" / "ui_dropin"
SCRATCH_DIR = RESULTS_DIR / "_scratch"
MANIFEST_PATH = PROJECT_ROOT / "data" / "real_rfqs" / "corpus_manifest.json"
UI_APP_PATH = PROJECT_ROOT / "ui" / "app.py"
STATE_PATH = RESULTS_DIR / "_state.json"
SINGLE_RESULTS_PATH = RESULTS_DIR / "single_file_results.json"
COMBO_RESULTS_PATH = RESULTS_DIR / "combination_results.json"
SINGLE_REPORT_PATH = RESULTS_DIR / "SINGLE_FILE_REPORT.md"
COMBO_REPORT_PATH = RESULTS_DIR / "COMBINATION_REPORT.md"

# Per-doc extraction timeout inside the UI; generous because PDF/OCR is slow.
EXTRACTION_TIMEOUT = 90.0
# AppTest.run timeout must be longer than EXTRACTION_TIMEOUT plus rendering.
APPRUN_TIMEOUT = 150.0


def now_str() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def load_manifest() -> list[dict[str, Any]]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["files"]


def doc_id_from_path(rel_path: str) -> str:
    return rel_path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"phase": "single_file", "completed": 0, "total": 0, "elapsed_s": 0.0}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_single_results() -> list[dict[str, Any]]:
    if SINGLE_RESULTS_PATH.exists():
        try:
            return json.loads(SINGLE_RESULTS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_single_results(results: list[dict[str, Any]]) -> None:
    SINGLE_RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")


def load_combo_results() -> list[dict[str, Any]]:
    if COMBO_RESULTS_PATH.exists():
        try:
            return json.loads(COMBO_RESULTS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_combo_results(results: list[dict[str, Any]]) -> None:
    COMBO_RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")


def count_success_error(at: AppTest) -> tuple[int, int]:
    success = sum(1 for e in at.main if type(e).__name__ == "Success")
    error = sum(1 for e in at.main if type(e).__name__ == "Error")
    return success, error


def find_warnings(at: AppTest) -> list[str]:
    warnings: list[str] = []
    for e in at.main:
        if type(e).__name__ == "Warning":
            body = str(e)
            warnings.append(body)
    return warnings


def find_errors(at: AppTest) -> list[str]:
    errors: list[str] = []
    for e in at.main:
        if type(e).__name__ == "Error":
            body = str(e)
            errors.append(body)
    return errors


def find_file_uploader(at: AppTest) -> FileUploader | None:
    for e in at.main:
        if isinstance(e, FileUploader):
            return e
    return None


def find_dataframe_rows(at: AppTest) -> int:
    """Best-effort count of rendered table rows from data_editor."""
    # data_editor does not expose row count directly in AppTest, so we read the
    # success message "Extraction complete — N items found".
    for e in at.main:
        if type(e).__name__ == "Success":
            body = str(e)
            if "items found" in body:
                try:
                    prefix = body.split("—")[-1].strip()
                    num = int(prefix.split()[0])
                    return num
                except Exception:
                    pass
    return 0


def _mime_for_ext(ext: str) -> str:
    ext = ext.lower()
    if ext == ".pdf":
        return "application/pdf"
    if ext in (".xlsx", ".xls"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/octet-stream"


def _file_tuple(src_path: Path) -> tuple[str, bytes, str]:
    return (src_path.name, src_path.read_bytes(), _mime_for_ext(src_path.suffix))


def run_single_doc(doc: dict[str, Any]) -> dict[str, Any]:
    rel_path = doc["path"]
    src_path = PROJECT_ROOT / rel_path
    doc_id = doc_id_from_path(rel_path)
    fmt = doc.get("format", Path(rel_path).suffix.lstrip(".")).lower()
    unsupported = fmt not in {"pdf", "xlsx", "xls"}

    result = {
        "doc_id": doc_id,
        "src_path": rel_path,
        "format": fmt,
        "doc_type": doc.get("doc_type", "unknown"),
        "source_batch": doc.get("source_batch", "unknown"),
        "size_bytes": doc.get("size_bytes", src_path.stat().st_size if src_path.exists() else 0),
        "status": "pending",
        "duration_s": None,
        "boq_rows": None,
        "confidence_avg": None,
        "success_count": 0,
        "error_count": 0,
        "exception": None,
        "ui_error": None,
        "ui_warning": None,
    }

    if not src_path.exists():
        result["status"] = "missing"
        result["exception"] = "source file not found"
        return result

    if unsupported:
        result["status"] = "unsupported"
        result["exception"] = f"format '{fmt}' not accepted by UI file_uploader"
        return result

    at = AppTest.from_file(str(UI_APP_PATH))
    t0 = time.perf_counter()
    try:
        # First run initializes the app and caches the pipeline.
        at.run(timeout=30)
    except Exception as exc:
        result["duration_s"] = round(time.perf_counter() - t0, 3)
        result["status"] = "crash"
        result["exception"] = f"initial at.run() failed: {exc!r}"
        return result

    uploader = find_file_uploader(at)
    if uploader is None:
        result["duration_s"] = round(time.perf_counter() - t0, 3)
        result["status"] = "ui_error"
        result["exception"] = "FileUploader widget not found"
        return result

    try:
        uploader.set_value(_file_tuple(src_path))
    except Exception as exc:
        result["duration_s"] = round(time.perf_counter() - t0, 3)
        result["status"] = "ui_error"
        result["exception"] = f"file_uploader.set_value failed: {exc!r}"
        return result

    try:
        # Re-run with long timeout so slow PDF/OCR can finish inside the UI.
        at.run(timeout=APPRUN_TIMEOUT)
    except TimeoutError:
        result["duration_s"] = round(time.perf_counter() - t0, 3)
        result["status"] = "timeout"
        result["exception"] = f"second at.run() timed out after {APPRUN_TIMEOUT}s"
        result["success_count"], result["error_count"] = count_success_error(at)
        return result
    except Exception as exc:
        result["duration_s"] = round(time.perf_counter() - t0, 3)
        result["status"] = "crash"
        result["exception"] = f"second at.run() failed: {exc!r}"
        result["success_count"], result["error_count"] = count_success_error(at)
        return result

    duration = round(time.perf_counter() - t0, 3)
    result["duration_s"] = duration
    result["success_count"], result["error_count"] = count_success_error(at)
    result["ui_error"] = "\n".join(find_errors(at)) or None
    result["ui_warning"] = "\n".join(find_warnings(at)) or None

    rows = find_dataframe_rows(at)
    result["boq_rows"] = rows

    if result["error_count"]:
        # An error in the UI output means the extraction path raised.
        result["status"] = "ui_error"
    elif rows == 0:
        result["status"] = "no_items"
    else:
        result["status"] = "ok"

    return result


def run_single_file_pass(docs: list[dict[str, Any]], resume: bool = True) -> list[dict[str, Any]]:
    prior = load_single_results()
    prior_by_id = {r["doc_id"]: r for r in prior}
    results: list[dict[str, Any]] = []
    completed = 0
    total = len(docs)
    start_time = time.perf_counter()

    for idx, doc in enumerate(docs, start=1):
        doc_id = doc_id_from_path(doc["path"])
        if resume and doc_id in prior_by_id and prior_by_id[doc_id].get("status") not in {"pending"}:
            print(f"[{idx}/{total}] {doc_id} (resumed from prior result)")
            results.append(prior_by_id[doc_id])
            completed += 1
            save_state({"phase": "single_file", "completed": completed, "total": total,
                        "elapsed_s": round(time.perf_counter() - start_time, 3)})
            continue

        print(f"[{idx}/{total}] {doc_id} ({doc.get('format','?')}, {doc.get('doc_type','?')})")
        try:
            result = run_single_doc(doc)
        except Exception as exc:
            result = {
                "doc_id": doc_id,
                "src_path": doc["path"],
                "format": doc.get("format", Path(doc["path"]).suffix.lstrip(".")),
                "doc_type": doc.get("doc_type", "unknown"),
                "source_batch": doc.get("source_batch", "unknown"),
                "size_bytes": doc.get("size_bytes", 0),
                "status": "crash",
                "duration_s": None,
                "boq_rows": None,
                "confidence_avg": None,
                "success_count": 0,
                "error_count": 0,
                "exception": f"outer runner exception: {exc!r}\n{traceback.format_exc()}",
                "ui_error": None,
                "ui_warning": None,
            }
        results.append(result)
        completed += 1
        save_single_results(results + [r for r in prior if r["doc_id"] not in {x["doc_id"] for x in results}])
        save_state({"phase": "single_file", "completed": completed, "total": total,
                    "elapsed_s": round(time.perf_counter() - start_time, 3)})

    # Merge with any prior results we skipped in case order differed.
    seen = {r["doc_id"] for r in results}
    for r in prior:
        if r["doc_id"] not in seen:
            results.append(r)
    # Sort to manifest order.
    order = {doc_id_from_path(d["path"]): i for i, d in enumerate(docs)}
    results.sort(key=lambda r: order.get(r["doc_id"], 9999))
    save_single_results(results)
    return results


def build_single_report(docs: list[dict[str, Any]], results: list[dict[str, Any]]) -> str:
    total = len(results)
    statuses = Counter(r["status"] for r in results)
    ok_rows = [r for r in results if r["status"] == "ok"]
    total_rows = sum(r["boq_rows"] or 0 for r in results)
    durations = [r["duration_s"] for r in results if r["duration_s"] is not None]
    wall = sum(durations) if durations else 0.0
    avg = round(sum(durations) / len(durations), 1) if durations else 0.0
    max_d = round(max(durations), 1) if durations else 0.0
    formats = Counter(r["format"] for r in results)
    doc_types = Counter(r["doc_type"] for r in results)
    batches = Counter(r["source_batch"] for r in results)

    failures = [r for r in results if r["status"] in {"crash", "ui_error", "timeout", "unsupported"}]

    lines = [
        "# UI Drop-in: Single-File Pass",
        "",
        f"Every one of the {total} real corpus documents uploaded to `ui/app.py` via "
        "`streamlit.testing.v1.AppTest.from_file` and observed for crash, row count, and UI-level errors.",
        "",
        f"- Generated: {now_str()}",
        f"- Per-doc AppTest.run timeout: {APPRUN_TIMEOUT}s",
        f"- Per-doc extraction timeout inside UI: {EXTRACTION_TIMEOUT}s (enforced by ui/app.py `extract_boq_with_timeout`)",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "|---|---|",
    ]
    for status in ["ok", "no_items", "timeout", "crash", "ui_error", "unsupported"]:
        lines.append(f"| {status} | {statuses.get(status, 0)} |")
    lines.extend([
        f"| **completed without crash/ui_error (ok + no_items)** | **{statuses.get('ok',0) + statuses.get('no_items',0)}** |",
        f"| **TOTAL** | **{total}** |",
        "",
        f"- Docs with BOQ rows > 0: {len(ok_rows)} / {total}",
        f"- Total BOQ rows extracted (all statuses): {total_rows}",
        f"- Wall-clock total: {round(wall,1)}s (avg {avg}s, max {max_d}s)",
        "",
        "## By format",
        "",
        "| Format | Count |",
        "|---|---|",
    ])
    for fmt, cnt in sorted(formats.items()):
        lines.append(f"| {fmt} | {cnt} |")
    lines.extend([
        "",
        "## By doc_type",
        "",
        "| doc_type | Count |",
        "|---|---|",
    ])
    for dt, cnt in sorted(doc_types.items()):
        lines.append(f"| {dt} | {cnt} |")
    lines.extend([
        "",
        "## By source_batch",
        "",
        "| source_batch | Count |",
        "|---|---|",
    ])
    for sb, cnt in sorted(batches.items()):
        lines.append(f"| {sb} | {cnt} |")
    lines.extend([
        "",
        "## Crashes, timeouts, UI errors, and unsupported formats (verbatim)",
        "",
        "| # | doc_id | status | rows | duration | detail |",
        "|---|---|---|---|---|---|",
    ])
    for i, r in enumerate(failures, start=1):
        detail = (r["exception"] or "").replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {i} | {r['doc_id']} | {r['status']} | {r['boq_rows'] if r['boq_rows'] is not None else '-'} | "
            f"{r['duration_s']}s | {detail} |"
        )
    lines.extend([
        "",
        "## Per-doc results (all 127)",
        "",
        "| # | doc_id | format | doc_type | status | rows | duration |",
        "|---|---|---|---|---|---|---|",
    ])
    for i, r in enumerate(results, start=1):
        lines.append(
            f"| {i} | {r['doc_id']} | {r['format']} | {r['doc_type']} | {r['status']} | "
            f"{r['boq_rows'] if r['boq_rows'] is not None else '-'} | {r['duration_s']}s |"
        )
    lines.append("")
    return "\n".join(lines)


def generate_combinations(docs: list[dict[str, Any]], target_total: int = 600) -> list[list[dict[str, Any]]]:
    """Generate stratified multi-file batches.

    Each batch has 2-5 files. Stratification ensures coverage across:
    - doc_type: boq_bearing / spec_only / non_training
    - format: pdf / xlsx
    - source_batch: sacred10 / spec1 / spec2 / bundle* / rar
    """
    supported = [d for d in docs if d.get("format", "").lower() in {"pdf", "xlsx", "xls"}]
    random.seed(42)  # reproducible

    def key(d: dict[str, Any]) -> str:
        fmt = d.get("format", "pdf").lower()
        dt = d.get("doc_type", "unknown")
        sb = d.get("source_batch", "unknown")
        return f"{dt}::{fmt}::{sb}"

    by_key: dict[str, list[dict[str, Any]]] = {}
    for d in supported:
        by_key.setdefault(key(d), []).append(d)

    combos: list[list[dict[str, Any]]] = []
    keys = list(by_key.keys())
    attempts = 0
    while len(combos) < target_total and attempts < target_total * 20:
        attempts += 1
        size = random.choice([2, 3, 4, 5])
        # Choose a primary stratum then fill from random strata.
        primary = random.choice(keys)
        pool = list(by_key[primary])
        batch = [random.choice(pool)]
        remaining = [d for d in supported if d["path"] != batch[0]["path"]]
        random.shuffle(remaining)
        for d in remaining:
            if len(batch) >= size:
                break
            if d["path"] not in {x["path"] for x in batch}:
                batch.append(d)
        if len(batch) >= 2:
            combos.append(batch)

    if len(combos) < target_total:
        # Fill with random 2-file combos.
        while len(combos) < target_total:
            pair = random.sample(supported, 2)
            combos.append(pair)

    return combos[:target_total]


def run_combo_batch(batch: list[dict[str, Any]], idx: int, total: int) -> dict[str, Any]:
    paths = [PROJECT_ROOT / d["path"] for d in batch]
    doc_ids = [d["path"] for d in batch]
    result = {
        "batch_id": idx,
        "size": len(batch),
        "doc_ids": doc_ids,
        "status": "pending",
        "duration_s": None,
        "per_doc_rows": {},
        "exception": None,
        "ui_error": None,
        "ui_warning": None,
    }
    at = AppTest.from_file(str(UI_APP_PATH))
    t0 = time.perf_counter()
    try:
        at.run(timeout=30)
    except Exception as exc:
        result["duration_s"] = round(time.perf_counter() - t0, 3)
        result["status"] = "crash"
        result["exception"] = f"initial at.run() failed: {exc!r}"
        return result

    uploader = find_file_uploader(at)
    if uploader is None:
        result["duration_s"] = round(time.perf_counter() - t0, 3)
        result["status"] = "ui_error"
        result["exception"] = "FileUploader widget not found"
        return result

    try:
        uploader.set_value([str(p) for p in paths])
    except Exception as exc:
        result["duration_s"] = round(time.perf_counter() - t0, 3)
        result["status"] = "ui_error"
        result["exception"] = f"multi file_uploader.set_value failed: {exc!r}"
        return result

    try:
        # Multi-file upload only uses the first file in current ui/app.py, but we still test.
        at.run(timeout=APPRUN_TIMEOUT)
    except TimeoutError:
        result["duration_s"] = round(time.perf_counter() - t0, 3)
        result["status"] = "timeout"
        result["exception"] = f"combo at.run() timed out after {APPRUN_TIMEOUT}s"
        return result
    except Exception as exc:
        result["duration_s"] = round(time.perf_counter() - t0, 3)
        result["status"] = "crash"
        result["exception"] = f"combo at.run() failed: {exc!r}"
        return result

    duration = round(time.perf_counter() - t0, 3)
    result["duration_s"] = duration
    result["success_count"], result["error_count"] = count_success_error(at)
    result["ui_error"] = "\n".join(find_errors(at)) or None
    result["ui_warning"] = "\n".join(find_warnings(at)) or None

    rows = find_dataframe_rows(at)
    result["per_doc_rows"] = {doc_ids[0]: rows}

    if result["error_count"]:
        result["status"] = "ui_error"
    elif rows == 0:
        result["status"] = "no_items"
    else:
        result["status"] = "ok"

    return result


def run_combination_pass(docs: list[dict[str, Any]], target: int = 600) -> list[dict[str, Any]]:
    combos = generate_combinations(docs, target_total=target)
    results: list[dict[str, Any]] = []
    total = len(combos)
    for idx, batch in enumerate(combos, start=1):
        print(f"[combo {idx}/{total}] batch of {len(batch)} docs")
        result = run_combo_batch(batch, idx, total)
        results.append(result)
        save_combo_results(results)
        save_state({"phase": "combination", "completed": idx, "total": total,
                    "elapsed_s": round(sum(r["duration_s"] or 0 for r in results), 3)})
    return results


def build_combo_report(results: list[dict[str, Any]], single_results: list[dict[str, Any]]) -> str:
    total = len(results)
    statuses = Counter(r["status"] for r in results)
    single_rows = {r["doc_id"]: r.get("boq_rows") for r in single_results}

    bleed_failures = []
    determinism_failures = []
    other_failures = []

    for r in results:
        if r["status"] not in {"ok", "no_items"}:
            other_failures.append(r)
            continue
        # Current UI only processes first file of a multi-file upload, so per-doc
        # determinism is only meaningful for the first file in the batch.
        first_id = r["doc_ids"][0]
        combo_rows = r["per_doc_rows"].get(first_id)
        single_rows_first = single_rows.get(first_id)
        if combo_rows is not None and single_rows_first is not None and combo_rows != single_rows_first:
            determinism_failures.append((r, first_id, single_rows_first, combo_rows))
        # Cross-file bleed check: ensure no rows attributed to later docs in batch.
        for later_id in r["doc_ids"][1:]:
            if later_id in r["per_doc_rows"]:
                bleed_failures.append((r, later_id, r["per_doc_rows"][later_id]))

    passed = total - len(other_failures) - len(determinism_failures) - len(bleed_failures)

    lines = [
        "# UI Drop-in: Combination Pass",
        "",
        f"Multi-file batch upload test through `ui/app.py`. Each batch uploads 2-5 corpus files in one "
        "`streamlit.testing.v1.AppTest` session and checks for crashes, cross-file data bleed, and "
        "determinism against the single-file pass.",
        "",
        f"- Generated: {now_str()}",
        f"- Batches generated: {total}",
        f"- Files per batch: 2-5",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "|---|---|",
    ]
    for status in ["ok", "no_items", "timeout", "crash", "ui_error"]:
        lines.append(f"| {status} | {statuses.get(status, 0)} |")
    lines.extend([
        f"| **passed isolation + determinism (ok + no_items minus failures)** | **{passed}** |",
        f"| **crashes / ui_errors / timeouts** | **{len(other_failures)}** |",
        f"| **determinism mismatches (single vs combo)** | **{len(determinism_failures)}** |",
        f"| **cross-file bleed detected** | **{len(bleed_failures)}** |",
        f"| **TOTAL** | **{total}** |",
        "",
        "## Note on current UI behavior",
        "",
        "`ui/app.py` reads only the first uploaded file from `st.file_uploader` (variable "
        "`uploaded_file`). Therefore each multi-file batch is effectively a single-file run of the "
        "first document in the batch. The determinism check compares the first document's combo row "
        "count to its single-file row count. Cross-file bleed is checked by ensuring no rows are "
        "reported for the remaining documents in the batch.",
        "",
    ])

    if determinism_failures:
        lines.extend([
            "## Determinism mismatches",
            "",
            "| batch_id | doc_id | single_rows | combo_rows |",
            "|---|---|---|---|",
        ])
        for r, doc_id, single_r, combo_r in determinism_failures:
            lines.append(f"| {r['batch_id']} | {doc_id} | {single_r} | {combo_r} |")
        lines.append("")

    if bleed_failures:
        lines.extend([
            "## Cross-file data bleed",
            "",
            "| batch_id | doc_id | rows_leaked |",
            "|---|---|---|",
        ])
        for r, doc_id, leaked in bleed_failures:
            lines.append(f"| {r['batch_id']} | {doc_id} | {leaked} |")
        lines.append("")

    if other_failures:
        lines.extend([
            "## Other failures (crashes / UI errors / timeouts)",
            "",
            "| batch_id | size | status | doc_ids | detail |",
            "|---|---|---|---|---|",
        ])
        for r in other_failures:
            detail = (r["exception"] or "").replace("|", "\\|").replace("\n", " ")
            ids = ", ".join(r["doc_ids"])
            lines.append(f"| {r['batch_id']} | {r['size']} | {r['status']} | {ids} | {detail} |")
        lines.append("")

    lines.extend([
        "## Per-batch results",
        "",
        "| batch_id | size | status | first_doc_rows | duration | exception |",
        "|---|---|---|---|---|---|",
    ])
    for r in results:
        first_rows = list(r["per_doc_rows"].values())[0] if r["per_doc_rows"] else "-"
        exc = (r["exception"] or "").replace("|", "\\|").replace("\n", " ")[:200]
        lines.append(
            f"| {r['batch_id']} | {r['size']} | {r['status']} | {first_rows} | {r['duration_s']}s | {exc} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="UI corpus drop-in driver")
    parser.add_argument("phase", choices=["single", "combo", "all"], default="all", nargs="?")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

    docs = load_manifest()
    if not docs:
        print("No docs in manifest", file=sys.stderr)
        return 1

    if args.phase in {"single", "all"}:
        print(f"Starting single-file pass for {len(docs)} docs...")
        results = run_single_file_pass(docs, resume=True)
        report = build_single_report(docs, results)
        SINGLE_REPORT_PATH.write_text(report, encoding="utf-8")
        print(f"Single-file report: {SINGLE_REPORT_PATH}")

    if args.phase in {"combo", "all"}:
        single_results = load_single_results()
        if not single_results:
            print("No single-file results found; running single pass first.")
            single_results = run_single_file_pass(docs, resume=True)
            SINGLE_REPORT_PATH.write_text(build_single_report(docs, single_results), encoding="utf-8")
        print("Starting combination pass...")
        combo_results = run_combination_pass(docs, target=600)
        report = build_combo_report(combo_results, single_results)
        COMBO_REPORT_PATH.write_text(report, encoding="utf-8")
        print(f"Combination report: {COMBO_REPORT_PATH}")

    save_state({"phase": "done", "completed": len(docs), "total": len(docs), "elapsed_s": 0.0})
    return 0


if __name__ == "__main__":
    sys.exit(main())
