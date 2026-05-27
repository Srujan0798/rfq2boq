#!/usr/bin/env python3
"""Validate annotation quality — BIOES consistency, entity distribution."""

import json
import sys
from collections import defaultdict
from pathlib import Path


def load_annotations(path):
    with open(path) as f:
        return json.load(f)


def validate_bioes(tags, tokens, sample_id):
    """Check BIOES tag consistency.

    Rules:
    - B-X must be followed by I-X, E-X, or itself (same type continue)
    - S-X is standalone (no I/E follow)
    - I-X must follow B-X or I-X of same type
    - E-X must follow B-X or I-X of same type
    - O can be anywhere
    """
    errors = []
    i = 0
    while i < len(tags):
        tag = tags[i]
        if tag == 'O':
            i += 1
            continue

        if tag.startswith('S-'):
            i += 1
            continue

        if tag.startswith('B-'):
            ent_type = tag[2:]
            j = i + 1
            # Check next tags
            while j < len(tags) and tags[j] == f'I-{ent_type}':
                j += 1
            if j < len(tags):
                next_tag = tags[j]
                if next_tag == f'B-{ent_type}':
                    pass  # new entity starting
                elif next_tag.startswith('B-') or next_tag == 'O' or next_tag.startswith('S-'):
                    pass  # valid end
                elif next_tag.startswith('E-') and next_tag != f'E-{ent_type}':
                    errors.append(f"Sample {sample_id}: E tag type mismatch at pos {j}")
            i += 1
        elif tag.startswith('I-') or tag.startswith('E-'):
            errors.append(f"Sample {sample_id}: I/E tag at pos {i} without preceding B-")
            i += 1
        else:
            errors.append(f"Sample {sample_id}: Unknown tag format at pos {i}: {tag}")
            i += 1

    return errors


def count_entity_types(data):
    counts = defaultdict(lambda: {'train': 0, 'val': 0, 'test': 0})

    for item in data:
        for tag in item['ner_tags']:
            if tag == 'O':
                continue
            if tag.startswith('B-') or tag.startswith('S-'):
                ent_type = tag[2:]
                counts[ent_type]['train'] += 1

    return counts


def main():
    base = Path('data/annotations')

    train = load_annotations(base / 'train.json')
    val = load_annotations(base / 'val.json')
    test = load_annotations(base / 'test.json')

    print("=== ANNOTATION QUALITY REPORT ===\n")
    print(f"Train: {len(train)} samples")
    print(f"Val:   {len(val)} samples")
    print(f"Test:  {len(test)} samples\n")

    # BIOES validation
    print("--- BIOES Consistency ---")
    all_errors = []
    for name, data in [('train', train), ('val', val), ('test', test)]:
        for idx, item in enumerate(data):
            errs = validate_bioes(item['ner_tags'], item['tokens'], f"{name}_{idx}")
            all_errors.extend(errs)

    if all_errors:
        print(f"ERRORS FOUND: {len(all_errors)}")
        for err in all_errors[:10]:
            print(f"  {err}")
        if len(all_errors) > 10:
            print(f"  ... and {len(all_errors) - 10} more")
    else:
        print("All BIOES tags valid")

    # Entity distribution
    print("\n--- Entity Distribution ---")
    entity_types = ['MATERIAL', 'QUANTITY', 'UNIT', 'LOCATION', 'DIMENSION', 'STANDARD', 'ACTION', 'GRADE']

    dataset_counts = {}
    for name, data in [('train', train), ('val', val), ('test', test)]:
        counts = defaultdict(int)
        for item in data:
            for tag in item['ner_tags']:
                if tag == 'O':
                    continue
                if tag.startswith('B-') or tag.startswith('S-'):
                    counts[tag[2:]] += 1
        dataset_counts[name] = counts

    header = f"{'Entity':<10} {'Train':>6} {'Val':>6} {'Test':>6} {'Total':>6}"
    print(header)
    print("-" * len(header))

    for et in entity_types:
        t = sum(dataset_counts[name].get(et, 0) for name in ['train', 'val', 'test'])
        print(f"{et:<10} {dataset_counts['train'].get(et, 0):>6} {dataset_counts['val'].get(et, 0):>6} {dataset_counts['test'].get(et, 0):>6} {t:>6}")

    total_all = sum(sum(dataset_counts[n].values()) for n in ['train', 'val', 'test'])
    print("-" * len(header))
    print(f"{'TOTAL':<10} {sum(dataset_counts['train'].values()):>6} {sum(dataset_counts['val'].values()):>6} {sum(dataset_counts['test'].values()):>6} {total_all:>6}")

    # Tag format check
    print("\n--- Tag Format Check ---")
    all_tags = set()
    for _name, data in [('train', train), ('val', val), ('test', test)]:
        for item in data:
            all_tags.update(item['ner_tags'])

    valid_prefixes = ['B-', 'I-', 'E-', 'S-', 'O']
    bad_tags = [t for t in all_tags if not any(t.startswith(p) for p in valid_prefixes)]
    if bad_tags:
        print(f"Invalid tag formats found: {bad_tags}")
    else:
        print("All tags use valid BIOES format")

    # Token-tag alignment
    print("\n--- Token-Tag Alignment ---")
    misaligned = 0
    for name, data in [('train', train), ('val', val), ('test', test)]:
        for idx, item in enumerate(data):
            if len(item['tokens']) != len(item['ner_tags']):
                misaligned += 1
                if misaligned <= 3:
                    print(f"  {name}_{idx}: {len(item['tokens'])} tokens vs {len(item['ner_tags'])} tags")

    if misaligned == 0:
        print("All tokens aligned with tags")
    else:
        print(f"Misaligned samples: {misaligned}")

    print("\n=== END REPORT ===")
    return 0 if not all_errors else 1


if __name__ == "__main__":
    sys.exit(main())
