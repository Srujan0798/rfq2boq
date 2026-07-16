#!/usr/bin/env python3
"""Evaluate v5 model on the 10 SWA sacred held-out files.

Usage:
    .venv-lora/bin/python scripts/eval_v5_on_swa.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.constants import ID2LABEL, LABEL2ID, NUM_LABELS

MODEL_DIR = Path("models/rfq2boq-ner-lora-v5")
GOLD_DIR = Path("data/real_rfqs/gold")


def load_gold_files() -> list[dict]:
    docs = []
    for f in sorted(GOLD_DIR.glob("swa_*.json")):
        with open(f) as fh:
            doc = json.load(fh)
        docs.append(doc)
    return docs


def evaluate():
    import torch
    from peft import PeftModel
    from transformers import AutoModelForTokenClassification, AutoTokenizer

    if not MODEL_DIR.exists():
        print(f"Model not found: {MODEL_DIR}")
        sys.exit(1)

    device = "cpu"
    tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")
    base_model = AutoModelForTokenClassification.from_pretrained(
        "bert-base-cased",
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    model = PeftModel.from_pretrained(base_model, str(MODEL_DIR))
    model.to(device)
    model.eval()

    docs = load_gold_files()
    print(f"Evaluating on {len(docs)} SWA gold files...")

    all_preds, all_labels = [], []

    for doc in docs:
        tokens = doc.get("tokens", [])
        true_tags = doc.get("ner_tags", doc.get("labels", []))
        if not tokens or not true_tags:
            continue

        n = min(len(tokens), len(true_tags))
        tokens = tokens[:n]
        true_tags = true_tags[:n]

        encoded = tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        input_ids = encoded["input_ids"].to(device)
        attention_mask = encoded["attention_mask"].to(device)
        word_ids = encoded.word_ids(batch_index=0)

        with torch.no_grad():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            preds = outputs.logits.argmax(-1).cpu().numpy()[0]

        pred_tags = []
        true_aligned = []
        prev_word_idx = None
        for i, word_idx in enumerate(word_ids):
            if word_idx is None:
                continue
            if word_idx != prev_word_idx:
                pred_tags.append(ID2LABEL.get(preds[i], "O"))
                true_aligned.append(true_tags[word_idx])
                prev_word_idx = word_idx

        all_preds.append(pred_tags)
        all_labels.append(true_aligned)

    from seqeval.metrics import classification_report, f1_score, precision_score, recall_score

    print("\n" + "=" * 60)
    print("V5 Model — SWA Sacred 10 Evaluation")
    print("=" * 60)
    print(classification_report(all_labels, all_preds, digits=4))

    f1 = f1_score(all_labels, all_preds)
    p = precision_score(all_labels, all_preds)
    r = recall_score(all_labels, all_preds)
    print(f"\nOverall: P={p:.4f} R={r:.4f} F1={f1:.4f}")


if __name__ == "__main__":
    evaluate()
