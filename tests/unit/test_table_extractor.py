"""Tests for TableExtractor."""



from src.ingest.table_extractor import ExtractedTable, TableExtractor


class TestTableExtractor:
    def test_init(self):
        extractor = TableExtractor()
        assert extractor.flavor == "auto"

    def test_init_custom_flavor(self):
        extractor = TableExtractor(flavor="lattice")
        assert extractor.flavor == "lattice"

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
        assert result["quantity"] == "100"
        assert result["unit"] == "bags"

    def test_parse_boq_row_short(self):
        extractor = TableExtractor()
        table = ExtractedTable(page_number=1, rows=[], headers=[])
        row = ["short"]
        result = extractor._parse_boq_row(row, table)
        assert result is None
