# mypy: ignore-errors
"""LayoutLMv3 NER model for layout-aware extraction."""

from typing import Any

import torch
from transformers import LayoutLMv3ForTokenClassification, LayoutLMv3Tokenizer

LABEL2ID = {
    "O": 0,
    "B-MATERIAL": 1,
    "I-MATERIAL": 2,
    "E-MATERIAL": 3,
    "S-MATERIAL": 4,
    "B-QUANTITY": 5,
    "I-QUANTITY": 6,
    "E-QUANTITY": 7,
    "S-QUANTITY": 8,
    "B-UNIT": 9,
    "I-UNIT": 10,
    "E-UNIT": 11,
    "S-UNIT": 12,
    "B-LOCATION": 13,
    "I-LOCATION": 14,
    "E-LOCATION": 15,
    "S-LOCATION": 16,
    "B-DIMENSION": 17,
    "I-DIMENSION": 18,
    "E-DIMENSION": 19,
    "S-DIMENSION": 20,
    "B-STANDARD": 21,
    "I-STANDARD": 22,
    "E-STANDARD": 23,
    "S-STANDARD": 24,
    "B-ACTION": 25,
    "I-ACTION": 26,
    "E-ACTION": 27,
    "S-ACTION": 28,
    "B-GRADE": 29,
    "I-GRADE": 30,
    "E-GRADE": 31,
    "S-GRADE": 32,
}

ID2LABEL = {v: k for k, v in LABEL2ID.items()}


class LayoutLMv3NER:
    """LayoutLMv3 wrapper for named entity recognition with layout awareness."""

    def __init__(
        self,
        model_dir: str | None = None,
        model_name: str = "microsoft/layoutlmv3-base",
        num_labels: int = 33,
    ):
        self.model_name = model_name
        self.num_labels = num_labels
        self.label2id = LABEL2ID
        self.id2label = ID2LABEL

        if model_dir:
            self.model = LayoutLMv3ForTokenClassification.from_pretrained(
                model_dir,
                num_labels=num_labels,
                id2label=ID2LABEL,
                label2id=LABEL2ID,
            )
            self.tokenizer = LayoutLMv3Tokenizer.from_pretrained(model_dir)
        else:
            self.model = None
            self.tokenizer = None

    def predict(
        self,
        tokens: list[str],
        bboxes: list[list[int]],
        text: str | None = None,
    ) -> list[dict[str, Any]]:
        """Predict entities given tokens and bounding boxes."""
        if not self.model or not self.tokenizer:
            return []

        inputs = self.tokenizer(
            tokens,
            return_tensors="pt",
            padding="max_length",
            max_length=512,
            truncation=True,
        )

        bbox = torch.tensor(bboxes[:512], dtype=torch.long).unsqueeze(0)
        attention_mask = inputs["attention_mask"]

        with torch.no_grad():
            outputs = self.model(
                input_ids=inputs["input_ids"],
                bbox=bbox,
                attention_mask=attention_mask,
            )

        logits = outputs.logits
        predictions = torch.argmax(logits, dim=-1)

        batch_idx = 0
        results = []
        for seq_idx, pred_id in enumerate(predictions[batch_idx]):
            if attention_mask[batch_idx][seq_idx] == 0:
                continue
            label = ID2LABEL.get(pred_id.item(), "O")
            if label != "O":
                token_text = tokens[seq_idx] if seq_idx < len(tokens) else ""
                results.append(
                    {
                        "text": token_text,
                        "label": label,
                        "bbox": bboxes[seq_idx] if seq_idx < len(bboxes) else [0, 0, 0, 0],
                        "confidence": 0.85,
                    }
                )

        return results

    def forward(
        self,
        input_ids: torch.Tensor,
        bbox: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor | None = None,
    ) -> dict[str, Any]:
        """Forward pass with optional labels for training."""
        outputs = self.model(
            input_ids=input_ids,
            bbox=bbox,
            attention_mask=attention_mask,
            labels=labels,
        )
        return {"loss": outputs.loss, "logits": outputs.logits}

    @property
    def device(self) -> torch.device:
        """Get model device."""
        if self.model:
            return next(self.model.parameters()).device
        return torch.device("cpu")

    def save(self, checkpoint_path: str):
        if self.model:
            self.model.save_pretrained(checkpoint_path)

    def load(self, checkpoint_path: str):
        if self.model:
            self.model.from_pretrained(checkpoint_path)


LayoutAwareNER = LayoutLMv3NER


def load_layoutlm_ner(model_dir: str) -> LayoutLMv3NER:
    """Load LayoutLM NER model from directory."""
    return LayoutLMv3NER(model_dir=model_dir)


def load_pretrained_layoutlm(
    model_dir: str,
    id2label: dict[int, str] | None = None,
    label2id: dict[str, int] | None = None,
) -> LayoutLMv3NER:
    """Load pretrained LayoutLM NER model with label mappings."""
    return LayoutLMv3NER(model_dir=model_dir)
