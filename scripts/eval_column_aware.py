#!/usr/bin/env python3
"""Per-doc column-aware extraction eval (P3_02).

Generates per-doc results in ``results/column_eval/per_doc/`` and
updates ``results/column_eval/COLUMN_EVAL.md`` with the before/after
table for every TRAIN/DEV PDF whose page(s) yield reliable column
detection.

The script is read-only on the corpus (no source edits) and reports
the detected bands + row count for each file. The text "BEFORE" and
"AFTER" comparison is the row count and the description cleanliness,
captured in COLUMN_EVAL.md §4.

Usage:
    python3 scripts/eval_column_aware.py [--split all|train|dev|test]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path.cwd()
sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / "results" / "column_eval"
PER_DOC_DIR = OUT_DIR / "per_doc"


def _load_manifest() -> dict:
    return json.loads((REPO_ROOT / "data/real_rfqs/corpus_manifest.json").read_text())


def _load_split() -> dict:
    return json.loads((REPO_ROOT / "data/real_rfqs/split_test.json").read_text())


def _resolve(path: str) -> Path | None:
    p = REPO_ROOT / path
    if p.exists():
        return p
    base = Path(path).name
    candidates = [
        REPO_ROOT / "resources/Specifications" / base,
        REPO_ROOT / "resources/Specifications/rar_extra" / base,
        REPO_ROOT / "data/real_rfqs/ALL_RFQS" / f"spec1__{base}",
        REPO_ROOT / "data/real_rfqs/ALL_RFQS" / f"spec2__{base}",
        REPO_ROOT / "data/real_rfqs/ALL_RFQS" / f"sacred10__{base}",
        REPO_ROOT / "data/real_rfqs/ALL_RFQS" / f"rar__{base}",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _eval_doc(path: Path, fmt: str) -> dict:
    """Run the column-aware extraction on a single file. Returns a
    dict with the diagnostic + table information."""
    from src.ingest.pdf_extractor import PDFExtractor

    ext = PDFExtractor()
    out: dict = {"path": str(path), "format": fmt, "diagnostics": [], "tables": []}
    if fmt != "pdf":
        return out
    try:
        diag = ext.extract_column_aware_diagnostics(str(path))
        out["diagnostics"] = diag
    except Exception as exc:
        out["error"] = f"diagnostics failed: {exc!r}"
    try:
        tables = ext.extract_column_aware_tables(str(path))
        # Build per-page table summary.
        for t in tables:
            out["tables"].append(
                {
                    "page": t.page_number,
                    "rows": len(t.rows),
                    "first_3_rows": [list(r[:6]) for r in t.rows[:3]],
                }
            )
    except Exception as exc:
        out["error"] = (out.get("error", "") + f" tables failed: {exc!r}").strip()
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="all", choices=["all", "train", "dev", "test"])
    parser.add_argument("--type", default="boq_bearing", choices=["all", "boq_bearing"])
    parser.add_argument("--limit", type=int, default=0, help="0 = no limit")
    args = parser.parse_args()

    manifest = _load_manifest()
    split_data = _load_split()

    docs = manifest["files"]
    if args.split != "all":
        split_paths = set()
        for key in ("test", "dev", "train"):
            if args.split in ("all", key):
                sd = split_data.get(key, {})
                split_paths.update(sd.get("all_paths", sd.get("sacred10", [])))
                split_paths.update(sd.get("bundle_duplicates_of_sacred10", []))
        docs = [f for f in docs if f["path"] in split_paths or args.split == "all"]
    if args.type != "all":
        docs = [f for f in docs if f.get("doc_type") == args.type]

    PER_DOC_DIR.mkdir(parents=True, exist_ok=True)
    summary = []
    n = 0
    for f in docs:
        on_disk = _resolve(f["path"])
        if not on_disk:
            continue
        fmt = f.get("format", "pdf")
        result = _eval_doc(on_disk, fmt)
        # Save per-doc result.
        safe_name = f["path"].replace("/", "__").replace(" ", "_")
        (PER_DOC_DIR / f"{safe_name}.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
        summary.append(
            {
                "doc_id": on_disk.stem,
                "path": str(on_disk),
                "format": fmt,
                "doc_type": f.get("doc_type"),
                "n_tables": len(result.get("tables", [])),
                "n_rows": sum(t["rows"] for t in result.get("tables", [])),
                "diagnostics_count": len(result.get("diagnostics", [])),
                "error": result.get("error", None),
            }
        )
        n += 1
        if args.limit and n >= args.limit:
            break

    summary_path = OUT_DIR / "summary.json"
    summary_path.write_text(
        json.dumps({"docs": summary, "n_docs": len(summary)}, indent=2) + "\n"
    )
    print(f"\nEVAL DONE: {len(summary)} docs")
    print(f"Per-doc results: {PER_DOC_DIR}")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
