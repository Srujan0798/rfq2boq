"""Unit tests for UI components (confidence, dataframe, etc.)."""

import pytest

pytest.importorskip("streamlit")
from unittest.mock import MagicMock


class TestUIComponents:
    def test_components_module_imports(self):
        from ui import components

        assert hasattr(components, "confidence_pill")
        assert hasattr(components, "confidence_color")
        assert hasattr(components, "render_confidence_guide")
        assert hasattr(components, "render_boq_table")
        assert hasattr(components, "render_downloads_strip")
        assert hasattr(components, "build_boq_dataframe")
        assert hasattr(components, "header_strip")
        assert hasattr(components, "sidebar_settings")

    def test_confidence_pill(self):
        from ui.components import confidence_pill

        assert confidence_pill(0.90) == "🟢 Good"
        assert confidence_pill(0.70) == "🟡 Check"
        assert confidence_pill(0.30) == "🔴 Verify"
        assert confidence_pill(0.85) == "🟢 Good"
        assert confidence_pill(0.50) == "🟡 Check"

    def test_confidence_color(self):
        from ui.components import confidence_color

        assert "d4edda" in confidence_color(0.90)
        assert "fff3cd" in confidence_color(0.70)
        assert "f8d7da" in confidence_color(0.30)

    def test_build_boq_dataframe_empty(self):
        from ui.components import build_boq_dataframe

        result = MagicMock()
        result.boq_items = []
        df = build_boq_dataframe(result)
        assert len(df) == 0

    def test_build_boq_dataframe_with_items(self):
        from decimal import Decimal

        from ui.components import build_boq_dataframe

        item = MagicMock()
        item.quantity = Decimal("500")
        item.rate = Decimal("200")
        item.amount = Decimal("100000")
        item.confidence = 0.85
        item.material = "Cement"
        item.unit = "kg"
        item.standard = ["IS 456"]
        item.grade = "M20"
        item.item_no = 1

        result = MagicMock()
        result.boq_items = [item]
        result.project_name = "Test"
        result.doc_id = "test-001"

        df = build_boq_dataframe(result)
        assert len(df) == 1
        assert df.iloc[0]["Description"] == "Cement"
        assert df.iloc[0]["Quantity"] == 500.0
        assert df.iloc[0]["Quality"] == "Good"

    def test_result_to_dataframe_low_confidence(self):
        from decimal import Decimal

        from ui.components import build_boq_dataframe

        item = MagicMock()
        item.quantity = Decimal("10")
        item.rate = Decimal("0")
        item.amount = Decimal("0")
        item.confidence = 0.3
        item.material = "Unknown Material"
        item.unit = "nos"
        item.standard = []
        item.grade = ""
        item.item_no = 1

        result = MagicMock()
        result.boq_items = [item]

        df = build_boq_dataframe(result)
        assert df.iloc[0]["Quality"] == "Verify"

    def test_pdf_viewer_imports(self):
        from ui import pdf_viewer

        assert hasattr(pdf_viewer, "render_pdf_pages")
        assert hasattr(pdf_viewer, "count_pdf_pages")
        assert hasattr(pdf_viewer, "render_pdf_viewer")

    def test_pdf_viewer_render_pdf_pages_callable(self):
        from ui.pdf_viewer import render_pdf_pages

        assert callable(render_pdf_pages)

    def test_boq_row_style(self):
        from ui.components import boq_row_style

        css = boq_row_style()
        assert "boq-quality-good" in css
        assert "boq-quality-check" in css
        assert "boq-quality-verify" in css

    def test_header_strip(self, monkeypatch):
        import streamlit as st

        monkeypatch.setattr(st, "title", lambda x: None)
        monkeypatch.setattr(st, "markdown", lambda x, **kw: None)
        from ui.components import header_strip

        header_strip()

    def test_sidebar_settings(self, monkeypatch):
        import streamlit as st

        calls = {}
        monkeypatch.setattr(st.sidebar, "markdown", lambda x: calls.__setitem__("md", True))
        monkeypatch.setattr(st.sidebar, "divider", lambda: calls.__setitem__("div", True))
        monkeypatch.setattr(st.sidebar, "text_input", lambda *a, **kw: "Test Project")
        monkeypatch.setattr(st.sidebar, "selectbox", lambda *a, **kw: "Delhi")
        monkeypatch.setattr(st.sidebar, "button", lambda *a, **kw: False)
        monkeypatch.setattr(st.sidebar, "caption", lambda x: None)
        from ui.components import sidebar_settings

        result = sidebar_settings()
        assert result["project_name"] == "Test Project"

    def test_downloads_strip_csv_bytes(self, monkeypatch):
        import streamlit as st

        monkeypatch.setattr(st, "columns", lambda n: [MagicMock() for _ in range(n)])
        monkeypatch.setattr(st, "download_button", lambda **kw: None)
        from ui.components import _generate_csv_bytes

        result = MagicMock()
        result.boq_items = []
        assert isinstance(_generate_csv_bytes(result), bytes)

    def test_result_to_dataframe_grade_extraction(self):
        from decimal import Decimal

        from ui.components import build_boq_dataframe

        item = MagicMock()
        item.quantity = Decimal("100")
        item.rate = Decimal("50")
        item.amount = Decimal("5000")
        item.confidence = 0.95
        item.material = "Concrete M30"
        item.unit = "cum"
        item.standard = ["IS 456"]
        item.grade = "M30"
        item.item_no = 1

        result = MagicMock()
        result.boq_items = [item]

        df = build_boq_dataframe(result)
        assert df.iloc[0]["Grade"] == "M30"
        assert df.iloc[0]["Quality"] == "Good"

    def test_result_to_dataframe_no_grade(self):
        from decimal import Decimal

        from ui.components import build_boq_dataframe

        item = MagicMock()
        item.quantity = Decimal("200")
        item.rate = Decimal("100")
        item.amount = Decimal("20000")
        item.confidence = 0.75
        item.material = "Brickwork"
        item.unit = "cum"
        item.standard = []
        item.grade = ""
        item.item_no = 1

        result = MagicMock()
        result.boq_items = [item]

        df = build_boq_dataframe(result)
        assert df.iloc[0]["Grade"] == ""
        assert df.iloc[0]["Quality"] == "Check"
