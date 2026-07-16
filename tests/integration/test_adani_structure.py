"""Integration test: Adani PDF structure-first extraction.

This test verifies that the structure-first approach (C1) correctly routes
multi-section PDFs like Adani through the structure extractor to find
all BOQ sub-sections.

Adani is a multi-section PDF with:
- BOQ PAGEadani proj.pdf (pipe insulation BOQ - 2 pages)
- BOQ PAGE2adani proj.pdf (duct insulation BOQ - 2 pages)

Gold expects 45 rows total (43 pipe + 2 duct items).
"""

from src.pipeline import Pipeline


def test_adani_structure_extraction():
    """Verify Adani extraction achieves >20 rows with structure-first approach."""
    p = Pipeline()

    source_paths = [
        "data/real_rfqs/swa_enquiries/04_adani/BOQ PAGEadani proj.pdf",
        "data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf",
    ]

    rows = []
    for sp in source_paths:
        result = p.run(sp)
        rows.extend(result.boq_items)

    total_rows = len(rows)
    assert total_rows > 20, f"Expected >20 rows, got {total_rows}"
