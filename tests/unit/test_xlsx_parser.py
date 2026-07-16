"""Tests for XLSX parsing."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from src.ingest.xlsx_parser import XLSXParser


class TestXLSXParser:
    """Tests for XLSXParser using mocked openpyxl."""

    def test_parse_empty_workbook(self):
        with TemporaryDirectory() as tmpdir:
            xlsx_file = Path(tmpdir) / "empty.xlsx"
            wb_patch = MagicMock()
            wb_patch.sheetnames = []
            ws_patch = MagicMock()
            ws_patch.iter_rows.return_value = iter([])
            wb_patch.__getitem__ = MagicMock(return_value=ws_patch)

            with patch("openpyxl.load_workbook", return_value=wb_patch):
                parser = XLSXParser()
                result = parser.parse(xlsx_file)

            assert result.metadata["sheet_count"] == 0
            assert result.metadata["total_rows"] == 0

    def test_parse_single_sheet_single_row(self):
        with TemporaryDirectory() as tmpdir:
            xlsx_file = Path(tmpdir) / "single.xlsx"
            wb_patch = MagicMock()
            wb_patch.sheetnames = ["Sheet1"]
            ws_patch = MagicMock()
            ws_patch.iter_rows.return_value = iter([("Header1", "Header2")])
            wb_patch.__getitem__ = MagicMock(return_value=ws_patch)

            with patch("openpyxl.load_workbook", return_value=wb_patch):
                parser = XLSXParser()
                result = parser.parse(xlsx_file)

            assert result.metadata["sheet_count"] == 1
            assert result.metadata["total_rows"] == 0
            assert len(result.sheets) == 1
            assert result.sheets[0].name == "Sheet1"
            assert result.sheets[0].headers == ["Header1", "Header2"]
            assert result.sheets[0].rows == []

    def test_parse_multiple_sheets(self):
        with TemporaryDirectory() as tmpdir:
            xlsx_file = Path(tmpdir) / "multi.xlsx"
            wb_patch = MagicMock()
            wb_patch.sheetnames = ["Sheet1", "Sheet2"]
            ws1 = MagicMock()
            ws1.iter_rows.return_value = iter([("A", "B"), ("1", "2")])
            ws2 = MagicMock()
            ws2.iter_rows.return_value = iter([("X", "Y"), ("10", "20")])
            wb_patch.__getitem__ = MagicMock(side_effect=lambda s: {"Sheet1": ws1, "Sheet2": ws2}[s])

            with patch("openpyxl.load_workbook", return_value=wb_patch):
                parser = XLSXParser()
                result = parser.parse(xlsx_file)

            assert result.metadata["sheet_count"] == 2
            assert len(result.sheets) == 2
            assert result.sheets[0].name == "Sheet1"
            assert result.sheets[0].headers == ["A", "B"]
            assert result.sheets[0].rows == [["1", "2"]]
            assert result.sheets[1].name == "Sheet2"
            assert result.sheets[1].headers == ["X", "Y"]
            assert result.sheets[1].rows == [["10", "20"]]

    def test_parse_handles_none_cells(self):
        with TemporaryDirectory() as tmpdir:
            xlsx_file = Path(tmpdir) / "none.xlsx"
            wb_patch = MagicMock()
            wb_patch.sheetnames = ["Sheet1"]
            ws_patch = MagicMock()
            ws_patch.iter_rows.return_value = iter([(None, "Header2", None), ("val1", None, "val3")])
            wb_patch.__getitem__ = MagicMock(return_value=ws_patch)

            with patch("openpyxl.load_workbook", return_value=wb_patch):
                parser = XLSXParser()
                result = parser.parse(xlsx_file)

            assert result.sheets[0].headers == ["", "Header2", ""]
            assert result.sheets[0].rows == [["val1", "", "val3"]]

    def test_parse_strips_whitespace(self):
        with TemporaryDirectory() as tmpdir:
            xlsx_file = Path(tmpdir) / "strip.xlsx"
            wb_patch = MagicMock()
            wb_patch.sheetnames = ["Sheet1"]
            ws_patch = MagicMock()
            ws_patch.iter_rows.return_value = iter([("  Header  ",), ("  data  ",)])
            wb_patch.__getitem__ = MagicMock(return_value=ws_patch)

            with patch("openpyxl.load_workbook", return_value=wb_patch):
                parser = XLSXParser()
                result = parser.parse(xlsx_file)

            assert result.sheets[0].headers == ["Header"]
            assert result.sheets[0].rows == [["data"]]

    def test_parse_skips_empty_rows(self):
        with TemporaryDirectory() as tmpdir:
            xlsx_file = Path(tmpdir) / "empty_rows.xlsx"
            wb_patch = MagicMock()
            wb_patch.sheetnames = ["Sheet1"]
            ws_patch = MagicMock()
            ws_patch.iter_rows.return_value = iter(
                [
                    ("H1", "H2"),
                    (None, None),
                    ("val1", "val2"),
                    (None, None),
                ]
            )
            wb_patch.__getitem__ = MagicMock(return_value=ws_patch)

            with patch("openpyxl.load_workbook", return_value=wb_patch):
                parser = XLSXParser()
                result = parser.parse(xlsx_file)

            assert result.sheets[0].rows == [["val1", "val2"]]

    def test_metadata_total_rows_and_max_row(self):
        with TemporaryDirectory() as tmpdir:
            xlsx_file = Path(tmpdir) / "meta.xlsx"
            wb_patch = MagicMock()
            wb_patch.sheetnames = ["S1", "S2"]
            ws1 = MagicMock()
            ws1.iter_rows.return_value = iter([("H",), ("a",), ("b",), ("c",)])
            ws2 = MagicMock()
            ws2.iter_rows.return_value = iter([("X",), ("y",), ("z",)])
            wb_patch.__getitem__ = MagicMock(side_effect=lambda s: {"S1": ws1, "S2": ws2}[s])

            with patch("openpyxl.load_workbook", return_value=wb_patch):
                parser = XLSXParser()
                result = parser.parse(xlsx_file)

            assert result.metadata["total_rows"] == 5
            assert result.metadata["max_row"] == 3
