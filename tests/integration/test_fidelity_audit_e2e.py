"""Integration test: fidelity audit end-to-end on 2 sacred docs (P1_02)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402
from src.domain.fidelity import FidelityAuditor  # noqa: E402


@pytest.fixture(scope="module")
def source_truth() -> dict:
    import json

    return json.loads((REPO_ROOT / "data/real_rfqs/source_truth.json").read_text())


@pytest.fixture(scope="module")
def auditor() -> FidelityAuditor:
    return FidelityAuditor()


def test_audit_02_isro_end_to_end(auditor: FidelityAuditor, source_truth: dict) -> None:
    """02_isro: 4 source rows, pipeline should capture all 4 → PASS."""
    from src.pipeline_xlsx import XLSXRowPipeline

    xlsx = REPO_ROOT / "data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx"
    if not xlsx.exists():
        pytest.skip(f"source file missing: {xlsx}")
    rows = XLSXRowPipeline().run(str(xlsx))
    report = auditor.audit("02_isro_vssc", rows, source_truth)
    assert report.source_row_count == 4, f"expected 4 source rows, got {report.source_row_count}"
    # 02_isro should PASS (4 captured, 0 missing, 0 extra) per P0_02
    assert report.verdict == "PASS", f"02_isro should PASS: {report.missing_count} missing, {report.extra_count} extra"


def test_audit_03_zydus_end_to_end(auditor: FidelityAuditor, source_truth: dict) -> None:
    """03_zydus: 33 source rows, pipeline should capture all 33 → PASS."""
    from src.pipeline_xlsx import XLSXRowPipeline

    xlsx = REPO_ROOT / "data/real_rfqs/swa_enquiries/03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx"
    if not xlsx.exists():
        pytest.skip(f"source file missing: {xlsx}")
    rows = XLSXRowPipeline().run(str(xlsx))
    report = auditor.audit("03_zydus_matoda_osd", rows, source_truth)
    assert report.source_row_count == 33, f"expected 33 source rows, got {report.source_row_count}"
    assert report.verdict == "PASS", f"03_zydus should PASS: {report.missing_count} missing, {report.extra_count} extra"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
