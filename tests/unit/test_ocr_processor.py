"""Tests for OCR processor using Tesseract."""

from unittest.mock import MagicMock, patch


class TestOCRProcessor:
    def test_initialization(self):
        from src.ingest.ocr_processor import OCRProcessor
        processor = OCRProcessor()
        assert processor.tesseract_cmd == "tesseract"

        processor_custom = OCRProcessor(tesseract_cmd="/usr/bin/tesseract")
        assert processor_custom.tesseract_cmd == "/usr/bin/tesseract"

    @patch("src.ingest.ocr_processor.OCRProcessor.process_image")
    def test_process_pdf_returns_ocr_result(self, mock_process_image):
        from src.ingest.ocr_processor import OCRLine, OCRPage, OCRProcessor

        mock_page = OCRPage(
            page_number=1,
            text="Hello world",
            lines=[OCRLine(words=[], text="Hello world")],
            conf_avg=0.85,
        )
        mock_process_image.return_value = type("MockResult", (), {
            "pages": [mock_page],
            "conf_avg": 0.85
        })()

        with patch("pdf2image.convert_from_path") as mock_convert:
            mock_image = MagicMock()
            mock_convert.return_value = [mock_image]

            processor = OCRProcessor()
            result = processor.process_pdf("dummy.pdf", dpi=300)

            assert len(result.pages) == 1

    @patch("src.ingest.ocr_processor.OCRProcessor.process_image")
    def test_process_pdf_multiple_pages(self, mock_process_image):
        from src.ingest.ocr_processor import OCRPage, OCRProcessor

        mock_pages = [
            OCRPage(page_number=i, text=f"Page {i}", lines=[], conf_avg=0.85)
            for i in range(1, 3)
        ]
        mock_result = type("MockResult", (), {
            "pages": mock_pages,
            "conf_avg": 0.85
        })()
        mock_process_image.return_value = mock_result

        with patch("pdf2image.convert_from_path") as mock_convert:
            mock_convert.return_value = [MagicMock(), MagicMock()]

            processor = OCRProcessor()
            result = processor.process_pdf("multi_page.pdf", dpi=300)

            assert len(result.pages) >= 1

    def test_process_image_returns_result(self):
        from src.ingest.ocr_processor import OCRProcessor

        with patch("pytesseract.image_to_data") as mock_ocr:
            mock_ocr.return_value = {
                "text": ["test", "page"],
                "conf": ["95", "90"],
                "left": [0, 10],
                "top": [0, 0],
                "width": [10, 10],
                "height": [5, 5],
                "line_num": [0, 0],
            }
            with patch("PIL.Image.open") as mock_img:
                mock_img.return_value = MagicMock()

                processor = OCRProcessor()
                result = processor.process_image("/tmp/test.png")

                assert result.pages[0].text == "test page"

    def test_process_image_handles_exception(self):
        from src.ingest.ocr_processor import OCRProcessor

        with patch("PIL.Image.open") as mock_img:
            mock_img.side_effect = Exception("Image open failed")

            processor = OCRProcessor()
            result = processor.process_image("/tmp/invalid.png")

            assert len(result.pages) == 0
            assert result.conf_avg == 0.0


class TestOCRPage:
    def test_ocr_page_creation(self):
        from src.ingest.ocr_processor import OCRPage
        page = OCRPage(page_number=1, text="Test OCR", lines=[], conf_avg=0.85)
        assert page.page_number == 1
        assert page.text == "Test OCR"
        assert page.conf_avg == 0.85


class TestOCRResult:
    def test_ocr_result_creation(self):
        from src.ingest.ocr_processor import OCRPage, OCRResult
        pages = [
            OCRPage(page_number=1, text="Page 1", lines=[], conf_avg=0.90),
            OCRPage(page_number=2, text="Page 2", lines=[], conf_avg=0.80),
        ]
        result = OCRResult(pages=pages, conf_avg=0.85)
        assert len(result.pages) == 2
        assert result.conf_avg == 0.85
