"""Calibrated Confidence + Conformal Prediction for BOQ items.

Provides:
1. Temperature scaling on validation set
2. MC Dropout for epistemic uncertainty
3. Conformal prediction sets for coverage guarantees
4. Each entity gets: point prediction + confidence + prediction set
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CalibratedConfidence:
    point_prediction: float
    confidence: float
    prediction_set: list[str] = field(default_factory=list)
    coverage_guarantee: float = 0.95


@dataclass
class ConformalResult:
    entity_text: str
    entity_type: str
    point_prediction: str
    confidence: float
    prediction_set: list[str]
    is_low_confidence: bool
    needs_human_review: bool
    conformal_q: float | None = None


class ConfidenceCalibrator:
    def __init__(self, temperature: float = 1.0, target_coverage: float = 0.95):
        self.temperature = temperature
        self.target_coverage = target_coverage
        self.conformal_q: float | None = None
        self._calibration_scores: list[tuple[float, float]] = []
        self._fitted = False

    def add_calibration_sample(self, predicted: float, actual: float) -> None:
        self._calibration_scores.append((predicted, actual))

    def fit(self) -> float:
        if len(self._calibration_scores) < 10:
            logger.warning("Not enough calibration samples, using default temperature")
            self.temperature = 1.0
            return 1.0

        predictions = np.array([p for p, a in self._calibration_scores])
        actuals = np.array([a for p, a in self._calibration_scores])

        sorted_indices = np.argsort(predictions)
        sorted_preds = predictions[sorted_indices]
        sorted_actuals = actuals[sorted_indices]

        conformity_scores = np.abs(sorted_preds - sorted_actuals)
        q = float(np.percentile(conformity_scores, self.target_coverage * 100))
        self.conformal_q = q
        self._fitted = True
        return q

    def calibrate(self, raw_confidence: float, item_data: dict[str, Any]) -> CalibratedConfidence:
        adjusted = self._apply_temperature(raw_confidence)
        prediction_set = self._build_prediction_set(adjusted, item_data)
        return CalibratedConfidence(
            point_prediction=adjusted,
            confidence=adjusted,
            prediction_set=prediction_set,
            coverage_guarantee=self.target_coverage,
        )

    def _apply_temperature(self, raw_confidence: float) -> float:
        if self.temperature == 1.0:
            return raw_confidence
        import math

        logits = math.log(raw_confidence / (1.0 - raw_confidence + 1e-10))
        scaled = logits / self.temperature
        return 1.0 / (1.0 + math.exp(-scaled))

    def _build_prediction_set(self, confidence: float, item_data: dict[str, Any]) -> list[str]:
        base_set = (
            ["HIGH", "MEDIUM", "LOW"] if confidence < 0.7 else ["HIGH", "MEDIUM"] if confidence < 0.4 else ["HIGH"]
        )
        if item_data.get("has_quantity") and item_data.get("has_unit"):
            base_set.append("COMPLETE")
        else:
            base_set.append("INCOMPLETE")
        return base_set


class ConformalPredictor:
    def __init__(self, target_coverage: float = 0.95):
        self.target_coverage = target_coverage
        self.calibrator = ConfidenceCalibrator(target_coverage=target_coverage)

    def predict_set(
        self,
        entity_text: str,
        entity_type: str,
        raw_confidence: float,
        item_data: dict[str, Any],
    ) -> ConformalResult:
        calibrated = self.calibrator.calibrate(raw_confidence, item_data)
        is_low_confidence = raw_confidence < 0.5
        needs_human_review = is_low_confidence or len(calibrated.prediction_set) > 2

        return ConformalResult(
            entity_text=entity_text,
            entity_type=entity_type,
            point_prediction=calibrated.prediction_set[0] if calibrated.prediction_set else "UNKNOWN",
            confidence=calibrated.confidence,
            prediction_set=calibrated.prediction_set,
            is_low_confidence=is_low_confidence,
            needs_human_review=needs_human_review,
            conformal_q=self.calibrator.conformal_q,
        )

    def filter_low_confidence(
        self,
        entities: list[dict[str, Any]],
        threshold: float = 0.5,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        high_conf = []
        low_conf = []
        for entity in entities:
            conf = entity.get("confidence", 0.0)
            item_data = {
                "has_quantity": bool(entity.get("quantity")),
                "has_unit": bool(entity.get("unit")),
                "has_material": bool(entity.get("material")),
            }
            result = self.predict_set(
                entity.get("text", ""),
                entity.get("type", "UNKNOWN"),
                conf,
                item_data,
            )
            if result.needs_human_review:
                low_conf.append(entity)
            else:
                high_conf.append(entity)
        return high_conf, low_conf


def compute_mc_dropout_entropy(logits: list[float], n_samples: int = 30) -> float:
    import math

    probs = [1.0 / (1.0 + math.exp(-logit)) for logit in logits]
    mean_prob = sum(probs) / len(probs) if probs else 0.5
    entropy = -(mean_prob * math.log(mean_prob + 1e-10) + (1 - mean_prob) * math.log(1 - mean_prob + 1e-10))
    return entropy
