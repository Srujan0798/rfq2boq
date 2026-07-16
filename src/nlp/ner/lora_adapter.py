# mypy: ignore-errors
"""LoRA few-shot NER adapter for BERT token classification.

Wraps a pretrained AutoModelForTokenClassification with LoRA adapters
for efficient fine-tuning on small gold datasets (20-50 docs).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from transformers import AutoTokenizer

try:
    from config.constants import ID2LABEL, LABEL2ID, NUM_LABELS
except Exception:
    NUM_LABELS = 33
    ID2LABEL = None
    LABEL2ID = None

logger = logging.getLogger(__name__)


class LoRANERAdapter:
    """LoRA adapter wrapper for BERT token classification models.

    Exposes predict(text: str) -> list[dict] matching the LazyNERModel interface
    so it can be used as a drop-in replacement in NLPPipeline.
    """

    def __init__(
        self,
        base_model_path: str,
        num_labels: int = 33,
        r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.1,
        target_modules: list[str] | None = None,
    ) -> None:
        if target_modules is None:
            target_modules = ["query", "value"]

        self.base_model_path = base_model_path
        self.num_labels = num_labels
        self._tokenizer: Any = None
        self._model: Any = None
        self._device: Any = None

        try:
            import torch
            from peft import LoraConfig, TaskType, get_peft_model
            from transformers import AutoConfig, AutoModelForTokenClassification

            if torch.backends.mps.is_available():
                self._device = torch.device("mps")
            else:
                self._device = torch.device("cpu")

            self._tokenizer = AutoTokenizer.from_pretrained(base_model_path)

            cfg_kwargs = {"num_labels": num_labels, "ignore_mismatched_sizes": True}
            if ID2LABEL is not None and LABEL2ID is not None:
                cfg_kwargs.update({"id2label": ID2LABEL, "label2id": LABEL2ID})
            base_cfg = AutoConfig.from_pretrained(
                base_model_path, **{k: v for k, v in cfg_kwargs.items() if k != "ignore_mismatched_sizes"}
            )
            self._model = AutoModelForTokenClassification.from_pretrained(
                base_model_path,
                config=base_cfg,
                ignore_mismatched_sizes=True,
            )
            lora_config = LoraConfig(
                task_type=TaskType.TOKEN_CLS,
                r=r,
                lora_alpha=lora_alpha,
                lora_dropout=lora_dropout,
                bias="none",
                target_modules=target_modules,
            )
            self._model = get_peft_model(self._model, lora_config)
            self._model.to(self._device)
            self._model.eval()
            self._model.print_trainable_parameters()
        except ImportError:
            logger.warning("peft not installed; LoRA adapter unavailable")
            self._model = None
        except Exception:
            logger.exception("Failed to initialize LoRA adapter")
            self._model = None

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def save(self, path: str) -> None:
        if self._model is None:
            raise RuntimeError("LoRA model not initialized")
        Path(path).mkdir(parents=True, exist_ok=True)
        self._model.save_pretrained(path)

    @classmethod
    def load(cls, base_model_path: str, adapter_path: str, num_labels: int = 33) -> LoRANERAdapter:
        try:
            import torch
            from peft import PeftModel
            from transformers import AutoConfig, AutoModelForTokenClassification

            device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")

            tokenizer = AutoTokenizer.from_pretrained(base_model_path)
            # Force authoritative 33-label head (from config.constants) so adapter (trained for 33) matches
            cfg_kwargs = {"num_labels": num_labels, "ignore_mismatched_sizes": True}
            if ID2LABEL is not None and LABEL2ID is not None:
                cfg_kwargs.update({"id2label": ID2LABEL, "label2id": LABEL2ID})
            base_cfg = AutoConfig.from_pretrained(
                base_model_path, **{k: v for k, v in cfg_kwargs.items() if k != "ignore_mismatched_sizes"}
            )
            base = AutoModelForTokenClassification.from_pretrained(
                base_model_path,
                config=base_cfg,
                ignore_mismatched_sizes=True,
            )
            model = PeftModel.from_pretrained(base, adapter_path)
            model.to(device)
            model.eval()

            instance = cls.__new__(cls)
            instance.base_model_path = base_model_path
            instance.num_labels = num_labels
            instance._model = model
            instance._tokenizer = tokenizer
            instance._device = device
            return instance
        except ImportError:
            logger.warning("peft not installed; cannot load LoRA adapter")
            return cls(base_model_path, num_labels)
        except Exception:
            logger.exception("Failed to load LoRA adapter from %s", adapter_path)
            return cls(base_model_path, num_labels)

    def predict(self, text: str) -> list[dict]:
        """Extract entities from text. Matches LazyNERModel.predict() interface."""
        if self._model is None or self._tokenizer is None:
            return []
        import torch

        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
            return_offsets_mapping=True,
        )
        offset_mapping = inputs.pop("offset_mapping")[0]
        input_ids = inputs["input_ids"].to(self._device)
        attention_mask = inputs["attention_mask"].to(self._device)

        with torch.no_grad():
            outputs = self._model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits
            predictions = torch.argmax(logits, dim=-1)[0]

        tokens = self._tokenizer.convert_ids_to_tokens(input_ids[0].tolist())
        pred_ids = predictions.tolist()

        entities: list[dict] = []
        current_entity: dict | None = None

        for idx, (token, pred_id) in enumerate(zip(tokens, pred_ids, strict=False)):
            if token in ("[CLS]", "[SEP]", "[PAD]"):
                continue

            tok_start, tok_end = offset_mapping[idx].tolist()
            label = self._model.config.id2label.get(pred_id, "O")
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
                    "source": "lora",
                }
            elif prefix in ("I", "E") and current_entity and current_entity["type"] == entity_type:
                current_entity["text"] += tok_text
                current_entity["end"] = tok_end
            else:
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None

        if current_entity:
            entities.append(current_entity)

        return entities
