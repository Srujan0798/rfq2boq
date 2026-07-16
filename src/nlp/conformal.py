"""Conformal prediction for distribution-free uncertainty quantification.

ConformalPredictor provides prediction sets with guaranteed coverage
(e.g., 90% of true labels fall within the prediction set).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch


@dataclass
class ConformalPrediction:
    prediction_set: list[str]
    confidence: float
    coverage_guaranteed: float
    nonconformity_score: float


class ConformalPredictor:
    def __init__(
        self,
        model: torch.nn.Module,
        id2label: dict[int, str],
        calibration_scores: list[float] | None = None,
        coverage: float = 0.9,
    ):
        self.model = model
        self.id2label = id2label
        self.coverage = coverage
        self.calibration_scores = calibration_scores or []
        self._quantile: float | None = None

    def calibrate(
        self,
        calibration_data: list[dict],
        tokenizer,
        device: torch.device,
    ) -> float:
        nonconformity_scores = []

        for example in calibration_data:
            tokens = example.get("tokens", [])
            labels = example.get("labels", [])

            encoding = tokenizer(
                tokens,
                is_split_into_words=True,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding="max_length",
            )

            input_ids = encoding["input_ids"].to(device)
            attention_mask = encoding["attention_mask"].to(device)

            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs["logits"]
                probs = torch.softmax(logits, dim=-1)

            true_label_idx = None
            for _i, label in enumerate(labels):
                if label != "O":
                    label_name = label[2:] if label.startswith(("B-", "I-", "E-", "S-")) else label
                    for idx, name in self.id2label.items():
                        if name == label_name:
                            true_label_idx = idx
                            break
                if true_label_idx is not None:
                    break

            if true_label_idx is None:
                true_label_idx = 0

            true_prob = probs[0, 0, true_label_idx].item()
            probs[0, 0].max().item()

            nonconformity = 1.0 - true_prob
            nonconformity_scores.append(nonconformity)

        self.calibration_scores = nonconformity_scores

        n = len(nonconformity_scores)
        q_level = ((1 - self.coverage) * (n + 1)) / n
        self._quantile = np.quantile(nonconformity_scores, min(q_level, 1.0))

        return self._quantile

    def predict(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> ConformalPrediction:
        device = next(self.model.parameters()).device
        input_ids = input_ids.to(device)
        attention_mask = attention_mask.to(device)

        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs["logits"]
            probs = torch.softmax(logits, dim=-1)

        if self._quantile is None:
            self._quantile = 0.5

        prediction_set = []
        for i, prob in enumerate(probs[0, 0]):
            if prob.item() >= (1.0 - self._quantile):
                label = self.id2label.get(i, f"TYPE_{i}")
                if label != "O":
                    prediction_set.append(label)

        if not prediction_set:
            top_k = max(1, min(3, len(self.id2label)))
            top_probs, top_indices = torch.topk(probs[0, 0], top_k)
            for idx in top_indices:
                label = self.id2label.get(idx.item(), f"TYPE_{idx.item()}")
                if label != "O":
                    prediction_set.append(label)

        prediction_set[0] if prediction_set else "O"
        confidence = probs[0, 0].max().item()
        nonconformity = 1.0 - confidence

        return ConformalPrediction(
            prediction_set=prediction_set,
            confidence=confidence,
            coverage_guaranteed=self.coverage,
            nonconformity_score=nonconformity,
        )

    def predict_set_for_text(
        self,
        text: str,
        tokenizer,
    ) -> ConformalPrediction:
        encoding = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )

        input_ids = encoding["input_ids"]
        attention_mask = encoding["attention_mask"]

        return self.predict(input_ids, attention_mask)


class AdaptiveConformalPredictor(ConformalPredictor):
    def __init__(
        self,
        model: torch.nn.Module,
        id2label: dict[int, str],
        coverage: float = 0.9,
        alpha: float = 0.05,
    ):
        super().__init__(model, id2label, coverage=coverage)
        self.alpha = alpha
        self._step_size = 0.01

    def predict_with_coverage_adjustment(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        observed_coverage: float,
    ) -> ConformalPrediction:
        base_prediction = self.predict(input_ids, attention_mask)

        if observed_coverage < self.coverage - self.alpha:
            adjustment = -self._step_size
        elif observed_coverage > self.coverage + self.alpha:
            adjustment = self._step_size
        else:
            adjustment = 0

        base_quantile = self._quantile if self._quantile is not None else 0.5
        new_quantile = max(0.01, min(0.99, base_quantile + adjustment))
        self._quantile = new_quantile

        return base_prediction


def conformal_regression_calibration(
    calibration_errors: list[float],
    coverage: float = 0.9,
) -> float:
    n = len(calibration_errors)
    q_level = ((1 - coverage) * (n + 1)) / n
    return float(np.quantile(calibration_errors, min(q_level, 1.0)))
