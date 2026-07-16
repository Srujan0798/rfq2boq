"""Integration tests for scripts/fidelity_audit.py.

Verifies the audit runs without error on at least 2 SWA enquiries and that
the output structure is correct.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure src.* imports work when tests run from the project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.fidelity_audit import (
    ENQUIRIES,
    audit_enquiry,
    format_audit_report,
    format_summary_table,
)
from src.pipeline import Pipeline


@pytest.fixture(scope="module")
def pipeline() -> Pipeline:
    return Pipeline()


# Two enquiries chosen: one PDF (04_adani) and one XLSX (02_isro)
AUDIT_EIDS = ["04_adani", "02_isro"]


@pytest.mark.parametrize("eid", AUDIT_EIDS)
def test_audit_runs_without_error(eid: str, pipeline: Pipeline) -> None:
    """audit_enquiry must return a result dict with no 'error' key."""
    info = ENQUIRIES[eid]
    result = audit_enquiry(eid, info, pipeline)
    assert "error" not in result, f"Audit failed for {eid}: {result.get('error')}"


@pytest.mark.parametrize("eid", AUDIT_EIDS)
def test_audit_result_fields(eid: str, pipeline: Pipeline) -> None:
    """Result must contain all required fields with sensible types."""
    info = ENQUIRIES[eid]
    result = audit_enquiry(eid, info, pipeline)
    if "error" in result:
        pytest.skip(f"Audit errored for {eid}: {result['error']}")

    assert result["eid"] == eid
    assert isinstance(result["source_row_count"], int)
    assert result["source_row_count"] > 0, "source_row_count must be > 0"
    assert isinstance(result["extracted_count"], int)
    assert result["extracted_count"] >= 0
    assert isinstance(result["missing"], int)
    assert result["missing"] >= 0
    assert isinstance(result["low_confidence_count"], int)
    assert 0.0 <= result["fidelity"] <= 1.0
    assert isinstance(result["items"], list)
    assert isinstance(result["flagged"], list)


@pytest.mark.parametrize("eid", AUDIT_EIDS)
def test_format_audit_report(eid: str, pipeline: Pipeline) -> None:
    """Formatted report must contain the enquiry ID and key headings."""
    info = ENQUIRIES[eid]
    result = audit_enquiry(eid, info, pipeline)
    if "error" in result:
        pytest.skip(f"Audit errored for {eid}: {result['error']}")

    report = format_audit_report(result)
    assert eid in report
    assert "FIDELITY AUDIT" in report
    assert "Source BOQ rows" in report
    assert "Extracted rows" in report
    assert "Fidelity" in report


def test_format_summary_table(pipeline: Pipeline) -> None:
    """Summary table must include a TOTAL row and all audited enquiry IDs."""
    results = [audit_enquiry(eid, ENQUIRIES[eid], pipeline) for eid in AUDIT_EIDS]
    table = format_summary_table(results)
    assert "TOTAL" in table
    for eid in AUDIT_EIDS:
        assert eid in table


def test_fidelity_is_ratio_not_percentage(pipeline: Pipeline) -> None:
    """fidelity field must be a float in [0, 1], not a percentage integer."""
    eid = AUDIT_EIDS[0]
    result = audit_enquiry(eid, ENQUIRIES[eid], pipeline)
    if "error" in result:
        pytest.skip(f"Audit errored for {eid}: {result['error']}")
    assert 0.0 <= result["fidelity"] <= 1.0
