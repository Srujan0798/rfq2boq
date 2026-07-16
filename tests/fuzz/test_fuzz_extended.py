"""Extended fuzz tests for RFQ2BOQ pipeline robustness."""

import random
import string
from decimal import Decimal

import pytest
from src.domain.boq_assembler import BOQAssembler
from src.domain.models import BoqRow, EntitySourceType, EntitySpan, ExtractionMetadata, ExtractionResult
from src.nlp.pipeline import NLPPipeline


class TestFuzzExtended:
    def test_random_garbage_text(self):
        """Test pipeline with random garbage text - should not crash."""
        pipeline = NLPPipeline()
        for _ in range(100):
            text = "".join(random.choices(string.printable, k=random.randint(10, 500)))
            try:
                result = pipeline.process(text)
                assert result is not None
            except Exception:
                pytest.fail("Pipeline crashed on random garbage")

    def test_extremely_long_text(self):
        """Test pipeline with very long text - should handle gracefully."""
        pipeline = NLPPipeline()
        text = "word " * 50000
        try:
            result = pipeline.process(text)
            assert result is not None
        except Exception:
            pytest.fail("Pipeline crashed on extremely long text")

    def test_only_numbers(self):
        """Test pipeline with only numbers - should not crash."""
        pipeline = NLPPipeline()
        text = " ".join([str(random.randint(0, 9999)) for _ in range(100)])
        try:
            result = pipeline.process(text)
            assert result is not None
        except Exception:
            pytest.fail("Pipeline crashed on numbers only")

    def test_only_special_characters(self):
        """Test pipeline with only special characters - should not crash."""
        pipeline = NLPPipeline()
        text = "".join(random.choices(string.punctuation + string.whitespace, k=200))
        try:
            result = pipeline.process(text)
            assert result is not None
        except Exception:
            pytest.fail("Pipeline crashed on special characters only")

    def test_empty_string(self):
        """Test pipeline with empty string - should not crash."""
        pipeline = NLPPipeline()
        result = pipeline.process("")
        assert result is not None

    def test_unicode_mixed_languages(self):
        """Test pipeline with mixed unicode - should handle gracefully."""
        pipeline = NLPPipeline()
        texts = [
            "ಕನ್ನಡ ಪಠ್ಯ",
            "日本語テキスト",
            "العربية نص",
            "עברית טקסט",
            "中文文本",
        ]
        for text in texts:
            try:
                result = pipeline.process(text)
                assert result is not None
            except Exception:
                pytest.fail(f"Pipeline crashed on unicode text: {text}")

    def test_newlines_only(self):
        """Test pipeline with only newlines - should not crash."""
        pipeline = NLPPipeline()
        text = "\n" * 100
        result = pipeline.process(text)
        assert result is not None

    def test_boq_with_extreme_quantity(self):
        """Test BOQ row with extreme quantity values."""
        row = BoqRow(
            item_no=1,
            material="steel",
            quantity=Decimal("999999999999999"),
            unit="kg",
            confidence=0.5,
        )
        assert row.quantity > 0

    def test_boq_with_negative_quantity(self):
        """Test BOQ row with negative quantity - should be handled."""
        row = BoqRow(
            item_no=1,
            material="cement",
            quantity=Decimal("-100"),
            unit="bags",
            confidence=0.5,
        )
        assert row.quantity < 0

    def test_boq_with_very_long_material(self):
        """Test BOQ with extremely long material string."""
        row = BoqRow(
            item_no=1,
            material="x" * 10000,
            quantity=Decimal("100"),
            unit="kg",
            confidence=0.5,
        )
        assert len(row.material) == 10000

    def test_boq_assembler_empty_entities(self):
        """Test assembler with empty entity list."""
        assembler = BOQAssembler()
        result = assembler.assemble([], [], "")
        assert len(result) >= 0

    def test_boq_assembler_malformed_entities(self):
        """Test assembler with malformed entities - should not crash."""
        assembler = BOQAssembler()
        entities = [
            EntitySpan(text="", type="MATERIAL", start=0, end=0, page=1, conf=0.0, source=EntitySourceType.BERT),
            EntitySpan(text="valid", type="QUANTITY", start=1, end=6, page=1, conf=0.5, source=EntitySourceType.BERT),
        ]
        try:
            result = assembler.assemble(entities, [], "test")
            assert result is not None
        except Exception:
            pytest.fail("Assembler crashed on malformed entities")

    def test_extraction_result_empty(self):
        """Test creating ExtractionResult with minimal data."""
        result = ExtractionResult(doc_id="test-123")
        assert result.doc_id == "test-123"
        assert len(result.boq_items) == 0

    def test_extraction_result_large_metadata(self):
        """Test ExtractionResult with large entity counts."""
        result = ExtractionResult(
            doc_id="test-456",
            metadata=ExtractionMetadata(
                total_items=10000,
                avg_confidence=0.75,
                processing_time_sec=300.0,
                pages_processed=500,
                entity_counts={"MATERIAL": 5000, "QUANTITY": 3000},
            ),
        )
        assert result.metadata.total_items == 10000

    def test_boq_assembler_many_materials(self):
        """Test assembler with many materials - should handle."""
        assembler = BOQAssembler()
        entities = [
            EntitySpan(
                text=f"material{i}",
                type="MATERIAL",
                start=i * 10,
                end=i * 10 + 5,
                page=1,
                conf=0.9,
                source=EntitySourceType.BERT,
            )
            for i in range(100)
        ]
        result = assembler.assemble(entities, [], " ".join([e.text for e in entities]))
        assert len(result) >= 0

    def test_pipeline_control_characters(self):
        """Test pipeline with control characters."""
        pipeline = NLPPipeline()
        text = "Hello\x00World\x1fTest\x7f"
        result = pipeline.process(text)
        assert result is not None

    def test_boq_row_with_special_unit(self):
        """Test BOQ row with special unit characters."""
        row = BoqRow(
            item_no=1,
            material="concrete",
            quantity=Decimal("100"),
            unit="m³/s",  # unusual unit
            confidence=0.8,
        )
        assert row.unit == "m³/s"

    def test_repeated_pattern_text(self):
        """Test pipeline with repeated patterns."""
        pipeline = NLPPipeline()
        text = "supply 100 kg " * 1000
        result = pipeline.process(text)
        assert result is not None

    def test_boq_empty_action(self):
        """Test BOQ with empty action string."""
        row = BoqRow(
            item_no=1,
            material="cement",
            quantity=Decimal("50"),
            unit="bags",
            action="",
            confidence=0.9,
        )
        assert row.action == ""

    def test_boq_multiple_standards(self):
        """Test BOQ with multiple standards."""
        row = BoqRow(
            item_no=1,
            material="steel",
            quantity=Decimal("500"),
            unit="kg",
            standard=["IS 2062", "ASTM A615", "BS EN 10025"],
            confidence=0.9,
        )
        assert len(row.standard) == 3

    def test_pipeline_single_character(self):
        """Test pipeline with single character repeated."""
        pipeline = NLPPipeline()
        text = "a" * 1000
        result = pipeline.process(text)
        assert result is not None

    def test_boq_zero_confidence(self):
        """Test BOQ with zero confidence."""
        row = BoqRow(
            item_no=1,
            material="cement",
            quantity=Decimal("100"),
            unit="bags",
            confidence=0.0,
        )
        assert row.confidence == 0.0

    def test_assembler_unicode_text(self):
        """Test assembler with unicode text."""
        assembler = BOQAssembler()
        text = "ಕನ್ನಡ ಪಠ್ಯ 500 kg"
        entities = [
            EntitySpan(text="ಕನ್ನಡ", type="MATERIAL", start=0, end=6, page=1, conf=0.9, source=EntitySourceType.BERT),
            EntitySpan(text="500", type="QUANTITY", start=13, end=16, page=1, conf=0.9, source=EntitySourceType.BERT),
        ]
        result = assembler.assemble(entities, [], text)
        assert len(result) >= 0

    def test_whitespace_only_text(self):
        """Test pipeline with whitespace only."""
        pipeline = NLPPipeline()
        text = "   \n\n\t\t  "
        result = pipeline.process(text)
        assert result is not None
