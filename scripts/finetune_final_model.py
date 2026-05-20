#!/usr/bin/env python3
"""Fine-tune final NER model on synthetic + real RFQ data."""

import json
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


def load_synthetic_annotations(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data


def load_real_annotations(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    return data


def convert_to_train_format(example: dict, source: str = "synthetic") -> dict:
    tokens = example["tokens"]
    tags = example.get("bioes_tags") or example.get("ner_tags") or example.get("labels", [])
    if len(tags) != len(tokens):
        min_len = min(len(tags), len(tokens))
        tokens = tokens[:min_len]
        tags = tags[:min_len]
    return {"tokens": tokens, "labels": tags, "source": source}


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
        texts = [f.get("tokens", f.get("sentence", "").split()) for f in features]
        if not texts or not texts[0]:
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
            feature_labels = feature.get("labels", feature.get("bioes_tags", []))
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
        for p, lbl in zip(pred, label, strict=False):
            if lbl != -100:
                temp_pred.append(ID2LABEL[p])
                temp_label.append(ID2LABEL[lbl])
        if temp_pred:
            true_predictions.append(temp_pred)
            true_labels.append(temp_label)

    from seqeval.metrics import f1_score, precision_score, recall_score

    return {
        "precision": precision_score(true_labels, true_predictions),
        "recall": recall_score(true_labels, true_predictions),
        "f1": f1_score(true_labels, true_predictions),
    }


def compute_per_entity_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=2)

    entity_results = {
        entity: {"tp": 0, "fp": 0, "fn": 0}
        for entity in ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]
    }

    for pred_seq, label_seq in zip(predictions, labels, strict=False):
        current_entity = None
        current_entity_type = None

        for pred, label in zip(pred_seq, label_seq, strict=False):
            if label == -100:
                continue
            pred_tag = ID2LABEL[pred]
            true_tag = ID2LABEL[label]

            if pred_tag.startswith("S-"):
                entity_type = pred_tag[2:]
                if entity_type in entity_results:
                    if true_tag == pred_tag:
                        entity_results[entity_type]["tp"] += 1
                    else:
                        entity_results[entity_type]["fp"] += 1
                        if true_tag.startswith("S-") and true_tag[2:] == entity_type:
                            entity_results[entity_type]["fn"] += 1

            elif pred_tag.startswith("B-"):
                if current_entity and true_tag.startswith("E-") and true_tag[2:] == current_entity_type:
                    entity_results[current_entity_type]["fn"] += 1
                current_entity = []
                current_entity_type = pred_tag[2:]
                current_entity.append(pred_tag)

            elif pred_tag.startswith("I-") and current_entity:
                current_entity.append(pred_tag)

            elif pred_tag == "O":
                if current_entity:
                    if true_tag.startswith("E-") and true_tag[2:] == current_entity_type:
                        entity_results[current_entity_type]["fn"] += 1
                    current_entity = None
                    current_entity_type = None

    metrics = {}
    for entity, counts in entity_results.items():
        tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        metrics[f"precision_{entity}"] = precision
        metrics[f"recall_{entity}"] = recall
        metrics[f"f1_{entity}"] = f1

    return metrics


def main():
    print(f"Using device: {DEVICE}")

    base_path = Path(__file__).parent.parent.resolve()

    print("=" * 60)
    print("STEP 1: Loading and combining data")
    print("=" * 60)

    synthetic_train = load_synthetic_annotations(base_path / "data/annotations/train.json")
    synthetic_val = load_synthetic_annotations(base_path / "data/annotations/val.json")
    synthetic_test = load_synthetic_annotations(base_path / "data/annotations/test.json")
    print(f"Synthetic - Train: {len(synthetic_train)}, Val: {len(synthetic_val)}, Test: {len(synthetic_test)}")

    real_dir = base_path / "data/real_rfqs/annotated"
    real_files = list(real_dir.glob("*.json"))
    real_data = []
    for rf in real_files:
        real_data.extend(load_real_annotations(rf))
    print(f"Real annotations: {len(real_data)}")

    synthetic_train_fmt = [convert_to_train_format(ex, "synthetic") for ex in synthetic_train]
    synthetic_val_fmt = [convert_to_train_format(ex, "synthetic") for ex in synthetic_val]
    synthetic_test_fmt = [convert_to_train_format(ex, "synthetic") for ex in synthetic_test]
    real_fmt = [convert_to_train_format(ex, "real") for ex in real_data]

    combined_train = synthetic_train_fmt + real_fmt

    print(f"\nCombined train: {len(combined_train)} (syn={len(synthetic_train_fmt)}, real={len(real_fmt)})")
    print(f"Hold-out test (synthetic only): {len(synthetic_test_fmt)}")

    print("\n" + "=" * 60)
    print("STEP 2: Saving combined datasets")
    print("=" * 60)

    combined_dir = base_path / "data/annotations_combined"
    combined_dir.mkdir(parents=True, exist_ok=True)

    with open(combined_dir / "train.json", "w", encoding="utf-8") as f:
        json.dump(combined_train, f, ensure_ascii=False, indent=2)
    with open(combined_dir / "val.json", "w", encoding="utf-8") as f:
        json.dump(synthetic_val_fmt, f, ensure_ascii=False, indent=2)
    with open(combined_dir / "test.json", "w", encoding="utf-8") as f:
        json.dump(synthetic_test_fmt, f, ensure_ascii=False, indent=2)
    print(f"Saved to {combined_dir}")

    print("\n" + "=" * 60)
    print("STEP 3: Loading model and tokenizer")
    print("=" * 60)

    existing_model_path = base_path / "models/rfq2boq-ner-final/final_model"
    if existing_model_path.exists():
        model_name = str(existing_model_path)
        print(f"Loading from existing model: {model_name}")
        tokenizer = AutoTokenizer.from_pretrained(str(existing_model_path.parent / "tokenizer"))
        model = AutoModelForTokenClassification.from_pretrained(
            model_name,
            num_labels=NUM_LABELS,
            id2label=ID2LABEL,
            label2id=LABEL2ID,
        )
    else:
        model_name = "bert-base-cased"
        print(f"Base model: {model_name}")
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
    print("STEP 4: Training")
    print("=" * 60)

    output_dir = base_path / "models/rfq2boq-ner-final"
    output_dir.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=8,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        learning_rate=1e-5,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=10,
        fp16=False,
        report_to=["none"],
        seed=42,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=NERDataset(combined_train),
        eval_dataset=NERDataset(synthetic_val_fmt),
        data_collator=data_collator,
        compute_metrics=compute_metrics_seqeval,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )

    print("Starting training...")
    trainer.train()

    print("\n" + "=" * 60)
    print("STEP 5: Evaluating on held-out test set")
    print("=" * 60)

    eval_results = trainer.evaluate(eval_dataset=NERDataset(synthetic_test_fmt))
    print("\nTest set results:")
    print(f"  Loss: {eval_results['eval_loss']:.4f}")
    print(f"  Precision: {eval_results['eval_precision']:.4f}")
    print(f"  Recall: {eval_results['eval_recall']:.4f}")
    print(f"  F1: {eval_results['eval_f1']:.4f}")

    predictions = trainer.predict(test_dataset=NERDataset(synthetic_test_fmt))
    pred_logits = predictions.predictions
    eval_pred = (pred_logits, predictions.label_ids)
    per_entity = compute_per_entity_metrics(eval_pred)

    print("\n--- Per-Entity F1 on Synthetic Test ---")
    entities = ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]
    for entity in entities:
        p = per_entity.get(f"precision_{entity}", 0)
        r = per_entity.get(f"recall_{entity}", 0)
        f = per_entity.get(f"f1_{entity}", 0)
        print(f"  {entity:12s}  P: {p:.4f}  R: {r:.4f}  F1: {f:.4f}")

    print("\n" + "=" * 60)
    print("STEP 6: Saving model")
    print("=" * 60)

    model.save_pretrained(output_dir / "final_model")
    tokenizer.save_pretrained(output_dir / "tokenizer")

    metrics = {
        "test_f1": eval_results["eval_f1"],
        "test_precision": eval_results["eval_precision"],
        "test_recall": eval_results["eval_recall"],
        "test_loss": eval_results["eval_loss"],
        "per_entity_f1": {entity: per_entity.get(f"f1_{entity}", 0.0) for entity in entities},
        "training_samples": len(combined_train),
        "validation_samples": len(synthetic_val_fmt),
        "test_samples": len(synthetic_test_fmt),
        "real_samples": len(real_fmt),
        "base_model": model_name,
        "epochs": 8,
        "learning_rate": 1e-5,
        "batch_size": 16,
    }
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved metrics to {output_dir / 'metrics.json'}")

    print("\n" + "=" * 60)
    print("STEP 7: Evaluating on real RFQ annotations")
    print("=" * 60)

    real_predictions = trainer.predict(test_dataset=NERDataset(real_fmt))
    real_pred_logits = real_predictions.predictions
    real_eval_pred = (real_pred_logits, real_predictions.label_ids)
    real_per_entity = compute_per_entity_metrics(real_eval_pred)

    tp_total = fp_total = fn_total = 0
    for entity in entities:
        tp_total += real_per_entity.get(f"tp_{entity}", 0)
        fp_total += real_per_entity.get(f"fp_{entity}", 0)
        fn_total += real_per_entity.get(f"fn_{entity}", 0)

    micro_p = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0
    micro_r = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0

    print("\nReal RFQ Test Set Results:")
    print(f"  Micro F1: {micro_f1:.4f}")
    print(f"  Micro Precision: {micro_p:.4f}")
    print(f"  Micro Recall: {micro_r:.4f}")

    print("\n--- Per-Entity F1 on Real RFQs ---")
    for entity in entities:
        p = real_per_entity.get(f"precision_{entity}", 0)
        r = real_per_entity.get(f"recall_{entity}", 0)
        f = real_per_entity.get(f"f1_{entity}", 0)
        print(f"  {entity:12s}  P: {p:.4f}  R: {r:.4f}  F1: {f:.4f}")

    real_metrics = {
        "real_test_f1": micro_f1,
        "real_test_precision": micro_p,
        "real_test_recall": micro_r,
        "per_entity_f1": {entity: real_per_entity.get(f"f1_{entity}", 0.0) for entity in entities},
    }

    results_dir = base_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    with open(results_dir / "final_model_eval.json", "w") as f:
        json.dump({**metrics, **real_metrics}, f, indent=2)
    print(f"\nSaved evaluation results to {results_dir / 'final_model_eval.json'}")

    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Synthetic test F1:   {eval_results['eval_f1']:.4f}")
    print(f"Real RFQ test F1:   {micro_f1:.4f}")
    print(f"Model saved to:     {output_dir}")
    print(f"Target F1 >= 0.75: {'PASS' if micro_f1 >= 0.75 else 'BELOW TARGET'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
