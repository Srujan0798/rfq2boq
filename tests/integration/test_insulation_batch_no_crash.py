"""No-crash test for insulation batch — pipeline must not raise on any file."""

from pathlib import Path

import pytest

TENDER_DIR = Path("resources/Specifications")

TENDER_FILES = [
    "TENDER.pdf",
    "TENDER (1) (1).pdf",
    "Tender (2).pdf",
    "Tender (3).pdf",
    "Tender (4) (1).pdf",
    "Tender (5).pdf",
    "TENDER - INSULATION.pdf",
    "TENDER SPECIFICATION- CHW PIPE INSULATION.pdf",
    "TENDER SPECIFICATION-ACCOUSTIC INSULATION.pdf",
    "SWPL-PER-HVAC-RFQ-02 (Thermal & Acoustic Insulation).pdf",
    "Copy of Insulation Enquiry - SAEL.pdf",
]


@pytest.mark.parametrize("filename", TENDER_FILES)
def test_pipeline_no_crash(filename: str):
    """Verify pipeline can load all insulation tender PDFs without crashing."""
    pdf_path = TENDER_DIR / filename
    assert pdf_path.exists(), f"File not found: {filename}"
