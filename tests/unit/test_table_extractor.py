"""Tests for TableExtractor."""

from src.ingest.table_extractor import ExtractedTable, TableExtractor


class TestTableExtractor:
    def test_init(self):
        extractor = TableExtractor()
        assert extractor._section_headers == {}

    def test_map_to_boq_rows_empty(self):
        extractor = TableExtractor()
        result = extractor.map_to_boq_rows([])
        assert result == []

    def test_looks_like_boq_table_positive(self):
        extractor = TableExtractor()
        table = ExtractedTable(
            page_number=1,
            rows=[
                ["Item", "Description", "Quantity", "Unit"],
                ["1", "Cement", "100", "bags"],
            ],
            headers=["Item", "Description", "Quantity", "Unit"],
        )
        assert extractor._looks_like_boq_table(table) is True

    def test_looks_like_boq_table_negative(self):
        extractor = TableExtractor()
        table = ExtractedTable(
            page_number=1,
            rows=[["Random", "Data", "Here"]],
            headers=["Random", "Data", "Here"],
        )
        assert extractor._looks_like_boq_table(table) is False

    def test_looks_like_boq_table_empty(self):
        extractor = TableExtractor()
        table = ExtractedTable(page_number=1, rows=[], headers=[])
        assert extractor._looks_like_boq_table(table) is False

    def test_has_header(self):
        extractor = TableExtractor()
        table = ExtractedTable(
            page_number=1,
            rows=[["Item", "Description"]],
            headers=["Item", "Description"],
        )
        assert extractor._has_header(table) is True

    def test_has_header_missing(self):
        extractor = TableExtractor()
        table = ExtractedTable(
            page_number=1,
            rows=[["Data", "Here"]],
            headers=[],
        )
        assert extractor._has_header(table) is False

    def test_parse_boq_row(self):
        extractor = TableExtractor()
        table = ExtractedTable(page_number=1, rows=[], headers=[])
        row = ["1", "Cement", "100", "bags", "M20", "foundation"]
        result = extractor._parse_boq_row(row, table)
        assert result is not None
        assert result["material"] == "Cement"
        assert result["quantity"] == 100.0
        assert result["unit"] == "bags"

    def test_parse_boq_row_short(self):
        extractor = TableExtractor()
        table = ExtractedTable(page_number=1, rows=[], headers=[])
        row = ["short"]
        result = extractor._parse_boq_row(row, table)
        assert result is None


class TestB1MergedCellSplit:
    def test_merged_cell_splits_into_two_rows(self):
        extractor = TableExtractor()
        table = ExtractedTable(page_number=1, rows=[], headers=[])
        row = ["2.1", "500 mm dia\n400 mm dia", "1044", "Rmt."]
        result = extractor._parse_boq_row(row, table)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["material"] == "500 mm dia"
        assert result[1]["material"] == "400 mm dia"
        assert result[0]["quantity"] == 1044.0
        assert result[1]["quantity"] == 1044.0

    def test_merged_cell_splits_into_three_rows(self):
        extractor = TableExtractor()
        table = ExtractedTable(page_number=1, rows=[], headers=[])
        row = ["3.1", "300 mm dia\n400 mm dia\n500 mm dia", "200", "Rmt."]
        result = extractor._parse_boq_row(row, table)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_non_merged_cell_returns_single_row(self):
        extractor = TableExtractor()
        table = ExtractedTable(page_number=1, rows=[], headers=[])
        row = ["1", "Cement", "100", "bags"]
        result = extractor._parse_boq_row(row, table)
        assert isinstance(result, dict)
        assert result["material"] == "Cement"

    def test_newline_without_dim_pattern_does_not_split(self):
        extractor = TableExtractor()
        table = ExtractedTable(page_number=1, rows=[], headers=[])
        row = ["1", "Item A\nItem B", "100", "kg"]
        result = extractor._parse_boq_row(row, table)
        assert isinstance(result, dict)


class TestB2HeaderInference:
    def test_pure_dimension_prepends_header(self):
        extractor = TableExtractor()
        extractor._section_headers = {1: "Acoustic Lining"}
        table = ExtractedTable(page_number=1, rows=[], headers=[])
        row = ["1", "15 mm thick", "100", "sqm"]
        result = extractor._parse_boq_row(row, table)
        assert result is not None
        assert "Acoustic Lining" in result["material"]

    def test_no_header_available_stays_unchanged(self):
        extractor = TableExtractor()
        extractor._section_headers = {}
        table = ExtractedTable(page_number=1, rows=[], headers=[])
        row = ["1", "15 mm thick", "100", "sqm"]
        result = extractor._parse_boq_row(row, table)
        assert result is not None
        assert result["material"] == "15 mm thick"

    def test_material_with_name_not_affected(self):
        extractor = TableExtractor()
        extractor._section_headers = {1: "Acoustic Lining"}
        table = ExtractedTable(page_number=1, rows=[], headers=[])
        row = ["1", "Cement 15 mm thick", "100", "sqm"]
        result = extractor._parse_boq_row(row, table)
        assert result is not None
        assert "Acoustic" not in result["material"]

    def test_find_section_header_returns_title_case(self):
        extractor = TableExtractor()
        header = extractor._find_section_header("ACOUSTIC LINING\nItem details follow")
        assert header == "Acoustic Lining"

    def test_find_section_header_skips_boilerplate(self):
        extractor = TableExtractor()
        header = extractor._find_section_header("SCHEDULE OF QUANTITIES\nItem details follow")
        assert header == ""


class TestB3Timeout:
    def test_extract_nonexistent_returns_empty(self):
        extractor = TableExtractor()
        result = extractor.extract("nonexistent.pdf", timeout_sec=0.001, max_pages=5)
        assert result == []


class TestMapToBoqRows:
    def test_map_to_boq_rows_handles_list_from_parse(self):
        extractor = TableExtractor()
        table = ExtractedTable(
            page_number=1,
            rows=[
                ["Item", "Description", "Qty", "Unit"],
                ["2.1", "500 mm dia\n400 mm dia", "1044", "Rmt."],
            ],
            headers=["Item", "Description", "Qty", "Unit"],
        )
        result = extractor.map_to_boq_rows([table])
        assert len(result) == 2


class TestC1MissingUnits:
    def test_cell_is_unit_mtrs(self):
        extractor = TableExtractor()
        assert extractor._cell_is_unit("mtrs") is True

    def test_cell_is_unit_rmtr(self):
        extractor = TableExtractor()
        assert extractor._cell_is_unit("Rmtr") is True

    def test_cell_is_unit_m(self):
        extractor = TableExtractor()
        assert extractor._cell_is_unit("M") is True


class TestC2RawMaterialCellFallback:
    def test_parse_boq_row_fallback_with_ro_qty(self):
        """Rows where qty is 'RO' (not numeric) must not crash with UnboundLocalError.

        Regression: raw_material_cell was only assigned in the primary branch
        (unit_idx != -1 and qty_idx != -1).  When qty_idx stayed -1 (RO is not
        numeric), the fallback branch ran and then hit ``raw_material_cell or
        material`` at the end — raising UnboundLocalError and returning None.
        """
        extractor = TableExtractor()
        table = ExtractedTable(page_number=1, rows=[], headers=[])
        row = ["3.02", "32 mm Dia", "Rmt.", "RO", ""]
        result = extractor._parse_boq_row(row, table)
        assert result is not None
        assert isinstance(result, dict)
        assert result["material"] == "32 mm Dia"
        assert result["unit"] == "Rmt."
        assert result["rate_only"] is True

    def test_parse_boq_row_fallback_with_qty_in_prev_cell(self):
        """Fallback branch should still return a dict when unit is found but qty is not."""
        extractor = TableExtractor()
        table = ExtractedTable(page_number=1, rows=[], headers=[])
        row = ["", "600 mm dia", "Rmtr", "1 44.00", ""]
        result = extractor._parse_boq_row(row, table)
        assert result is not None
        assert isinstance(result, dict)
        assert "600 mm dia" in result["material"]
        assert result["unit"] == "Rmtr"
