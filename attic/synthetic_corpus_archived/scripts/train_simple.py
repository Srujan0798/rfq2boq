#!/usr/bin/env python3
"""Minimal NER training script - CPU only, no HuggingFace Trainer."""

import json
import os

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

from config.constants import ID2LABEL, LABEL2ID


class SimpleNERDataset(torch.utils.data.Dataset):
    def __init__(self, data, tokenizer, label2id, max_len=128):
        self.data = data
        self.tokenizer = tokenizer
        self.label2id = label2id
        self.max_len = max_len

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        tokens = item["tokens"]
        labels = item["ner_tags"]

        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            max_length=self.max_len,
            padding="max_length",
            return_tensors="pt",
        )

        word_ids = encoding.word_ids()
        label_ids = []
        for word_id in word_ids:
            if word_id is None:
                label_ids.append(-100)
            else:
                label = labels[word_id] if word_id < len(labels) else "O"
                label_ids.append(self.label2id.get(label, self.label2id.get("O", 0)))

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(label_ids, dtype=torch.long),
        }


class BERTBiLSTMNER(nn.Module):
    def __init__(self, model_name, num_labels, hidden_size=128):
        super().__init__()
        self.bert = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(0.1)
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_labels)
        self.num_labels = num_labels

    def forward(self, input_ids, attention_mask, labels=None):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state
        sequence_output = self.dropout(sequence_output)
        logits = self.classifier(sequence_output)

        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss(ignore_index=-100)
            loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))

        return {"loss": loss, "logits": logits}


def train_epoch(model, dataloader, optimizer, device):
    model.train()
    total_loss = 0
    for batch in tqdm(dataloader, desc="Training"):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        optimizer.zero_grad()
        outputs = model(input_ids, attention_mask, labels)
        loss = outputs["loss"]
        if loss is not None:
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
    return total_loss / len(dataloader)


def evaluate(model, dataloader, device):
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids, attention_mask, labels)
            if outputs["loss"] is not None:
                total_loss += outputs["loss"].item()

            preds = torch.argmax(outputs["logits"], dim=-1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    # Compute micro F1
    from sklearn.metrics import f1_score, precision_score, recall_score

    y_true = []
    y_pred = []
    for preds, labels in zip(all_preds, all_labels, strict=False):
        for p, l in zip(preds, labels, strict=False):
            if l != -100:
                y_pred.append(ID2LABEL.get(p, "O"))
                y_true.append(ID2LABEL.get(l, "O"))

    f1 = f1_score(y_true, y_pred, average="micro", zero_division=0)
    precision = precision_score(y_true, y_pred, average="micro", zero_division=0)
    recall = recall_score(y_true, y_pred, average="micro", zero_division=0)

    return total_loss / max(len(dataloader), 1), f1, precision, recall


def main():
    print("Loading data...")
    with open("data/annotations/train.json") as f:
        train_data = json.load(f)
    with open("data/annotations/val.json") as f:
        val_data = json.load(f)

    print(f"Train: {len(train_data)}, Val: {len(val_data)}")

    tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")
    num_labels = len(LABEL2ID)
    print(f"Num labels: {num_labels}")

    print("Creating datasets...")
    train_ds = SimpleNERDataset(train_data, tokenizer, LABEL2ID, max_len=128)
    val_ds = SimpleNERDataset(val_data, tokenizer, LABEL2ID, max_len=128)

    train_loader = DataLoader(train_ds, batch_size=8, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=8, shuffle=False, num_workers=0)

    print("Creating model...")
    device = torch.device("cpu")
    model = BERTBiLSTMNER("bert-base-cased", num_labels)
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)

    print("Training...")
    best_f1 = 0
    for epoch in range(3):
        print(f"\nEpoch {epoch + 1}/3")
        train_loss = train_epoch(model, train_loader, optimizer, device)
        val_loss, f1, precision, recall = evaluate(model, val_loader, device)
        print(f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        print(f"F1: {f1:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}")

        if f1 > best_f1:
            best_f1 = f1
            torch.save(model.state_dict(), "models/ner-bert-bilstm-crf-v1/model.pt")
            print("  -> Saved best model")

    print(f"\nBest F1: {best_f1:.4f}")
    print("Training complete!")


if __name__ == "__main__":
    main()
