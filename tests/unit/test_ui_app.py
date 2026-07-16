"""Tests for ui/app.py — upload routing, size limits, preview guard, offline model."""

import pytest

pytest.importorskip("streamlit")
import tempfile
from pathlib import Path
from unittest.mock import MagicMock


class MockUploadedFile:
    def __init__(self, name: str, size_bytes: int, content: bytes = b""):
        self.name = name
        self._size = size_bytes
        self._content = content

    @property
    def size(self) -> int:
        return self._size

    def getbuffer(self):
        return self._content


class TestFileSizeCheck:
    from ui.app import MAX_FILE_SIZE_MB

    def test_file_within_limit(self):
        from ui.app import check_file_size

        mock_file = MockUploadedFile("test.pdf", 10 * 1024 * 1024)
        result = check_file_size(mock_file)
        assert result is None

    def test_file_exceeds_limit(self):
        from ui.app import MAX_FILE_SIZE_MB, check_file_size

        mock_file = MockUploadedFile("test.pdf", (MAX_FILE_SIZE_MB + 10) * 1024 * 1024)
        result = check_file_size(mock_file)
        assert result is not None
        assert f"{MAX_FILE_SIZE_MB}MB" in result

    def test_file_at_exact_limit(self):
        from ui.app import MAX_FILE_SIZE_MB, check_file_size

        mock_file = MockUploadedFile("test.pdf", MAX_FILE_SIZE_MB * 1024 * 1024)
        result = check_file_size(mock_file)
        assert result is None


class TestUploadRouting:
    def test_pdf_extension_accepted(self):
        from ui.app import get_temp_file_path

        pdf_file = MockUploadedFile("tender.pdf", 1024, b"PDF content here")
        path = get_temp_file_path(pdf_file)
        assert path.suffix == ".pdf"

    def test_xlsx_extension_accepted(self):
        from ui.app import get_temp_file_path

        xlsx_file = MockUploadedFile("boq.xlsx", 2048, b"xlsx content")
        path = get_temp_file_path(xlsx_file)
        assert path.suffix == ".xlsx"

    def test_xls_extension_accepted(self):
        from ui.app import get_temp_file_path

        xls_file = MockUploadedFile("boq.xls", 1024, b"xls content")
        path = get_temp_file_path(xls_file)
        assert path.suffix == ".xls"


class TestPreviewGuard:
    def test_render_pdf_viewer_handles_missing_file(self, monkeypatch):
        from ui.pdf_viewer import render_pdf_viewer

        calls = []
        monkeypatch.setattr("streamlit.warning", lambda *a, **kw: calls.append(a))
        monkeypatch.setattr("streamlit.image", lambda *a, **kw: None)

        missing_path = Path("/nonexistent/file.pdf")
        render_pdf_viewer(missing_path)
        assert any("poppler" in str(a).lower() or "install" in str(a).lower() for a in calls)

    def test_render_pdf_pages_handles_corrupted_pdf(self, monkeypatch):
        from ui.pdf_viewer import render_pdf_pages

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(b"not a real PDF")
            tmp_path = tmp.name

        result = render_pdf_pages(tmp_path)
        assert result == []

        Path(tmp_path).unlink()


class TestOfflineModelLoading:
    def test_pipeline_loads_without_network(self):
        import os

        os.environ["HF_HUB_OFFLINE"] = "1"

        from src.pipeline import Pipeline

        p = Pipeline()
        assert p is not None
        assert p.nlp_pipeline is not None

    def test_load_pipeline_cached_no_download(self):
        import os

        os.environ["HF_HUB_OFFLINE"] = "1"

        from ui.app import load_pipeline

        pipeline = load_pipeline()
        assert pipeline is not None

    def test_ner_model_loads_offline_no_crash(self):
        import os

        os.environ["HF_HUB_OFFLINE"] = "1"

        # Phase 0 clean-slate: no pre-trained ML NER. Pattern-based only.
        from src.nlp.pipeline import NLPPipeline

        nlp = NLPPipeline()
        assert nlp.ner is None  # No ML model loaded
        assert nlp.regex_entities_fn is not None  # Patterns available
        # Pattern extraction should work without crash
        result = nlp.process("Supply 500 kg cement at ground floor M20 grade")
        assert isinstance(result.entities, list)


class TestPipelineXLSXHandling:
    def test_pipeline_runs_on_xlsx_file(self):
        from src.pipeline import Pipeline

        xlsx_path = Path("data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx")
        if xlsx_path.exists():
            p = Pipeline()
            result = p.run(str(xlsx_path))
            assert result is not None
            assert result.boq_items is not None
            assert len(result.boq_items) >= 0


class TestTimeoutAndProgress:
    def test_extract_boq_timeout_returns_error(self):
        from ui.app import extract_boq_with_timeout

        class SlowPipeline:
            def run(self, path):
                import time

                time.sleep(5)
                return None

        result, error = extract_boq_with_timeout(SlowPipeline(), Path("/tmp/nonexistent.pdf"), timeout_sec=1)
        assert result is None
        assert error is not None
        assert "timed out" in error.lower()


class TestUIAppMain:
    def test_app_structure_valid(self):
        import ast

        app_path = Path("ui/app.py")
        code = app_path.read_text()
        ast.parse(code)

    def test_all_imports_work(self):
        from ui import app, components, pdf_viewer

        assert hasattr(app, "load_pipeline")
        assert hasattr(app, "check_file_size")
        assert hasattr(app, "extract_boq_with_timeout")
        assert hasattr(app, "get_temp_file_path")
        assert hasattr(components, "build_boq_dataframe")
        assert hasattr(pdf_viewer, "render_pdf_viewer")

    def test_max_file_size_from_settings(self):
        from config.settings import settings
        from ui.app import MAX_FILE_SIZE_MB

        assert MAX_FILE_SIZE_MB == settings.MAX_FILE_SIZE_MB

    # test_sample_file_path_resolved removed (S2_PURGE_DEMO_SAMPLE: SAMPLE_PDF feature deleted, no longer relevant)


class TestExcelExport:
    def test_excel_generator_from_ui_components(self):
        from ui.components import _generate_excel_bytes

        result = MagicMock()
        result.boq_items = []
        result.project_name = "Test"
        result.doc_id = "test-001"

        data = _generate_excel_bytes(result)
        assert isinstance(data, bytes)
