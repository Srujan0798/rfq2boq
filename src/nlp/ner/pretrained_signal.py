"""Pretrained neural NER signal for RFQ2BOQ.

Loads a small, widely-used HuggingFace token-classification model
(dslim/bert-base-NER) and maps its generic CoNLL labels to the project's
8-entity schema.  This is an *additional* signal — it never replaces
rule-based or dictionary extraction.

Expected entity format (matches src.nlp.patterns.regex_patterns):
    {"text": str, "type": str, "start": int, "end": int,
     "confidence": float, "source": "pretrained_ner"}
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Default model: small, cased BERT fine-tuned on CoNLL-2003.
# ~110 MB, 108 M parameters, widely used, no attribution burden.
DEFAULT_MODEL_NAME = "dslim/bert-base-NER"

# Module-level cache so multiple NLPPipeline instances share one model load.
_MODEL_CACHE: dict[str, tuple[Any, Any, str]] = {}

# Mapping from generic CoNLL labels → project EntityType values.
# Only labels listed here are emitted; everything else is dropped.
LABEL_MAP: dict[str, str] = {
    "LOC": "LOCATION",
    "MISC": "MATERIAL",
}

# Confidence per mapped label (MISC is noisy, so lower).
LABEL_CONFIDENCE: dict[str, float] = {
    "LOC": 0.60,
    "MISC": 0.45,
}


class PretrainedNERSignal:
    """Lightweight wrapper around a generic pretrained NER model."""

    def __init__(self, model_name: str | None = None, enabled: bool | None = None):
        self.model_name = model_name or DEFAULT_MODEL_NAME
        # Honor explicit arg, then env var, then default True.
        if enabled is None:
            env_flag = os.environ.get("RFQ2BOQ_PRETRAINED_NER_ENABLED", "true")
            self.enabled = env_flag.lower() in {"1", "true", "yes", "on"}
        else:
            self.enabled = enabled

        self._tokenizer: Any = None
        self._model: Any = None
        self._device: str = "cpu"

    def _load(self) -> None:
        """Lazy-load tokenizer + model.  Called on first predict()."""
        if self._model is not None or not self.enabled:
            return

        cache_key = f"{self.model_name}:{self.enabled}"
        if cache_key in _MODEL_CACHE:
            self._tokenizer, self._model, self._device = _MODEL_CACHE[cache_key]
            return

        try:
            import torch
            from transformers import AutoModelForTokenClassification, AutoTokenizer
        except Exception as exc:
            logger.warning("transformers/torch not available, pretrained NER disabled: %s", exc)
            self.enabled = False
            return

        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForTokenClassification.from_pretrained(self.model_name)
        except Exception as exc:
            logger.warning("Failed to load pretrained NER model %s: %s", self.model_name, exc)
            self.enabled = False
            return

        # MPS on Apple Silicon, else CPU (no CUDA on this machine).
        if torch.backends.mps.is_available():
            self._device = "mps"
        else:
            self._device = "cpu"
        self._model.to(self._device)
        self._model.eval()
        _MODEL_CACHE[cache_key] = (self._tokenizer, self._model, self._device)
        logger.info("Pretrained NER model loaded on %s (%s)", self._device, self.model_name)

    def predict(self, text: str) -> list[dict]:
        """Run the pretrained model on *text* and return mapped entities.

        Returns empty list when disabled or when model fails to load.
        """
        if not self.enabled or not text.strip():
            return []
        self._load()
        if self._model is None or self._tokenizer is None:
            return []

        try:
            return self._predict_impl(text)
        except Exception as exc:
            logger.debug("Pretrained NER inference failed: %s", exc, exc_info=True)
            return []

    def _predict_impl(self, text: str) -> list[dict]:
        import torch

        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            return_offsets_mapping=True,
        )
        offset_mapping = inputs.pop("offset_mapping")[0].tolist()

        inputs = {k: v.to(self._device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self._model(**inputs)

        predictions = outputs.logits.argmax(dim=-1)[0].tolist()
        id2label = self._model.config.id2label

        entities: list[dict] = []
        current: dict | None = None

        for pred_id, (char_start, char_end) in zip(predictions, offset_mapping, strict=False):
            # Skip special tokens and zero-width offsets.
            if char_start == char_end:
                continue

            label = id2label.get(pred_id, "O")
            if label == "O":
                if current is not None:
                    entities.append(current)
                    current = None
                continue

            # dslim/bert-base-NER uses IOB2: B-*, I-*
            prefix = label[:2]
            tag = label[2:]
            mapped_type = LABEL_MAP.get(tag)
            if mapped_type is None:
                # Drop unsupported labels (PER, ORG, …)
                if current is not None:
                    entities.append(current)
                    current = None
                continue

            if prefix == "B-" or current is None or current["type"] != mapped_type:
                if current is not None:
                    entities.append(current)
                current = {
                    "text": text[char_start:char_end],
                    "type": mapped_type,
                    "start": char_start,
                    "end": char_end,
                    "confidence": LABEL_CONFIDENCE.get(tag, 0.5),
                    "source": "pretrained_ner",
                }
            else:
                # Continue / inside same entity.
                current["text"] = text[current["start"]:char_end]
                current["end"] = char_end
                # Average confidence (simple heuristic).
                current["confidence"] = (
                    current["confidence"] + LABEL_CONFIDENCE.get(tag, 0.5)
                ) / 2.0

        if current is not None:
            entities.append(current)

        # Post-filter: drop single-character or whitespace-only entities.
        filtered: list[dict] = []
        for e in entities:
            stripped = e["text"].strip()
            if len(stripped) >= 2:
                e["text"] = stripped
                filtered.append(e)

        return filtered
