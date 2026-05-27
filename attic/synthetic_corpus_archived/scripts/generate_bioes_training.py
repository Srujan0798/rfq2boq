#!/usr/bin/env python3
"""Convert synthetic RFQ documents to BIOES training format for NER.

Reads synthetic JSON documents from data/synthetic/ and produces
training-ready BIOES format with:
- Token-level BIOES tags aligned to source text
- Material, quantity, unit, location, dimension, standard, action, grade entities
"""

import json
import random
import re
from pathlib import Path
from typing import Any

random.seed(42)

MATERIALS_DATA = {
    "concrete": ["M20 concrete", "M25 concrete", "M30 concrete", "M35 concrete", "PCC", "RCC"],
    "steel": ["TMT steel", "MS plate", "structural steel", "GI sheet", "rebar"],
    "brickwork": ["brick masonry", "AAC block", "fly ash brick", "hollow block"],
    "finishes": ["cement plaster", "POP", "tile", "paint", "putty"],
    "piping": ["GI pipe", "PVC pipe", "HDPE pipe", "CI pipe", "SWR pipe"],
    "doors_windows": ["flush door", "aluminum window", "MS door", "glass"],
    "waterproofing": ["brickbat coba", "membrane", "integral waterproofing", "DPC"],
    "electrical": ["cable", "GI conduit", "switch", "light fixture", "DB"],
}

GRADES = {
    "concrete": ["M20", "M25", "M30", "M35", "M40"],
    "steel": ["Fe415", "Fe500", "Fe550"],
    "brickwork": ["Class A", "Class B", "Class C"],
    "finishes": ["Class 1", "Class 2"],
}

DIMENSIONS = [
    "100mm thick", "150mm thick", "200mm thick", "230mm thick", "300mm thick",
    "12mm thick", "16mm thick", "20mm thick", "25mm thick",
    "100 x 100mm", "150 x 150mm", "200 x 200mm",
    "6mm diameter", "8mm diameter", "10mm diameter", "12mm diameter", "16mm diameter",
]

UNITS = ["cum", "sqm", "rmt", "kg", "nos", "ls", "ltr", "set"]

ACTIONS = [
    "Supply and install", "Supply and lay", "Supply and fix",
    "Provide and install", "Provide and lay", "Provide and fix",
    "Erect", "Fabricate and erect", "Lay", "Cast", "Plaster",
    "Apply", "Fix", "Install", "Supply"
]

LOCATIONS = [
    "ground floor", "first floor", "second floor", "roof level",
    "basement", "exterior walls", "interior walls", "balcony",
    "bathroom", "kitchen", "terrace", "compound wall",
]

STANDARDS = {
    "concrete": ["IS 456", "IS 383", "IS 269"],
    "steel": ["IS 2062", "IS 1786", "IS 1139"],
    "brickwork": ["IS 1077", "IS 2185", "IS 12894"],
    "finishes": ["IS 1661", "IS 101", "IS 15622"],
    "piping": ["IS 1239", "IS 4985", "IS 4984"],
    "waterproofing": ["IS 3144", "IS 1322", "IS 1582"],
    "electrical": ["IS 694", "IS 9537", "IS 3043"],
}

ENTITY_PATTERNS = {
    "MATERIAL": [
        r"M20 concrete", r"M25 concrete", r"M30 concrete", r"M35 concrete",
        r"PCC", r"RCC", r"TMT steel", r"MS plate", r"structural steel",
        r"GI sheet", r"rebar", r"brick masonry", r"AAC block",
        r"fly ash brick", r"hollow block", r"cement plaster", r"POP",
        r"tile", r"paint", r"putty", r"GI pipe", r"PVC pipe",
        r"HDPE pipe", r"CI pipe", r"SWR pipe", r"flush door",
        r"aluminum window", r"MS door", r"glass", r"cable",
    ],
    "GRADE": [
        r"M20", r"M25", r"M30", r"M35", r"M40",
        r"Fe415", r"Fe500", r"Fe550",
        r"Class A", r"Class B", r"Class C",
    ],
    "STANDARD": [
        r"IS \d+", r"ASTM [A-Z]\d+", r"BS EN \d+",
    ],
    "DIMENSION": [
        r"\d+\s*mm\s*thick", r"\d+\s*cm\s*thick",
        r"\d+\s*m\s*x\s*\d+\s*m",
        r"\d+\s*mm\s*diameter",
    ],
    "UNIT": [
        r"m³", r"cum", r"m3", r"m²", r"sqm", r"m2",
        r"kg", r"nos", r"no\.", r"rmt", r"ltr", r"set", r"ls",
    ],
    "ACTION": [
        r"Supply and install", r"Supply and lay", r"Supply and fix",
        r"Provide and install", r"Provide and lay", r"Provide and fix",
        r"Erect", r"Fabricate and erect", r"Lay", r"Cast", r"Plaster",
        r"Apply", r"Fix", r"Install",
    ],
    "LOCATION": [
        r"ground floor", r"first floor", r"second floor", r"roof level",
        r"basement", r"exterior walls", r"interior walls", r"balcony",
        r"bathroom", r"kitchen", r"terrace", r"compound wall",
    ],
    "QUANTITY": [
        r"\d+(?:,\d{3})*(?:\.\d+)?",
    ],
}


def find_entities_in_text(text: str) -> list[dict[str, Any]]:
    """Find all entity spans in text with BIOES-compatible formatting."""
    entities = []

    for entity_type, patterns in ENTITY_PATTERNS.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append({
                    "text": match.group(0),
                    "type": entity_type,
                    "start": match.start(),
                    "end": match.end(),
                })

    entities.sort(key=lambda x: (x["start"], x["end"]))
    return entities


def text_to_bioes_tokens(text: str, entities: list[dict]) -> tuple[list[str], list[str]]:
    """Convert text to token-level BIOES tags."""
    tokens = []
    tags = []

    sorted_entities = sorted(entities, key=lambda x: (x["start"], x["end"]))

    current_pos = 0

    while current_pos < len(text):
        if text[current_pos].isspace():
            current_pos += 1
            continue

        best_entity = None

        for _i, ent in enumerate(sorted_entities):
            if ent["start"] == current_pos:
                best_entity = ent
                break

        if best_entity:
            token_text = best_entity["text"]
            entity_type = best_entity["type"]

            if len(token_text.split()) == 1:
                tokens.append(token_text)
                tags.append(f"S-{entity_type}")
            else:
                words = token_text.split()
                tokens.append(words[0])
                tags.append(f"B-{entity_type}")
                for word in words[1:-1]:
                    tokens.append(word)
                    tags.append(f"I-{entity_type}")
                tokens.append(words[-1])
                tags.append(f"E-{entity_type}")

            current_pos = best_entity["end"]
        else:
            match = re.match(r"\S+", text[current_pos:])
            if match:
                tokens.append(match.group(0))
                tags.append("O")
                current_pos += len(match.group(0))
            else:
                current_pos += 1

    return tokens, tags


def convert_doc_to_bioes(doc: dict) -> dict:
    """Convert a synthetic document to BIOES training format."""
    text = doc.get("text", "")
    boq_ground_truth = doc.get("metadata", {}).get("boq_ground_truth", [])

    entities = find_entities_in_text(text)
    tokens, tags = text_to_bioes_tokens(text, entities)

    return {
        "id": doc.get("id", ""),
        "tokens": tokens,
        "tags": tags,
        "text": text,
        "entities": entities,
        "boq_ground_truth": boq_ground_truth,
    }


def generate_synthetic_document(doc_id: int) -> dict:
    """Generate a single synthetic RFQ document with BIOES annotations."""
    import random
    random.seed(doc_id)

    materials_list = list(MATERIALS_DATA.keys())
    random.shuffle(materials_list)

    num_items = random.randint(5, 12)
    items = []

    for i in range(num_items):
        cat = materials_list[i % len(materials_list)]
        mat_list = MATERIALS_DATA[cat]
        material = random.choice(mat_list)
        grade = random.choice(GRADES.get(cat, [""]))
        action = random.choice(ACTIONS)
        qty = str(random.randint(10, 500))
        unit = random.choice(UNITS)
        dim = random.choice(DIMENSIONS) if random.random() > 0.3 else ""
        std = random.choice(STANDARDS.get(cat, ["IS 456"]))
        loc = random.choice(LOCATIONS)

        grade_str = f"{grade} " if grade else ""
        if dim:
            desc = f"{action} {grade_str}{material} {dim} at {loc}"
        else:
            desc = f"{action} {grade_str}{material} {qty} {unit} at {loc}"

        items.append(desc)

        if random.random() > 0.5:
            items.append(f"Conforming to {std}")

    text = " ".join(items)

    entities = find_entities_in_text(text)
    tokens, tags = text_to_bioes_tokens(text, entities)

    boq_ground_truth = []
    for i, item_desc in enumerate(items[:num_items]):
        boq_ground_truth.append({
            "item_no": i + 1,
            "description": item_desc,
            "text_for_entity": item_desc,
        })

    return {
        "id": f"syn_{doc_id:04d}",
        "tokens": tokens,
        "tags": tags,
        "text": text,
        "entities": entities,
        "boq_ground_truth": boq_ground_truth,
    }


def generate_bioes_dataset(num_docs: int = 300, output_dir: str = "data/bioes_training"):
    """Generate a complete BIOES training dataset."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Generating {num_docs} BIOES-format training documents...")

    for i in range(num_docs):
        doc = generate_synthetic_document(i + 1)

        doc_path = output_path / f"{doc['id']}.json"
        with open(doc_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)

        if (i + 1) % 50 == 0:
            print(f"  Generated {i + 1}/{num_docs}")

    print(f"\nGenerated {num_docs} BIOES training documents in {output_path}")

    train_path = output_path / "train.json"
    val_path = output_path / "val.json"

    all_docs = []
    for doc_file in output_path.glob("syn_*.json"):
        with open(doc_file, encoding="utf-8") as f:
            all_docs.append(json.load(f))

    random.shuffle(all_docs)
    split_idx = int(len(all_docs) * 0.9)
    train_docs = all_docs[:split_idx]
    val_docs = all_docs[split_idx:]

    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_docs, f, indent=2, ensure_ascii=False)

    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(val_docs, f, indent=2, ensure_ascii=False)

    print(f"  {len(train_docs)} training documents")
    print(f"  {len(val_docs)} validation documents")

    return output_path


def convert_existing_synthetic(input_dir: str = "data/synthetic", output_dir: str = "data/bioes_training"):
    """Convert existing synthetic documents to BIOES format."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    doc_files = list(input_path.glob("syn_*.json"))
    print(f"Converting {len(doc_files)} existing synthetic documents...")

    all_docs = []
    for doc_file in doc_files:
        with open(doc_file, encoding="utf-8") as f:
            doc = json.load(f)

        bioes_doc = convert_doc_to_bioes(doc)

        output_file = output_path / f"{doc.get('id', doc_file.stem)}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(bioes_doc, f, indent=2, ensure_ascii=False)

        all_docs.append(bioes_doc)

    print(f"Converted {len(doc_files)} documents to {output_path}")
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate BIOES training data")
    parser.add_argument("--output-dir", type=str, default="data/bioes_training")
    parser.add_argument("--num-docs", type=int, default=300)
    parser.add_argument("--convert-existing", action="store_true")
    parser.add_argument("--input-dir", type=str, default="data/synthetic")
    args = parser.parse_args()

    if args.convert_existing:
        convert_existing_synthetic(args.input_dir, args.output_dir)
    else:
        generate_bioes_dataset(args.num_docs, args.output_dir)


if __name__ == "__main__":
    import sys
    sys.exit(main())
