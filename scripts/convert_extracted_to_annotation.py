#!/usr/bin/env python3
"""Convert extracted JSON to gold annotations for real PDFs."""
import json
from pathlib import Path

ANNOTATED = Path("data/real_rfqs/annotated")
EXTRACTED = Path("data/real_rfqs/extracted")

def char_to_token_span(text, tokens):
    token_spans = []
    char_pos = 0
    for tok in tokens:
        idx = text.find(tok, char_pos)
        if idx == -1:
            idx = char_pos
        token_spans.append((idx, idx + len(tok)))
        char_pos = idx + len(tok)
    return token_spans

for json_file in ANNOTATED.glob("*.json"):
    extracted_name = json_file.stem + ".pdf.json"
    extracted_path = EXTRACTED / extracted_name

    # Try without .pdf suffix
    if not extracted_path.exists():
        # Check if there's a matching extracted file
        for en in EXTRACTED.glob(f"{json_file.stem}*.json"):
            extracted_path = en
            break

    if not extracted_path.exists():
        print(f"No extracted for {json_file.name}")
        continue

    with open(json_file) as f:
        ann = json.load(f)

    with open(extracted_path) as f:
        ext = json.load(f)

    text = " ".join(ann["tokens"])
    tokens = ann["tokens"]
    spans = char_to_token_span(text, tokens)

    entities = ext.get("entities", [])
    ner_tags = ["O"] * len(tokens)

    for ent in entities:
        ent_text = ent.get("text", "")
        ent_type = ent.get("type", "")
        start = ent.get("start", 0)
        end = ent.get("end", start + len(ent_text))
        conf = ent.get("confidence", 0)

        if conf < 0.65:
            continue

        matched = []
        for i, (ts, te) in enumerate(spans):
            if te > start and ts < end:
                matched.append(i)

        if not matched:
            continue

        if len(matched) == 1:
            ner_tags[matched[0]] = f"S-{ent_type}"
        else:
            for j, idx in enumerate(matched):
                if j == 0:
                    ner_tags[idx] = f"B-{ent_type}"
                elif j == len(matched) - 1:
                    ner_tags[idx] = f"E-{ent_type}"
                else:
                    ner_tags[idx] = f"I-{ent_type}"

    ann["ner_tags"] = ner_tags
    ann["labels"] = ner_tags

    non_o = sum(1 for t in ner_tags if t != "O")

    with open(json_file, "w") as f:
        json.dump(ann, f, indent=2)

    print(f"{json_file.name}: {len(tokens)} tokens, {non_o} entities tagged")
