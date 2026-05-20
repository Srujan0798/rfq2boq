#!/usr/bin/env python3
"""Auto-annotation pipeline: Convert synthetic RFQs to BIOES-tagged NER data.

Reads data/synthetic/*.json, converts entity spans to BIOES tags at token level,
generates train/val/test splits (70/15/15).
"""

import argparse
import json
import random
import re
from pathlib import Path
from typing import Any

random.seed(42)

ENTITY_LABELS = [
    "MATERIAL", "QUANTITY", "UNIT", "LOCATION",
    "DIMENSION", "STANDARD", "ACTION", "GRADE"
]

ACTION_WORDS = [
    "supply", "install", "lay", "cast", "plaster", "apply", "fix", "erect",
    "provide", "fabricate", "construct", "build", "deliver", "place", "pour"
]

MATERIAL_WORDS = [
    "concrete", "steel", "brick", "tile", "cement", "mortar", "plaster",
    "pipe", "sheet", "plate", "bar", "block", "paint", "putty", "sand",
    "aggregate", "glass", "wood", "PVC", "GI", "MS", "TMT", "AAC"
]

UNIT_WORDS = [
    "sqm", "cum", "rmt", "kg", "nos", "ls", "m", "mm", "ltr", "set",
    "cu.m", "sq.m", "R.m", "r.m.", "running meter", "square meter", "cubic meter"
]

GRADE_WORDS = ["M20", "M25", "M30", "M35", "M40", "Fe415", "Fe500", "Fe550", "Class A", "Class B", "Class 1", "Class 2"]

LOCATION_WORDS = [
    "ground floor", "first floor", "second floor", "roof", "basement", "bathroom",
    "kitchen", "balcony", "terrace", "exterior", "interior", "compound"
]

DIMENSION_WORDS = ["mm", "cm", "m", "thick", "diameter", "x", "×"]

STANDARD_PATTERNS = [
    r"IS\s*\d+",
    r"ASTM\s*[A-Z]\d+",
    r"BS\s*(EN\s*)?\d+",
    r"EN\s*\d+",
]


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[\w'/]+|[^\s]", text)
    return tokens


def find_entity_spans(text: str) -> list[tuple[int, int, str]]:
    spans = []
    text_lower = text.lower()

    for action in ACTION_WORDS:
        pattern = rf"\b{action}\b"
        for m in re.finditer(pattern, text_lower):
            spans.append((m.start(), m.end(), "ACTION"))

    for material in MATERIAL_WORDS:
        pattern = rf"\b{material}\b"
        for m in re.finditer(pattern, text_lower):
            spans.append((m.start(), m.end(), "MATERIAL"))

    for unit in UNIT_WORDS:
        pattern = rf"\b{re.escape(unit)}\b"
        for m in re.finditer(pattern, text_lower):
            spans.append((m.start(), m.end(), "UNIT"))

    for grade in GRADE_WORDS:
        pattern = rf"\b{re.escape(grade)}\b"
        for m in re.finditer(pattern, text_lower):
            spans.append((m.start(), m.end(), "GRADE"))

    for loc in LOCATION_WORDS:
        pattern = rf"\b{re.escape(loc)}\b"
        for m in re.finditer(pattern, text_lower):
            spans.append((m.start(), m.end(), "LOCATION"))

    for dim in DIMENSION_WORDS:
        pattern = rf"\b{re.escape(dim)}\b"
        for m in re.finditer(pattern, text_lower):
            spans.append((m.start(), m.end(), "DIMENSION"))

    for pattern in STANDARD_PATTERNS:
        for m in re.finditer(pattern, text):
            spans.append((m.start(), m.end(), "STANDARD"))

    number_pattern = r"\b\d+(?:\.\d+)?\b"
    for m in re.finditer(number_pattern, text):
        spans.append((m.start(), m.end(), "QUANTITY"))

    spans.sort(key=lambda x: x[0])
    return spans


def resolve_overlaps(spans: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    if not spans:
        return []

    resolved = [spans[0]]
    for current in spans[1:]:
        prev = resolved[-1]
        if current[0] < prev[1]:
            if current[2] == prev[2]:
                resolved[-1] = (prev[0], current[1], prev[2])
            else:
                if current[1] > prev[1]:
                    resolved.append((prev[1], current[1], current[2]))
        else:
            resolved.append(current)

    return resolved


def spans_to_bioes(spans: list[tuple[int, int, str]], text: str) -> list[str]:
    tags = ["O"] * len(text)

    for start, end, label in spans:
        length = end - start
        if length <= 0:
            continue

        if start >= len(text) or end > len(text):
            continue

        if length == 1:
            tags[start] = f"S-{label}"
        else:
            tags[start] = f"B-{label}"
            for i in range(start + 1, end - 1):
                tags[i] = f"I-{label}"
            tags[end - 1] = f"E-{label}"

    return tags


def align_tokens_with_tags(tokens: list[str], char_tags: list[str], text: str) -> list[str]:
    token_tags = []
    char_to_token = [None] * len(text)

    token_start = 0
    for tok_i, token in enumerate(tokens):
        for c_i in range(token_start, len(text)):
            if c_i < len(char_to_token) and char_to_token[c_i] is None:
                char_to_token[c_i] = tok_i
            if text[c_i : c_i + len(token)] == token:
                token_start = c_i + len(token)
                break

    for token_idx, _token in enumerate(tokens):
        tags_in_token = []
        for char_idx, tok_assign in enumerate(char_to_token):
            if tok_assign == token_idx and char_idx < len(char_tags):
                tag = char_tags[char_idx]
                if tag != "O":
                    tags_in_token.append(tag)

        if tags_in_token:
            first_tag = tags_in_token[0]
            if first_tag.startswith("S-"):
                token_tags.append(first_tag)
            elif first_tag.startswith("B-"):
                all_same = all(t.startswith("I-") or t.startswith("E-") or t == first_tag for t in tags_in_token)
                if all_same:
                    token_tags.append(first_tag)
                else:
                    token_tags.append("O")
            else:
                token_tags.append("O")
        else:
            token_tags.append("O")

    return token_tags


def convert_doc_to_ner_format(doc: dict[str, Any]) -> dict[str, Any]:
    text = doc.get("text_for_ner", doc.get("text", ""))
    tokens = tokenize(text)
    char_spans = find_entity_spans(text)
    resolved_spans = resolve_overlaps(char_spans)
    char_tags = spans_to_bioes(resolved_spans, text)
    token_tags = align_tokens_with_tags(tokens, char_tags, text)

    return {
        "tokens": tokens,
        "labels": token_tags,
        "ner_tags": token_tags,
        "doc_id": doc.get("id", ""),
    }


def main():
    parser = argparse.ArgumentParser(description="Annotate synthetic RFQ data for NER")
    parser.add_argument("--input-dir", type=str, default="data/synthetic")
    parser.add_argument("--output-dir", type=str, default="data/annotations")
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = list(input_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return 1

    print(f"Loading {len(json_files)} synthetic documents...")
    all_data = []
    for f in json_files:
        with open(f, encoding="utf-8") as fp:
            doc = json.load(fp)
            ner_doc = convert_doc_to_ner_format(doc)
            all_data.append(ner_doc)

    random.shuffle(all_data)

    n = len(all_data)
    n_train = int(n * args.train_ratio)
    n_val = int(n * args.val_ratio)

    train_data = all_data[:n_train]
    val_data = all_data[n_train:n_train + n_val]
    test_data = all_data[n_train + n_val:]

    splits = {
        "train.json": train_data,
        "val.json": val_data,
        "test.json": test_data,
    }

    for filename, data in splits.items():
        out_path = output_dir / filename
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        print(f"  Wrote {len(data)} examples to {out_path}")

    print("\nAnnotation complete:")
    print(f"  Train: {len(train_data)}")
    print(f"  Val:   {len(val_data)}")
    print(f"  Test:  {len(test_data)}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
