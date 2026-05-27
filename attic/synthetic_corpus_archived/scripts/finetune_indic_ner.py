"""Fine-tune IndicBERT on construction NER for English + Hindi.

Usage:
    python scripts/finetune_indic_ner.py --data data/annotations --output models/indic-ner-en-hi
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AdamW, AutoModelForTokenClassification, AutoTokenizer, get_linear_schedule_with_warmup

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.constants import BIOES_LABELS, ID2LABEL, LABEL2ID


class NERDataset(Dataset):
    def __init__(self, documents: list[dict], tokenizer, label2id: dict, max_len: int = 128):
        self.documents = documents
        self.tokenizer = tokenizer
        self.label2id = label2id
        self.max_len = max_len

    def __len__(self):
        return len(self.documents)

    def __getitem__(self, idx):
        doc = self.documents[idx]
        tokens = doc.get("tokens", doc.get("text", "").split())
        labels = doc.get("ner_tags", ["O"] * len(tokens))

        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            padding="max_length",
            truncation=True,
            max_length=self.max_len,
            return_tensors="pt"
        )

        word_ids = encoding.word_ids()
        label_ids = []
        for word_id in word_ids:
            if word_id is None:
                label_ids.append(-100)
            else:
                if word_id < len(labels):
                    label = labels[word_id]
                    label_ids.append(self.label2id.get(label, 0))
                else:
                    label_ids.append(-100)

        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "labels": torch.tensor(label_ids)
        }


def load_bioes_data(data_dir: Path) -> list[dict]:
    documents = []
    for json_file in sorted(data_dir.glob("*.json")):
        try:
            with open(json_file) as f:
                data = json.load(f)
            if "documents" in data:
                documents.extend(data["documents"])
            elif "tokens" in data:
                documents.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    return documents


def fine_tune(
    model_name: str = "ai4bharat/indic-bert",
    train_data: list[dict] | None = None,
    val_data: list[dict] | None = None,
    output_dir: str = "models/indic-ner-en-hi",
    epochs: int = 10,
    batch_size: int = 16,
    lr: float = 3e-5,
    max_len: int = 128
):
    print(f"Loading IndicBERT model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=len(BIOES_LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID
    )

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model.to(device)
    print(f"Using device: {device}")

    if not train_data:
        train_data = load_bioes_data(Path("data/annotations"))
    if not val_data:
        val_data = []

    train_ds = NERDataset(train_data, tokenizer, LABEL2ID, max_len)
    val_ds = NERDataset(val_data, tokenizer, LABEL2ID, max_len) if val_data else None

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size) if val_ds else None

    optimizer = AdamW(model.parameters(), lr=lr)
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=total_steps // 10, num_training_steps=total_steps)

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            scheduler.step()
            total_loss += loss.item()

        avg_train_loss = total_loss / len(train_loader)
        print(f"Epoch {epoch + 1}/{epochs} - Train Loss: {avg_train_loss:.4f}")

        if val_loader:
            model.eval()
            total_val_loss = 0
            with torch.no_grad():
                for batch in val_loader:
                    input_ids = batch["input_ids"].to(device)
                    attention_mask = batch["attention_mask"].to(device)
                    labels = batch["labels"].to(device)
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                    total_val_loss += outputs.loss.item()
            avg_val_loss = total_val_loss / len(val_loader)
            print(f"  Val Loss: {avg_val_loss:.4f}")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)

    metrics = {
        "model": model_name,
        "epochs": epochs,
        "train_samples": len(train_data),
        "val_samples": len(val_data) if val_data else 0,
        "final_train_loss": avg_train_loss,
        "timestamp": datetime.now().isoformat()
    }
    with open(output_path / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Model saved to {output_path}")
    print(f"Metrics: {metrics}")
    return model, metrics


def main():
    parser = argparse.ArgumentParser(description="Fine-tune IndicBERT for NER")
    parser.add_argument("--model", default="ai4bharat/indic-bert", help="Base model name")
    parser.add_argument("--data", default="data/annotations", help="Training data directory")
    parser.add_argument("--output", default="models/indic-ner-en-hi", help="Output model directory")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate")
    args = parser.parse_args()

    train_data = load_bioes_data(Path(args.data))
    print(f"Loaded {len(train_data)} training documents")

    fine_tune(
        model_name=args.model,
        train_data=train_data,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch,
        lr=args.lr
    )


if __name__ == "__main__":
    main()
