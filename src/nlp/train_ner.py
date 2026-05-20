"""BERT NER training script for construction entity extraction."""

import json
import random
from pathlib import Path

import numpy as np
import torch
from seqeval.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForTokenClassification,
    AutoTokenizer,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
)

LABEL_LIST = [
    "O",
    "S-MATERIAL", "B-MATERIAL", "I-MATERIAL", "E-MATERIAL",
    "S-QUANTITY", "B-QUANTITY", "I-QUANTITY", "E-QUANTITY",
    "S-UNIT", "B-UNIT", "I-UNIT", "E-UNIT",
    "S-LOCATION", "B-LOCATION", "I-LOCATION", "E-LOCATION",
    "S-DIMENSION", "B-DIMENSION", "I-DIMENSION", "E-DIMENSION",
    "S-STANDARD", "B-STANDARD", "I-STANDARD", "E-STANDARD",
    "S-ACTION", "B-ACTION", "I-ACTION", "E-ACTION",
    "S-GRADE", "B-GRADE", "I-GRADE", "E-GRADE",
]
LABEL2ID = {label: i for i, label in enumerate(LABEL_LIST)}
ID2LABEL = {i: label for label, i in LABEL2ID.items()}
NUM_LABELS = len(LABEL_LIST)


def load_annotations(path: str | Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["annotations"]


def convert_to_train_format(example: dict) -> dict:
    tokens = example["tokens"]
    tags = example["bioes_tags"]
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
        texts = [f.get("tokens", f.get("sentence", "").split()) for f in features]
        if not texts or not texts[0]:
            texts = [["EMPTY"] for _ in features]
        tokenized = self.tokenizer(
            texts,
            is_split_into_words=True,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        )

        labels = []
        for batch_idx, feature in enumerate(features):
            tag_ids = []
            feature_labels = feature.get("labels", feature.get("bioes_tags", []))
            input_ids = tokenized["input_ids"][batch_idx]
            self.tokenizer.convert_ids_to_tokens(input_ids)

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

    return {
        "precision": precision_score(true_labels, true_predictions),
        "recall": recall_score(true_labels, true_predictions),
        "f1": f1_score(true_labels, true_predictions),
    }


def compute_per_entity_metrics(eval_pred):
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=2)

    entity_results = {entity: {"tp": 0, "fp": 0, "fn": 0} for entity in [
        "MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"
    ]}

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
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using device: {device}")

    annotations_path = Path("/Users/srujansai/Desktop/rfq2boq/data/nerAnnotations.json")
    output_dir = Path("/Users/srujansai/Desktop/rfq2boq/models/ner_model")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading annotations...")
    annotations = load_annotations(annotations_path)
    print(f"Loaded {len(annotations)} sentences")

    random.seed(42)
    train_data, val_data = train_test_split(annotations, test_size=0.2, random_state=42)

    train_formatted = [convert_to_train_format(ex) for ex in train_data]
    val_formatted = [convert_to_train_format(ex) for ex in val_data]

    print(f"Train samples: {len(train_formatted)}, Val samples: {len(val_formatted)}")

    model_name = "bert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model = AutoModelForTokenClassification.from_pretrained(
        model_name,
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    model.to(device)

    data_collator = NERDataCollator(tokenizer, LABEL2ID)

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
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=NERDataset(train_formatted),
        eval_dataset=NERDataset(val_formatted),
        data_collator=data_collator,
        compute_metrics=compute_metrics_seqeval,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )

    print("\nStarting training...")
    trainer.train()

    print("\nEvaluating on validation set...")
    eval_results = trainer.evaluate()

    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print(f"Validation Loss: {eval_results['eval_loss']:.4f}")
    print(f"Precision: {eval_results['eval_precision']:.4f}")
    print(f"Recall: {eval_results['eval_recall']:.4f}")
    print(f"F1 Score: {eval_results['eval_f1']:.4f}")

    predictions = trainer.predict(val_formatted)
    pred_logits = predictions.predictions
    np.argmax(pred_logits, axis=2)

    eval_pred = (pred_logits, predictions.label_ids)
    per_entity = compute_per_entity_metrics(eval_pred)

    print("\n" + "-"*60)
    print("PER-ENTITY F1 SCORES")
    print("-"*60)
    entities = ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]
    for entity in entities:
        p = per_entity.get(f"precision_{entity}", 0)
        r = per_entity.get(f"recall_{entity}", 0)
        f = per_entity.get(f"f1_{entity}", 0)
        print(f"{entity:12s}  P: {p:.4f}  R: {r:.4f}  F1: {f:.4f}")

    model.save_pretrained(output_dir / "final_model")
    tokenizer.save_pretrained(output_dir / "tokenizer")
    print(f"\nModel saved to {output_dir / 'final_model'}")

    print("\n" + "-"*60)
    print("SAMPLE PREDICTIONS ON VALIDATION DATA")
    print("-"*60)
    for i in range(min(5, len(val_formatted))):
        example = val_formatted[i]
        inputs = tokenizer(
            example["tokens"],
            is_split_into_words=True,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128,
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)

        pred_ids = torch.argmax(outputs.logits, dim=-1)[0].cpu().tolist()
        word_ids = inputs.word_ids()

        predicted_tags = []
        last_word_id = None
        for token_idx, word_id in enumerate(word_ids):
            if word_id is None:
                continue
            if word_id != last_word_id:
                pred_tag = ID2LABEL.get(pred_ids[token_idx], "O")
                predicted_tags.append(pred_tag)
            last_word_id = word_id

        print(f"\nSentence: {' '.join(example['tokens'])}")
        print(f"Predicted: {predicted_tags}")
        print(f"True:      {example['labels']}")


if __name__ == "__main__":
    main()
