# mypy: ignore-errors
"""NER Trainer class for model training with evaluation."""

from dataclasses import dataclass
from pathlib import Path

import torch
from src.nlp.ner.bert_ner import ConstructionNER
from src.nlp.ner.dataset import NERDataset
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import PreTrainedTokenizer


@dataclass
class TrainingResult:
    train_loss: float
    eval_loss: float
    f1: float
    precision: float
    recall: float


class NERTrainer:
    def __init__(
        self,
        model: ConstructionNER,
        train_dataset: NERDataset,
        val_dataset: NERDataset,
        output_dir: str | Path,
        id2label: dict[int, str],
        label2id: dict[str, int],
        tokenizer: PreTrainedTokenizer,
        learning_rate: float = 2e-5,
        batch_size: int = 16,
        epochs: int = 8,
        warmup_ratio: float = 0.1,
        device: str | None = None,
    ):
        self.model = model
        self.train_dataset = train_dataset
        self.val_dataset = val_dataset
        self.output_dir = Path(output_dir)
        self.id2label = id2label
        self.label2id = label2id
        self.tokenizer = tokenizer
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.warmup_ratio = warmup_ratio

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.model.model.to(self.device)

        self.optimizer = torch.optim.AdamW(
            self.model.model.parameters(),
            lr=learning_rate,
        )

        self.train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=0,
        )

        self.val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=0,
        )

    def train(self) -> TrainingResult:
        total_steps = len(self.train_loader) * self.epochs
        warmup_steps = int(total_steps * self.warmup_ratio)

        scheduler = torch.optim.lr_scheduler.LinearLR(
            self.optimizer,
            start_factor=0.1,
            end_factor=1.0,
            total_iters=warmup_steps,
        )

        best_f1 = 0.0
        best_model_state = None

        for epoch in range(self.epochs):
            self.model.model.train()
            train_loss = 0.0

            for batch in tqdm(self.train_loader, desc=f"Epoch {epoch + 1}/{self.epochs}"):
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                self.optimizer.zero_grad()

                outputs = self.model.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )

                loss = outputs["loss"]
                loss.backward()

                torch.nn.utils.clip_grad_norm_(self.model.model.parameters(), 1.0)

                self.optimizer.step()
                scheduler.step()

                train_loss += loss.item()

            train_loss /= len(self.train_loader)

            eval_loss, f1, precision, recall = self.evaluate()

            print(f"Epoch {epoch + 1}: train_loss={train_loss:.4f}, eval_loss={eval_loss:.4f}, f1={f1:.4f}")

            if f1 > best_f1:
                best_f1 = f1
                best_model_state = {k: v.cpu().clone() for k, v in self.model.model.state_dict().items()}

        if best_model_state is not None:
            self.model.model.load_state_dict(best_model_state)

        eval_loss, f1, precision, recall = self.evaluate()

        return TrainingResult(
            train_loss=train_loss,
            eval_loss=eval_loss,
            f1=f1,
            precision=precision,
            recall=recall,
        )

    def evaluate(self) -> tuple[float, float, float, float]:
        self.model.model.eval()
        total_loss = 0.0

        all_predictions = []
        all_labels = []

        with torch.no_grad():
            for batch in self.val_loader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels = batch["labels"].to(self.device)

                outputs = self.model.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                )

                total_loss += outputs["loss"].item()

                predictions = torch.argmax(outputs["logits"], dim=-1)

                for pred, label in zip(predictions, labels, strict=False):
                    mask = label != self.label2id.get("O", 0)
                    if mask.any():
                        all_predictions.extend(pred[mask].cpu().tolist())
                        all_labels.extend(label[mask].cpu().tolist())

        avg_loss = total_loss / len(self.val_loader)

        if all_predictions:
            f1, precision, recall = self._compute_metrics(all_predictions, all_labels)
        else:
            f1, precision, recall = 0.0, 0.0, 0.0

        return avg_loss, f1, precision, recall

    def _compute_metrics(
        self,
        predictions: list[int],
        labels: list[int],
    ) -> tuple[float, float, float]:
        from collections import Counter

        pred_counts = Counter(predictions)
        label_counts = Counter(labels)

        tp = sum((pred_counts & label_counts).values())
        fp = sum((pred_counts - label_counts).values())
        fn = sum((label_counts - pred_counts).values())

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return f1, precision, recall


def train_ner(
    train_data_path: str | Path,
    val_data_path: str | Path,
    output_dir: str | Path,
    model_name: str = "bert-base-cased",
    num_labels: int = 41,
    id2label: dict[int, str] | None = None,
    label2id: dict[str, int] | None = None,
    learning_rate: float = 2e-5,
    batch_size: int = 16,
    epochs: int = 8,
    warmup_ratio: float = 0.1,
) -> TrainingResult:
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    train_dataset = NERDataset(
        data_path=train_data_path,
        tokenizer=tokenizer,
        max_length=512,
        label2id=label2id,
    )

    val_dataset = NERDataset(
        data_path=val_data_path,
        tokenizer=tokenizer,
        max_length=512,
        label2id=label2id,
    )

    model = ConstructionNER(
        model_name=model_name,
        num_labels=num_labels,
        id2label=id2label,
        label2id=label2id,
    )

    trainer = NERTrainer(
        model=model,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        output_dir=output_dir,
        id2label=id2label,
        label2id=label2id,
        tokenizer=tokenizer,
        learning_rate=learning_rate,
        batch_size=batch_size,
        epochs=epochs,
        warmup_ratio=warmup_ratio,
    )

    return trainer.train()
