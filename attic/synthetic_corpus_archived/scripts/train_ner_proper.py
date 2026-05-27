#!/usr/bin/env python3
"""Proper NER training script using NERTrainer class.

Uses src.nlp.ner.dataset.NERDataset (correct word-to-token alignment)
and src.nlp.ner.trainer.NERTrainer (proper training loop with MPS support).
"""

import json
import sys
from pathlib import Path

import torch
from transformers import AutoTokenizer

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.constants import ID2LABEL, LABEL2ID, NUM_LABELS
from src.nlp.ner.bert_ner import ConstructionNER
from src.nlp.ner.dataset import NERDataset
from src.nlp.ner.trainer import NERTrainer

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")


def main():
    base_path = Path(__file__).parent.parent

    print(f"Device: {DEVICE}")

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")

    print("Loading datasets...")
    train_dataset = NERDataset(
        data_path=str(base_path / "data/annotations/train.json"),
        tokenizer=tokenizer,
        max_length=256,
        label2id=LABEL2ID,
    )
    val_dataset = NERDataset(
        data_path=str(base_path / "data/annotations/val.json"),
        tokenizer=tokenizer,
        max_length=256,
        label2id=LABEL2ID,
    )
    test_dataset = NERDataset(
        data_path=str(base_path / "data/annotations/test.json"),
        tokenizer=tokenizer,
        max_length=256,
        label2id=LABEL2ID,
    )

    print(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}, Test: {len(test_dataset)}")

    print("Initializing model...")
    model = ConstructionNER(
        model_name="bert-base-cased",
        num_labels=NUM_LABELS,
        lstm_hidden=384,
        lstm_layers=1,
        dropout=0.1,
        use_crf=False,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    output_dir = base_path / "models/rfq2boq-ner-v2"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Setting up trainer...")
    trainer = NERTrainer(
        model=model,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        output_dir=str(output_dir),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        tokenizer=tokenizer,
        learning_rate=2e-5,
        batch_size=16,
        epochs=5,
        warmup_ratio=0.1,
        device=str(DEVICE),
    )

    print("Starting training...")
    result = trainer.train()

    print("\nTraining complete:")
    print(f"  Train loss: {result.train_loss:.4f}")
    print(f"  Eval loss:  {result.eval_loss:.4f}")
    print(f"  F1:         {result.f1:.4f}")
    print(f"  Precision:  {result.precision:.4f}")
    print(f"  Recall:     {result.recall:.4f}")

    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump({
            "train_loss": result.train_loss,
            "eval_loss": result.eval_loss,
            "f1": result.f1,
            "precision": result.precision,
            "recall": result.recall,
            "epochs": 5,
            "learning_rate": 2e-5,
            "batch_size": 16,
            "lstm_hidden": 384,
            "lstm_layers": 1,
            "device": str(DEVICE),
        }, f, indent=2)
    print(f"Metrics saved to {metrics_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())