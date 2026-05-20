"""Uncertainty estimation using Monte Carlo Dropout.

Runs multiple stochastic forward passes with dropout enabled
to estimate epistemic uncertainty per prediction.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn


@dataclass
class UncertaintyEstimate:
    point_prediction: str
    point_confidence: float
    epistemic_uncertainty: float
    prediction_set: list[str]
    set_confidence: float
    mutual_information: float


class MCDropoutEstimator:
    def __init__(
        self,
        model: nn.Module,
        num_passes: int = 10,
        dropout_rate: float = 0.1,
    ):
        self.model = model
        self.num_passes = num_passes
        self.dropout_rate = dropout_rate

    def enable_dropout(self):
        for module in self.model.modules():
            if isinstance(module, (torch.nn.Dropout, torch.nn.Dropout2d)):
                module.train()

    def estimate(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        id2label: dict[int, str],
    ) -> UncertaintyEstimate:
        self.enable_dropout()

        all_logits = []

        for _ in range(self.num_passes):
            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs["logits"]
                all_logits.append(logits)

        stacked_logits = torch.stack(all_logits, dim=0)
        mean_logits = stacked_logits.mean(dim=0)
        variance = stacked_logits.var(dim=0)

        probs = torch.softmax(mean_logits, dim=-1)
        predictions = torch.argmax(probs, dim=-1)

        point_pred_idx = predictions[0, 0].item()
        point_confidence = probs[0, 0, point_pred_idx].item()
        point_prediction = id2label.get(point_pred_idx, f"TYPE_{point_pred_idx}")

        epistemic = variance[0, 0].mean().item()

        pred_counts = torch.bincount(predictions[0], minlength=probs.size(-1))
        top_k = min(3, len(pred_counts))
        top_k_indices = pred_counts.topk(top_k).indices

        prediction_set = [id2label.get(idx.item(), f"TYPE_{idx.item()}") for idx in top_k_indices]
        set_confidence = pred_counts.max().item() / self.num_passes

        mutual_info = torch.mean(torch.sum(probs * torch.log(probs + 1e-10), dim=-1)).item()

        return UncertaintyEstimate(
            point_prediction=point_prediction,
            point_confidence=point_confidence,
            epistemic_uncertainty=epistemic,
            prediction_set=prediction_set,
            set_confidence=set_confidence,
            mutual_information=mutual_info,
        )

    def estimate_batch(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        id2label: dict[int, str],
    ) -> list[UncertaintyEstimate]:
        self.enable_dropout()

        all_logits = []

        for _ in range(self.num_passes):
            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs["logits"]
                all_logits.append(logits)

        stacked_logits = torch.stack(all_logits, dim=0)
        mean_logits = stacked_logits.mean(dim=0)
        variance = stacked_logits.var(dim=0)

        batch_size = input_ids.size(0)
        estimates = []

        for b in range(batch_size):
            probs = torch.softmax(mean_logits[b], dim=-1)
            predictions = torch.argmax(probs, dim=-1)

            point_pred_idx = predictions[0].item()
            point_confidence = probs[0, point_pred_idx].item()
            point_prediction = id2label.get(point_pred_idx, f"TYPE_{point_pred_idx}")

            epistemic = variance[b].mean().item()

            pred_counts = torch.bincount(predictions, minlength=probs.size(-1))
            top_k = min(3, len(pred_counts))
            top_k_indices = pred_counts.topk(top_k).indices

            prediction_set = [id2label.get(idx.item(), f"TYPE_{idx.item()}") for idx in top_k_indices]
            set_confidence = pred_counts.max().item() / self.num_passes

            mutual_info = torch.mean(torch.sum(probs * torch.log(probs + 1e-10), dim=-1)).item()

            estimates.append(UncertaintyEstimate(
                point_prediction=point_prediction,
                point_confidence=point_confidence,
                epistemic_uncertainty=epistemic,
                prediction_set=prediction_set,
                set_confidence=set_confidence,
                mutual_information=mutual_info,
            ))

        return estimates


def compute_predictive_entropy(probs: torch.Tensor) -> torch.Tensor:
    return -torch.sum(probs * torch.log(probs + 1e-10), dim=-1)


def compute_mutual_information(
    all_probs: torch.Tensor,
) -> torch.Tensor:
    mean_probs = all_probs.mean(dim=0)
    entropy_mean = -torch.sum(mean_probs * torch.log(mean_probs + 1e-10), dim=-1)
    mean_entropy = -torch.mean(torch.sum(all_probs * torch.log(all_probs + 1e-10), dim=-1), dim=0)
    return entropy_mean - mean_entropy


class BayesianUncertaintyEstimator:
    def __init__(
        self,
        model: nn.Module,
        num_passes: int = 10,
    ):
        self.model = model
        self.num_passes = num_passes

    def predict_with_uncertainty(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        id2label: dict[int, str],
    ) -> UncertaintyEstimate:
        mc_estimator = MCDropoutEstimator(self.model, num_passes=self.num_passes)
        return mc_estimator.estimate(input_ids, attention_mask, id2label)
