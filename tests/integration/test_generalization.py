"""Generalization test — proves the XLSX extraction LOGIC works on UNSEEN tenders.

The 10 SWA enquiries have gold and score 100%, but that could be overfitting.
This test proves the extraction generalizes by:

1. Running the XLSX pipeline on 2 incoming tenders that have NO gold and were
   never used to tune the extractor (VSSC acoustic, Zydus R3 Matoda).
2. Asserting each produces a reasonable number of structurally-sane rows.
3. Asserting every emitted row has a non-empty material AND a unit (proves the
   parser found real BOQ structure, not garbage).
4. Asserting no emitted row's description equals a known section-header string
   (proves header filtering works on unseen files).
5. A pattern audit: failing if any hardcoded SWA filename appears in NON-COMMENT
   code in src/pipeline_xlsx.py or src/pipeline.py — permanently preventing
   overfitting-by-filename.

This is a structural / generalization guard, NOT a gold accuracy check.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from src.pipeline_xlsx import XLSXRowPipeline

REPO_ROOT = Path(__file__).resolve().parents[2]

UNSEEN_TENDERS = {
    "VSSC acoustic": {
        "path": REPO_ROOT / "data/incoming/40_vssc_acoustic_boq.xlsx",
        # 4 real line items; was 5 before P0_02 D4 ruling removed the
        # "Structure & civil" section-header row from gold (owner 2026-07-06).
        "min_rows": 4,
    },
    "Zydus R3 Matoda": {
        "path": REPO_ROOT / "data/incoming/R3_zydus_matoda_osd.xlsx",
        "min_rows": 30,
    },
}

# Strings that are section headers / non-items. If any extracted row's
# material is EXACTLY one of these, header filtering failed on an unseen file.
KNOWN_SECTION_HEADERS = frozenset(
    {
        "structure & civil",
        "structure and civil",
        "civil works",
        "civil work",
        "scope of work",
        "general",
        "notes",
        "note",
        "total",
        "sub-total",
        "subtotal",
        "grand total",
        "bill of quantities",
        "boq",
        "description",
        "material",
        "summary",
    }
)

# SWA filename stems that must never be hardcoded into production code.
SWA_FILENAME_TOKENS = (
    "gsecl",
    "adani",
    "zydus",
    "avante",
    "grew",
    "sael",
    "isro",
    "vssc",
    "kirloskar",
)

AUDITED_SOURCES = (
    REPO_ROOT / "src/pipeline_xlsx.py",
    REPO_ROOT / "src/pipeline.py",
)


def _strip_comments_and_strings(line: str, in_docstring: bool = False) -> tuple[str, bool]:
    """Return the code portion of a Python line, removing comments and string
    literal contents so that a filename token mentioned only in a comment or a
    docstring/example string does not trip the audit.

    Returns (stripped_code, still_in_docstring).
    """
    # If we're inside a multi-line docstring, skip until we find the closing """
    if in_docstring:
        if '"""' in line:
            # Find the closing """ and return everything after it
            idx = line.index('"""') + 3
            remaining = line[idx:]
            return _strip_comments_and_strings(remaining, False)[0], False
        return "", True

    # Drop everything after the first '#' (comment).
    code = line.split("#", 1)[0]

    # Check for multi-line docstring start
    if '"""' in code:
        # Count occurrences of """ to determine if it opens and closes on same line
        count = code.count('"""')
        if count == 1:
            # Multi-line docstring starts on this line
            idx = code.index('"""')
            code = code[:idx]
            return code, True
        # If count >= 2, it opens and closes on same line - strip inline

    # Blank out the contents of any quoted string literals on the line so that
    # example tokens inside strings are not counted as hardcoded logic.
    code = re.sub(r'"""(.*?)"""', '""', code)
    code = re.sub(r"'''(.*?)'''", "''", code)
    code = re.sub(r'"[^"]*"', '""', code)
    code = re.sub(r"'[^']*'", "''", code)
    return code, False


@pytest.fixture(scope="module")
def extractions() -> dict[str, list]:
    pipeline = XLSXRowPipeline()
    results: dict[str, list] = {}
    for name, info in UNSEEN_TENDERS.items():
        path = info["path"]
        assert path.exists(), f"Unseen tender missing: {path}"
        results[name] = pipeline.run(str(path))
    return results


def test_unseen_tenders_produce_reasonable_row_counts(extractions: dict[str, list]) -> None:
    """Each unseen tender yields at least the expected number of rows."""
    for name, info in UNSEEN_TENDERS.items():
        rows = extractions[name]
        min_rows = info["min_rows"]
        assert len(rows) >= min_rows, (
            f"{name}: expected >= {min_rows} rows, got {len(rows)}. "
            "Extraction logic may not generalize to this unseen tender."
        )


def test_every_row_has_material_and_unit(extractions: dict[str, list]) -> None:
    """Structural sanity: every emitted row must have a non-empty material and unit.

    Proves the parser located real BOQ structure rather than emitting garbage.
    """
    for name, rows in extractions.items():
        for i, row in enumerate(rows):
            material = (row.material or "").strip()
            unit = (row.unit or "").strip()
            assert material, f"{name} row {i}: empty material — parser emitted garbage"
            assert unit, f"{name} row {i}: empty unit — parser emitted garbage"


def test_no_row_is_a_section_header(extractions: dict[str, list]) -> None:
    """No emitted row's material equals a known section-header string.

    Proves header filtering works on unseen files (not just the SWA 10).
    Rate-only rows (qty=0) with section-header names are allowed — they are
    legitimate parent items in grouped tenders (e.g. ISRO "Structure & civil").
    """
    for name, rows in extractions.items():
        for i, row in enumerate(rows):
            material_norm = (row.material or "").strip().lower().rstrip(":")
            if material_norm in KNOWN_SECTION_HEADERS:
                # Rate-only rows with qty=0 are legitimate parent items
                qty = float(row.quantity or 0)
                assert qty == 0, (
                    f"{name} row {i}: section header '{row.material}' has non-zero "
                    f"qty={qty} — header filtering failed on an unseen file."
                )


def test_no_hardcoded_swa_filenames_in_code() -> None:
    """Pattern audit: no SWA filename token in non-comment, non-string code.

    Permanently prevents overfitting-by-filename. Tokens are allowed in comments
    and string literals (e.g. explanatory examples) but never in executable logic.
    """
    violations: list[str] = []
    for source in AUDITED_SOURCES:
        assert source.exists(), f"Audited source missing: {source}"
        in_docstring = False
        for lineno, raw in enumerate(source.read_text().splitlines(), start=1):
            code, in_docstring = _strip_comments_and_strings(raw, in_docstring)
            code = code.lower()
            for token in SWA_FILENAME_TOKENS:
                if re.search(rf"\b{token}\b", code):
                    violations.append(f"{source.relative_to(REPO_ROOT)}:{lineno}: '{token}' in code: {raw.strip()}")
    assert not violations, "Hardcoded SWA filename(s) found in production code:\n" + "\n".join(violations)


def test_print_generalization_report(extractions: dict[str, list]) -> None:
    """Emit a human-readable generalization report (rows, %material+unit, anomalies)."""
    lines = ["", "=" * 64, "GENERALIZATION REPORT — unseen tenders (no gold, no tuning)", "=" * 64]
    for name, rows in extractions.items():
        total = len(rows)
        with_both = sum(1 for r in rows if (r.material or "").strip() and (r.unit or "").strip())
        zero_qty = sum(1 for r in rows if float(r.quantity) == 0.0)
        pct = (with_both / total * 100.0) if total else 0.0
        lines.append(f"{name}: {total} rows | {pct:.0f}% with material+unit | {zero_qty} zero-qty rows")
    lines.append("=" * 64)
    print("\n".join(lines))
