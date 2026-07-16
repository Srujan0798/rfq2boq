#!/usr/bin/env python3
"""Train LoRA NER on REAL + HUMAN-VERIFIED data only.

Per ETERNAL_PROTOCOL.md / tasks/sonnet/T6:
- Machine-labeled data (silver from gazetteer, pseudo-labels) NEVER trains this model.
  There is no opt-in flag for it — a prior incident (2026-07-02/03) saw an agent set
  such a flag and train on circular labels. The only way in is human sign-off via
  review_annotation.py + convert_to_bioes.py, landing in data/annotations/verified/.
- Training input = gold (human) + verified/ ONLY.
- Sacred SWA 10 never enter TRAIN/VAL here.

Uses seqeval for honest validation metrics aligned with sacred-10 evaluation.

Usage:
    .venv-lora/bin/python scripts/train_lora_ner_real_only.py
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
BASE_MODEL = "bert-base-cased"
TOKENIZER_NAME = "bert-base-cased"
OUTPUT_DIR = Path("models/rfq2boq-ner-lora-real")

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


def load_real_docs() -> list[dict]:
    docs = []

    # Gold annotations (human verified real tenders)
    gold = load_json(GOLD_FILE)
    for doc in gold:
        d = normalize_doc(doc, "gold")
        if d:
            docs.append(d)
    logger.info("Gold docs: %d", len([d for d in docs if d["source"] == "gold"]))

    # Human-verified from review_annotation.py (explicit owner sign-off only).
    # These live in data/annotations/verified/*.json after review + convert.
    verified_dir = Path("data/annotations/verified")
    verified_count = 0
    if verified_dir.exists():
        for p in sorted(verified_dir.glob("*.json")):
            try:
                with open(p) as f:
                    v = json.load(f)
                d = normalize_doc(v, "verified")
                if d:
                    docs.append(d)
                    verified_count += 1
            except Exception:
                pass
    logger.info("Verified (human sign-off) docs: %d", verified_count)
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
            max_length=512,
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
    """Use seqeval for honest entity-level metrics aligned with sacred-10 eval."""
    import numpy as np
    from seqeval.metrics import f1_score, precision_score, recall_score

    predictions, labels = pred
    preds = np.argmax(predictions, axis=-1)

    # Convert id sequences to label strings, ignoring -100 padding
    pred_labels = []
    true_labels = []
    for pred_row, label_row in zip(preds, labels, strict=False):
        pred_seq = []
        true_seq = []
        for p, l in zip(pred_row, label_row, strict=False):
            if l == -100:
                continue
            true_seq.append(ID2LABEL.get(l, "O"))
            pred_seq.append(ID2LABEL.get(p, "O"))
        if true_seq:
            true_labels.append(true_seq)
            pred_labels.append(pred_seq)

    if not true_labels:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    precision = precision_score(true_labels, pred_labels)
    recall = recall_score(true_labels, pred_labels)
    f1 = f1_score(true_labels, pred_labels)

    return {"precision": precision, "recall": recall, "f1": f1}


def main():
    docs = load_real_docs()
    if len(docs) < 10:
        logger.error("Need at least 10 docs. Found %d", len(docs))
        sys.exit(1)

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
    ds = build_dataset(docs, tokenizer)
    logger.info("Dataset: %d examples", len(ds))

    # 85/15 split (sacred 10 is the real held-out test)
    split = ds.train_test_split(test_size=0.15, seed=42)
    train_ds = split["train"]
    val_ds = split["test"]
    logger.info("Train: %d, Val: %d", len(train_ds), len(val_ds))

    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import AutoModelForTokenClassification, Trainer, TrainingArguments

    device = "cpu"
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
        lora_dropout=0.1,  # Increased dropout for tiny dataset
        bias="none",
        target_modules=["query", "value"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=15,  # Reduced from 20; tiny dataset overfits fast
        per_device_train_batch_size=4,
        per_device_eval_batch_size=8,
        gradient_accumulation_steps=2,
        learning_rate=5e-5,  # Lower LR for stability
        weight_decay=0.05,
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
        logging_steps=5,
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

    logger.info("Starting LoRA training (REAL data only)...")
    start = time.time()
    trainer.train()
    elapsed = time.time() - start
    logger.info("Training completed in %.1f min", elapsed / 60)

    model.save_pretrained(str(OUTPUT_DIR))
    logger.info("Adapter saved to %s", OUTPUT_DIR)

    # Final eval on val set
    val_results = trainer.evaluate(val_ds)
    logger.info("Val results: %s", {k: f"{v:.4f}" for k, v in val_results.items()})

    adapter_size_mb = sum(f.stat().st_size for f in OUTPUT_DIR.rglob("*") if f.is_file()) / (1024 * 1024)
    logger.info("Adapter size: %.1f MB", adapter_size_mb)


if __name__ == "__main__":
    main()
