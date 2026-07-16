"""Tests for table_classifier (P3_03)."""

from src.ingest.table_classifier import TableType, classify_table


class TestMakeListHeuristic:
    def test_empty_make_column_is_boq_not_make_list(self):
        """A table with a 'Make' header but mostly empty cells is a BOQ with an
        optional vendor tracking column, not a vendor/make list."""
        header = ["S. No.", "DESCRIPTION", "Unit", "QTY", "Make"]
        sample = [
            [1, "THERMAL INSULATION FOR DUCT", None, None, "Armaflex/ ALP Aeroflex / K-Flex"],
            [None, "Supplying and fixing...", None, None, None],
            [None, "Thermal insulation material...", None, None, None],
            [1.1, "19 mm", "SQM.", 135, None],
            [None, None, None, None, None],
            [2, "DUCT ACOUSTIC LINING", None, None, None],
            [None, "Supplying and fixing...", None, None, None],
            [2.1, "15mm", "SQM.", 55, None],
            [None, None, None, None, None],
            [None, None, None, None, None],
        ]
        result = classify_table(header, sample)
        assert result == TableType.BOQ

    def test_filled_make_column_is_make_list(self):
        """When the Make column is populated in most rows, it really is a make list."""
        header = ["S. No.", "DESCRIPTION", "Unit", "QTY", "Make"]
        sample = [
            [1, "THERMAL INSULATION", "SQM", 135, "Armaflex"],
            [2, "ACOUSTIC LINING", "SQM", 200, "K-Flex"],
            [3, "DUCT INSULATION", "SQM", 50, "Armaflex"],
        ]
        result = classify_table(header, sample)
        assert result == TableType.MAKE_LIST

    def test_no_make_column_is_boq(self):
        """Classic BOQ table without any make/vendor column."""
        header = ["Sr. No.", "Description", "Unit", "Qty"]
        sample = [
            [1, "Cement", "bags", 100],
            [2, "Sand", "cum", 5],
        ]
        result = classify_table(header, sample)
        assert result == TableType.BOQ

    def test_single_filled_make_cell_is_boq(self):
        """Only one Make cell filled in 10 rows → still BOQ."""
        header = ["Item", "Description", "Unit", "Qty.", "Make"]
        sample = [
            [7, "Underdeck insulation", "Sqm", 1100, "Armaflex / ALP Aeroflex / K-Flex"],
            [None, None, None, None, None],
            [None, None, None, None, None],
            [None, None, None, None, None],
            [None, None, None, None, None],
            [None, None, None, None, None],
            [None, None, None, None, None],
            [None, None, None, None, None],
            [None, None, None, None, None],
            [None, None, None, None, None],
        ]
        result = classify_table(header, sample)
        assert result == TableType.BOQ
