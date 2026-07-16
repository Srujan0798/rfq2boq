"""NER module for RFQ2BOQ."""


class NERModel:
    """Simplified NER model interface for project_classifier compatibility."""

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path
        self._model = None
        self._tokenizer = None
        if model_path:
            self._load()

    def _load(self):
        try:
            from pathlib import Path

            from transformers import AutoModelForTokenClassification, AutoTokenizer  # noqa: F401

            path = Path(self.model_path)
            if path.exists():
                self._tokenizer = AutoTokenizer.from_pretrained(str(path))
                self._model = AutoModelForTokenClassification.from_pretrained(str(path))
        except Exception:
            self._model = None
            self._tokenizer = None

    def predict(self, text: str) -> list[dict]:
        if self._model is None or self._tokenizer is None:
            return []
        try:
            from src.nlp.ner_inference import LABEL_LIST

            inputs = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            outputs = self._model(**inputs)
            predictions = outputs.logits.argmax(dim=-1)[0]
            tokens = self._tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
            entities = []
            current_entity: dict | None = None
            for token, pred_id in zip(tokens, predictions, strict=False):
                if token in ["[CLS]", "[SEP]", "[PAD]"]:
                    continue
                label = LABEL_LIST[pred_id] if pred_id < len(LABEL_LIST) else "O"
                if label.startswith("S-") or label.startswith("B-"):
                    if current_entity:
                        entities.append(current_entity)
                    current_entity = {"text": token, "type": label[2:], "start": 0, "end": 0, "confidence": 1.0}
                elif label.startswith("I-") and current_entity and current_entity["type"] == label[2:]:
                    current_entity["text"] += token
                else:
                    if current_entity:
                        entities.append(current_entity)
                        current_entity = None
            if current_entity:
                entities.append(current_entity)
            return entities
        except Exception:
            return []
