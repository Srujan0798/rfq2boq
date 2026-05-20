#!/usr/bin/env python3
"""NER training CLI script."""

import argparse
import json
import sys
from pathlib import Path

from config.constants import ID2LABEL, LABEL2ID
from src.nlp.ner.bert_ner import ConstructionNER
from src.nlp.ner.dataset import NERDataset
from src.nlp.ner.trainer import NERTrainer
from transformers import AutoTokenizer


def main():
    parser = argparse.ArgumentParser(description="Train NER model")
    parser.add_argument("--train-data", type=str, required=True, help="Path to training data JSON")
    parser.add_argument("--val-data", type=str, required=True, help="Path to validation data JSON")
    parser.add_argument("--output-dir", type=str, default="models/ner-bert-bilstm-crf-v1")
    parser.add_argument("--model-name", type=str, default="bert-base-cased")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--lstm-hidden", type=int, default=256)
    parser.add_argument("--warmup-ratio", type=float, default=0.1)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading tokenizer: {args.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    print(f"Loading training data from {args.train_data}")
    train_dataset = NERDataset(
        data_path=args.train_data,
        tokenizer=tokenizer,
        max_length=512,
        label2id=LABEL2ID,
    )

    print(f"Loading validation data from {args.val_data}")
    val_dataset = NERDataset(
        data_path=args.val_data,
        tokenizer=tokenizer,
        max_length=512,
        label2id=LABEL2ID,
    )

    print("Initializing NER model")
    num_labels = len(LABEL2ID)
    model = ConstructionNER(
        model_name=args.model_name,
        num_labels=num_labels,
        lstm_hidden=args.lstm_hidden,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    print("Setting up trainer")
    trainer = NERTrainer(
        model=model,
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        output_dir=str(output_dir),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        tokenizer=tokenizer,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        epochs=args.epochs,
        warmup_ratio=args.warmup_ratio,
    )

    print("Starting training")
    result = trainer.train()

    print("\nTraining complete:")
    print(f"  Train loss: {result.train_loss:.4f}")
    print(f"  Eval loss:  {result.eval_loss:.4f}")
    print(f"  F1:         {result.f1:.4f}")
    print(f"  Precision:  {result.precision:.4f}")
    print(f"  Recall:     {result.recall:.4f}")

    checkpoint_path = output_dir / "model.pt"
    print(f"\nSaving model to {checkpoint_path}")
    model.save(str(checkpoint_path))

    metrics = {
        "train_loss": result.train_loss,
        "eval_loss": result.eval_loss,
        "f1": result.f1,
        "precision": result.precision,
        "recall": result.recall,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "lstm_hidden": args.lstm_hidden,
    }
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics to {metrics_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
