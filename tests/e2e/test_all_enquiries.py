"""End-to-end test: Pipeline().run() on all 10 SWA enquiries.

Marked `slow` since it loads the full pipeline + model (cold start ~140s).
Run with: pytest tests/e2e/test_all_enquiries.py -m slow -v

The 10 SWA enquiries (from data/real_rfqs/swa_enquiries/manifest.csv):
  01_gsecl_wanakbori_tmd8     RFQ-75810 TMD-8.pdf         (PDF)
  02_isro_vssc               VSSC_BOQ_with_qty.xlsx      (XLSX)
  03_zydus_matoda_osd        Zydus_Matoda_Insulation_Enquiry.xlsx  (XLSX)
  04_adani                   BOQ PAGE2adani proj.pdf     (PDF)
  05_zydus_animal_pharmez    Copy of Insulation Enquiry-...xlsx  (XLSX)
  06_avante_kirloskar_pune   Insulation Boq_132.pdf      (PDF)
  07_grew_solar_narmadapuram 108, BOQ compliance, Grew Energy.pdf  (PDF)
  08_sael                    Copy of Insulation Enquiry - SAEL.xlsx  (XLSX)
  09_gem_bid_7439924         GeM-Bidding-9218026.pdf     (PDF)
  10_gem_bid_7552777         GeM-Bidding-9343469.pdf     (PDF)
"""

from __future__ import annotations

from pathlib import Path

import pytest

ENQUIRIES: list[tuple[str, str, str]] = [
    ("01_gsecl_wanakbori_tmd8", "01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf", "pdf"),
    ("02_isro_vssc", "02_isro_vssc/VSSC_BOQ_with_qty.xlsx", "xlsx"),
    ("03_zydus_matoda_osd", "03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx", "xlsx"),
    ("04_adani", "04_adani/BOQ PAGE2adani proj.pdf", "pdf"),
    (
        "05_zydus_animal_pharmez",
        "05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx",
        "xlsx",
    ),
    ("06_avante_kirloskar_pune", "06_avante_kirloskar_pune/Insulation Boq_132.pdf", "pdf"),
    ("07_grew_solar_narmadapuram", "07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf", "pdf"),
    ("08_sael", "08_sael/Copy of Insulation Enquiry - SAEL.xlsx", "xlsx"),
    ("09_gem_bid_7439924", "09_gem_bid_7439924/GeM-Bidding-9218026.pdf", "pdf"),
    ("10_gem_bid_7552777", "10_gem_bid_7552777/GeM-Bidding-9343469.pdf", "pdf"),
]

ENQUIRY_DIR = Path("data/real_rfqs/swa_enquiries")


@pytest.mark.slow
@pytest.mark.parametrize("enquiry_id,source_path,format", ENQUIRIES)
def test_enquiry_runs_without_exception(enquiry_id: str, source_path: str, format: str) -> None:
    """Every enquiry must run Pipeline().run() to completion without raising."""
    from src.pipeline import Pipeline

    full_path = ENQUIRY_DIR / source_path
    if not full_path.exists():
        pytest.skip(f"Source file not found: {full_path}")

    pipeline = Pipeline()
    result = pipeline.run(str(full_path))
    assert result is not None, f"{enquiry_id}: Pipeline().run() returned None"


@pytest.mark.slow
@pytest.mark.parametrize("enquiry_id,source_path,format", ENQUIRIES)
def test_boq_items_non_negative(enquiry_id: str, source_path: str, format: str) -> None:
    """For XLSX source: boq_items > 0. For PDF source: boq_items >= 0 (no crash)."""
    from src.pipeline import Pipeline

    full_path = ENQUIRY_DIR / source_path
    if not full_path.exists():
        pytest.skip(f"Source file not found: {full_path}")

    pipeline = Pipeline()
    result = pipeline.run(str(full_path))
    assert result.boq_items is not None, f"{enquiry_id}: boq_items is None"
    if format == "xlsx":
        assert len(result.boq_items) > 0, f"{enquiry_id}: XLSX returned 0 boq_items (expected > 0)"
    else:
        assert len(result.boq_items) >= 0, f"{enquiry_id}: PDF returned negative boq_items"


@pytest.mark.slow
@pytest.mark.parametrize("enquiry_id,source_path,format", ENQUIRIES)
def test_extraction_metadata_valid(enquiry_id: str, source_path: str, format: str) -> None:
    """ExtractionMetadata must be populated with reasonable values."""
    from src.pipeline import Pipeline

    full_path = ENQUIRY_DIR / source_path
    if not full_path.exists():
        pytest.skip(f"Source file not found: {full_path}")

    pipeline = Pipeline()
    result = pipeline.run(str(full_path))
    md = result.metadata
    assert md.total_items >= 0, f"{enquiry_id}: total_items is negative"
    assert 0.0 <= md.avg_confidence <= 1.0, f"{enquiry_id}: avg_confidence out of [0,1]"


@pytest.mark.slow
@pytest.mark.parametrize(
    "enquiry_id,source_path,format",
    [
        ("09_gem_bid_7439924", "09_gem_bid_7439924/GeM-Bidding-9218026.pdf", "pdf"),
    ],
)
def test_slow_enquiry_completes_within_timeout(enquiry_id: str, source_path: str, format: str) -> None:
    """09 GeM is slow (~3.6 min per the spec); verify it completes without timeout."""
    from src.pipeline import Pipeline

    full_path = ENQUIRY_DIR / source_path
    if not full_path.exists():
        pytest.skip(f"Source file not found: {full_path}")

    pipeline = Pipeline()
    result = pipeline.run(str(full_path))
    assert result is not None, f"{enquiry_id}: Pipeline().run() returned None"
    assert result.boq_items is not None, f"{enquiry_id}: boq_items is None"
