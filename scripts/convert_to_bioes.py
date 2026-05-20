#!/usr/bin/env python3
"""Convert various annotation formats to BIOES token-level format for NER training."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def text_to_tokens(text: str) -> list[str]:
    """Simple whitespace tokenizer."""
    return text.split()


def spans_to_bioes(tokens: list[str], entities: list[dict], text: str) -> list[str]:
    """Convert character-offset spans to BIOES token tags."""
    tags = ["O"] * len(tokens)

    token_start_chars = []
    token_end_chars = []
    pos = 0
    for tok in tokens:
        start = text.find(tok, pos)
        end = start + len(tok)
        token_start_chars.append(start)
        token_end_chars.append(end)
        pos = end

    for ent in entities:
        ent.get("text", "")
        ent_type = ent.get("label", ent.get("type", ""))
        start = ent.get("start", -1)
        end = ent.get("end", -1)

        if start < 0 or end < 0:
            continue

        start_token = -1
        end_token = -1
        for i, (ts, te) in enumerate(zip(token_start_chars, token_end_chars, strict=False)):
            if ts == start:
                start_token = i
            if te == end:
                end_token = i
                break

        if start_token == -1 or end_token == -1:
            continue

        length = end_token - start_token + 1
        if length == 1:
            tags[start_token] = f"S-{ent_type}"
        else:
            tags[start_token] = f"B-{ent_type}"
            for j in range(start_token + 1, end_token):
                tags[j] = f"I-{ent_type}"
            tags[end_token] = f"E-{ent_type}"

    return tags


def convert_golden():
    """Convert golden_30.json to BIOES format."""
    with open("data/gold/golden_30.json") as f:
        data = json.load(f)

    examples = []
    for item in data:
        text = item["input_text"]
        tokens = text_to_tokens(text)
        entities = item.get("expected_entities", [])
        tags = spans_to_bioes(tokens, entities, text)
        examples.append({"tokens": tokens, "ner_tags": tags})

    return examples


def convert_real_rfq():
    """Convert real_rfq_samples.json - already in BIOES format."""
    with open("data/real_rfqs/annotations/real_rfq_samples.json") as f:
        data = json.load(f)

    examples = []
    for item in data:
        tokens = item["tokens"]
        tags = item["ner_tags"]
        if len(tokens) == len(tags):
            examples.append({"tokens": tokens, "ner_tags": tags})

    return examples


def convert_synthetic(idx: int, data: dict) -> list[dict]:
    """Convert one synthetic sample to BIOES format."""
    text = data.get("text_for_ner", data.get("text", ""))
    tokens = text_to_tokens(text)

    boq = data.get("metadata", {}).get("boq_ground_truth", [])
    entities = []
    for item in boq:
        action = item.get("action", "")
        material = item.get("material", "")
        grade = item.get("grade", "")
        dimension = item.get("dimension", "")
        quantity = item.get("quantity", "")
        unit = item.get("unit", "")
        standard_list = item.get("standard", [])

        pos = 0
        for field_val, field_type in [
            (action, "ACTION"),
            (material, "MATERIAL"),
            (grade, "GRADE"),
            (dimension, "DIMENSION"),
            (quantity, "QUANTITY"),
            (unit, "UNIT"),
        ]:
            if field_val:
                found = text.find(str(field_val), pos)
                if found >= 0:
                    entities.append({
                        "text": str(field_val),
                        "label": field_type,
                        "start": found,
                        "end": found + len(str(field_val)),
                    })
                    pos = found + len(str(field_val))

        for std in standard_list:
            if std:
                found = text.find(str(std), pos)
                if found >= 0:
                    entities.append({
                        "text": str(std),
                        "label": "STANDARD",
                        "start": found,
                        "end": found + len(str(std)),
                    })

    tags = spans_to_bioes(tokens, entities, text)
    return [{"tokens": tokens, "ner_tags": tags}]


def main():
    print("Converting golden_30.json...")
    golden = convert_golden()
    print(f"  Converted {len(golden)} golden examples")

    print("Converting real_rfq_samples.json...")
    real = convert_real_rfq()
    print(f"  Converted {len(real)} real RFQ examples")

    print("Converting synthetic samples...")
    synth_count = 0
    synth_dir = Path("data/synthetic")
    synth_examples = []
    for json_file in sorted(synth_dir.glob("syn_*.json"))[:300]:
        try:
            with open(json_file) as f:
                data = json.load(f)
            exs = convert_synthetic(synth_count, data)
            synth_examples.extend(exs)
            synth_count += 1
        except Exception as e:
            print(f"  Skipping {json_file.name}: {e}")
    print(f"  Converted {synth_count} synthetic samples ({len(synth_examples)} examples)")

    all_examples = golden + real + synth_examples
    print(f"\nTotal examples: {len(all_examples)}")

    split_idx = int(len(all_examples) * 0.8)
    train = all_examples[:split_idx]
    val = all_examples[split_idx:]

    print(f"Train: {len(train)}, Val: {len(val)}")

    with open("data/interim/train_ner.json", "w") as f:
        json.dump(train, f)
    with open("data/interim/val_ner.json", "w") as f:
        json.dump(val, f)

    print("Saved data/interim/train_ner.json and data/interim/val_ner.json")


if __name__ == "__main__":
    sys.exit(main())
