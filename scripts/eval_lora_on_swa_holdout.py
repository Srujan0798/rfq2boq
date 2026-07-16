#!/usr/bin/env python3
"""Evaluate NER model on the 10 SWA held-out set.

Usage:
    .venv-lora/bin/python scripts/eval_lora_on_swa_holdout.py --model models/rfq2boq-ner-final/final_model [--use-lora] [--lora-path models/rfq2boq-ner-lora-v1]

Writes:
    results/lora_eval_on_swa10.json  (or prod_eval_on_swa10.json)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch
from seqeval.metrics import f1_score as seqeval_f1
from seqeval.metrics import precision_score as seqeval_p
from seqeval.metrics import recall_score as seqeval_r
from transformers import AutoModelForTokenClassification, AutoTokenizer

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from config.constants import ID2LABEL, LABEL2ID  # noqa: E402

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
GOLD_DIR = ROOT / "data/real_rfqs/gold"
SWA_HOLDOUT = GOLD_DIR  # we filter to swa_*.json only


def load_swa_holdout() -> list[dict]:
    """Load the 10 SWA gold files as the held-out set."""
    items: list[dict] = []
    for f in sorted(SWA_HOLDOUT.glob("swa_*.json")):
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        if not d.get("tokens") or not d.get("ner_tags"):
            continue
        items.append(
            {
                "tokens": d["tokens"],
                "labels": d["ner_tags"],
                "source_file": f.name,
                "doc_id": d.get("doc_id", f.stem),
            }
        )
    return items


def tokenize_for_eval(items: list[dict], tokenizer):
    """Tokenize pre-split word lists; return (encodings, word_ids, gold_token_labels)."""
    encodings = tokenizer(
        [it["tokens"] for it in items],
        is_split_into_words=True,
        truncation=True,
        max_length=512,
        padding=True,
        return_tensors="pt",
    )
    word_ids_batch = [encodings.word_ids(batch_index=i) for i in range(len(items))]
    labels_batch: list[list[int]] = []
    for i, it in enumerate(items):
        word_ids = word_ids_batch[i]
        gold = it["labels"]
        prev = None
        out: list[int] = []
        for w in word_ids:
            if w is None:
                out.append(-100)
            elif w != prev:
                out.append(LABEL2ID.get(gold[w], LABEL2ID["O"]) if w < len(gold) else -100)
                prev = w
            else:
                out.append(-100)
        labels_batch.append(out)
    return encodings, word_ids_batch, labels_batch


def predict(model, encodings, labels_batch) -> tuple[list[list[int]], list[list[int]]]:
    model.eval()
    with torch.no_grad():
        logits = model(
            input_ids=encodings["input_ids"].to(DEVICE),
            attention_mask=encodings["attention_mask"].to(DEVICE),
        ).logits
    preds = logits.argmax(dim=-1).cpu().numpy()
    pred_seqs: list[list[int]] = []
    gold_seqs: list[list[int]] = []
    for i in range(preds.shape[0]):
        p_row, l_row = preds[i].tolist(), labels_batch[i]
        pp, ll = [], []
        for p, l in zip(p_row, l_row, strict=False):
            if l != -100:
                pp.append(ID2LABEL[p])
                ll.append(ID2LABEL[l])
        pred_seqs.append(pp)
        gold_seqs.append(ll)
    return pred_seqs, gold_seqs


def per_entity_counts(pred_seqs, gold_seqs) -> dict:
    """Per-entity P/R/F1 (seqeval classification report for span-level)."""
    from seqeval.metrics import classification_report

    report: dict = classification_report(gold_seqs, pred_seqs, zero_division=0, output_dict=True)
    types = ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]
    out: dict = {}
    for t in types:
        m = report.get(t, {"precision": 0.0, "recall": 0.0, "f1-score": 0.0, "support": 0})
        out[t] = {
            "tp": int(round(m["precision"] * m["support"])) if m["support"] else 0,
            "support": int(m["support"]),
            "precision": m["precision"],
            "recall": m["recall"],
            "f1": m["f1-score"],
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Base model path")
    parser.add_argument("--tokenizer", default="bert-base-cased", help="Tokenizer to use")
    parser.add_argument("--use-lora", action="store_true", help="Load LoRA adapter on top of base model")
    parser.add_argument("--lora-path", default="models/rfq2boq-ner-lora-v1", help="LoRA adapter dir")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    items = load_swa_holdout()
    print(f"Held-out set: {len(items)} SWA files")
    for it in items:
        print(
            f"  {it['source_file']}: {len(it['tokens'])} tokens, {sum(1 for t in it['labels'] if t != 'O')} entity tags"
        )

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    encodings, word_ids, labels_batch = tokenize_for_eval(items, tokenizer)

    # Build base model with the 33-label head (configs differ from BASE_MODEL)
    model = AutoModelForTokenClassification.from_pretrained(
        args.model,
        num_labels=len(LABEL2ID),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True,
    )
    model.to(DEVICE)

    if args.use_lora:
        from peft import PeftModel

        if not Path(args.lora_path).exists():
            print(f"ERROR: LoRA adapter not found at {args.lora_path}")
            return 1
        model = PeftModel.from_pretrained(model, args.lora_path)
        print(f"Loaded LoRA adapter from {args.lora_path}")
    else:
        print(f"Loaded base model (no LoRA) from {args.model}")

    pred_seqs, gold_seqs = predict(model, encodings, labels_batch)

    # seqeval (industry standard, strict mode)
    micro_p = seqeval_p(gold_seqs, pred_seqs, zero_division=0)
    micro_r = seqeval_r(gold_seqs, pred_seqs, zero_division=0)
    micro_f1 = seqeval_f1(gold_seqs, pred_seqs, zero_division=0)

    per_ent = per_entity_counts(pred_seqs, gold_seqs)

    print(f"\n=== SWA held-out ({len(items)} files, {sum(len(it['tokens']) for it in items)} tokens) ===")
    print(f"seqeval micro F1:  {micro_f1:.4f}")
    print(f"seqeval precision: {micro_p:.4f}")
    print(f"seqeval recall:    {micro_r:.4f}")
    print("\nPer-entity F1 (seqeval span-level):")
    for t, m in per_ent.items():
        tp = m.get("tp", 0)
        sup = m.get("support", 0)
        print(f"  {t:12s}  support={sup:5d}  P={m['precision']:.3f}  R={m['recall']:.3f}  F1={m['f1']:.3f}  (TP~{tp})")

    out = {
        "model": str(args.model),
        "use_lora": args.use_lora,
        "lora_path": str(args.lora_path) if args.use_lora else None,
        "test_files": [it["source_file"] for it in items],
        "test_items": len(items),
        "total_tokens": sum(len(it["tokens"]) for it in items),
        "seqeval_micro_precision": float(micro_p),
        "seqeval_micro_recall": float(micro_r),
        "seqeval_micro_f1": float(micro_f1),
        "per_entity": {
            t: {k: (v if not isinstance(v, float) else round(v, 4)) for k, v in m.items()} for t, m in per_ent.items()
        },
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
