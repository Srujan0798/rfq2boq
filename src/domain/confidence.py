"""Confidence scoring for BOQ items."""

from src.domain.models import BoqRow, ExtractionResult


class ConfidenceScorer:
    def score_item(self, item: BoqRow) -> float:
        """Score a single BOQ item confidence."""
        conf = 0.5
        if item.material:
            conf += 0.15
        if item.quantity and item.quantity > 0:
            conf += 0.15
        if item.unit and item.unit not in ("no.", "nos"):
            conf += 0.1
        if item.action:
            conf += 0.1
        if item.grade:
            conf += 0.1
        if item.location:
            conf += 0.1
        if item.standard:
            conf += 0.1
        return min(conf, 1.0)

    def score_boq_item(self, item: BoqRow) -> float:
        """Alias for score_item."""
        return self.score_item(item)

    def score_extraction(self, result: ExtractionResult) -> float:
        """Score an entire extraction result."""
        if not result.boq_items:
            return 0.0
        return sum(self.score_item(item) for item in result.boq_items) / len(result.boq_items)

    def average_confidence(self, items: list[BoqRow]) -> float:
        """Calculate average confidence from a list of items."""
        if not items:
            return 0.0
        return sum(item.confidence for item in items) / len(items)
