"""IndicBERT-based NER inference for Hindi and multilingual text.

Falls back to ai4bharat/indic-bert or xlm-roberta-base when Hindi is detected.
"""

import os
from dataclasses import dataclass
from typing import Any

import torch
from config.constants import BIOES_LABELS, ID2LABEL, LABEL2ID
from transformers import AutoModelForTokenClassification, AutoTokenizer


@dataclass
class HindiEntity:
    text: str
    type: str
    start: int
    end: int
    confidence: float


class IndicNERInference:
    def __init__(
        self,
        model_dir: str | None = None,
        id2label: dict[int, str] | None = None,
        label2id: dict[str, int] | None = None,
    ):
        self.model_dir = model_dir
        self.id2label = id2label or ID2LABEL
        self.label2id = label2id or LABEL2ID

        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

        self.device = torch.device("cpu")
        if torch.backends.mps.is_available():
            try:
                self.device = torch.device("mps")
            except Exception:
                self.device = torch.device("cpu")

        self.tokenizer: Any = None
        self.model: Any = None
        self._init_model()

    def _init_model(self) -> None:
        """Initialize IndicBERT model."""
        base_models = ["ai4bharat/indic-bert", "xlm-roberta-base"]
        model_loaded = False

        if self.model_dir:
            model_path = os.path.join(self.model_dir, "config.json")
            if os.path.exists(model_path):
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir)
                    self.model = AutoModelForTokenClassification.from_pretrained(
                        self.model_dir,
                        local_files_only=True,
                    )
                    model_loaded = True
                except Exception:
                    pass

        if not model_loaded:
            for model_name in base_models:
                try:
                    self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                    self.model = AutoModelForTokenClassification.from_pretrained(
                        model_name,
                        num_labels=len(BIOES_LABELS),
                        id2label=self.id2label,
                        label2id=self.label2id,
                    )
                    model_loaded = True
                    break
                except Exception:
                    continue

        if self.model is not None:
            self.model.to(self.device)
            self.model.eval()

    def predict(self, text: str) -> list[dict]:
        """Extract entities from Hindi/multilingual text."""
        entities = self.extract_entities(text)
        return [
            {
                "text": e.text,
                "type": e.type,
                "start": e.start,
                "end": e.end,
                "confidence": e.confidence,
                "source": "indic_ner",
            }
            for e in entities
        ]

    def extract_entities(self, text: str) -> list[HindiEntity]:
        """Extract entities using BIOES tagging."""
        if not text or not self.tokenizer:
            return []

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )

        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)

        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits

        scores = torch.softmax(logits, dim=-1)
        predictions = torch.argmax(logits, dim=-1)

        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0])
        return self._bioes_to_entities(tokens, predictions[0], scores[0], text)

    def _bioes_to_entities(
        self,
        tokens: list[str],
        predictions: Any,
        scores: Any,
        original_text: str,
    ) -> list[HindiEntity]:
        """Convert BIOES predictions to HindiEntity list."""
        entities = []
        current_entity: HindiEntity | None = None
        char_offset = 0

        for token, pred_id, score in zip(tokens, predictions, scores, strict=False):
            if token in ["[CLS]", "[SEP]", "[PAD]", "<s>", "</s>"]:
                continue

            label = self.id2label.get(
                pred_id.item() if hasattr(pred_id, "item") else pred_id, "O"
            )

            if label == "O":
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
                char_offset += len(token) + 1
                continue

            prefix = label[:1]
            entity_type = label[2:] if len(label) > 1 else label

            if prefix == "S":
                if current_entity:
                    entities.append(current_entity)
                clean_token = self._clean_token(token)
                entities.append(HindiEntity(
                    text=clean_token,
                    type=entity_type,
                    start=char_offset,
                    end=char_offset + len(clean_token),
                    confidence=score[pred_id].item() if hasattr(score, "__getitem__") else 1.0,
                ))
                char_offset += len(clean_token) + 1
                current_entity = None

            elif prefix == "B":
                if current_entity:
                    entities.append(current_entity)
                clean_token = self._clean_token(token)
                current_entity = HindiEntity(
                    text=clean_token,
                    type=entity_type,
                    start=char_offset,
                    end=char_offset + len(clean_token),
                    confidence=score[pred_id].item() if hasattr(score, "__getitem__") else 1.0,
                )
                char_offset += len(clean_token) + 1

            elif prefix == "I" and current_entity:
                if entity_type == current_entity.type:
                    clean_token = self._clean_token(token)
                    current_entity.text += clean_token
                    current_entity.end = char_offset + len(clean_token)
                    current_entity.confidence = max(
                        current_entity.confidence,
                        score[pred_id].item() if hasattr(score, "__getitem__") else 1.0,
                    )
                    char_offset += len(clean_token) + 1
                else:
                    entities.append(current_entity)
                    current_entity = None
                    char_offset += len(token) + 1

            elif prefix == "E" and current_entity:
                if entity_type == current_entity.type:
                    clean_token = self._clean_token(token)
                    current_entity.text += clean_token
                    current_entity.end = char_offset + len(clean_token)
                    entities.append(current_entity)
                    current_entity = None
                    char_offset += len(clean_token) + 1
                else:
                    entities.append(current_entity)
                    current_entity = None
                    char_offset += len(token) + 1

        if current_entity:
            entities.append(current_entity)

        return entities

    def _clean_token(self, token: str) -> str:
        """Clean tokenizer output artifacts."""
        return token.replace("##", "").replace("▁", "").strip()


def load_indic_ner(
    model_dir: str | None = None,
) -> IndicNERInference:
    """Load IndicBERT NER model."""
    return IndicNERInference(model_dir=model_dir)
