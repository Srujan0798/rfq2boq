#!/usr/bin/env python3
"""Per-document fidelity audit CLI — the R1 proof artifact.

Usage:
    python3 scripts/audit_fidelity_per_doc.py --doc <id>
    python3 scripts/audit_fidelity_per_doc.py --all

Writes results/fidelity/<doc_id>.audit.md (human-readable table) and
results/fidelity/summary.json (machine-readable verdicts).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path.cwd()
sys.path.insert(0, str(REPO_ROOT))

from src.domain.fidelity import FidelityAuditor, render_audit_report  # noqa: E402

SOURCE_TRUTH_PATH = REPO_ROOT / "data/real_rfqs/source_truth.json"
RESULTS_DIR = REPO_ROOT / "results/fidelity"


def _load_source_truth() -> dict:
    return json.loads(SOURCE_TRUTH_PATH.read_text())


def _doc_id_matches_path(doc_id: str, path: str) -> bool:
    """True iff ``doc_id`` is the file's parent directory or its basename stem.

    Replaces the prior substring-based match. The old check
    ``doc_id.split("_")[0] in path`` produced false positives — e.g.
    ``"10" in "RFQ-75810 TMD-8.pdf"`` — causing ``10_gem_bid_7552777`` to be
    audited against ``01_gsecl_wanakbori_tmd8``'s source file (the
    ``RFQ-75810`` substring collision). Two exact-component checks cover the
    real layout:

    - sacred-10 docs live at ``data/real_rfqs/swa_enquiries/<doc_id>/<file>``
      → parent dir name == doc_id.
    - spec files live at ``data/specifications/<category>/<file>`` where the
      source_truth ``doc_id`` is the file's stem (basename without ext).

    Also handles disambiguated doc_ids (e.g. ``"BOQ - Insulation (spec2 XLSX)"``)
    by stripping the trailing parenthetical suffix before matching.
    """
    if not doc_id or not path:
        return False
    p = Path(path)
    if p.parent.name == doc_id:
        return True
    if p.stem == doc_id:
        return True
    # Disambiguated suffixes: " (spec1 PDF)", " (spec2 XLSX)", " (bundle copy)"
    stripped = re.sub(r"\s*\([^)]*\)$", "", doc_id)
    return bool(stripped != doc_id and (p.parent.name == stripped or p.stem == stripped))


def _get_boq_output(doc_id: str) -> list:
    """Run the appropriate pipeline to get BOQ output rows for a doc."""
    st = _load_source_truth()
    entry = None
    for e in st.get("entries", []):
        if e["doc_id"] == doc_id:
            entry = e
            break
    if not entry:
        return []

    # Bundle copies redirect to their duplicate_of doc_id so we match the
    # same physical file(s) and avoid a false "0 rows" verdict.
    effective_doc_id = entry.get("duplicate_of") or doc_id

    # Find source files on disk.
    #
    # Multi-file packages (04_adani: BOQ PAGE + BOQ PAGE2 under one folder)
    # contribute rows that source_truth counts together. Aggregate ONLY when
    # the doc folder has 2+ non-spec (boq_bearing) files. Preferring non-spec
    # unconditionally would break 08_sael (manifest labels the TDS as
    # boq_bearing and the real BOQ enquiry as spec_only — first-match must
    # keep using the enquiry file that yields 16 rows).
    #
    # Spec-tree docs (doc_id == file stem under data/specifications/) stay
    # single-file with exact stem match so "BOQ PAGE (003)" does not pull in
    # sibling "BOQ PAGE.pdf".
    manifest = json.loads((REPO_ROOT / "data/real_rfqs/corpus_manifest.json").read_text())
    matching_files = [
        f for f in manifest["files"] if _doc_id_matches_path(effective_doc_id, f.get("path", ""))
    ]
    if not matching_files:
        return []

    dir_scoped = [
        f
        for f in matching_files
        if Path(f.get("path", "")).parent.name == effective_doc_id
    ]
    if dir_scoped:
        non_spec = [f for f in dir_scoped if f.get("doc_type") != "spec_only"]
        files_to_run = (
            non_spec
            if len(non_spec) >= 2
            # Preserve historical first-match order (manifest order among all
            # dir-scoped matches — may intentionally pick a file labelled
            # spec_only when it is the real BOQ, e.g. 08_sael enquiry).
            else dir_scoped[:1]
        )
    else:
        exact_stem = [
            f for f in matching_files if Path(f.get("path", "")).stem == effective_doc_id
        ]
        pool = exact_stem if exact_stem else matching_files
        files_to_run = pool[:1]

    def _run_files(files: list) -> list:
        out: list = []
        try:
            from src.pipeline import Pipeline
            from src.pipeline_xlsx import XLSXRowPipeline

            for f in files:
                p = REPO_ROOT / f["path"]
                if not p.exists():
                    continue
                fmt = f.get("format", "pdf")
                try:
                    if fmt == "xlsx":
                        out.extend(XLSXRowPipeline().run(str(p)))
                    else:
                        result = Pipeline().run(str(p))
                        out.extend(result.boq_items)
                except Exception as exc:  # noqa: BLE001
                    print(
                        f"  WARN: pipeline error for {doc_id} on {p.name}: {exc!r}",
                        file=sys.stderr,
                    )
        except Exception as exc:  # noqa: BLE001
            print(f"  WARN: pipeline error for {doc_id}: {exc!r}", file=sys.stderr)
        return out

    return _run_files(files_to_run)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--doc", help="Single doc ID")
    parser.add_argument("--all", action="store_true", help="Audit all docs in source_truth")
    args = parser.parse_args()

    if not args.doc and not args.all:
        parser.print_help()
        return 1

    st = _load_source_truth()
    doc_ids = [e["doc_id"] for e in st.get("entries", [])] if args.all else [args.doc]
    auditor = FidelityAuditor()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    summaries = []
    for did in doc_ids:
        print(f"Auditing {did}...", end=" ", flush=True)
        boq_output = _get_boq_output(did)
        report = auditor.audit(did, boq_output, st)
        md = render_audit_report(report)
        (RESULTS_DIR / f"{did}.audit.md").write_text(md)
        s = {
            "doc_id": did,
            "source_row_count": report.source_row_count,
            "captured": report.captured_count,
            "missing": report.missing_count,
            "extra": report.extra_count,
            "flagged": report.flagged_count,
            "verdict": report.verdict,
        }
        summaries.append(s)
        print(
            f"verdict={report.verdict} ({report.captured_count}/{report.source_row_count} captured, {report.missing_count} missing, {report.extra_count} extra)"
        )

    (RESULTS_DIR / "summary.json").write_text(json.dumps({"docs": summaries}, indent=2) + "\n")
    print(f"\nWrote {len(summaries)} audit reports to {RESULTS_DIR}")
    n_pass = sum(1 for s in summaries if s["verdict"] == "PASS")
    print(f"PASS: {n_pass}/{len(summaries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
