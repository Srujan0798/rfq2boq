"""Optimized NER inference with lazy MPS/CPU loading and offset-aware decoding."""

import json
import os
import time
from typing import Any


class LazyNERModel:
    """Lazy-loading NER model with MPS support and proper offset tracking."""

    _instance: "LazyNERModel | None" = None

    def __init__(self, model_dir: str, base_model: str = "bert-base-cased"):
        self.model_dir = model_dir
        self.base_model = base_model
        self._model: Any | None = None
        self._tokenizer: Any | None = None
        self._id2label: dict[int, str] = {}
        self._loaded = False
        self._load_time: float | None = None
        self._device: Any | None = None

    @classmethod
    def get_instance(cls, model_dir: str | None = None, base_model: str = "bert-base-cased") -> "LazyNERModel":
        if cls._instance is None:
            if model_dir is None:
                model_dir = "models/rfq2boq-ner-final/final_model"
            cls._instance = cls(model_dir, base_model)
        return cls._instance

    def _load(self) -> None:
        if self._loaded:
            return

        print(f"Loading NER model from {self.model_dir}...")
        start = time.time()

        config_path = os.path.join(self.model_dir, "config.json")
        with open(config_path) as f:
            cfg = json.load(f)
        self._id2label = cfg.get("id2label", {})

        import torch
        if torch.backends.mps.is_available():
            self._device = torch.device("mps")
        else:
            self._device = torch.device("cpu")

        from transformers import AutoModelForTokenClassification, AutoTokenizer

        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_dir,
            local_files_only=True,
        )

        self._model = AutoModelForTokenClassification.from_pretrained(self.model_dir)
        self._model.to(self._device)
        self._model.eval()

        self._load_time = time.time() - start
        self._loaded = True
        total_params = sum(p.numel() for p in self._model.parameters())
        print(f"Model loaded in {self._load_time:.1f}s ({total_params / 1e6:.0f}M params) on {self._device}")

    def predict(self, text: str) -> list[dict]:
        if not self._loaded:
            self._load()

        import torch

        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=256,
            return_offsets_mapping=True,
        )

        offset_mapping = inputs.pop("offset_mapping")[0]
        attention_mask = inputs["attention_mask"].to(self._device)
        input_ids = inputs["input_ids"].to(self._device)

        with torch.no_grad():
            outputs = self._model(input_ids, attention_mask)
            logits = outputs.logits
            predictions = torch.argmax(logits, dim=-1)[0]

        tokens = self._tokenizer.convert_ids_to_tokens(input_ids[0].tolist())
        pred_ids = predictions.tolist()

        entities = []
        current_entity: dict | None = None

        for idx, (token, pred_id) in enumerate(zip(tokens, pred_ids, strict=False)):
            if token in ("[CLS]", "[SEP]", "[PAD]"):
                continue

            tok_start, tok_end = offset_mapping[idx].tolist()
            label = self._id2label.get(str(pred_id), "O")

            if label == "O":
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
                continue

            if token.startswith("##"):
                tok_text = text[tok_start:tok_end] if tok_start < tok_end else token[2:]
            else:
                tok_text = text[tok_start:tok_end] if tok_start < tok_end else token

            prefix, entity_type = label.split("-", 1)

            if prefix in ("S", "B"):
                if current_entity:
                    entities.append(current_entity)
                current_entity = {
                    "text": tok_text,
                    "type": entity_type,
                    "start": tok_start,
                    "end": tok_end,
                    "confidence": 0.9,
                    "source": "ner",
                }
            elif prefix == "I" and current_entity and current_entity["type"] == entity_type:
                current_entity["text"] += tok_text
                current_entity["end"] = tok_end
            elif prefix == "E" and current_entity and current_entity["type"] == entity_type:
                current_entity["text"] += tok_text
                current_entity["end"] = tok_end
                entities.append(current_entity)
                current_entity = None

        if current_entity:
            entities.append(current_entity)

        return entities

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def load_time(self) -> float | None:
        return self._load_time


def get_ner_model(model_dir: str | None = None) -> LazyNERModel:
    return LazyNERModel.get_instance(model_dir)


if __name__ == "__main__":
    model = get_ner_model()
    text = "Supply 500 kg cement at ground floor as per IS 456 M20 grade"
    print(f"Extracting from: {text!r}")
    entities = model.predict(text)
    print(f"Entities ({len(entities)}):")
    for e in entities:
        print(f"  {e}")
    print(f"Load time: {model.load_time:.1f}s")
