# mypy: ignore-errors
"""NER inference module for batch and single predictions."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Entity:
    text: str
    type: str
    start: int
    end: int
    confidence: float


class NERInference:
    def __init__(
        self,
        model_dir: str,
        id2label: dict[int, str],
        label2id: dict[str, int],
        model_name: str = "bert-base-cased",
    ):
        self.model_dir = model_dir
        self.id2label = id2label
        self.label2id = label2id

        import os

        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

        import torch

        self.device = torch.device("cpu")

        from transformers import AutoModelForTokenClassification, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        try:
            self.model = AutoModelForTokenClassification.from_pretrained(model_dir)
        except OSError:
            self.model = AutoModelForTokenClassification.from_pretrained(model_name, num_labels=len(label2id))
        self.model.to(self.device)
        self.model.eval()

    def extract_entities(self, text: str) -> list[Entity]:
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)

        import torch

        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            logits = outputs.logits

        scores = torch.softmax(logits, dim=-1)
        predictions = torch.argmax(logits, dim=-1)

        tokens = self.tokenizer.convert_ids_to_tokens(input_ids[0])
        entities = self._bio_to_entities(tokens, predictions[0], scores[0], text)

        return entities

    def extract_batch(self, texts: list[str]) -> list[list[Entity]]:
        all_entities = []
        for text in texts:
            entities = self.extract_entities(text)
            all_entities.append(entities)
        return all_entities

    def _bio_to_entities(
        self,
        tokens: list[str],
        predictions: Any,
        scores: Any,
        original_text: str,
    ) -> list[Entity]:
        entities = []
        current_entity = None
        char_offset = 0

        for token, pred_id, score in zip(tokens, predictions, scores, strict=False):
            if token in ["[CLS]", "[SEP]", "[PAD]"]:
                continue

            label = self.id2label.get(pred_id.item() if hasattr(pred_id, "item") else pred_id, "O")

            if label.startswith("S-"):
                if current_entity:
                    entities.append(current_entity)
                entity_text = token.replace("##", "")
                entities.append(
                    Entity(
                        text=entity_text,
                        type=label[2:],
                        start=char_offset,
                        end=char_offset + len(entity_text),
                        confidence=score[pred_id].item() if hasattr(score, "__getitem__") else 1.0,
                    )
                )
                char_offset += len(entity_text) + 1
                current_entity = None

            elif label.startswith("B-"):
                if current_entity:
                    entities.append(current_entity)
                entity_text = token.replace("##", "")
                current_entity = Entity(
                    text=entity_text,
                    type=label[2:],
                    start=char_offset,
                    end=char_offset + len(entity_text),
                    confidence=score[pred_id].item() if hasattr(score, "__getitem__") else 1.0,
                )
                char_offset += len(entity_text) + 1

            elif label.startswith("I-") and current_entity:
                if label[2:] == current_entity.type:
                    entity_text = token.replace("##", "")
                    current_entity.text += entity_text
                    current_entity.end = char_offset + len(entity_text)
                    current_entity.confidence = max(
                        current_entity.confidence,
                        score[pred_id].item() if hasattr(score, "__getitem__") else 1.0,
                    )
                    char_offset += len(entity_text) + 1
                else:
                    entities.append(current_entity)
                    current_entity = None
                    char_offset += len(token) + 1

            elif label == "O":
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
                char_offset += len(token) + 1

        if current_entity:
            entities.append(current_entity)

        return entities


def load_ner_model(
    model_dir: str,
    model_name: str = "bert-base-cased",
    id2label: dict[int, str] | None = None,
    label2id: dict[str, int] | None = None,
) -> NERInference:
    from config.constants import ID2LABEL, LABEL2ID

    return NERInference(
        model_dir=model_dir,
        id2label=id2label or ID2LABEL,
        label2id=label2id or LABEL2ID,
        model_name=model_name,
    )
