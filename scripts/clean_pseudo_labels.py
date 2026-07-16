#!/usr/bin/env python3
"""Clean pseudo-labeled data by removing obvious false positives.

Reconstructs full entity spans before checking validity.
"""

import json
import re
from pathlib import Path

INPUT = Path("data/annotations/pseudo_labeled.json")
OUTPUT = Path("data/annotations/pseudo_labeled_clean.json")


def extract_entity_spans(tokens, tags):
    """Extract (start_idx, end_idx, text, type) for each entity."""
    entities = []
    i = 0
    while i < len(tags):
        if tags[i] == "O":
            i += 1
            continue

        etype = tags[i].split("-")[1]
        prefix = tags[i].split("-")[0]

        if prefix == "S":
            entities.append((i, i + 1, tokens[i], etype))
            i += 1
        elif prefix == "B":
            start = i
            i += 1
            while i < len(tags) and tags[i] != "O" and tags[i].split("-")[1] == etype:
                if tags[i].split("-")[0] in ("E", "S"):
                    i += 1
                    break
                i += 1
            ent_text = " ".join(tokens[start:i])
            entities.append((start, i, ent_text, etype))
        else:
            i += 1
    return entities


def is_date(text: str) -> bool:
    return bool(re.match(r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}", text))


def is_reference_number(text: str) -> bool:
    return bool(re.search(r"[A-Za-z/]", text)) and not text.startswith(("IS", "ASTM", "BS", "EN", "ACI"))


def is_valid_standard(text: str) -> bool:
    return bool(re.match(r"^(IS|ASTM|BS|EN|ACI|ISO)\s*[A-Z]?\d+", text, re.IGNORECASE))


def main():
    with open(INPUT) as f:
        docs = json.load(f)

    cleaned = []
    removed_counts = {"QUANTITY": 0, "STANDARD": 0}

    for doc in docs:
        tokens = doc["tokens"]
        tags = doc["ner_tags"]

        entities = extract_entity_spans(tokens, tags)

        # Mark all as O first
        new_tags = ["O"] * len(tags)

        for start, end, text, etype in entities:
            should_keep = True

            if etype == "QUANTITY" and (is_date(text) or is_reference_number(text)):
                should_keep = False
                removed_counts["QUANTITY"] += 1

            if etype == "STANDARD" and not is_valid_standard(text):
                should_keep = False
                removed_counts["STANDARD"] += 1

            if should_keep:
                if end - start == 1:
                    new_tags[start] = f"S-{etype}"
                else:
                    new_tags[start] = f"B-{etype}"
                    for j in range(start + 1, end - 1):
                        new_tags[j] = f"I-{etype}"
                    new_tags[end - 1] = f"E-{etype}"

        has_entities = any(t != "O" for t in new_tags)
        if has_entities:
            doc["ner_tags"] = new_tags
            cleaned.append(doc)

    with open(OUTPUT, "w") as f:
        json.dump(cleaned, f, indent=2)

    print(f"Cleaned: {len(cleaned)} docs (from {len(docs)})")
    print(f"Removed: {removed_counts}")

    entities = {}
    for doc in cleaned:
        for tag in doc["ner_tags"]:
            if tag != "O":
                etype = tag.split("-")[1]
                entities[etype] = entities.get(etype, 0) + 1
    print(f"Entities after cleaning: {entities}")


if __name__ == "__main__":
    main()
