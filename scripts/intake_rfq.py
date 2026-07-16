#!/usr/bin/env python3
"""Standing intake command for a NEW RFQ from SWA.

Usage:
    python3 scripts/intake_rfq.py <file> --source "email from X" --client "Y"

What it does:
  1. sha256 the file → duplicate check against corpus_manifest.json (refuses if known)
  2. copies into data/real_rfqs/incoming/<date>/<filename>
  3. appends a manifest entry (sha256, provenance, date, doc_type=pending, split)
  4. assigns split per the frozen POLICY (TRAIN default; every 5th → DEV; never TEST)
  5. runs the pipeline (XLSX or PDF) + emits an intake report (rows, flags, needs?)
  6. never crashes on unprocessable formats → manifest entry + needs_conversion flag

Split policy (docs/CORPUS_DEFINITION.md):
  - new docs default to TRAIN
  - every 5th intake (by counter in manifest) → DEV
  - TEST stays frozen at 42 forever — NO code path assigns test
  - the intake fidelity audit is how new-doc generalization is measured, not by growing TEST
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path.cwd()
MANIFEST_PATH = REPO_ROOT / "data/real_rfqs/corpus_manifest.json"
SPLIT_PATH = REPO_ROOT / "data/real_rfqs/split_test.json"
INCOMING_DIR = REPO_ROOT / "data/real_rfqs/incoming"
DOC_EXTS = {".pdf": "pdf", ".xlsx": "xlsx", ".xls": "xlsx", ".doc": "doc", ".docx": "docx"}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: Path | None = None) -> dict:
    return json.loads((path or MANIFEST_PATH).read_text())


def save_manifest(manifest: dict, path: Path | None = None) -> None:
    (path or MANIFEST_PATH).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def find_duplicate(manifest: dict, sha: str) -> dict | None:
    for f in manifest["files"]:
        if f["sha256"] == sha:
            return f
    return None


def assign_split(manifest: dict) -> str:
    """Frozen policy: TRAIN default; every 5th intake → DEV; never TEST."""
    n = len(manifest["files"])
    # every 5th NEW doc (counting from the current total) → DEV
    if (n + 1) % 5 == 0:
        return "dev"
    return "train"


def run_pipeline(path: Path) -> dict:
    """Run the appropriate pipeline; return a report dict. Never raises."""
    try:
        ext = path.suffix.lower()
        if ext in (".xlsx", ".xls"):
            from src.pipeline_xlsx import XLSXRowPipeline

            rows = XLSXRowPipeline().run(str(path))
            return {"rows_extracted": len(rows), "needs_source_truth_count": len(rows) > 0, "error": None}
        if ext == ".pdf":
            from src.pipeline import Pipeline

            result = Pipeline().run(str(path))
            return {
                "rows_extracted": len(result.boq_items),
                "needs_source_truth_count": len(result.boq_items) > 0,
                "error": None,
            }
        return {
            "rows_extracted": 0,
            "needs_source_truth_count": False,
            "error": f"format {ext} not directly processable",
            "needs_conversion": True,
        }
    except Exception as exc:  # noqa: BLE001 — intake must never crash
        return {
            "rows_extracted": 0,
            "needs_source_truth_count": False,
            "error": f"pipeline error: {exc!r}",
            "needs_conversion": True,
        }


def intake(
    file_path: Path,
    source: str,
    client: str,
    run_pipe: bool = True,
    manifest_path: Path | None = None,
    incoming_dir: Path | None = None,
) -> dict:
    """Core intake. Returns a structured report dict. Does NOT call sys.exit.

    Tests pass tmp ``manifest_path`` and ``incoming_dir`` so no real file is touched.
    """
    if not file_path.exists():
        return {"status": "error", "reason": f"file not found: {file_path}"}

    m_path = manifest_path or MANIFEST_PATH
    in_dir = incoming_dir or INCOMING_DIR
    manifest = load_manifest(m_path)
    sha = _sha256(file_path)
    dup = find_duplicate(manifest, sha)
    if dup:
        return {
            "status": "refused_duplicate",
            "sha256": sha,
            "existing_doc": dup,
            "reason": f"duplicate of existing manifest entry: {dup['path']} (source_batch={dup.get('source_batch')})",
        }

    date_str = datetime.now(UTC).strftime("%Y-%m-%d")
    dest_dir = in_dir / date_str
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / file_path.name
    if dest.exists():
        dest = dest_dir / f"{file_path.stem}_{sha[:8]}{file_path.suffix}"
    shutil.copy2(file_path, dest)
    rel_dest = str(dest.relative_to(REPO_ROOT)) if dest.is_relative_to(REPO_ROOT) else str(dest)

    split = assign_split(manifest)
    ext = file_path.suffix.lower()
    entry = {
        "path": rel_dest,
        "sha256": sha,
        "source_batch": "incoming",
        "client": client,
        "received_date": date_str,
        "doc_type": "pending",
        "format": DOC_EXTS.get(ext, ext.lstrip(".")),
        "size_bytes": file_path.stat().st_size,
        "split": split,
        "intake_source": source,
        "intake_date": datetime.now(UTC).isoformat(),
    }

    pipe_report = (
        run_pipeline(file_path)
        if run_pipe
        else {"rows_extracted": 0, "needs_source_truth_count": False, "error": "skipped"}
    )
    if pipe_report.get("needs_conversion"):
        entry["intake_status"] = "needs_conversion"
    elif pipe_report.get("error"):
        entry["intake_status"] = "pipeline_error"
    else:
        entry["intake_status"] = "intaked"

    manifest["files"].append(entry)
    manifest["total_docs"] = len(manifest["files"])
    save_manifest(manifest, m_path)

    return {
        "status": "intaked",
        "sha256": sha,
        "dest": rel_dest,
        "split": split,
        "pipeline": pipe_report,
        "manifest_entry": entry,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="Path to the RFQ file to intake")
    parser.add_argument("--source", required=True, help='Provenance, e.g. "email from SWA 2026-07-06"')
    parser.add_argument("--client", required=True, help='Client name, e.g. "GSECL"')
    parser.add_argument("--no-pipeline", action="store_true", help="Skip the pipeline run (manifest+copy only)")
    args = parser.parse_args()

    report = intake(Path(args.file), args.source, args.client, run_pipe=not args.no_pipeline)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["status"] == "refused_duplicate":
        return 2
    if report["status"] == "error":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
