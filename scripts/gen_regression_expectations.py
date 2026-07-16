#!/usr/bin/env python3
"""Generate the regression test expectations from an accepted fidelity summary.

Tier-1 regression (tests/regression/test_corpus_exact.py) consumes
``tests/regression/expectations.json`` — a human-reviewable file that locks
the exact per-doc verdicts, captured counts, and source-file paths the
regression suite asserts. This script is the only sanctioned way to write
that file: it reads an accepted ``results/fidelity/summary.json`` plus the
``data/real_rfqs/source_truth.json`` ruler, and writes (or dry-run diffs) the
expectations.

This is one of the sanctioned frozen-file tasks per task P5_02. The
regression test file (tests/regression/test_corpus_exact.py) calls this on
import to load expectations; the orchestrator re-pins expectations.json
itself after the agent's diff is reviewed (Rule 5 inverted).

Modes:
    # Dry-run: print a unified diff and exit non-zero if expectations are stale
    python3 scripts/gen_regression_expectations.py --check

    # Write expectations.json (only after a human has reviewed the diff!)
    python3 scripts/gen_regression_expectations.py --write

The expectations are derived from entries with ``verdict == "PASS"`` in the
accepted summary. FAIL docs are explicitly listed as
``"scope": "out-of-scope-until-fixed"`` so they are visible-and-accounted-for
in the JSON (per the spec's gotcha: "EXCLUDED with the reason string —
visible, not forgotten") but not asserted by the Tier-1 regression.

Non-sacred, non-BOQ-bearing, or 0/0-trivially-PASS docs are still included
with their captured counts so the regression is exhaustive across the
summary, not cherry-picked.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SUMMARY_PATH = REPO_ROOT / "results" / "fidelity" / "summary.json"
SOURCE_TRUTH_PATH = REPO_ROOT / "data" / "real_rfqs" / "source_truth.json"
EXPECTATIONS_PATH = REPO_ROOT / "tests" / "regression" / "expectations.json"
CORPUS_MANIFEST = REPO_ROOT / "data" / "real_rfqs" / "corpus_manifest.json"

# Sacred-10 docs — the project's regression anchor. Six now PASS under the
# accepted source-truth ruler (01_gsecl was corrected and committed in task 1);
# four remain FAIL (out-of-scope-until-fixed per task P5_02 §4 + the D6 ruling
# in 04_LEDGER.md). Listing them explicitly here keeps the expectations
# reviewer-facing rather than auto-derived.
SACRED_10 = [
    "01_gsecl_wanakbori_tmd8",
    "02_isro_vssc",
    "03_zydus_matoda_osd",
    "04_adani",
    "05_zydus_animal_pharmez",
    "06_avante_kirloskar_pune",
    "07_grew_solar_narmadapuram",
    "08_sael",
    "09_gem_bid_7439924",
    "10_gem_bid_7552777",
]

# Owner-acknowledged FAIL baselines (task P5_02 spec). These are not
# regressions — they're accepted baseline until the named owner-ruling lands.
# The reason strings are short, reviewer-readable, and ledger-citable.
SACRED_FAIL_REASONS: dict[str, str] = {
    "04_adani": (
        "Two source PDFs in the doc bundle; aggregate source row count not "
        "yet reconciled. P1_01 left this as needs_manual_count; not a "
        "regression, a known baseline gap."
    ),
    "06_avante_kirloskar_pune": (
        "D6 ruling pending — source_truth 36 vs gold-based 31. Pipeline "
        "already produces 31 (post-P3_03); locked as out-of-scope until "
        "D6 ruling applied to source_truth.json."
    ),
    "07_grew_solar_narmadapuram": (
        "D6 ruling pending — source_truth 11 vs gold-based 9. Pipeline "
        "already produces 9 (post-P3_02 P3_03); locked as out-of-scope "
        "until D6 ruling applied to source_truth.json."
    ),
    "08_sael": (
        "D6 ruling pending — source_truth 19 vs gold-based 16. Also: "
        "source_truth points at the TDS file, not the BOQ enquiry file "
        "(per SOURCE_TRUTH_REVIEW_06_07_08.md). Locked as out-of-scope "
        "until both source_truth file + count are corrected."
    ),
}

# The 6 sacred-10 PASS docs that the regression suite locks exact after the
# 01_gsecl source_truth correction (3 real BOQ rows on page 61, committed and
# owner-verified). The summary is consulted only for the captured/flagged
# counts to lock.
SACRED_PASS_DOC_IDS: set[str] = {
    "01_gsecl_wanakbori_tmd8",
    "02_isro_vssc",
    "03_zydus_matoda_osd",
    "05_zydus_animal_pharmez",
    "09_gem_bid_7439924",
    "10_gem_bid_7552777",
}


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")
    return json.loads(path.read_text())


def _resolve_source_path(doc_id: str, manifest: dict) -> tuple[str, str]:
    """Return (relative_path, sha256) for a doc, preferring exact path match.

    Mirrors the rule in scripts/audit_fidelity_per_doc.py: parent dir ==
    doc_id, OR file stem == doc_id. Returns ("", "") if no match — caller
    decides how to handle.
    """
    for f in manifest.get("files", []):
        path = f.get("path", "")
        if not path:
            continue
        pp = Path(path)
        if pp.parent.name == doc_id or pp.stem == doc_id:
            return path, f.get("sha256", "")
    return "", ""


def _build_expectations() -> dict[str, Any]:
    summary = _load_json(SUMMARY_PATH)
    source_truth = _load_json(SOURCE_TRUTH_PATH)
    manifest = _load_json(CORPUS_MANIFEST)

    # Build a lookup from source_truth for cross-checks.
    st_by_id: dict[str, dict] = {e.get("doc_id"): e for e in source_truth.get("entries", [])}

    pass_docs: list[dict[str, Any]] = []
    excluded_docs: list[dict[str, Any]] = []
    fail_docs_summary: list[dict[str, Any]] = []

    for entry in summary.get("docs", []):
        doc_id = entry.get("doc_id", "")
        verdict = entry.get("verdict", "FAIL")
        captured = int(entry.get("captured", 0))
        source_rows = int(entry.get("source_row_count", 0))
        flagged = int(entry.get("flagged", 0))

        path, sha = _resolve_source_path(doc_id, manifest)
        st_entry = st_by_id.get(doc_id, {})
        # Cross-check: the summary's source_row_count must match source_truth
        # if source_truth is also non-zero. If they disagree, the expectations
        # file is invalid — surface that loudly.
        st_source = st_entry.get("source_row_count", -1)
        if st_source != -1 and st_source != source_rows:
            # We allow disagreement only for sacred FAILs (D6-pending / source_truth
            # correction pending) — and we flag it.
            cross_check_ok = doc_id in SACRED_FAIL_REASONS
            if not cross_check_ok:
                raise SystemExit(
                    f"ERROR: source_row_count mismatch for {doc_id}: "
                    f"summary={source_rows}, source_truth={st_source}. "
                    f"Refusing to write expectations — investigate before locking."
                )

        record = {
            "doc_id": doc_id,
            "source_path": path,
            "source_sha256": sha,
            "source_row_count": source_rows,
            "captured_count": captured,
            "flagged_count": flagged,
            "verdict": verdict,
        }

        if doc_id in SACRED_FAIL_REASONS:
            record["scope"] = "out-of-scope-until-fixed"
            record["reason"] = SACRED_FAIL_REASONS[doc_id]
            record["sacred10_baseline_fail"] = True
            excluded_docs.append(record)
            fail_docs_summary.append(record)
            continue

        if doc_id in SACRED_PASS_DOC_IDS:
            # The sacred-10 PASS docs are the project's regression anchor.
            # Verify the summary also reports PASS; if it doesn't, surface a
            # hard error so a regression is caught at generation time.
            if verdict != "PASS":
                raise SystemExit(
                    f"ERROR: sacred PASS doc {doc_id} has verdict={verdict} "
                    f"in current summary. Regression! The pipeline has "
                    f"stopped producing its accepted baseline. "
                    f"Investigate before regenerating expectations."
                )
            record["scope"] = "verify-exact"
            record["sacred10_baseline_pass"] = True
            pass_docs.append(record)
            continue

        if verdict == "PASS":
            # Per task P5_02 §6, every PASS-verdict doc in the accepted summary
            # is locked in Tier 1 — not only the sacred-10. The sacred-10 PASS
            # docs are the regression anchor, but non-sacred TRAIN/DEV docs that
            # are currently PASS are also owner-visible counts; omitting them
            # would silently allow a regression on as-yet-unverified docs. They
            # are marked scope="non-sacred-pass" for visibility.
            if doc_id in SACRED_PASS_DOC_IDS:
                record["scope"] = "verify-exact"
                record["sacred10_baseline_pass"] = True
            else:
                record["scope"] = "non-sacred-pass"
                record["note"] = (
                    "Non-sacred PASS doc in the current summary — locked "
                    "visible-and-accounted-for per P5_02 §6. Exact captured "
                    "count is asserted by Tier 1."
                )
            pass_docs.append(record)
            continue

        # Remaining FAIL docs (non-sacred) are listed visible-and-accounted-for
        # but not asserted.
        record["scope"] = "non-sacred-fail"
        record["note"] = (
            "TRAIN/DEV-pool doc with non-100% fidelity — out of "
            "Tier-1 scope until owner/agent processes it. Not asserted."
        )
        if int(entry.get("extra", 0)) > 0 and source_rows == 0:
            record["note"] = (
                f"R1 RULE 9 (never invent) VIOLATION: source_row_count=0 "
                f"but pipeline emitted {int(entry.get('extra', 0))} extra rows "
                f"on this spec-only doc. Locked as out-of-scope until the "
                f"pipeline is fixed to suppress non-BOQ output on 0-row docs. "
                f"This is a real product bug, not a regression of the test."
            )
        excluded_docs.append(record)
        fail_docs_summary.append(record)

    expectations = {
        "schema_version": "1.0.0",
        "generated_note": (
            "Regenerated by scripts/gen_regression_expectations.py. Do not "
            "edit by hand — re-run the script after any source_truth.json "
            "or results/fidelity/summary.json change, review the diff, and "
            "commit. This file is the project lock per task P5_02."
        ),
        "source_files": {
            "summary": str(SUMMARY_PATH.relative_to(REPO_ROOT)),
            "summary_sha256": hashlib.sha256(SUMMARY_PATH.read_bytes()).hexdigest(),
            "source_truth": str(SOURCE_TRUTH_PATH.relative_to(REPO_ROOT)),
            "source_truth_sha256": hashlib.sha256(SOURCE_TRUTH_PATH.read_bytes()).hexdigest(),
        },
        "pass_doc_count": len(pass_docs),
        "excluded_doc_count": len(excluded_docs),
        "pass_docs": sorted(pass_docs, key=lambda r: r["doc_id"]),
        "excluded_docs": sorted(excluded_docs, key=lambda r: r["doc_id"]),
    }
    return expectations


def _diff_text(old: str, new: str, label: str) -> str:
    diff = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"a/{label} (current)",
        tofile=f"b/{label} (would-be)",
    )
    return "".join(diff)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="Dry-run: print a diff and exit non-zero if stale")
    parser.add_argument("--write", action="store_true", help="Write expectations.json")
    parser.add_argument(
        "--print-summary", action="store_true", help="Print pass/excluded counts to stdout (used by tests)"
    )
    args = parser.parse_args()

    if not (args.check or args.write or args.print_summary):
        parser.print_help()
        return 1

    expectations = _build_expectations()

    if args.print_summary:
        print(f"pass_doc_count={expectations['pass_doc_count']}")
        print(f"excluded_doc_count={expectations['excluded_doc_count']}")
        for d in expectations["pass_docs"]:
            print(
                f"PASS {d['doc_id']}: source={d['source_row_count']} captured={d['captured_count']} flagged={d['flagged_count']}"
            )
        for d in expectations["excluded_docs"]:
            print(
                f"EXCL {d['doc_id']}: verdict={d['verdict']} scope={d.get('scope','?')}"
            )
        return 0

    new_text = json.dumps(expectations, indent=2) + "\n"
    old_text = EXPECTATIONS_PATH.read_text() if EXPECTATIONS_PATH.exists() else ""

    if args.write:
        EXPECTATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        EXPECTATIONS_PATH.write_text(new_text)
        print(f"Wrote {EXPECTATIONS_PATH} ({len(expectations['pass_docs'])} pass + {len(expectations['excluded_docs'])} excluded)")
        return 0

    if args.check:
        if new_text == old_text:
            print("OK: expectations match accepted summary (no diff)")
            return 0
        sys.stdout.write(_diff_text(old_text, new_text, "expectations.json"))
        print(
            "\nFAIL: expectations.json is stale relative to "
            "results/fidelity/summary.json + source_truth.json. "
            "Review the diff above, then run "
            "`python3 scripts/gen_regression_expectations.py --write` "
            "and commit the regenerated expectations.json.",
            file=sys.stderr,
        )
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
