#!/usr/bin/env python3
"""Evaluate NER model on a frozen test set and compare to production."""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import torch
from seqeval.metrics import f1_score, precision_score, recall_score
from transformers import AutoModelForTokenClassification, AutoTokenizer

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.constants import ID2LABEL

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")


def load_gold_files(gold_dir: Path, exclude_draft: bool = True) -> list[dict]:
    """Load gold files, optionally excluding draft files."""
    files = sorted(gold_dir.glob("*.json"))
    result = []

    EXCLUDE = set()
    if exclude_draft:
        EXCLUDE = {
            "cpwd_Guidelines_for_Hassle_Free_Bid_Submission_1778959268.json",
            "epi_addendum_1709810880.json",
            "epi_emrs_ap_nit235.json",
            "epi_vol3_price_bid.json",
            "delhi_pwd_Tender.json",
            "ireps_2724bb1eff78.json",
            "ireps_bc341034058b.json",
        }

    for f in files:
        if f.name in EXCLUDE:
            continue
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            data = [data]
        for item in data:
            item["_source_file"] = f.name
        result.extend(data)
    return result


def has_valid_tags(item: dict) -> bool:
    tags = item.get("ner_tags", item.get("labels", []))
    return any(t != "O" for t in tags)


def convert_to_train_format(item: dict) -> dict:
    tokens = item.get("tokens", [])
    tags = item.get("ner_tags", item.get("labels", []))
    if len(tags) != len(tokens):
        min_len = min(len(tags), len(tokens))
        tokens = tokens[:min_len]
        tags = tags[:min_len]
    return {"tokens": tokens, "labels": tags, "_source": item.get("_source_file", "unknown")}


def tokenize_and_align_labels(features, tokenizer, label2id):
    texts = [f.get("tokens", []) for f in features]
    if not texts or not all(texts):
        texts = [["EMPTY"] for _ in features]

    tokenized = tokenizer(
        texts,
        is_split_into_words=True,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt",
    )

    word_ids_list = [tokenized.word_ids(batch_index=i) for i in range(len(features))]

    labels_batch = []
    for batch_idx2, feature in enumerate(features):
        tag_ids = []
        feature_labels = feature.get("labels", [])
        word_ids = word_ids_list[batch_idx2]
        word_to_token = {}
        for token_idx, word_id in enumerate(word_ids):
            if word_id is not None and word_id not in word_to_token:
                word_to_token[word_id] = token_idx

        for token_idx, word_id in enumerate(word_ids):
            if word_id is None:
                tag_ids.append(-100)
            elif word_id in word_to_token and word_id < len(feature_labels):
                if token_idx == word_to_token[word_id]:
                    tag_ids.append(label2id.get(feature_labels[word_id], 0))
                else:
                    tag_ids.append(-100)
            else:
                tag_ids.append(-100)
        labels_batch.append(tag_ids)

    return tokenized, word_ids_list, labels_batch


def evaluate_model(model, tokenizer, dataset, label2id):
    """Run seqeval evaluation."""
    model.eval()
    loader = torch.utils.data.DataLoader(dataset, batch_size=4, shuffle=False, collate_fn=lambda x: x)

    all_preds, all_labels = [], []
    for features in loader:
        tokenized, _, labels_batch = tokenize_and_align_labels(features, tokenizer, label2id)
        tokenized = {k: v.to(DEVICE) for k, v in tokenized.items() if k not in ["token_type_ids"]}

        with torch.no_grad():
            logits = model(**tokenized).logits
        preds = logits.argmax(dim=-1).cpu().numpy()

        for i in range(preds.shape[0]):
            all_preds.append(preds[i])
            all_labels.append(labels_batch[i])

    true_predictions, true_labels = [], []
    for pred_seq, label_seq in zip(all_preds, all_labels, strict=False):
        temp_pred, temp_label = [], []
        for p, l in zip(pred_seq, label_seq, strict=False):
            if l != -100:
                temp_pred.append(ID2LABEL[p])
                temp_label.append(ID2LABEL[l])
        if temp_pred:
            true_predictions.append(temp_pred)
            true_labels.append(temp_label)

    if not true_predictions:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    return {
        "precision": precision_score(true_labels, true_predictions),
        "recall": recall_score(true_labels, true_predictions),
        "f1": f1_score(true_labels, true_predictions),
    }


def per_entity_f1(model, tokenizer, test_items, label2id):
    """Compute per-entity F1 on test set — simple batch loop."""
    all_doc_preds = [None] * len(test_items)
    all_doc_labels = [None] * len(test_items)

    model.eval()
    batch_size = 4

    for batch_start in range(0, len(test_items), batch_size):
        batch_items = test_items[batch_start : batch_start + batch_size]
        tokenized, _, labels_batch = tokenize_and_align_labels(batch_items, tokenizer, label2id)
        tokenized = {k: v.to(DEVICE) for k, v in tokenized.items() if k not in ["token_type_ids"]}

        with torch.no_grad():
            logits = model(**tokenized).logits
        preds = logits.argmax(dim=-1).cpu().numpy()

        for i in range(preds.shape[0]):
            idx = batch_start + i
            all_doc_preds[idx] = preds[i]
            all_doc_labels[idx] = labels_batch[i]

    entity_f1s = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    for doc_idx, feature in enumerate(test_items):
        labels = feature.get("labels", [])
        doc_pred = all_doc_preds[doc_idx]
        doc_labels = all_doc_labels[doc_idx]
        seq_len = min(len(labels), len(doc_labels))

        for ent_type in ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]:
            for prefix in ["B-", "S-"]:
                tag = prefix + ent_type
                tag_id = label2id.get(tag, -1)
                in_pred = in_label = False
                for i in range(seq_len):
                    if doc_labels[i] >= 0:
                        if doc_pred[i] == tag_id:
                            in_pred = True
                        if doc_labels[i] == label2id.get(tag, -1):
                            in_label = True
                if in_pred and in_label:
                    entity_f1s[ent_type]["tp"] += 1
                elif in_pred and not in_label:
                    entity_f1s[ent_type]["fp"] += 1
                elif not in_pred and in_label:
                    entity_f1s[ent_type]["fn"] += 1

    per_entity = {}
    for ent_type, counts in entity_f1s.items():
        tp, fp, fn = counts["tp"], counts["fp"], counts["fn"]
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        per_entity[ent_type] = {"precision": prec, "recall": rec, "f1": f1}
    return per_entity


def main():
    parser = argparse.ArgumentParser(description="Evaluate NER model on frozen test set")
    parser.add_argument("--model", type=str, required=True, help="Path to model directory")
    parser.add_argument("--base-model", type=str, default="bert-base-cased", help="Base model name")
    parser.add_argument(
        "--test-files", type=str, default=None, help="JSON file with list of test file names (frozen IDs)"
    )
    parser.add_argument("--output", type=str, default=None, help="Output JSON path")
    parser.add_argument("--exclude-draft", action="store_true", default=True, help="Exclude draft gold files")
    args = parser.parse_args()

    gold_dir = Path("data/real_rfqs/gold")

    # Determine test files
    if args.test_files:
        with open(args.test_files) as f:
            test_file_ids = set(json.load(f))
        print(f"Using provided frozen test files ({len(test_file_ids)}): {sorted(test_file_ids)}")
    else:
        # Load all gold and create document-level split
        gold_items = load_gold_files(gold_dir, exclude_draft=args.exclude_draft)
        with_tags = [item for item in gold_items if has_valid_tags(item)]

        # Use last 20% as test
        import random

        random.seed(42)
        random.shuffle(with_tags)
        n = len(with_tags)
        test_items_full = with_tags[int(n * 0.8) :]
        test_file_ids = set(item.get("_source_file", "unknown") for item in test_items_full)
        print(f"Auto-split test files ({len(test_file_ids)}): {sorted(test_file_ids)}")

    # Load and prepare test set
    gold_items = load_gold_files(gold_dir, exclude_draft=args.exclude_draft)
    test_items = [
        convert_to_train_format(item)
        for item in gold_items
        if has_valid_tags(item) and item.get("_source_file") in test_file_ids
    ]
    print(f"Test set: {len(test_items)} items from {len(test_file_ids)} files")

    if not test_items:
        print("ERROR: No test items found!")
        return 1

    # Load model — handle non-standard id2label in production model config
    print(f"\nLoading model from {args.model}...")
    model_path = Path(args.model)
    config_path = model_path / "config.json"
    with open(config_path) as f:
        cfg = json.load(f)

    # Rebuild id2label with integer keys from config
    id2label_cfg = {int(k): v for k, v in cfg.get("id2label", {}).items()}
    label2id_cfg = {v: k for k, v in id2label_cfg.items()}

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    model = AutoModelForTokenClassification.from_pretrained(
        model_path,
        num_labels=len(id2label_cfg),
        id2label=id2label_cfg,
        label2id=label2id_cfg,
    )
    model.to(DEVICE)
    model.eval()

    # Evaluate
    print("\nEvaluating...")
    label2id = label2id_cfg
    test_result = evaluate_model(model, tokenizer, test_items, label2id)
    per_entity = per_entity_f1(model, tokenizer, test_items, label2id)

    print("\n=== Results on frozen test set ===")
    print(f"Micro F1: {test_result['f1']:.4f}")
    print(f"Precision: {test_result['precision']:.4f}")
    print(f"Recall: {test_result['recall']:.4f}")
    print("\nPer-entity F1:")
    for ent, m in sorted(per_entity.items()):
        print(f"  {ent:12s}  P={m['precision']:.3f}  R={m['recall']:.3f}  F1={m['f1']:.3f}")

    output = {
        "model": str(args.model),
        "test_files": sorted(list(test_file_ids)),
        "test_items": len(test_items),
        "micro_f1": test_result["f1"],
        "micro_precision": test_result["precision"],
        "micro_recall": test_result["recall"],
        "per_entity": per_entity,
    }

    if args.output:
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nSaved to {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
