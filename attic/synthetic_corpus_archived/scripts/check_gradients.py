#!/usr/bin/env python3
"""Minimal gradient-check script to verify training works."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json

import torch
from config.constants import ID2LABEL, LABEL2ID, NUM_LABELS
from scripts.finetune_final_model import (
    NERDataCollator,
    NERDataset,
    convert_to_train_format,
    load_synthetic_annotations,
)
from transformers import AutoModelForTokenClassification, AutoTokenizer

DEVICE = torch.device("mps")

def check_gradients():
    print("=" * 60)
    print("STEP 1: Load data")
    print("=" * 60)

    syn_train = load_synthetic_annotations(Path("data/annotations/train.json"))
    syn_val = load_synthetic_annotations(Path("data/annotations/val.json"))
    syn_test = load_synthetic_annotations(Path("data/annotations/test.json"))

    real_dir = Path("data/real_rfqs/annotated")
    real_files = list(real_dir.glob("*.json"))
    real_data = []
    for rf in real_files:
        with open(rf) as f:
            real_data.extend([json.load(f)])

    syn_train_fmt = [convert_to_train_format(ex, "synthetic") for ex in syn_train]
    syn_val_fmt = [convert_to_train_format(ex, "synthetic") for ex in syn_val]
    syn_test_fmt = [convert_to_train_format(ex, "synthetic") for ex in syn_test]
    real_fmt = [convert_to_train_format(ex, "real") for ex in real_data]

    combined_train = syn_train_fmt + real_fmt
    print(f"Train: {len(combined_train)}, Val: {len(syn_val_fmt)}, Test: {len(syn_test_fmt)}")

    print("\n" + "=" * 60)
    print("STEP 2: Verify label coverage")
    print("=" * 60)

    all_labels = set()
    for ex in combined_train:
        for lbl in ex["labels"]:
            all_labels.add(lbl)
    print(f"Unique labels in train: {len(all_labels)}")
    missing = [l for l in all_labels if l not in LABEL2ID]
    print(f"Missing from LABEL2ID: {missing if missing else 'none'}")

    print("\n" + "=" * 60)
    print("STEP 3: Gradient check on single batch")
    print("=" * 60)

    tokenizer = AutoTokenizer.from_pretrained("bert-base-cased")
    model = AutoModelForTokenClassification.from_pretrained(
        "bert-base-cased",
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    model.to(DEVICE)

    data_collator = NERDataCollator(tokenizer, LABEL2ID)
    dataset = NERDataset(combined_train)

    batch = [dataset[0]]
    collated = data_collator(batch)
    collated = {k: v.to(DEVICE) for k, v in collated.items()}

    logits = model(**{k: v for k, v in collated.items() if k != "labels"}).logits
    labels = collated["labels"]

    loss = torch.nn.functional.cross_entropy(
        logits.view(-1, NUM_LABELS),
        labels.view(-1),
        reduction="mean",
        ignore_index=-100,
    )

    print(f"Loss: {loss.item():.4f}")
    print(f"Logit shape: {logits.shape}")
    print(f"Labels shape: {labels.shape}")

    model.zero_grad()
    loss.backward()

    classifier_grad_norm = 0.0
    for name, param in model.named_parameters():
        if param.grad is not None:
            grad_norm = param.grad.norm().item()
            if "classifier" in name and "weight" in name:
                classifier_grad_norm = grad_norm

    print(f"Classifier weight grad norm: {classifier_grad_norm:.6f}")
    if classifier_grad_norm < 1e-8:
        print("WARNING: Classifier has near-zero gradients!")
        return False

    print("\n" + "=" * 60)
    print("STEP 4: Quick training loop (3 steps, 5 batches each)")
    print("=" * 60)

    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-5, weight_decay=0.01)

    model.train()
    step = 0
    for _epoch in range(1, 2):
        for batch_idx in range(5):
            batch = dataset[batch_idx * 2 : batch_idx * 2 + 2]
            collated = data_collator(batch)
            collated = {k: v.to(DEVICE) for k, v in collated.items()}

            logits = model(**{k: v for k, v in collated.items() if k != "labels"}).logits
            labels = collated["labels"]

            loss = torch.nn.functional.cross_entropy(
                logits.view(-1, NUM_LABELS),
                labels.view(-1),
                reduction="mean",
                ignore_index=-100,
            )

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            step += 1
            print(f"  Step {step}: loss={loss.item():.4f}, grad_norm={classifier_grad_norm:.6f}")

            if step >= 3:
                break
        if step >= 3:
            break

    print("\n" + "=" * 60)
    print("STEP 5: Evaluate on test set")
    print("=" * 60)

    model.eval()
    all_preds = []
    all_labels = []
    LABEL2ID["O"]

    with torch.no_grad():
        for i in range(min(5, len(syn_test_fmt))):
            ex = syn_test_fmt[i]
            tokens = ex["tokens"]
            labels_raw = ex["labels"]

            encoded = tokenizer(
                tokens,
                is_split_into_words=True,
                padding=True,
                truncation=True,
                max_length=256,
                return_tensors="pt",
            )
            encoded = {k: v.to(DEVICE) for k, v in encoded.items()}
            logits = model(**encoded).logits[0]
            preds = torch.argmax(logits, dim=1)

            word_ids = encoded.word_ids()
            for pos, wid in enumerate(word_ids):
                if wid is None:
                    continue
                pred = ID2LABEL[preds[pos].item()]
                actual = labels_raw[wid] if wid < len(labels_raw) else "O"
                all_preds.append(pred)
                all_labels.append(actual)

    non_o_preds = sum(1 for p in all_preds if p != "O")
    non_o_actual = sum(1 for a in all_labels if a != "O")
    print(f"Tokens evaluated: {len(all_preds)}")
    print(f"Non-O predictions: {non_o_preds}, Non-O actual: {non_o_actual}")

    if non_o_preds == 0 and non_o_actual > 0:
        print("WARNING: Model predicts all-O despite non-O labels in data!")
        return False

    print("Gradient check PASSED")
    return True


if __name__ == "__main__":
    ok = check_gradients()
    sys.exit(0 if ok else 1)
