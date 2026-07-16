#!/usr/bin/env python3
"""Train LoRA NER v5 on expanded corpus: gold + synthetic + pseudo-labeled.

Uses LoRA adapters (fast) on bert-base-cased with all available training data.

Usage:
    .venv-lora/bin/python scripts/train_lora_ner_v5.py
"""

import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GOLD_FILE = Path("data/real_rfqs/annotations/gold_annotations.json")
SYNTH_TRAIN = Path("data/annotations/train.json")
PSEUDO_FILE = Path("data/annotations/pseudo_labeled_clean.json")
BASE_MODEL = "bert-base-cased"
TOKENIZER_NAME = "bert-base-cased"
OUTPUT_DIR = Path("models/rfq2boq-ner-lora-v5")

from config.constants import ID2LABEL, LABEL2ID, NUM_LABELS  # noqa: E402  # constants import after Path() setup


def load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    return data


def normalize_doc(doc: dict, source: str) -> dict | None:
    """Normalize various doc formats to consistent tokens + ner_tags."""
    tokens = doc.get("tokens", [])
    tags = doc.get("ner_tags", doc.get("labels", doc.get("bioes_tags", [])))
    if not tokens or not tags:
        return None
    return {"tokens": tokens, "ner_tags": tags, "source": source}


def load_all_docs() -> list[dict]:
    docs = []

    # Gold annotations
    gold = load_json(GOLD_FILE)
    for doc in gold:
        d = normalize_doc(doc, "gold")
        if d:
            docs.append(d)
    logger.info("Gold docs: %d", len([d for d in docs if d["source"] == "gold"]))

    # Synthetic
    synth = load_json(SYNTH_TRAIN)
    for doc in synth:
        d = normalize_doc(doc, "synthetic")
        if d:
            docs.append(d)
    logger.info("Synthetic docs: %d", len([d for d in docs if d["source"] == "synthetic"]))

    # Pseudo-labeled
    pseudo = load_json(PSEUDO_FILE)
    for doc in pseudo:
        d = normalize_doc(doc, "pseudo")
        if d:
            docs.append(d)
    logger.info("Pseudo docs: %d", len([d for d in docs if d["source"] == "pseudo"]))

    logger.info("Total docs: %d", len(docs))
    return docs


def build_dataset(docs: list[dict], tokenizer):
    from datasets import Dataset

    all_input_ids = []
    all_attention_mask = []
    all_labels = []

    for doc in docs:
        tokens = doc["tokens"]
        ner_tags = doc["ner_tags"]
        if not tokens or not ner_tags:
            continue

        n = min(len(tokens), len(ner_tags))
        tokens = tokens[:n]
        ner_tags = ner_tags[:n]

        encoded = tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            max_length=256,
            return_tensors="pt",
        )

        input_ids = encoded["input_ids"][0].tolist()
        attention_mask = encoded["attention_mask"][0].tolist()
        word_ids = encoded.word_ids(batch_index=0)

        aligned_labels = []
        prev_word_idx = None
        for word_idx in word_ids:
            if word_idx is None:
                aligned_labels.append(-100)
            elif word_idx != prev_word_idx:
                aligned_labels.append(LABEL2ID.get(ner_tags[word_idx], LABEL2ID["O"]))
                prev_word_idx = word_idx
            else:
                aligned_labels.append(-100)

        all_input_ids.append(input_ids)
        all_attention_mask.append(attention_mask)
        all_labels.append(aligned_labels)

    ds = Dataset.from_dict(
        {
            "input_ids": all_input_ids,
            "attention_mask": all_attention_mask,
            "labels": all_labels,
        }
    )
    return ds


def compute_metrics(pred):
    import numpy as np

    predictions, labels = pred
    preds = np.argmax(predictions, axis=-1)

    true_entities = {"MATERIAL": 0, "QUANTITY": 0, "UNIT": 0, "STANDARD": 0, "GRADE": 0, "DIMENSION": 0}
    pred_entities = {"MATERIAL": 0, "QUANTITY": 0, "UNIT": 0, "STANDARD": 0, "GRADE": 0, "DIMENSION": 0}
    correct_entities = {"MATERIAL": 0, "QUANTITY": 0, "UNIT": 0, "STANDARD": 0, "GRADE": 0, "DIMENSION": 0}

    def extract_entities(label_ids):
        ents = set()
        current_type = None
        start = None
        for i, lid in enumerate(label_ids):
            tag = ID2LABEL.get(lid, "O")
            if tag.startswith("S-"):
                ents.add((tag[2:], i, i))
            elif tag.startswith("B-"):
                current_type = tag[2:]
                start = i
            elif tag.startswith("E-") and current_type == tag[2:]:
                ents.add((current_type, start, i))
                current_type = None
            elif tag == "O" or tag.startswith("B-") or tag.startswith("S-"):
                current_type = None
        return ents

    for pred_row, label_row in zip(preds, labels, strict=False):
        pred_filtered = [p for p, l in zip(pred_row, label_row, strict=False) if l != -100]
        label_filtered = [l for l in label_row if l != -100]
        pred_ents = extract_entities(pred_filtered)
        true_ents = extract_entities(label_filtered)
        for etype, _s, _e in true_ents:
            true_entities[etype] = true_entities.get(etype, 0) + 1
        for etype, _s, _e in pred_ents:
            pred_entities[etype] = pred_entities.get(etype, 0) + 1
        for etype, _s, _e in pred_ents & true_ents:
            correct_entities[etype] = correct_entities.get(etype, 0) + 1

    total_correct = sum(correct_entities.values())
    total_pred = sum(pred_entities.values())
    total_true = sum(true_entities.values())

    precision = total_correct / total_pred if total_pred > 0 else 0
    recall = total_correct / total_true if total_true > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    results = {"precision": precision, "recall": recall, "f1": f1}
    for etype in true_entities:
        tp = correct_entities.get(etype, 0)
        p = pred_entities.get(etype, 0)
        t = true_entities.get(etype, 0)
        e_p = tp / p if p > 0 else 0
        e_r = tp / t if t > 0 else 0
        e_f1 = 2 * e_p * e_r / (e_p + e_r) if (e_p + e_r) > 0 else 0
        results[f"{etype}_f1"] = e_f1

    return results


def main():
    docs = load_all_docs()
    if len(docs) < 10:
        logger.error("Need at least 10 docs. Found %d", len(docs))
        sys.exit(1)

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
    ds = build_dataset(docs, tokenizer)
    logger.info("Dataset: %d examples", len(ds))

    # 85/15 split (no separate test - we evaluate on sacred 10 later)
    split = ds.train_test_split(test_size=0.15, seed=42)
    train_ds = split["train"]
    val_ds = split["test"]
    logger.info("Train: %d, Val: %d", len(train_ds), len(val_ds))

    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import AutoModelForTokenClassification, Trainer, TrainingArguments

    device = "cpu"  # Use CPU to avoid MPS thermal throttling
    logger.info("Using device: %s", device)

    model = AutoModelForTokenClassification.from_pretrained(
        BASE_MODEL,
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True,
    )
    model.to(device)

    lora_config = LoraConfig(
        task_type=TaskType.TOKEN_CLS,
        r=32,
        lora_alpha=64,
        lora_dropout=0.05,
        bias="none",
        target_modules=["query", "value"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=20,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=16,
        gradient_accumulation_steps=2,
        learning_rate=1e-4,
        weight_decay=0.01,
        warmup_ratio=0.1,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        save_total_limit=2,
        fp16=False,
        dataloader_num_workers=0,
        report_to="none",
        logging_steps=10,
        seed=42,
    )

    from transformers import DataCollatorForTokenClassification

    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    logger.info("Starting LoRA training v5...")
    start = time.time()
    trainer.train()
    elapsed = time.time() - start
    logger.info("Training completed in %.1f min", elapsed / 60)

    model.save_pretrained(str(OUTPUT_DIR))
    logger.info("Adapter saved to %s", OUTPUT_DIR)

    # Final eval on val set
    val_results = trainer.evaluate(val_ds)
    logger.info("Val results: %s", {k: f"{v:.4f}" for k, v in val_results.items()})

    logger.info("Per-entity F1 on val set:")
    for k, v in val_results.items():
        if k.endswith("_f1"):
            logger.info("  %s: %.4f", k.replace("_f1", ""), v)

    adapter_size_mb = sum(f.stat().st_size for f in OUTPUT_DIR.rglob("*") if f.is_file()) / (1024 * 1024)
    logger.info("Adapter size: %.1f MB", adapter_size_mb)


if __name__ == "__main__":
    main()
