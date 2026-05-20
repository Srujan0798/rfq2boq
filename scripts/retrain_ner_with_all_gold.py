#!/usr/bin/env python3
"""Retrain NER model using all 20 gold annotations.

This script:
1. Loads all 20 gold annotations from gold_annotations.json
2. Splits into 14 train / 3 val / 3 test
3. Combines with synthetic data
4. Fine-tunes from ner-bert-bilstm-crf-v1 base model
5. Evaluates on held-out 3 gold examples
"""

import json
import random
import sys
from pathlib import Path

import numpy as np
import torch
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
)

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.constants import ID2LABEL, LABEL2ID, NUM_LABELS

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using device: {DEVICE}")


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


class NERDataset(torch.utils.data.Dataset):
    def __init__(self, examples: list[dict]):
        self.examples = examples

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict:
        return self.examples[idx]


class NERDataCollator:
    def __init__(self, tokenizer, label2id: dict[str, int]):
        self.tokenizer = tokenizer
        self.label2id = label2id

    def __call__(self, features):
        texts = [f.get("tokens", []) for f in features]
        if not texts or not all(texts):
            texts = [["EMPTY"] for _ in features]
        tokenized = self.tokenizer(
            texts,
            is_split_into_words=True,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt",
        )

        labels = []
        for batch_idx, feature in enumerate(features):
            tag_ids = []
            feature_labels = feature.get("labels", [])
            tokenized["input_ids"][batch_idx]

            word_to_token = {}
            for token_idx, word_id in enumerate(tokenized.word_ids(batch_index=batch_idx)):
                if word_id is not None and word_id not in word_to_token:
                    word_to_token[word_id] = token_idx

            for token_idx, word_id in enumerate(tokenized.word_ids(batch_index=batch_idx)):
                if word_id is None:
                    tag_ids.append(-100)
                elif word_id in word_to_token and word_id < len(feature_labels):
                    if word_id == 0 or token_idx == word_to_token[word_id]:
                        tag_ids.append(self.label2id.get(feature_labels[word_id], 0))
                    else:
                        tag_ids.append(-100)
                else:
                    tag_ids.append(-100)
            labels.append(tag_ids)

        tokenized["labels"] = torch.tensor(labels)
        return tokenized


def compute_metrics_seqeval(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=2)

    true_predictions = []
    true_labels = []
    for pred, label in zip(predictions, labels, strict=False):
        temp_pred = []
        temp_label = []
        for p, l in zip(pred, label, strict=False):
            if l != -100:
                temp_pred.append(ID2LABEL[p])
                temp_label.append(ID2LABEL[l])
        if temp_pred:
            true_predictions.append(temp_pred)
            true_labels.append(temp_label)

    from seqeval.metrics import f1_score, precision_score, recall_score

    return {
        "precision": precision_score(true_labels, true_predictions),
        "recall": recall_score(true_labels, true_predictions),
        "f1": f1_score(true_labels, true_predictions),
    }


def compute_span_f1(predictions, labels, id2label):
    """Compute span-level F1 for entities."""
    true_entities = []
    pred_entities = []

    for pred_seq, label_seq in zip(predictions, labels, strict=False):
        true_spans = _extract_spans(label_seq, id2label)
        pred_spans = _extract_spans(pred_seq, id2label)
        true_entities.append(set(true_spans))
        pred_entities.append(set(pred_spans))

    tp = fp = fn = 0
    for true_set, pred_set in zip(true_entities, pred_entities, strict=False):
        tp += len(true_set & pred_set)
        fp += len(pred_set - true_set)
        fn += len(true_set - pred_set)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}


def _extract_spans(tag_seq, id2label):
    """Extract spans from BIOES tag sequence."""
    spans = []
    current_entity = None
    current_type = None

    for i, tag_id in enumerate(tag_seq):
        if tag_id == -100:
            continue
        tag = id2label.get(tag_id, "O")

        if tag.startswith("S-"):
            spans.append((tag[2:], i, i + 1))
        elif tag.startswith("B-"):
            if current_entity is not None:
                spans.append((current_type, current_entity[0], current_entity[1]))
            current_entity = [i, i + 1]
            current_type = tag[2:]
        elif tag.startswith("I-") and current_entity is not None:
            if tag[2:] == current_type:
                current_entity[1] = i + 1
            else:
                spans.append((current_type, current_entity[0], current_entity[1]))
                current_entity = None
                current_type = None
        elif tag == "O" and current_entity is not None:
            spans.append((current_type, current_entity[0], current_entity[1]))
            current_entity = None
            current_type = None

    if current_entity is not None:
        spans.append((current_type, current_entity[0], current_entity[1]))

    return spans


def main():
    base_path = Path("/Users/srujansai/Desktop/rfq2boq")

    print("=" * 60)
    print("STEP 1: Load and split gold annotations (20 docs)")
    print("=" * 60)

    gold_path = base_path / "data/real_rfqs/annotations/gold_annotations.json"
    gold_data = load_gold_annotations(gold_path)
    print(f"Loaded {len(gold_data)} gold annotations")

    random.seed(42)
    random.shuffle(gold_data)

    gold_train = gold_data[:14]
    gold_val = gold_data[14:17]
    gold_test = gold_data[17:20]

    print(f"Gold split: train={len(gold_train)}, val={len(gold_val)}, test={len(gold_test)}")

    print("\n" + "=" * 60)
    print("STEP 2: Load and combine with synthetic data")
    print("=" * 60)

    synthetic_train = load_synthetic_annotations(base_path / "data/annotations/train.json")
    synthetic_val = load_synthetic_annotations(base_path / "data/annotations/val.json")
    synthetic_test = load_synthetic_annotations(base_path / "data/annotations/test.json")
    print(f"Synthetic: train={len(synthetic_train)}, val={len(synthetic_val)}, test={len(synthetic_test)}")

    gold_train_fmt = [convert_gold_to_train_format(ex) for ex in gold_train]
    gold_val_fmt = [convert_gold_to_train_format(ex) for ex in gold_val]
    gold_test_fmt = [convert_gold_to_train_format(ex) for ex in gold_test]

    synthetic_train_fmt = [convert_synthetic_to_train_format(ex) for ex in synthetic_train]
    synthetic_val_fmt = [convert_synthetic_to_train_format(ex) for ex in synthetic_val]
    synthetic_test_fmt = [convert_synthetic_to_train_format(ex) for ex in synthetic_test]

    combined_train = synthetic_train_fmt + gold_train_fmt
    combined_val = synthetic_val_fmt + gold_val_fmt
    combined_test = synthetic_test_fmt + gold_test_fmt

    print(f"\nCombined train: {len(combined_train)} (syn={len(synthetic_train_fmt)}, gold={len(gold_train_fmt)})")
    print(f"Combined val: {len(combined_val)} (syn={len(synthetic_val_fmt)}, gold={len(gold_val_fmt)})")
    print(f"Combined test: {len(combined_test)} (syn={len(synthetic_test_fmt)}, gold={len(gold_test_fmt)})")

    print("\n" + "=" * 60)
    print("STEP 3: Save combined datasets")
    print("=" * 60)

    combined_dir = base_path / "data/annotations_combined"
    combined_dir.mkdir(parents=True, exist_ok=True)

    with open(combined_dir / "train.json", "w", encoding="utf-8") as f:
        json.dump(combined_train, f, ensure_ascii=False, indent=2)
    with open(combined_dir / "val.json", "w", encoding="utf-8") as f:
        json.dump(combined_val, f, ensure_ascii=False, indent=2)
    with open(combined_dir / "test.json", "w", encoding="utf-8") as f:
        json.dump(combined_test, f, ensure_ascii=False, indent=2)

    gold_dir = combined_dir / "gold"
    gold_dir.mkdir(parents=True, exist_ok=True)
    with open(gold_dir / "train.json", "w", encoding="utf-8") as f:
        json.dump(gold_train_fmt, f, ensure_ascii=False, indent=2)
    with open(gold_dir / "val.json", "w", encoding="utf-8") as f:
        json.dump(gold_val_fmt, f, ensure_ascii=False, indent=2)
    with open(gold_dir / "test.json", "w", encoding="utf-8") as f:
        json.dump(gold_test_fmt, f, ensure_ascii=False, indent=2)

    print(f"Saved to {combined_dir}")
    print(f"Gold data saved to {gold_dir}")

    print("\n" + "=" * 60)
    print("STEP 4: Initialize model from bert-base-cased")
    print("=" * 60)

    model_name = "bert-base-cased"
    print(f"Base model: {model_name}")
    print(f"Number of labels: {NUM_LABELS}")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    model.to(DEVICE)

    data_collator = NERDataCollator(tokenizer, LABEL2ID)

    print("\n" + "=" * 60)
    print("STEP 5: Training with early stopping")
    print("=" * 60)

    output_dir = base_path / "models/rfq2boq-ner-final"
    output_dir.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=10,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        learning_rate=2e-5,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=20,
        fp16=False,
        report_to=["none"],
        seed=42,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=NERDataset(combined_train),
        eval_dataset=NERDataset(combined_val),
        data_collator=data_collator,
        compute_metrics=compute_metrics_seqeval,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )

    print("Starting training...")
    trainer.train()

    print("\n" + "=" * 60)
    print("STEP 6: Evaluate on held-out gold test set (3 docs)")
    print("=" * 60)

    gold_test_dataset = NERDataset(gold_test_fmt)
    gold_predictions = trainer.predict(test_dataset=gold_test_dataset)
    gold_pred_logits = gold_predictions.predictions
    gold_labels = gold_predictions.label_ids

    pred_ids = np.argmax(gold_pred_logits, axis=2)

    span_metrics = compute_span_f1(pred_ids, gold_labels, ID2LABEL)
    print("\nGold test set span-level metrics:")
    print(f"  Precision: {span_metrics['precision']:.4f}")
    print(f"  Recall: {span_metrics['recall']:.4f}")
    print(f"  F1: {span_metrics['f1']:.4f}")

    print("\n" + "=" * 60)
    print("STEP 7: Save model and tokenizer")
    print("=" * 60)

    model.save_pretrained(output_dir / "final_model")
    tokenizer.save_pretrained(output_dir / "tokenizer")

    print("\n" + "=" * 60)
    print("STEP 8: Generate evaluation report")
    print("=" * 60)

    eval_results = trainer.evaluate(eval_dataset=NERDataset(combined_test))

    results = {
        "timestamp": "2026-05-17",
        "base_model": model_name,
        "epochs": 10,
        "real_test_f1": span_metrics['f1'],
        "real_test_precision": span_metrics['precision'],
        "real_test_recall": span_metrics['recall'],
        "synthetic_test_f1": eval_results.get("eval_f1", 0.0),
        "synthetic_test_precision": eval_results.get("eval_precision", 0.0),
        "synthetic_test_recall": eval_results.get("eval_recall", 0.0),
        "train_samples": len(combined_train),
        "gold_train_samples": len(gold_train_fmt),
        "gold_val_samples": len(gold_val_fmt),
        "gold_test_samples": len(gold_test_fmt),
        "note": "Gold test = 3 held-out gold annotations, synthetic test = held-out synthetic"
    }

    results_dir = base_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    with open(results_dir / "final_model_eval.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved evaluation to {results_dir / 'final_model_eval.json'}")

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Gold test F1 (3 held-out): {span_metrics['f1']:.4f}")
    print(f"Synthetic test F1: {eval_results.get('eval_f1', 0):.4f}")
    print(f"Target F1 >= 0.70: {'PASS' if span_metrics['f1'] >= 0.70 else 'BELOW TARGET'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
