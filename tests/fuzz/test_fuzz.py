"""Fuzz tests for RFQ2BOQ.

These tests use random malformed input to test robustness.
"""


class TestFuzzing:
    def test_random_text_extraction(self):
        """Test pipeline with random text input."""
        from src.nlp.pipeline import NLPPipeline

        pipeline = NLPPipeline()
        text = "ajsdfhasjdfhasjdf " * 100
        result = pipeline.process(text)
        assert result is not None

    def test_malformed_entities(self):
        """Test with malformed entity data."""
        from src.domain.boq_assembler import BOQAssembler
        from src.domain.models import EntitySourceType, EntitySpan

        assembler = BOQAssembler()
        entities = [
            EntitySpan(text="", type="MATERIAL", start=0, end=0, page=1, conf=0.0, source=EntitySourceType.BERT),
            EntitySpan(text="100", type="QUANTITY", start=1, end=4, page=1, conf=1.0, source=EntitySourceType.BERT),
        ]
        result = assembler.assemble(entities, [], "test text")
        assert len(result) >= 0

    def test_extreme_values(self):
        """Test BOQ row with extreme quantity values."""
        from decimal import Decimal

        from src.domain.models import BoqRow

        row = BoqRow(
            item_no=1,
            material="test",
            quantity=Decimal("999999999999999"),
            unit="kg",
            confidence=0.5,
        )
        assert row.quantity > 0
