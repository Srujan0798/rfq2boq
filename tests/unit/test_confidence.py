"""Tests for confidence scorer."""

from datetime import datetime
from decimal import Decimal

from src.domain.confidence import ConfidenceScorer
from src.domain.models import BoqRow, ExtractionMetadata, ExtractionResult


class TestConfidenceScorer:
    def test_score_item_complete(self):
        scorer = ConfidenceScorer()
        item = BoqRow(
            item_no=1,
            material="cement",
            grade="M20",
            quantity=Decimal("100"),
            unit="bags",
            location="ground floor",
            standard=["IS 456"],
            action="Supply",
            confidence=0.9,
        )
        score = scorer.score_item(item)
        assert 0.0 <= score <= 1.0

    def test_score_item_minimal(self):
        scorer = ConfidenceScorer()
        item = BoqRow(
            item_no=1,
            material="cement",
            quantity=Decimal("50"),
            unit="bags",
            confidence=0.5,
        )
        score = scorer.score_item(item)
        assert 0.0 <= score <= 1.0

    def test_score_item_no_confidence(self):
        scorer = ConfidenceScorer()
        item = BoqRow(
            item_no=1,
            material="steel",
            quantity=Decimal("0"),
            unit="kg",
            confidence=0.0,
        )
        score = scorer.score_item(item)
        assert 0.0 <= score <= 1.0

    def test_score_extraction_empty(self):
        scorer = ConfidenceScorer()
        result = ExtractionResult(
            doc_id="test-123",
            project_name="Test",
            extraction_date=datetime.now(),
            source_file="test.pdf",
            boq_items=[],
            metadata=ExtractionMetadata(
                total_items=0,
                avg_confidence=0.0,
                processing_time_sec=0.0,
                pages_processed=0,
            ),
        )
        score = scorer.score_extraction(result)
        assert score == 0.0

    def test_score_extraction_with_items(self):
        scorer = ConfidenceScorer()
        result = ExtractionResult(
            doc_id="test-456",
            project_name="Test",
            extraction_date=datetime.now(),
            source_file="test.pdf",
            boq_items=[
                BoqRow(item_no=1, material="cement", quantity=Decimal("100"), unit="bags", confidence=0.9),
                BoqRow(item_no=2, material="steel", quantity=Decimal("200"), unit="kg", confidence=0.8),
            ],
            metadata=ExtractionMetadata(
                total_items=2,
                avg_confidence=0.85,
                processing_time_sec=1.0,
                pages_processed=1,
            ),
        )
        score = scorer.score_extraction(result)
        assert 0.0 <= score <= 1.0
