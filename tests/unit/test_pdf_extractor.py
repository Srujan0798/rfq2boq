"""Tests for PDF text and table extraction."""

from unittest.mock import MagicMock, patch

from src.ingest.pdf_extractor import DocumentContent, PageText, PDFExtractor, TableData


class TestPDFExtractor:
    def test_initialization(self):
        extractor = PDFExtractor()
        assert extractor.min_chars_per_page == 50

        extractor_custom = PDFExtractor(min_chars_per_page=100)
        assert extractor_custom.min_chars_per_page == 100

    def test_is_scanned_true_for_empty_pages(self):
        extractor = PDFExtractor()
        pages = [PageText(page_number=1, text="", width=100, height=100)]
        assert extractor.is_scanned(pages) is True

    def test_is_scanned_false_for_text_pages(self):
        extractor = PDFExtractor()
        pages = [
            PageText(page_number=1, text="This is a long text with many characters" * 10, width=100, height=100),
            PageText(page_number=2, text="Another page with substantial content" * 10, width=100, height=100),
        ]
        assert extractor.is_scanned(pages) is False

    def test_is_scanned_below_threshold(self):
        extractor = PDFExtractor(min_chars_per_page=100)
        pages = [
            PageText(page_number=1, text="Short text", width=100, height=100),
            PageText(page_number=2, text="More short text", width=100, height=100),
        ]
        assert extractor.is_scanned(pages) is True

    def test_is_scanned_empty_pages_returns_true(self):
        extractor = PDFExtractor()
        assert extractor.is_scanned([]) is True

    @patch("pdfplumber.open")
    def test_extract_text_returns_list_of_page_text(self, mock_pdf_open):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test page content"
        mock_page.width = 612.0
        mock_page.height = 792.0
        mock_page.bbox = (0, 0, 612, 792)
        mock_page.extract_tables.return_value = []

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        extractor = PDFExtractor()
        result = extractor.extract_text("dummy.pdf")

        assert len(result) == 1
        assert result[0].text == "Test page content"
        assert result[0].page_number == 1

    @patch("pdfplumber.open")
    def test_extract_full_text_concatenates_pages(self, mock_pdf_open):
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page1.width = 612.0
        mock_page1.height = 792.0
        mock_page1.bbox = (0, 0, 612, 792)
        mock_page1.extract_tables.return_value = []

        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 content"
        mock_page2.width = 612.0
        mock_page2.height = 792.0
        mock_page2.bbox = (0, 0, 612, 792)
        mock_page2.extract_tables.return_value = []

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        extractor = PDFExtractor()
        result = extractor.extract_full_text("dummy.pdf")

        assert "Page 1 content" in result
        assert "Page 2 content" in result

    @patch("pdfplumber.open")
    def test_extract_tables_returns_table_data(self, mock_pdf_open):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Content with table"
        mock_page.width = 612.0
        mock_page.height = 792.0
        mock_page.bbox = (0, 0, 612, 792)
        mock_page.extract_tables.return_value = [
            ["Item", "Qty", "Unit"],
            ["Cement", "50", "bags"],
            ["Steel", "200", "kg"],
        ]

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        extractor = PDFExtractor()
        result = extractor.extract_tables("dummy.pdf")

        assert len(result) == 3
        assert result[0].rows == ["Item", "Qty", "Unit"]
        assert result[1].rows == ["Cement", "50", "bags"]
        assert result[2].rows == ["Steel", "200", "kg"]

    @patch("pdfplumber.open")
    def test_extract_returns_document_content(self, mock_pdf_open):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test content"
        mock_page.width = 612.0
        mock_page.height = 792.0
        mock_page.bbox = (0, 0, 612, 792)
        mock_page.extract_tables.return_value = []

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)
        mock_pdf_open.return_value = mock_pdf

        extractor = PDFExtractor()
        result = extractor.extract("dummy.pdf")

        assert isinstance(result, DocumentContent)
        assert result.pdf_path == "dummy.pdf"
        assert len(result.pages) == 1
        assert result.metadata["total_pages"] == 1
        assert result.metadata["has_tables"] is False


class TestPageText:
    def test_page_text_creation(self):
        page = PageText(page_number=1, text="Test", width=100.0, height=200.0)
        assert page.page_number == 1
        assert page.text == "Test"
        assert page.width == 100.0
        assert page.height == 200.0


class TestTableData:
    def test_table_data_creation(self):
        table = TableData(
            page_number=1,
            rows=[["A", "B"], ["C", "D"]],
            top=0.0,
            bottom=100.0,
            left=0.0,
            right=200.0,
        )
        assert table.page_number == 1
        assert len(table.rows) == 2
        assert table.rows[0] == ["A", "B"]
