"""BERT-BiLSTM-CRF NER model."""

import contextlib
from dataclasses import dataclass

import torch
import torch.nn as nn
from transformers import AutoModel


@dataclass
class NEROutput:
    entities: list[dict]
    logits: torch.Tensor
    predictions: torch.Tensor


class BERTBiLSTMCRF(nn.Module):
    def __init__(
        self,
        model_name: str = "bert-base-cased",
        num_labels: int = 41,
        lstm_hidden: int = 256,
        lstm_layers: int = 1,
        dropout: float = 0.1,
        use_crf: bool = True,
    ):
        super().__init__()
        self.num_labels = num_labels
        self.use_crf = use_crf

        self.bert = AutoModel.from_pretrained(model_name)
        self.hidden_size = self.bert.config.hidden_size

        self.lstm = nn.LSTM(
            input_size=self.hidden_size,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if lstm_layers > 1 else 0,
        )

        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(lstm_hidden * 2, num_labels)

        if use_crf:
            self.crf = nn.Linear(num_labels, 1)

    def forward(self, input_ids, attention_mask=None, labels=None):
        bert_output = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = bert_output.last_hidden_state

        lstm_output, _ = self.lstm(sequence_output)
        lstm_output = self.dropout(lstm_output)

        logits = self.classifier(lstm_output)

        loss = None
        if labels is not None:
            loss_fct = torch.nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))

        return {"loss": loss, "logits": logits} if loss is not None else {"logits": logits}


class ConstructionNER:
    def __init__(
        self,
        model_name: str = "bert-base-cased",
        num_labels: int = 41,
        lstm_hidden: int = 128,
        lstm_layers: int = 1,
        dropout: float = 0.1,
        use_crf: bool = False,
        id2label: dict[int, str] | None = None,
        label2id: dict[str, int] | None = None,
    ):
        self.model_name = model_name
        self.num_labels = num_labels
        self.id2label = id2label or {}
        self.label2id = label2id or {}
        self.device = torch.device("cpu")

        self.model = BERTBiLSTMCRF(
            model_name=model_name,
            num_labels=num_labels,
            lstm_hidden=lstm_hidden,
            lstm_layers=lstm_layers,
            dropout=dropout,
            use_crf=use_crf,
        )
        self.model.to(self.device)

    def load(self, checkpoint_path: str):
        state_dict = torch.load(checkpoint_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.eval()

    def save(self, checkpoint_path: str):
        torch.save(self.model.state_dict(), checkpoint_path)

    def predict(self, text: str, tokenizer) -> list[dict]:
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)

        with torch.no_grad():
            logits = self.model(input_ids=input_ids, attention_mask=attention_mask)

        predictions = torch.argmax(logits, dim=-1)
        scores = torch.softmax(logits, dim=-1)

        tokens = tokenizer.convert_ids_to_tokens(input_ids[0])
        entities = self._decode_predictions(tokens, predictions[0], scores[0])

        return entities

    def _decode_predictions(
        self, tokens: list[str], predictions: torch.Tensor, scores: torch.Tensor
    ) -> list[dict]:
        entities = []
        current_entity = None

        for i, (token, pred_id, score) in enumerate(zip(tokens, predictions, scores, strict=False)):
            if token in ["[CLS]", "[SEP]", "[PAD]"]:
                continue

            label = self.id2label.get(pred_id.item(), "O")

            if label.startswith("S-"):
                entities.append({
                    "text": token.replace("##", ""),
                    "type": label[2:],
                    "start": i,
                    "end": i + 1,
                    "confidence": score[pred_id].item(),
                })
            elif label.startswith("B-"):
                if current_entity:
                    entities.append(current_entity)
                current_entity = {
                    "text": token.replace("##", ""),
                    "type": label[2:],
                    "start": i,
                    "end": i + 1,
                    "confidence": score[pred_id].item(),
                }
            elif label.startswith("I-") and current_entity:
                if label[2:] == current_entity["type"]:
                    current_entity["text"] += token.replace("##", "")
                    current_entity["end"] = i + 1
                    current_entity["confidence"] = max(
                        current_entity["confidence"], score[pred_id].item()
                    )
                else:
                    entities.append(current_entity)
                    current_entity = None
            elif label == "O" and current_entity:
                entities.append(current_entity)
                current_entity = None

        if current_entity:
            entities.append(current_entity)

        return entities


def load_pretrained_ner(
    model_dir: str,
    model_name: str = "bert-base-cased",
    num_labels: int = 41,
    id2label: dict[int, str] | None = None,
    label2id: dict[str, int] | None = None,
) -> ConstructionNER:
    ner = ConstructionNER(
        model_name=model_name,
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id,
    )
    checkpoint_path = f"{model_dir}/model.pt"
    with contextlib.suppress(FileNotFoundError):
        ner.load(checkpoint_path)
    return ner
