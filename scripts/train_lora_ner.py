"""Train LoRA few-shot NER adapter on gold annotations.

Usage:
    python scripts/train_lora_ner.py

Requires: pip install peft datasets
"""

import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GOLD_DIR = Path("data/real_rfqs/annotations")
GOLD_COMBINED = GOLD_DIR / "gold_annotations.json"
BASE_MODEL = "bert-base-cased"  # Train from HF hub base (clean slate)
TOKENIZER_NAME = "bert-base-cased"
OUTPUT_DIR = Path("models/rfq2boq-ner-lora-v3")  # New version trained on real gold

# Full 33-label BIOES scheme from config.constants
BIOES_LABELS = ["O"] + [
    f"{prefix}-{label}"
    for label in ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]
    for prefix in ["B", "I", "E", "S"]
]
LABEL2ID = {label: i for i, label in enumerate(BIOES_LABELS)}
ID2LABEL = {i: label for label, i in LABEL2ID.items()}
NUM_LABELS = len(BIOES_LABELS)


def load_gold(path: Path) -> list[dict]:
    """Load gold annotations from combined file + individual annotation files."""
    docs = []

    # Load combined gold annotations if exists
    if GOLD_COMBINED.exists():
        with GOLD_COMBINED.open() as f:
            docs.extend(json.load(f))
        logger.info("Loaded %d docs from combined gold", len(docs))

    # Load individual annotation files
    for ann_file in GOLD_DIR.glob("*.json"):
        if ann_file.name == "gold_annotations.json":
            continue  # Already loaded
        if ann_file.name == "manifest.csv":
            continue
        if ann_file.name == "real_rfq_samples.json":
            continue
        if ann_file.name == "gold_annotation_template.json":
            continue
        try:
            with ann_file.open() as f:
                doc = json.load(f)
                if isinstance(doc, list):
                    docs.extend(doc)
                else:
                    docs.append(doc)
        except (json.JSONDecodeError, KeyError):
            continue

    logger.info("Total docs loaded: %d", len(docs))

    # Phase 0 audit: gold data must NEVER contain the 10 SWA held-out files.
    # This is an architectural guarantee, not a runtime filter.
    # Audit command: python3 -c "import json; d=json.load(open('data/real_rfqs/annotations/gold_annotations.json')); print([x.get('source_file','') for x in d])"
    filtered = []
    for doc in docs:
        # Skip synthetic docs only (not real gold docs)
        doc_id = doc.get("doc_id", "")
        if doc_id.startswith("syn_"):
            continue
        filtered.append(doc)

    logger.info("After filtering (no synthetic): %d docs", len(filtered))
    return filtered


def encode_labels(tags: list[str]) -> list[int]:
    """Map gold BIOES tags to full 33-label scheme."""
    return [LABEL2ID.get(t, LABEL2ID["O"]) for t in tags]


def build_dataset(docs: list[dict], tokenizer):
    """Tokenize gold docs and align BIOES labels at token level.

    Uses word_ids() to map subwords to original word indices. First subword of
    each word gets the word's label; continuation subwords get -100 (ignored
    by the loss). Special tokens also get -100.
    """
    from datasets import Dataset

    all_input_ids = []
    all_attention_mask = []
    all_labels = []

    for doc in docs:
        tokens = doc.get("tokens", [])
        ner_tags = doc.get("ner_tags", [])
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

        aligned_labels: list[int] = []
        prev_word_idx: int | None = None
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


def compute_metrics(pred) -> dict:
    """Compute per-entity F1, precision, recall."""
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
        # Mask out -100 positions (subword continuations + special tokens)
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


def main() -> None:
    if not GOLD_DIR.exists():
        logger.error("Gold annotations directory not found: %s", GOLD_DIR)
        sys.exit(1)

    docs = load_gold(GOLD_DIR)
    logger.info("Loaded %d gold documents", len(docs))

    if len(docs) < 5:
        logger.error("Need at least 5 gold documents for training. Found %d", len(docs))
        logger.error("Run: python3 scripts/annotate_rfq.py <file> to create annotations")
        sys.exit(1)

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
    ds = build_dataset(docs, tokenizer)
    logger.info("Dataset: %d examples", len(ds))

    # Split 80/10/10
    split1 = ds.train_test_split(test_size=0.2, seed=42)
    test_val = split1["test"].train_test_split(test_size=0.5, seed=42)
    train_ds = split1["train"]
    val_ds = test_val["train"]
    test_ds = test_val["test"]
    logger.info("Train: %d, Val: %d, Test: %d", len(train_ds), len(val_ds), len(test_ds))

    import torch
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import AutoModelForTokenClassification, Trainer, TrainingArguments

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
        num_train_epochs=10,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=8,
        gradient_accumulation_steps=4,
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
        logging_steps=10,
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

    logger.info("Starting LoRA training...")
    start = time.time()
    trainer.train()
    elapsed = time.time() - start
    logger.info("Training completed in %.1f min", elapsed / 60)

    # Save adapter
    model.save_pretrained(str(OUTPUT_DIR))
    logger.info("Adapter saved to %s", OUTPUT_DIR)

    # Final eval on test set
    test_results = trainer.evaluate(test_ds)
    logger.info("Test results: %s", {k: f"{v:.4f}" for k, v in test_results.items()})

    # Report per-entity F1
    logger.info("Per-entity F1 on test set:")
    for k, v in test_results.items():
        if k.endswith("_f1"):
            logger.info("  %s: %.4f", k.replace("_f1", ""), v)

    # Check adapter size
    adapter_size_mb = sum(f.stat().st_size for f in OUTPUT_DIR.rglob("*") if f.is_file()) / (1024 * 1024)
    logger.info("Adapter size: %.1f MB", adapter_size_mb)


if __name__ == "__main__":
    main()
