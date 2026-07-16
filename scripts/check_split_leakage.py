#!/usr/bin/env python3
"""Check for split leakage in the gold corpus."""

import json
import random
from collections import defaultdict
from pathlib import Path


def load_gold_files(gold_dir: Path) -> list[dict]:
    files = sorted(gold_dir.glob("*.json"))
    result = []
    EXCLUDE = {
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


def main():
    gold_dir = Path("data/real_rfqs/gold")
    gold_items = load_gold_files(gold_dir)
    with_tags = [item for item in gold_items if has_valid_tags(item)]

    # Document-level split (same as v3 train script)
    by_file = defaultdict(list)
    for item in with_tags:
        by_file[item.get("_source_file", "unknown")].append(item)

    files = sorted(by_file.keys())
    random.seed(42)
    random.shuffle(files)

    n = len(files)
    t = max(1, int(n * 0.70))
    v = max(1, int(n * 0.15))

    train_files = set(files[:t])
    val_files = set(files[t : t + v])
    test_files = set(files[t + v :])

    print("Document-level split:")
    print(f"  Train: {len(train_files)} files")
    print(f"  Val:   {len(val_files)} files")
    print(f"  Test:  {len(test_files)} files")

    print("\nTrain files:")
    for f in sorted(train_files):
        print(f"  {f}")

    print("\nVal files:")
    for f in sorted(val_files):
        print(f"  {f}")

    print("\nTest files (FROZEN):")
    for f in sorted(test_files):
        print(f"  {f}")

    # Check no overlap
    assert train_files.isdisjoint(val_files), "LEAKAGE: train ∩ val"
    assert train_files.isdisjoint(test_files), "LEAKAGE: train ∩ test"
    assert val_files.isdisjoint(test_files), "LEAKAGE: val ∩ test"
    print("\n✓ No overlap detected — split is clean")

    # Save frozen test IDs for eval scripts
    frozen_path = Path("results/frozen_test_files.json")
    with open(frozen_path, "w") as f:
        json.dump(sorted(list(test_files)), f, indent=2)
    print(f"\nSaved frozen test IDs to {frozen_path}")


if __name__ == "__main__":
    main()
