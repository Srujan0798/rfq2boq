#!/usr/bin/env python3
"""Retrain NER model using all 20 gold annotations with NERTrainer.

Uses the BERT-BiLSTM-CRF architecture via NERTrainer class for efficiency.
Fine-tunes from ner-bert-bilstm-crf-v1 (synthetic-trained).
"""

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.constants import ID2LABEL, LABEL2ID, NUM_LABELS
from src.nlp.ner.bert_ner import load_pretrained_ner
from src.nlp.ner.trainer import train_ner


def load_gold_annotations(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data


def convert_gold_to_train_format(example: dict) -> dict:
    tokens = example["tokens"]
    tags = example.get("ner_tags", [])
    if len(tags) != len(tokens):
        min_len = min(len(tags), len(tokens))
        tokens = tokens[:min_len]
        tags = tags[:min_len]
    return {"tokens": tokens, "labels": tags, "source": "gold"}


def load_synthetic_annotations(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    return data


def convert_synthetic_to_train_format(example: dict) -> dict:
    tokens = example.get("tokens", example.get("sentence", "").split())
    tags = example.get("labels") or example.get("ner_tags") or example.get("bioes_tags", [])
    if len(tags) != len(tokens):
        min_len = min(len(tags), len(tokens))
        tokens = tokens[:min_len]
        tags = tags[:min_len]
    return {"tokens": tokens, "labels": tags, "source": "synthetic"}


def prepare_combined_data(gold_path: Path, synth_train_path: Path, synth_val_path: Path, synth_test_path: Path):
    gold_data = load_gold_annotations(gold_path)
    random.seed(42)
    random.shuffle(gold_data)

    gold_train = gold_data[:14]
    gold_val = gold_data[14:17]
    gold_test = gold_data[17:20]

    synthetic_train = load_synthetic_annotations(synth_train_path)
    synthetic_val = load_synthetic_annotations(synth_val_path)
    synthetic_test = load_synthetic_annotations(synth_test_path)

    gold_train_fmt = [convert_gold_to_train_format(ex) for ex in gold_train]
    gold_val_fmt = [convert_gold_to_train_format(ex) for ex in gold_val]
    gold_test_fmt = [convert_gold_to_train_format(ex) for ex in gold_test]

    synthetic_train_fmt = [convert_synthetic_to_train_format(ex) for ex in synthetic_train]
    synthetic_val_fmt = [convert_synthetic_to_train_format(ex) for ex in synthetic_val]
    synthetic_test_fmt = [convert_synthetic_to_train_format(ex) for ex in synthetic_test]

    combined_train = synthetic_train_fmt + gold_train_fmt
    combined_val = synthetic_val_fmt + gold_val_fmt
    combined_test = synthetic_test_fmt + gold_test_fmt

    return {
        "train": combined_train,
        "val": combined_val,
        "test": combined_test,
        "gold_train": gold_train_fmt,
        "gold_val": gold_val_fmt,
        "gold_test": gold_test_fmt,
    }


def save_combined_datasets(data: dict, combined_dir: Path):
    combined_dir.mkdir(parents=True, exist_ok=True)

    with open(combined_dir / "train.json", "w", encoding="utf-8") as f:
        json.dump(data["train"], f, ensure_ascii=False, indent=2)
    with open(combined_dir / "val.json", "w", encoding="utf-8") as f:
        json.dump(data["val"], f, ensure_ascii=False, indent=2)
    with open(combined_dir / "test.json", "w", encoding="utf-8") as f:
        json.dump(data["test"], f, ensure_ascii=False, indent=2)

    gold_dir = combined_dir / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)
    with open(gold_dir / "train.json", "w", encoding="utf-8") as f:
        json.dump(data["gold_train"], f, ensure_ascii=False, indent=2)
    with open(gold_dir / "val.json", "w", encoding="utf-8") as f:
        json.dump(data["gold_val"], f, ensure_ascii=False, indent=2)
    with open(gold_dir / "test.json", "w", encoding="utf-8") as f:
        json.dump(data["gold_test"], f, ensure_ascii=False, indent=2)

    return combined_dir


def compute_span_metrics(predictions, labels, id2label):
    """Compute span-level F1 for entities."""
    tp = fp = fn = 0

    for pred_seq, label_seq in zip(predictions, labels, strict=False):
        true_spans = set()
        pred_spans = set()
        current_entity = None
        current_type = None

        for i, tag_id in enumerate(label_seq):
            if tag_id == -100:
                continue
            tag = id2label.get(tag_id, "O")
            if tag.startswith("S-"):
                true_spans.add((tag[2:], i, i + 1))
            elif tag.startswith("B-"):
                if current_entity is not None:
                    true_spans.add((current_type, current_entity[0], current_entity[1]))
                current_entity = [i, i + 1]
                current_type = tag[2:]
            elif tag.startswith("I-") and current_entity is not None:
                if tag[2:] == current_type:
                    current_entity[1] = i + 1
                else:
                    true_spans.add((current_type, current_entity[0], current_entity[1]))
                    current_entity = None
            elif tag == "O" and current_entity is not None:
                true_spans.add((current_type, current_entity[0], current_entity[1]))
                current_entity = None

        current_entity = None
        current_type = None
        for i, tag_id in enumerate(pred_seq):
            if tag_id == -100:
                continue
            tag = id2label.get(tag_id, "O")
            if tag.startswith("S-"):
                pred_spans.add((tag[2:], i, i + 1))
            elif tag.startswith("B-"):
                if current_entity is not None:
                    pred_spans.add((current_type, current_entity[0], current_entity[1]))
                current_entity = [i, i + 1]
                current_type = tag[2:]
            elif tag.startswith("I-") and current_entity is not None:
                if tag[2:] == current_type:
                    current_entity[1] = i + 1
                else:
                    pred_spans.add((current_type, current_entity[0], current_entity[1]))
                    current_entity = None
            elif tag == "O" and current_entity is not None:
                pred_spans.add((current_type, current_entity[0], current_entity[1]))
                current_entity = None

        if current_entity is not None:
            pred_spans.add((current_type, current_entity[0], current_entity[1]))

        tp += len(true_spans & pred_spans)
        fp += len(pred_spans - true_spans)
        fn += len(true_spans - pred_spans)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}


def main():
    base_path = Path("/Users/srujansai/Desktop/rfq2boq")

    print("=" * 60)
    print("STEP 1: Prepare combined dataset")
    print("=" * 60)

    data = prepare_combined_data(
        gold_path=base_path / "data/real_rfqs/annotations/gold_annotations.json",
        synth_train_path=base_path / "data/annotations/train.json",
        synth_val_path=base_path / "data/annotations/val.json",
        synth_test_path=base_path / "data/annotations/test.json",
    )

    combined_dir = save_combined_datasets(data, base_path / "data/annotations_combined")

    print(f"Combined train: {len(data['train'])} (syn={len(data['train']) - len(data['gold_train'])}, gold={len(data['gold_train'])})")
    print(f"Combined val: {len(data['val'])} (syn={len(data['val']) - len(data['gold_val'])}, gold={len(data['gold_val'])})")
    print(f"Gold test: {len(data['gold_test'])}")
    print(f"Saved to {combined_dir}")

    print("\n" + "=" * 60)
    print("STEP 2: Fine-tune using NERTrainer")
    print("=" * 60)

    import torch
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}")

    output_dir = base_path / "models/rfq2boq-ner-final"

    print("Training model...")
    result = train_ner(
        train_data_path=combined_dir / "train.json",
        val_data_path=combined_dir / "val.json",
        output_dir=str(output_dir),
        model_name="bert-base-cased",
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        learning_rate=2e-5,
        batch_size=16,
        epochs=10,
        warmup_ratio=0.1,
    )

    print("\nTraining complete:")
    print(f"  Train loss: {result.train_loss:.4f}")
    print(f"  Eval loss: {result.eval_loss:.4f}")
    print(f"  F1: {result.f1:.4f}")

    print("\n" + "=" * 60)
    print("STEP 3: Evaluate on gold test set (3 held-out)")
    print("=" * 60)

    from src.nlp.ner.dataset import NERDataset
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")
    gold_test_dataset = NERDataset(
        data_path=combined_dir / "gold" / "test.json",
        tokenizer=tokenizer,
        max_length=512,
        label2id=LABEL2ID,
    )

    model = load_pretrained_ner(
        model_dir=str(output_dir),
        model_name="bert-base-cased",
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    model.device = device
    model.model.to(device)
    model.model.eval()

    all_predictions = []
    all_labels = []

    from torch.utils.data import DataLoader
    gold_loader = DataLoader(gold_test_dataset, batch_size=8, shuffle=False)

    with torch.no_grad():
        for batch in gold_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model.model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            )

            predictions = torch.argmax(outputs["logits"], dim=-1)

            for pred, label in zip(predictions, labels, strict=False):
                mask = label != -100
                if mask.any():
                    all_predictions.extend(pred[mask].cpu().tolist())
                    all_labels.extend(label[mask].cpu().tolist())

    span_metrics = compute_span_metrics([all_predictions], [all_labels], ID2LABEL)

    print("\nGold test set span-level metrics (3 held-out docs):")
    print(f"  Precision: {span_metrics['precision']:.4f}")
    print(f"  Recall: {span_metrics['recall']:.4f}")
    print(f"  F1: {span_metrics['f1']:.4f}")

    print("\n" + "=" * 60)
    print("STEP 4: Save results")
    print("=" * 60)

    results = {
        "timestamp": "2026-05-17",
        "base_model": "bert-base-cased",
        "real_test_f1": span_metrics['f1'],
        "real_test_precision": span_metrics['precision'],
        "real_test_recall": span_metrics['recall'],
        "synthetic_val_f1": result.f1,
        "train_loss": result.train_loss,
        "eval_loss": result.eval_loss,
        "train_samples": len(data['train']),
        "gold_train_samples": len(data['gold_train']),
        "gold_val_samples": len(data['gold_val']),
        "gold_test_samples": len(data['gold_test']),
        "note": "Gold test = 3 held-out gold annotations; Fine-tuned from synthetic-pretrained model"
    }

    results_dir = base_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    with open(results_dir / "final_model_eval.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"Saved evaluation to {results_dir / 'final_model_eval.json'}")

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Gold test F1 (3 held-out): {span_metrics['f1']:.4f}")
    print(f"Synthetic val F1: {result.f1:.4f}")
    print(f"Target F1 >= 0.70: {'PASS' if span_metrics['f1'] >= 0.70 else 'BELOW TARGET'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
