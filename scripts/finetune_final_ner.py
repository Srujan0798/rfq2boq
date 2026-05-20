#!/usr/bin/env python3
"""Fine-tune rfq2boq-ner-final from combined synthetic+real data."""

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
print(f"Using device: {DEVICE}")


def load_annotations(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data


def convert_format(example: dict) -> dict:
    tokens = example["tokens"]
    tags = example.get("ner_tags") or example.get("bioes_tags") or example.get("labels", [])
    if len(tags) != len(tokens):
        min_len = min(len(tags), len(tokens))
        tokens = tokens[:min_len]
        tags = tags[:min_len]
    return {"tokens": tokens, "labels": tags}


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
            feature_labels = feature.get("labels", [])
            word_to_token = {}
            for _token_idx, word_id in enumerate(tokenized.word_ids(batch_index=batch_idx)):
                if word_id is not None and word_id not in word_to_token:
                    word_to_token[word_id] = _token_idx

            for _token_idx, _word_id in enumerate(tokenized.word_ids(batch_index=batch_idx)):
                if _word_id is None:
                    tag_ids.append(-100)
                elif word_id in word_to_token and word_id < len(feature_labels):
                    tag_ids.append(self.label2id.get(feature_labels[word_id], 0))
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
        current_entity = []
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
                if (current_entity and true_tag.startswith("E-") and
                    true_tag[2:] == current_entity_type and len(current_entity) == 1):
                    entity_results[current_entity_type]["fn"] += 1
                current_entity = [pred_tag]
                current_entity_type = pred_tag[2:]

            elif pred_tag.startswith("I-") and current_entity:
                current_entity.append(pred_tag)

            elif pred_tag == "O":
                if current_entity:
                    if true_tag.startswith("E-") and true_tag[2:] == current_entity_type:
                        pass
                    current_entity = []
                    current_entity_type = None

    metrics = {}
    for entity, counts in entity_results.items():
        tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        metrics[f"f1_{entity}"] = f1
        metrics[f"precision_{entity}"] = precision
        metrics[f"recall_{entity}"] = recall

    return metrics


def main():
    base_path = Path(__file__).parent.parent.resolve()

    print("=" * 60)
    print("Fine-tuning rfq2boq-ner-final on combined data")
    print("=" * 60)

    print("\n--- Loading data ---")
    train_data = load_annotations(base_path / "data/annotations_combined/train.json")
    val_data = load_annotations(base_path / "data/annotations_combined/val.json")
    test_data = load_annotations(base_path / "data/annotations_combined/test.json")

    train_fmt = [convert_format(ex) for ex in train_data]
    val_fmt = [convert_format(ex) for ex in val_data]
    test_fmt = [convert_format(ex) for ex in test_data]

    real_in_test = [ex for ex in test_fmt if ex.get("source") == "real"]
    print(f"Train: {len(train_fmt)}, Val: {len(val_fmt)}, Test: {len(test_fmt)}")
    print(f"Real examples in test: {len(real_in_test)}")

    print("\n--- Loading model from checkpoint-56 ---")
    checkpoint_path = base_path / "models/rfq2boq-ner-final/checkpoint-56"
    model_name = "allenai/scibert_scivocab_uncased"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(
        str(checkpoint_path),
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    model.to(DEVICE)

    data_collator = NERDataCollator(tokenizer, LABEL2ID)

    print("\n--- Training (8 epochs, lr=1e-5, batch=16) ---")
    output_dir = base_path / "models/rfq2boq-ner-final"

    training_args = TrainingArguments(
        output_dir=str(output_dir / "finetune_run"),
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
        logging_steps=5,
        fp16=False,
        report_to=["none"],
        seed=42,
        dataloader_num_workers=0,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=NERDataset(train_fmt),
        eval_dataset=NERDataset(val_fmt),
        data_collator=data_collator,
        compute_metrics=compute_metrics_seqeval,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )

    print("Starting training...")
    trainer.train()

    print("\n--- Evaluating on combined test set ---")
    eval_results = trainer.evaluate(eval_dataset=NERDataset(test_fmt))
    print("\nTest set metrics:")
    print(f"  F1: {eval_results['eval_f1']:.4f}")
    print(f"  Precision: {eval_results['eval_precision']:.4f}")
    print(f"  Recall: {eval_results['eval_recall']:.4f}")

    print("\n--- Per-entity F1 on test set ---")
    predictions = trainer.predict(test_dataset=NERDataset(test_fmt))
    pred_logits = predictions.predictions
    eval_pred = (pred_logits, predictions.label_ids)
    per_entity = compute_per_entity_metrics(eval_pred)

    entities = ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]
    for entity in entities:
        f = per_entity.get(f"f1_{entity}", 0)
        p = per_entity.get(f"precision_{entity}", 0)
        r = per_entity.get(f"recall_{entity}", 0)
        print(f"  {entity:12s}  P: {p:.4f}  R: {r:.4f}  F1: {f:.4f}")

    print("\n--- Evaluating on REAL test set only ---")
    real_test_only = [ex for ex in test_fmt if ex.get("source") == "real"]
    if real_test_only:
        real_pred = trainer.predict(test_dataset=NERDataset(real_test_only))
        real_pred_logits = real_pred.predictions
        real_eval_pred = (real_pred_logits, real_pred.label_ids)
        real_per_entity = compute_per_entity_metrics(real_eval_pred)

        for entity in entities:
            real_per_entity.get(f"tp_{entity}", 0) if "tp_" in str(real_per_entity) else 0
            real_per_entity.get(f"fp_{entity}", 0) if "fp_" in str(real_per_entity) else 0
            real_per_entity.get(f"fn_{entity}", 0) if "fn_" in str(real_per_entity) else 0

        real_per_entity.get("precision_MATERIAL", 0)
        real_per_entity.get("recall_MATERIAL", 0)
        micro_f1 = real_per_entity.get("f1_MATERIAL", 0)

        print(f"  Real test F1 (macro over entities): {micro_f1:.4f}")
        for entity in entities:
            f = real_per_entity.get(f"f1_{entity}", 0)
            print(f"    {entity:12s} F1: {f:.4f}")

    print("\n--- Saving model ---")
    model.save_pretrained(output_dir / "final_model")
    tokenizer.save_pretrained(output_dir / "tokenizer")

    metrics = {
        "test_f1": eval_results["eval_f1"],
        "test_precision": eval_results["eval_precision"],
        "test_recall": eval_results["eval_recall"],
        "test_loss": eval_results["eval_loss"],
        "per_entity_f1": {entity: per_entity.get(f"f1_{entity}", 0.0) for entity in entities},
        "training_samples": len(train_fmt),
        "validation_samples": len(val_fmt),
        "test_samples": len(test_fmt),
        "base_model": "allenai/scibert_scivocab_uncased",
        "epochs": 8,
        "learning_rate": 1e-5,
        "batch_size": 16,
        "source": "continued from checkpoint-56 on combined data",
    }
    with open(output_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("\n--- Saving results ---")
    results_dir = base_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "test_f1": eval_results["eval_f1"],
        "test_precision": eval_results["eval_precision"],
        "test_recall": eval_results["eval_recall"],
        "per_entity_f1": {entity: per_entity.get(f"f1_{entity}", 0.0) for entity in entities},
        "real_test_f1": micro_f1 if real_test_only else None,
        "real_per_entity_f1": {entity: real_per_entity.get(f"f1_{entity}", 0.0) for entity in entities} if real_test_only else {},
    }
    with open(results_dir / "final_model_eval.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved to {output_dir / 'metrics.json'}")
    print(f"Saved to {results_dir / 'final_model_eval.json'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
