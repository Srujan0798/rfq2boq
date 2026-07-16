#!/usr/bin/env python3
"""Batch corpus runner — crash-free survival inventory (P1_04).

Iterates the manifest, runs the pipeline per-doc with a timeout, catches
exceptions, writes results/corpus_run/<run_id>/status.json + run.log.

Usage:
    python3 scripts/run_corpus.py --split all --type all
    python3 scripts/run_corpus.py --split test --type boq_bearing --timeout 300
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path.cwd()
sys.path.insert(0, str(REPO_ROOT))

MANIFEST_PATH = REPO_ROOT / "data/real_rfqs/corpus_manifest.json"
SPLIT_PATH = REPO_ROOT / "data/real_rfqs/split_test.json"
RESULTS_DIR = REPO_ROOT / "results/corpus_run"


def _load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


def _load_split() -> dict:
    return json.loads(SPLIT_PATH.read_text())


def _resolve_on_disk(manifest_path: str) -> Path | None:
    """Resolve a manifest path to an on-disk file (handles path drift)."""
    p = REPO_ROOT / manifest_path
    if p.exists():
        return p
    # path drift: check resources/Specifications/ and ALL_RFQS/

    basename = Path(manifest_path).name
    candidates = [
        REPO_ROOT / "resources/Specifications" / basename,
        REPO_ROOT / "resources/Specifications/rar_extra" / basename,
        REPO_ROOT / "data/real_rfqs/ALL_RFQS" / f"spec1__{basename}",
        REPO_ROOT / "data/real_rfqs/ALL_RFQS" / f"spec2__{basename}",
        REPO_ROOT / "data/real_rfqs/ALL_RFQS" / f"sacred10__{basename}",
        REPO_ROOT / "data/real_rfqs/ALL_RFQS" / f"rar__{basename}",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


class TimeoutError(Exception):
    pass


def _run_with_timeout(func, timeout_s: int):
    """Run func with a signal-based timeout (macOS supports SIGALRM)."""

    def handler(signum, frame):
        raise TimeoutError(f"exceeded {timeout_s}s")

    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout_s)
    try:
        return func()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def _run_pipeline(path: Path, fmt: str) -> dict:
    if fmt == "xlsx":
        from src.pipeline_xlsx import XLSXRowPipeline

        rows = XLSXRowPipeline().run(str(path))
        return {"rows": len(rows)}
    from src.pipeline import Pipeline

    result = Pipeline().run(str(path))
    return {"rows": len(result.boq_items)}


def _process_docs(docs: list, log, timeout: int) -> tuple:
    """Iterate docs, run pipeline per-doc with timeout, return results + counters."""
    import time

    results = []
    n_ok, n_crash, n_timeout, n_missing = 0, 0, 0, 0
    for i, f in enumerate(docs, 1):
        did = f["path"].split("/")[-1]
        entry = {
            "doc_id": did,
            "manifest_path": f["path"],
            "format": f.get("format", "pdf"),
            "doc_type": f.get("doc_type", "?"),
            "status": "pending",
            "duration": 0.0,
            "rows": 0,
            "error": None,
        }
        on_disk = _resolve_on_disk(f["path"])
        if not on_disk:
            entry["status"] = "missing"
            entry["error"] = f"file not found on disk: {f['path']}"
            n_missing += 1
            results.append(entry)
            print(f"[{i}/{len(docs)}] {did}: MISSING", file=log)
            continue
        print(f"[{i}/{len(docs)}] {did} ({f.get('format')}): ", end="", file=log, flush=True)
        start = time.time()
        try:
            r = _run_with_timeout(lambda: _run_pipeline(on_disk, f.get("format", "pdf")), timeout)
            entry["status"] = "ok"
            entry["rows"] = r["rows"]
            entry["duration"] = time.time() - start
            n_ok += 1
            print(f"OK ({entry['rows']} rows, {entry['duration']:.1f}s)", file=log)
        except TimeoutError:
            entry["status"] = "timeout"
            entry["duration"] = time.time() - start
            entry["error"] = f"exceeded {timeout}s"
            n_timeout += 1
            print(f"TIMEOUT ({entry['duration']:.1f}s)", file=log)
        except Exception as exc:
            entry["status"] = "crash"
            entry["duration"] = time.time() - start
            entry["error"] = f"{type(exc).__name__}: {exc}"
            entry["traceback"] = traceback.format_exc()[:500]
            n_crash += 1
            print(f"CRASH: {entry['error']}", file=log)
        results.append(entry)
    return results, n_ok, n_crash, n_timeout, n_missing


def run_corpus(split: str, doc_type: str, timeout: int) -> dict:
    manifest = _load_manifest()
    split_data = _load_split()

    # filter by split
    if split == "all":
        docs = manifest["files"]
    else:
        split_paths = set()
        for key in ("test", "dev", "train"):
            if split in ("all", key):
                sd = split_data.get(key, {})
                split_paths.update(sd.get("all_paths", sd.get("sacred10", [])))
                split_paths.update(sd.get("bundle_duplicates_of_sacred10", []))
        docs = [f for f in manifest["files"] if f["path"] in split_paths or split == "all"]

    # filter by type
    if doc_type != "all":
        docs = [f for f in docs if f.get("doc_type") == doc_type]

    run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "run.log"
    with open(log_path, "w") as log:
        results, n_ok, n_crash, n_timeout, n_missing = _process_docs(docs, log, timeout)

    status = {
        "run_id": run_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "split": split,
        "type": doc_type,
        "timeout_s": timeout,
        "total": len(docs),
        "ok": n_ok,
        "crash": n_crash,
        "timeout": n_timeout,
        "missing": n_missing,
        "docs": results,
    }
    (run_dir / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n")
    print(f"\nRUN {run_id}: {n_ok} ok, {n_crash} crash, {n_timeout} timeout, {n_missing} missing (of {len(docs)})")
    print(f"Status: {run_dir / 'status.json'}")
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", default="all", choices=["all", "train", "dev", "test"])
    parser.add_argument("--type", default="all", choices=["all", "boq_bearing", "spec_only", "non_training"])
    parser.add_argument("--timeout", type=int, default=300, help="per-doc timeout seconds")
    args = parser.parse_args()
    run_corpus(args.split, args.type, args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
