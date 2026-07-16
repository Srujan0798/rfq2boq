"""Unit tests for the FidelityAuditor (P1_02)."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402
from src.domain.fidelity import (  # noqa: E402
    FidelityAuditor,
    OutputRow,
    SourceRow,
    _normalize_unit,
    _qty_agrees,
    _similarity,
)


def _src(desc: str, qty: Any = None, unit: str = "") -> SourceRow:
    return SourceRow(item_no=1, description=desc, quantity=qty, unit=unit)


def _out(desc: str, qty: Any = None, unit: str = "", conf: float = 0.95, warnings: list | None = None) -> OutputRow:
    return OutputRow(item_no=1, description=desc, quantity=qty, unit=unit, confidence=conf, warnings=warnings or [])


from typing import Any  # noqa: E402


def _make_source_truth(rows: list[SourceRow], doc_id: str = "test") -> dict:
    return {
        "entries": [
            {
                "doc_id": doc_id,
                "source_row_count": len(rows),
                "rows": [
                    {
                        "item_no": r.item_no,
                        "description": r.description,
                        "quantity": str(r.quantity) if r.quantity is not None else "",
                        "unit": r.unit,
                    }
                    for r in rows
                ],
            }
        ]
    }


@pytest.fixture
def auditor() -> FidelityAuditor:
    return FidelityAuditor()


def test_perfect_match(auditor: FidelityAuditor) -> None:
    rows = [_src("13 mm thick insulation", Decimal("100"), "sqm")]
    st = _make_source_truth(rows)
    out = [_out("13 mm thick insulation", Decimal("100"), "sqm")]
    r = auditor.audit("test", out, st)
    assert r.verdict == "PASS"
    assert r.captured_count == 1
    assert r.missing_count == 0 and r.extra_count == 0


def test_one_missing(auditor: FidelityAuditor) -> None:
    rows = [_src("row A", Decimal("10"), "kg"), _src("row B", Decimal("20"), "kg")]
    st = _make_source_truth(rows)
    out = [_out("row A", Decimal("10"), "kg")]
    r = auditor.audit("test", out, st)
    assert r.verdict == "FAIL"
    assert r.missing_count == 1
    assert r.missing[0].description == "row B"


def test_one_extra(auditor: FidelityAuditor) -> None:
    rows = [_src("row A", Decimal("10"), "kg")]
    st = _make_source_truth(rows)
    out = [_out("row A", Decimal("10"), "kg"), _out("row X", Decimal("99"), "kg")]
    r = auditor.audit("test", out, st)
    assert r.verdict == "FAIL"
    assert r.extra_count == 1
    assert r.extra[0].description == "row X"


def test_flagged_not_failing(auditor: FidelityAuditor) -> None:
    rows = [_src("row A", Decimal("10"), "kg")]
    st = _make_source_truth(rows)
    out = [_out("row A", Decimal("10"), "kg", conf=0.50, warnings=["low conf"])]
    r = auditor.audit("test", out, st)
    assert r.verdict == "PASS"  # flagged but matched → PASS
    assert r.flagged_count == 1
    assert r.captured_count == 1


def test_duplicate_description_disambiguation(auditor: FidelityAuditor) -> None:
    """Two source rows with same desc but different qty must match to different outputs."""
    rows = [_src("insulation", Decimal("10"), "sqm"), _src("insulation", Decimal("20"), "sqm")]
    st = _make_source_truth(rows)
    out = [_out("insulation", Decimal("10"), "sqm"), _out("insulation", Decimal("20"), "sqm")]
    r = auditor.audit("test", out, st)
    assert r.verdict == "PASS"
    assert r.captured_count == 2


def test_qty_mismatch_not_a_match(auditor: FidelityAuditor) -> None:
    rows = [_src("insulation", Decimal("10"), "sqm")]
    st = _make_source_truth(rows)
    out = [_out("insulation", Decimal("20"), "sqm")]
    r = auditor.audit("test", out, st)
    assert r.verdict == "FAIL"
    assert r.missing_count == 1 and r.extra_count == 1


def test_unit_normalization_match(auditor: FidelityAuditor) -> None:
    """MT vs tonne, sqm vs sq.m — normalized equal → match."""
    rows = [_src("insulation", Decimal("100"), "MT")]
    st = _make_source_truth(rows)
    out = [_out("insulation", Decimal("100"), "tonne")]
    r = auditor.audit("test", out, st)
    assert r.verdict == "PASS", (
        f"MT vs tonne should match; units normalized: {_normalize_unit('MT')} vs {_normalize_unit('tonne')}"
    )


def test_empty_doc_pass(auditor: FidelityAuditor) -> None:
    """Confirmed-zero source + empty output → PASS."""
    st = {"entries": [{"doc_id": "empty", "source_row_count": 0, "rows": []}]}
    r = auditor.audit("empty", [], st)
    assert r.verdict == "PASS"
    assert r.source_row_count == 0


def test_empty_doc_with_invented_rows_fails(auditor: FidelityAuditor) -> None:
    """Confirmed-zero source + non-empty output → FAIL-extra."""
    st = {"entries": [{"doc_id": "empty", "source_row_count": 0, "rows": []}]}
    out = [_out("invented", Decimal("1"), "kg")]
    r = auditor.audit("empty", out, st)
    assert r.verdict == "FAIL"
    assert r.extra_count == 1


def test_unit_helpers() -> None:
    assert _normalize_unit("Sq.M.") == _normalize_unit("sqm")
    assert _normalize_unit("RMT") == _normalize_unit("rm")
    assert _qty_agrees(None, "RO") is True
    assert _qty_agrees(Decimal("10"), Decimal("10")) is True
    assert _qty_agrees(Decimal("10"), Decimal("20")) is False
    assert _similarity("13 mm thick", "13mm thick") >= 0.80


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
