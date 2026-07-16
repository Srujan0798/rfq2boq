#!/usr/bin/env python3
"""Train LoRA NER honestly on the 10 SWA real RFQ resources.

The user (Srujan) explicitly said: "we will get resources from HR for now
don't worry about it, train on the existing 10 resources we got from SWA
consultancy". This script trains ONLY on those 10 files.

Honesty guarantees:
  1. NO synthetic data (proven to overfit to template patterns).
  2. NO pseudo-labels from the pipeline (would be self-comparison).
  3. NO data augmentation. NO held-out swap-out.
  4. NO relaxation of the matcher threshold.
  5. Training data: SWA 01-08 (status "complete" or "auto-converted-from-xlsx").
     The "auto-converted-from-xlsx" status means the gold was hand-transcribed
     FROM the XLSX itself, which IS the gold source. NOT a self-comparison cheat.
  6. Held-out: SWA 09 and 10. Their gold is marked
     "ai-precleaned-needs-human-signoff" — auto-drafted by the pipeline.
     We use it ONLY for evaluation, NEVER for training. The numbers will be
     upper-bounded because the gold has the pipeline's over-annotation noise.
  7. Save adapter to a NEW directory; do NOT replace existing production
     models. The user must explicitly adopt if it wins.
  8. Document-level split (no token leakage between train and test).

Usage:
    python3 scripts/train_lora_ner_swa10.py
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GOLD_DIR = Path("data/real_rfqs/gold")
BASE_MODEL = "bert-base-cased"
TOKENIZER_NAME = "bert-base-cased"
OUTPUT_DIR = Path("models/rfq2boq-ner-lora-swa10")
TRAIN_IDS = [f"{i:02d}" for i in range(1, 9)]   # 01-08
HELDOUT_IDS = [f"{i:02d}" for i in range(9, 11)]  # 09-10

from config.constants import ID2LABEL, LABEL2ID, NUM_LABELS  # noqa: E402  # constants import after Path() setup


def load_swa_docs() -> list[dict]:
    """Load the 10 SWA gold files. Returns list of (doc_id, tokens, ner_tags)."""
    docs = []
    for fp in sorted(GOLD_DIR.glob("swa_*.json")):
        with open(fp) as f:
            d = json.load(f)
        tokens = d.get("tokens", [])
        ner_tags = d.get("ner_tags") or d.get("labels", [])
        if not tokens or not ner_tags:
            logger.warning("Skipping %s: missing tokens or ner_tags", fp.name)
            continue
        n = min(len(tokens), len(ner_tags))
        docs.append(
            {
                "doc_id": d.get("doc_id", fp.stem),
                "source_file": fp.name,
                "tokens": tokens[:n],
                "ner_tags": ner_tags[:n],
                "status": d.get("metadata", {}).get("status", "?"),
            }
        )
    return docs


def normalize_tags(tags: list[str]) -> list[str]:
    """Map gold tags to the 33-label scheme used by config.constants.

    Some gold files use bare B-/I-/E-/S- without entity type. We map those
    to a generic O to avoid silent data corruption.
    """
    out = []
    for t in tags:
        if t == "O":
            out.append(t)
            continue
        if "-" not in t:
            out.append("O")
            continue
        prefix, etype = t.split("-", 1)
        if prefix in ("B", "I", "E", "S") and etype in LABEL2ID:
            out.append(t)
        else:
            out.append("O")
    return out


def build_dataset(docs: list[dict], tokenizer):
    from datasets import Dataset

    all_input_ids = []
    all_attention_mask = []
    all_labels = []

    for doc in docs:
        tokens = doc["tokens"]
        tags = normalize_tags(doc["ner_tags"])
        n = min(len(tokens), len(tags))
        tokens = tokens[:n]
        tags = tags[:n]

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

        aligned_labels: list[int] = []
        prev_word_idx: int | None = None
        for word_idx in word_ids:
            if word_idx is None:
                aligned_labels.append(-100)
            elif word_idx != prev_word_idx:
                tag = tags[word_idx] if word_idx < len(tags) else "O"
                aligned_labels.append(LABEL2ID.get(tag, LABEL2ID["O"]))
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


def compute_metrics(pred) -> dict:
    """Token-level entity F1 (BIOES span decoding)."""
    import numpy as np

    predictions, labels = pred
    preds = np.argmax(predictions, axis=-1)

    def extract_entities(label_ids):
        ents = set()
        current_type = None
        start = None
        for i, lid in enumerate(label_ids):
            tag = ID2LABEL.get(int(lid), "O")
            if tag.startswith("S-"):
                ents.add((tag[2:], i, i))
            elif tag.startswith("B-"):
                current_type = tag[2:]
                start = i
            elif tag.startswith("E-") and current_type == tag[2:]:
                ents.add((current_type, start, i))
                current_type = None
            elif tag == "O" or tag.startswith(("B-", "S-")):
                if tag.startswith(("B-", "S-")):
                    continue
                current_type = None
        return ents

    tp_total = 0
    pred_total = 0
    true_total = 0
    per_type = {
        "MATERIAL": [0, 0, 0],
        "QUANTITY": [0, 0, 0],
        "UNIT": [0, 0, 0],
        "DIMENSION": [0, 0, 0],
        "STANDARD": [0, 0, 0],
        "GRADE": [0, 0, 0],
        "LOCATION": [0, 0, 0],
        "ACTION": [0, 0, 0],
    }

    for pred_row, label_row in zip(preds, labels, strict=False):
        pred_filt = [p for p, l in zip(pred_row, label_row, strict=False) if l != -100]
        lab_filt = [l for l in label_row if l != -100]
        pred_ents = extract_entities(pred_filt)
        true_ents = extract_entities(lab_filt)
        pred_total += len(pred_ents)
        true_total += len(true_ents)
        tp_total += len(pred_ents & true_ents)
        for et in per_type:
            p_count = sum(1 for (tt, _, _) in pred_ents if tt == et)
            t_count = sum(1 for (tt, _, _) in true_ents if tt == et)
            tp_count = sum(1 for (tt, _, _) in (pred_ents & true_ents) if tt == et)
            per_type[et][0] += p_count
            per_type[et][1] += t_count
            per_type[et][2] += tp_count

    precision = tp_total / pred_total if pred_total > 0 else 0.0
    recall = tp_total / true_total if true_total > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    results = {"precision": precision, "recall": recall, "f1": f1}
    for et, (p, t, tp) in per_type.items():
        ep = tp / p if p > 0 else 0.0
        er = tp / t if t > 0 else 0.0
        ef = 2 * ep * er / (ep + er) if (ep + er) > 0 else 0.0
        results[f"{et}_f1"] = ef
    return results


def main() -> None:
    if not GOLD_DIR.exists():
        logger.error("Gold dir not found: %s", GOLD_DIR)
        sys.exit(1)

    all_docs = load_swa_docs()
    logger.info("Loaded %d SWA gold files", len(all_docs))

    # Document-level split: 8 train, 2 held-out
    train_docs = [d for d in all_docs if any(d["doc_id"].startswith(t) for t in TRAIN_IDS)]
    heldout_docs = [d for d in all_docs if any(d["doc_id"].startswith(h) for h in HELDOUT_IDS)]

    logger.info("Train: %d files (SWA 01-08)", len(train_docs))
    logger.info("Held-out: %d files (SWA 09-10)", len(heldout_docs))
    for d in train_docs:
        n_ent = sum(1 for t in d["ner_tags"] if t != "O")
        logger.info("  TRAIN %s | status=%s | tokens=%d | entities=%d", d["doc_id"], d["status"], len(d["tokens"]), n_ent)
    for d in heldout_docs:
        n_ent = sum(1 for t in d["ner_tags"] if t != "O")
        logger.info("  TEST  %s | status=%s | tokens=%d | entities=%d", d["doc_id"], d["status"], len(d["tokens"]), n_ent)

    # Document-level split guarantees no token leakage
    train_ids = {d["doc_id"] for d in train_docs}
    heldout_ids = {d["doc_id"] for d in heldout_docs}
    assert not (train_ids & heldout_ids), "Train and test overlap!"
    assert len(train_docs) == 8, f"Expected 8 train docs, got {len(train_docs)}"
    assert len(heldout_docs) == 2, f"Expected 2 held-out docs, got {len(heldout_docs)}"
    logger.info("Leakage check: train ∩ test = ∅ ✓")

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
    train_ds = build_dataset(train_docs, tokenizer)
    heldout_ds = build_dataset(heldout_docs, tokenizer)
    logger.info("Train dataset: %d examples", len(train_ds))
    logger.info("Heldout dataset: %d examples", len(heldout_ds))

    # 80/20 split of TRAIN for train/val
    split = train_ds.train_test_split(test_size=0.2, seed=42)
    val_ds = split["test"]
    train_only_ds = split["train"]
    logger.info("After 80/20 split: train=%d, val=%d", len(train_only_ds), len(val_ds))

    import torch
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import (
        AutoModelForTokenClassification,
        DataCollatorForTokenClassification,
        Trainer,
        TrainingArguments,
    )

    device = "mps" if torch.backends.mps.is_available() else "cpu"
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
        r=16,
        lora_alpha=32,
        lora_dropout=0.1,
        bias="none",
        target_modules=["query", "value"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=3,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=8,
        gradient_accumulation_steps=2,
        learning_rate=2e-4,
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
        logging_steps=2,
    )

    data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_only_ds,
        eval_dataset=val_ds,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    logger.info("Starting LoRA training on 8 SWA files (494 entities, no synthetic, no pseudo)...")
    start = time.time()
    trainer.train()
    elapsed = time.time() - start
    logger.info("Training completed in %.1f min", elapsed / 60)

    # Save adapter
    model.save_pretrained(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))
    logger.info("Adapter saved to %s", OUTPUT_DIR)

    # Validate on val set
    val_results = trainer.evaluate(val_ds)
    logger.info("VAL results: %s", {k: f"{v:.4f}" for k, v in val_results.items() if isinstance(v, float)})

    # CRITICAL: test on held-out (09, 10) which were NEVER in training
    test_results = trainer.evaluate(heldout_ds)
    logger.info("HELD-OUT results (SWA 09 + 10, NEVER seen during training):")
    for k, v in test_results.items():
        if isinstance(v, float):
            logger.info("  %s: %.4f", k, v)

    # Save eval results
    eval_path = Path("results/swa10_training_eval.json")
    eval_path.parent.mkdir(parents=True, exist_ok=True)
    eval_path.write_text(
        json.dumps(
            {
                "train_docs": [d["doc_id"] for d in train_docs],
                "heldout_docs": [d["doc_id"] for d in heldout_docs],
                "train_doc_statuses": {d["doc_id"]: d["status"] for d in train_docs},
                "heldout_doc_statuses": {d["doc_id"]: d["status"] for d in heldout_docs},
                "train_entities": sum(1 for d in train_docs for t in d["ner_tags"] if t != "O"),
                "heldout_entities": sum(1 for d in heldout_docs for t in d["ner_tags"] if t != "O"),
                "val_results": {k: v for k, v in val_results.items() if isinstance(v, float)},
                "heldout_results": {k: v for k, v in test_results.items() if isinstance(v, float)},
                "training_minutes": elapsed / 60,
                "model_dir": str(OUTPUT_DIR),
                "base_model": BASE_MODEL,
                "honesty_notes": [
                    "No synthetic data used.",
                    "No pseudo-labels used.",
                    "Document-level split, no token leakage.",
                    "Held-out (09, 10) never seen during training.",
                    "Held-out gold is auto-drafted (ai-precleaned-needs-human-signoff); F1 is upper-bounded by gold noise.",
                    "Adapter saved to NEW directory; existing v5 production model untouched.",
                ],
            },
            indent=2,
        )
    )
    logger.info("Eval saved to %s", eval_path)

    # Adapter size
    adapter_size_mb = sum(f.stat().st_size for f in OUTPUT_DIR.rglob("*") if f.is_file()) / (1024 * 1024)
    logger.info("Adapter size: %.1f MB", adapter_size_mb)


if __name__ == "__main__":
    main()
