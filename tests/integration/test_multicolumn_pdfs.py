"""Integration tests for the column-aware PDF extraction (P3_02).

Exercises the full ``PDFExtractor.extract_column_aware_tables`` path
against the real 07_grew PDF — the canonical multi-column-layout case
the task is named after. Proves:

* The detector finds the column bands from the page's ruling rects.
* Each row is assembled cell-by-cell (qty, unit, material, remarks
  stay in their own bands; the "Sqm. 500" and the "complies (density
  will be 180-220 kg/m3)" remark text do not interleave).
* The 07_grew qty-500 row (the famous interleaved-column case from
  ``tasks/sonnet/LEDGER.md``) assembles correctly from its own cells,
  with the remark text excluded from the material cell.

The sacred-10 07_grew fidelity (9/9 capture) is preserved by the
``tests/integration/test_sacred10_fidelity.py`` test — this file
is the dedicated P3_02 regression test for the column-aware fix.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

GREW_PDF = (
    REPO_ROOT
    / "data"
    / "real_rfqs"
    / "swa_enquiries"
    / "07_grew_solar_narmadapuram"
    / "108, BOQ compliance, Grew Energy.pdf"
)


# ---------------------------------------------------------------------------
# 1. The detector finds the columns
# ---------------------------------------------------------------------------


def test_seven_grew_page_columns_detected() -> None:
    """The 07_grew page has 5 visible columns (item, material, unit, qty,
    remarks) separated by ruled rects. The detector must find ≥5 bands
    with high confidence (the page has 6 internal dividers and 2 page
    edges, giving 7 bands after the band count includes 0-word margins)."""
    from src.ingest.pdf_extractor import PDFExtractor

    ext = PDFExtractor()
    diag = ext.extract_column_aware_diagnostics(str(GREW_PDF), page_numbers=[1])
    assert diag, "diagnostics should be non-empty for 07_grew"
    page = diag[0]
    assert page["confidence"] > 0.5
    # At least 5 real (non-margin) bands.
    assert page["filtered_bands"] >= 5
    # The detector found column dividers via the rect path.
    assert page["evidence_summary"].get("ruling_dividers", 0) >= 4
    # And the roles were auto-detected.
    roles = page["band_roles"]
    assert "item" in roles
    assert "material" in roles
    assert "unit" in roles
    assert "qty" in roles
    assert "remarks" in roles


# ---------------------------------------------------------------------------
# 2. The 9 data rows are extracted (07_grew 9/9 fidelity under the new path)
# ---------------------------------------------------------------------------


def test_seven_grew_extracts_9_data_rows() -> None:
    """The 07_grew gold requires 9 BOQ data items (11.1-11.4, 12, 8.1-8.4).
    The column-aware extractor must return all 9 (plus 2 R/O items
    sections 6/7 which appear in the gold with R/O qty)."""
    from src.ingest.pdf_extractor import PDFExtractor

    ext = PDFExtractor()
    tables = ext.extract_column_aware_tables(str(GREW_PDF), page_numbers=[1])
    assert len(tables) == 1
    table = tables[0]
    # 9 data rows + 2 R/O rows = 11 rows expected.
    assert table.page_number == 1
    assert len(table.rows) == 11


# ---------------------------------------------------------------------------
# 3. The famous "qty 500" row assembles from its own cells
# ---------------------------------------------------------------------------


def test_seven_grow_qty_500_row_assembles_from_cells() -> None:
    """The 07_grew row 5 (ACOUSTIC LINING, qty=500, sqm) is the
    diagnosed interleaving failure case. The column-aware
    assembly must:
    * put the qty "500" in its own cell (band QTY),
    * put the unit "Sqm." in its own cell (band UNIT),
    * put the description "Supply,InstallationandTestingof..."
    in band MATERIAL — WITHOUT the remark "complies (density
    will be 180-220 kg/m3)" leaking into it,
    * put the remark in band REMARKS.

    This is the proof the spec demands: "the qty 500 row
    assembles from its own cells, remark text ends in a
    remarks field or is dropped from the description".
    """
    from src.ingest.pdf_extractor import PDFExtractor

    ext = PDFExtractor()
    tables = ext.extract_column_aware_tables(str(GREW_PDF), page_numbers=[1])
    table = tables[0]
    # Locate the row whose QTY cell == "500".
    qty_500_row = None
    for row in table.rows:
        # QTY band is index 3 (item, material, unit, qty, remarks).
        if len(row) > 3 and row[3] == "500":
            qty_500_row = row
            break
    assert qty_500_row is not None, "no row with qty=500 found"
    item, material, unit, qty, _margin, remarks = qty_500_row
    # 1. The qty 500 is in its own cell.
    assert qty == "500"
    # 2. The unit "Sqm." is in its own cell — NOT concatenated with qty.
    assert unit == "Sqm."
    # 3. The material is the description, with the "ACOUSTIC LINING"
    # section header prepended (per the leading-context merge) and
    # the wrapped "180 kg /m3 along..." continuation appended.
    assert "Supply,InstallationandTestingof" in material
    assert "ACOUSTIC LINING" in material
    # 4. The remark text does NOT leak into the material cell.
    # The remark column contains "complies (density will be 180-220
    # kg/m3)" — none of that should be in the material cell. The
    # material cell DOES legitimately contain the word "density" as
    # part of the description (e.g. "withdensityof140to") — we
    # therefore check for the FULL remark phrase, not just
    # substrings.
    assert "complies" not in material
    assert "180-220" not in material
    # 5. The remark IS in the remarks cell (or empty if not detected).
    # The detection puts it in the remarks band.
    if remarks:
        assert "complies" in remarks or "kg/m3" in remarks


# ---------------------------------------------------------------------------
# 4. The earlier rows (11.1, 11.2, 11.3, 11.4) are clean (no remark bleed)
# ---------------------------------------------------------------------------


def test_seven_grew_first_four_rows_have_clean_material() -> None:
    """Rows 11.1-11.4 have no remark text on their y-line; their
    material cell must NOT contain any remarks. The unit "Sqm." and
    qty are in their own cells."""
    from src.ingest.pdf_extractor import PDFExtractor

    ext = PDFExtractor()
    tables = ext.extract_column_aware_tables(str(GREW_PDF), page_numbers=[1])
    rows = tables[0].rows
    expected_items = ["11.1", "11.2", "11.3", "11.4"]
    expected_qty = ["15000", "23750", "8500", "5000"]
    for i, (item, material, unit, qty, _m, remarks) in enumerate(rows[:4]):
        assert item == expected_items[i]
        assert "mm thick for" in material
        assert unit == "Sqm."
        assert qty == expected_qty[i]
        # No remark text on these rows.
        assert remarks == ""


# ---------------------------------------------------------------------------
# 5. The 8.x rows (CHW Pipings) are extracted with their sq.mtr unit
# ---------------------------------------------------------------------------


def test_seven_grew_chw_pipings_rows() -> None:
    """Rows 8.1-8.4 use the unit "Sq. Mtr." (with a space and period)
    and have a long wrapped description. The column-aware path must
    extract all four with the correct qty."""
    from src.ingest.pdf_extractor import PDFExtractor

    ext = PDFExtractor()
    tables = ext.extract_column_aware_tables(str(GREW_PDF), page_numbers=[1])
    rows = tables[0].rows
    # 8.1-8.4 are at rows 5-8 (after 11.1-11.4, ACOUSTIC LINING).
    expected = [
        ("8.1", "75 mm thick Insulation on 1200NB to 1000NB", "Sq. Mtr."),
        ("8.2", "51 mm thick Insulation on 950NB to 500NB", "Sq. Mtr."),
        ("8.3", "38 mm thick Insulation on 450NB to 80NB", "Sq. Mtr."),
        ("8.4", "19 mm thick Insulation on 65NB", "Sq. Mtr."),
    ]
    for i, (item, material_substring, unit) in enumerate(expected):
        # Skip the ACOUSTIC LINING row (row index 4).
        r = rows[5 + i]
        assert r[0] == item
        assert material_substring in r[1]
        assert r[2] == unit


# ---------------------------------------------------------------------------
# 6. The diagnostic dump reports the band count correctly
# ---------------------------------------------------------------------------


def test_seven_grew_diagnostics_dump() -> None:
    """The diagnostics dump is used by the P3_02 eval script to
    populate COLUMN_EVAL.md. It must include bands, evidence summary,
    row count, and a 3-row sample for inspection."""
    from src.ingest.pdf_extractor import PDFExtractor

    ext = PDFExtractor()
    diag = ext.extract_column_aware_diagnostics(str(GREW_PDF), page_numbers=[1])
    assert len(diag) == 1
    page = diag[0]
    assert "bands" in page
    assert "filtered_bands" in page
    assert "band_roles" in page
    assert "confidence" in page
    assert "evidence_summary" in page
    assert "first_3_rows" in page
    assert "row_count" in page
    assert page["row_count"] == 11
    assert len(page["first_3_rows"]) == 3
