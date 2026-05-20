"""Calibration module for confidence scores.

Implements TemperatureScaler to calibrate neural network confidence scores.
After temperature scaling, the model's confidence should match its actual accuracy.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset


class TemperatureScaler(nn.Module):
    def __init__(self):
        super().__init__()
        self.temperature = nn.Parameter(torch.ones(1) * 1.5)

    def forward(self, logits: torch.Tensor) -> torch.Tensor:
        return logits / self.temperature

    def scale(self, logits: torch.Tensor) -> torch.Tensor:
        return logits / self.temperature


class CalibrationDataset(Dataset):
    def __init__(self, examples: list[dict], tokenizer, label2id: dict[str, int], max_length: int = 512):
        self.tokenizer = tokenizer
        self.label2id = label2id
        self.max_length = max_length
        self.examples = self._prepare(examples)

    def _prepare(self, examples: list[dict]) -> list[dict]:
        prepared = []
        for ex in examples:
            tokens = ex.get("tokens", [])
            labels = ex.get("labels", [])

            encoding = self.tokenizer(
                tokens,
                is_split_into_words=True,
                return_tensors="pt",
                truncation=True,
                max_length=self.max_length,
                padding="max_length",
            )

            input_ids = encoding["input_ids"][0]
            attention_mask = encoding["attention_mask"][0]

            word_ids = encoding.word_ids(batch_index=0)
            label_ids = torch.full((self.max_length,), -100, dtype=torch.long)
            previous_word_id = None

            for token_index, word_id in enumerate(word_ids[: self.max_length]):
                if word_id is None:
                    previous_word_id = word_id
                    continue
                if word_id != previous_word_id and word_id < len(labels):
                    label_ids[token_index] = self.label2id.get(labels[word_id], self.label2id.get("O", 0))
                previous_word_id = word_id

            prepared.append({
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": label_ids,
            })

        return prepared

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict:
        return self.examples[idx]


def fit_temperature(
    model: nn.Module,
    calibration_data: list[dict],
    tokenizer,
    label2id: dict[str, int],
    device: torch.device,
    lr: float = 0.01,
    max_iter: int = 100,
) -> float:
    temp_scaler = TemperatureScaler()
    temp_scaler.to(device)
    optimizer = torch.optim.LBFGS([temp_scaler.temperature], lr=lr, max_iter=max_iter)

    calibration_dataset = CalibrationDataset(calibration_data, tokenizer, label2id)

    def compute_loss():
        optimizer.zero_grad()
        total_loss = 0.0

        for example in calibration_dataset:
            input_ids = example["input_ids"].unsqueeze(0).to(device)
            attention_mask = example["attention_mask"].unsqueeze(0).to(device)
            labels = example["labels"].unsqueeze(0).to(device)

            with torch.no_grad():
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs["logits"]

            scaled_logits = temp_scaler(logits)
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(scaled_logits.view(-1, logits.size(-1)), labels.view(-1))
            total_loss += loss

        return total_loss / len(calibration_dataset)

    optimizer.step(compute_loss)

    return temp_scaler.temperature.item()


def calibrate_confidence(
    raw_confidence: float,
    temperature: float,
) -> float:
    normalized = (raw_confidence - 0.5) / temperature + 0.5
    return max(0.0, min(1.0, normalized))


class CalibrationResults:
    def __init__(
        self,
        temperature: float = 1.0,
        before_ece: float = 0.0,
        after_ece: float = 0.0,
        num_samples: int = 0,
    ):
        self.temperature = temperature
        self.before_ece = before_ece
        self.after_ece = after_ece
        self.num_samples = num_samples

    def to_dict(self) -> dict[str, Any]:
        return {
            "temperature": self.temperature,
            "before_ece": self.before_ece,
            "after_ece": self.after_ece,
            "num_samples": self.num_samples,
        }

    def save(self, path: Path) -> None:
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


def compute_ece(
    confidences: list[float],
    accuracies: list[bool],
    n_bins: int = 10,
) -> float:
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_confidences = [[] for _ in range(n_bins)]
    bin_accuracies = [[] for _ in range(n_bins)]

    for conf, acc in zip(confidences, accuracies, strict=False):
        for i in range(n_bins):
            if bin_edges[i] <= conf < bin_edges[i + 1]:
                bin_confidences[i].append(conf)
                bin_accuracies[i].append(1.0 if acc else 0.0)
                break

    total_samples = len(confidences)
    if total_samples == 0:
        return 0.0

    ece = 0.0
    for i in range(n_bins):
        n_bin = len(bin_confidences[i])
        if n_bin == 0:
            continue

        avg_confidence = sum(bin_confidences[i]) / n_bin
        avg_accuracy = sum(bin_accuracies[i]) / n_bin
        ece += (n_bin / total_samples) * abs(avg_confidence - avg_accuracy)

    return ece
