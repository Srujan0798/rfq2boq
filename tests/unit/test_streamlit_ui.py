"""Tests for Streamlit UI functions."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("streamlit")
from src.domain.models import BoqRow, ExtractionMetadata, ExtractionResult


class MockUploadedFile:
    def __init__(self, size_bytes: int):
        self.size = size_bytes


class TestCheckFileSize:
    def test_file_within_limit(self):
        from ui.app import check_file_size

        mock_file = MockUploadedFile(size_bytes=10 * 1024 * 1024)
        result = check_file_size(mock_file)
        assert result is None

    def test_file_exceeds_limit(self):
        from ui.app import MAX_FILE_SIZE_MB, check_file_size

        mock_file = MockUploadedFile(size_bytes=(MAX_FILE_SIZE_MB + 10) * 1024 * 1024)
        result = check_file_size(mock_file)
        assert result is not None
        assert f"{MAX_FILE_SIZE_MB}MB" in result

    def test_file_at_exact_limit(self):
        from ui.app import MAX_FILE_SIZE_MB, check_file_size

        mock_file = MockUploadedFile(size_bytes=MAX_FILE_SIZE_MB * 1024 * 1024)
        result = check_file_size(mock_file)
        assert result is None


class TestBuildBoqDataFrame:
    def test_empty_result(self):
        from ui.app import build_boq_dataframe

        result = ExtractionResult(
            doc_id="test",
            project_name="Test",
            entities=[],
            boq_items=[],
            metadata=ExtractionMetadata(total_items=0, avg_confidence=0.0),
        )
        df = build_boq_dataframe(result)
        assert len(df) == 0

    def test_single_item(self):
        from ui.app import build_boq_dataframe

        item = BoqRow(
            item_no=1,
            material="cement",
            quantity=Decimal("100"),
            unit="bags",
            rate=Decimal("500"),
            confidence=0.9,
        )
        result = ExtractionResult(
            doc_id="test",
            project_name="Test",
            entities=[],
            boq_items=[item],
            metadata=ExtractionMetadata(total_items=1, avg_confidence=0.9),
        )
        df = build_boq_dataframe(result)
        assert len(df) == 1
        assert df.iloc[0]["Description"] == "cement"
        assert df.iloc[0]["Quantity"] == 100
        assert df.iloc[0]["Quality"] == "Good"

    def test_quality_thresholds(self):
        from ui.app import build_boq_dataframe

        items = [
            BoqRow(item_no=1, material="good", quantity=Decimal("1"), unit="nos", confidence=0.85),
            BoqRow(item_no=2, material="check", quantity=Decimal("1"), unit="nos", confidence=0.65),
            BoqRow(item_no=3, material="verify", quantity=Decimal("1"), unit="nos", confidence=0.30),
        ]
        result = ExtractionResult(
            doc_id="test",
            project_name="Test",
            entities=[],
            boq_items=items,
            metadata=ExtractionMetadata(total_items=3, avg_confidence=0.6),
        )
        df = build_boq_dataframe(result)
        qualities = df["Quality"].tolist()
        assert "Good" in qualities
        assert "Check" in qualities
        assert "Verify" in qualities

    def test_amount_not_calculated_in_ui(self):
        from ui.app import build_boq_dataframe

        item = BoqRow(
            item_no=1,
            material="steel",
            quantity=Decimal("50"),
            unit="kg",
            rate=Decimal("60"),
            confidence=0.9,
        )
        result = ExtractionResult(
            doc_id="test",
            project_name="Test",
            entities=[],
            boq_items=[item],
            metadata=ExtractionMetadata(total_items=1, avg_confidence=0.9),
        )
        df = build_boq_dataframe(result)
        assert "Amount (₹)" not in df.columns
        assert df.iloc[0]["Quantity"] == 50.0
        assert df.iloc[0]["Unit"] == "kg"


class TestHighlightEntities:
    def test_empty_entities(self):
        from ui.app import highlight_entities

        result = highlight_entities("Hello world", [])
        assert result == "Hello world"

    def test_single_entity(self):
        from ui.app import highlight_entities

        entities = [{"start": 0, "end": 5, "type": "MATERIAL", "confidence": 0.9}]
        result = highlight_entities("Hello world", entities)
        assert "<span" in result
        assert "MATERIAL" in result

    def test_multiple_entities(self):
        from ui.app import highlight_entities

        entities = [
            {"start": 0, "end": 5, "type": "MATERIAL", "confidence": 0.9},
            {"start": 6, "end": 11, "type": "QUANTITY", "confidence": 0.8},
        ]
        result = highlight_entities("Hello world", entities)
        assert result.count("<span") == 2


class TestRenderEntityLegend:
    def test_legend_renders_without_error(self):
        from ui.app import render_entity_legend

        with patch("streamlit.markdown"), patch("streamlit.columns") as mock_cols:
            mock_cols.return_value = [MagicMock() for _ in range(8)]
            render_entity_legend()


class TestAppStructure:
    def test_app_parses_successfully(self):
        import ast

        app_path = "ui/app.py"
        with open(app_path) as f:
            code = f.read()
        ast.parse(code)
