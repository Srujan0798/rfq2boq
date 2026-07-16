#!/usr/bin/env python3
"""NER Training Data Generator for RFQ2BOQ.

Extracts construction-specific NER training data with entities:
MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE
using BIOES tagging scheme (B=Begin, I=Inside, E=End, S=Single, O=Outside).

Author: Claude
"""

import json
import re
from pathlib import Path
from typing import TypedDict

from config.constants import EntityType

PDF_CONTENTS_PATH = Path("/Users/srujansai/Desktop/rfq2boq/docs/historical/research/COMPLETE_PDF_CONTENTS.md")
VIDEO_TRANSCRIPTS_PATH = Path("/Users/srujansai/Desktop/rfq2boq/docs/historical/research/VIDEO_TRANSCRIPTS.md")
OUTPUT_PATH = Path("/Users/srujansai/Desktop/rfq2boq/data/nerAnnotations.json")

MATERIALS = [
    "cement",
    "concrete",
    "steel",
    "reinforcement",
    "brick",
    "mortar",
    "timber",
    "wood",
    "PVC",
    "copper wire",
    "cable",
    "pipe",
    "drywall",
    "glass",
    "aluminum",
    "aggregate",
    "sand",
    "gravel",
    "bitumen",
    "asphalt",
    "tile",
    "ceramic",
    "granite",
    "marble",
    "plaster",
    "paint",
    "varnish",
    "sealant",
    "adhesive",
    "screw",
    "bolt",
    "nail",
    "rod",
    "bar",
    "mesh",
    "panel",
    "sheet",
    "block",
    "stone",
    "lime",
    "gypsum",
    " insulation",
    " waterproofing",
    "membrane",
    " cladding",
    "decking",
    "scaffolding",
    "formwork",
    "centering",
    "shuttering",
    "shoring",
    "anchor",
    "brace",
    "joist",
    "beam",
    "column",
    "slab",
    "wall",
    "foundation",
    "footing",
    "pile",
    "caisson",
    "door",
    "window",
    "frame",
    "partition",
    "ceiling",
    "flooring",
    "roofing",
    "TMT",
    "Fe415",
    "Fe500",
    " HYSD",
    "deformed bar",
    "plain bar",
]

ACTIONS = [
    "supply",
    "install",
    "construct",
    "pour",
    "place",
    "fix",
    "apply",
    "lay",
    "cast",
    "build",
    "erect",
    "fabricate",
    "weld",
    "bolt",
    "screw",
    "nail",
    "glue",
    "bond",
    "cure",
    "finish",
    "treat",
    "coat",
    "paint",
    "plaster",
    "point",
    "grout",
    "seal",
    "waterproof",
    "insulate",
    "level",
    "compact",
    "excavate",
    "backfill",
    "compact",
    "test",
    "inspect",
    "verify",
    "measure",
    "mark",
    "cut",
    "drill",
    "bore",
    "thread",
    "bend",
    "shape",
    "machine",
    "assemble",
    "dismantle",
    "remove",
    "replace",
    "repair",
    "maintain",
    "clean",
    "clear",
    "prepare",
    "prime",
    "spray",
    "roll",
    "brush",
]

UNITS = [
    "kg",
    "kilogram",
    "kilograms",
    "meter",
    "meters",
    "metre",
    "metres",
    "m²",
    "sqm",
    "sq.m",
    "square meter",
    "square metres",
    "m^2",
    "m³",
    "cum",
    "cu.m",
    "cubic meter",
    "cubic metres",
    "m^3",
    "ft²",
    "sft",
    "sq.ft",
    "square foot",
    "square feet",
    "ft^2",
    "ft³",
    "cft",
    "cubic foot",
    "cubic feet",
    "ft^3",
    "cm",
    "centimeter",
    "centimeters",
    "centimetre",
    "centimetres",
    "mm",
    "millimeter",
    "millimeters",
    "millimetre",
    "millimetres",
    "in",
    "inch",
    "inches",
    "ft",
    "foot",
    "feet",
    "nos",
    "pieces",
    "piece",
    "pc",
    "pcs",
    "no.",
    "numbers",
    "each",
    "bags",
    "bag",
    "sacks",
    "sack",
    "drums",
    "drum",
    "rolls",
    "roll",
    "liters",
    "litres",
    "ltr",
    "litre",
    "gallon",
    "gallons",
    "tonnes",
    "tonne",
    "tons",
    "ton",
    "MT",
    "t",
    "lm",
    "running meter",
    "linear meters",
    "linear metres",
    "set",
    "sets",
    "pair",
    "pairs",
    "box",
    "boxes",
    "kW",
    "kilowatt",
    "MW",
    "megawatt",
    "hp",
    "horsepower",
    "V",
    "volt",
    "volts",
    "A",
    "amp",
    "amps",
    "ampere",
    "kVA",
    "VA",
    "W",
    "watt",
    "watts",
    "bar",
    "psi",
    "kPa",
    "MPa",
    "N",
    "kN",
    "kgf",
    "hour",
    "hours",
    "day",
    "days",
    "week",
    "weeks",
    "ls",
    "lump.sum",
    "lumpsum",
    "lot",
    "job",
]

LOCATION_PATTERNS = [
    r"\bground floor\b",
    r"\bfirst floor\b",
    r"\bsecond floor\b",
    r"\bthird floor\b",
    r"\bbasement\b",
    r"\bmezzanine\b",
    r"\battic\b",
    r"\broof\b",
    r"\bterrace\b",
    r"\bbedroom\b",
    r"\bkitchen\b",
    r"\bbathroom\b",
    r"\btoilet\b",
    r"\bwc\b",
    r"\bliving room\b",
    r"\bdining room\b",
    r"\bhall\b",
    r"\bcorrider\b",
    r"\bstaircase\b",
    r"\bstairway\b",
    r"\bbalcony\b",
    r"\bveranda\b",
    r"\bporch\b",
    r"\bgarage\b",
    r"\bstore room\b",
    r"\butility\b",
    r"\bplant room\b",
    r"\bblock\s+[A-Z]\b",
    r"\bfloor\s+\d+\b",
    r"\blevel\s+\d+\b",
    r"\bexternal\b",
    r"\binternal\b",
    r"\binterior\b",
    r"\bexterior\b",
    r"\bwall\b",
    r"\bfloor\b",
    r"\bceiling\b",
    r"\broof\b",
    r"\bfoundation\b",
    r"\bfooting\b",
    r"\bslab\b",
    r"\bcolumn\b",
    r"\bbeam\b",
    r"\bwindow\b",
    r"\bdoor\b",
    r"\bopening\b",
    r"\bviewport\b",
]

DIMENSION_PATTERNS = [
    r"\d+\s*mm\s*(?:thick|diame)?ter?\b",
    r"\d+\s*cm\s*(?:thick|long|wide)?\b",
    r"\d+\s*m\s*(?:long|wide|high|thick)?\b",
    r"\d+\s*ft\s*(?:long|wide|high|thick)?\b",
    r"\d+\s*in(?:ch)?(?:es)?\b",
    r"\d+\s*[xX×]\s*\d+\s*(?:mm|cm|m|ft|in)\b",
    r"\d+\s*[xX×]\s*\d+\s*[xX×]\s*\d+\s*(?:mm|cm|m|ft|in)\b",
    r"\d+\.\d+\s*(?:mm|cm|m|ft|in)\b",
    r"Ø\s*\d+\s*mm\b",
    r"φ\s*\d+\s*mm\b",
    r"\d+\s*mm\s*rod\b",
    r"\d+\s*mm\s*bar\b",
    r"\d+\s*mm\s*pipe\b",
    r"\d+\s*mm\s*wire\b",
    r"(\d+)\s*(\+?\d+/\d+)?\s*(ft|in|m|cm|mm)\b",
]

STANDARD_PATTERNS = [
    r"\bIS\s*\d+\b",
    r"\bIS\s*\d+\.\d+\b",
    r"\bIS\s*\d+\s*\d+\b",
    r"\bBS\s*\d+\b",
    r"\bBS\s*\d+\.\d+\b",
    r"\bBS\s*EN\s*\d+\b",
    r"\bASTM\s*[A-Z]\d+\b",
    r"\bASTM\s*\d+\b",
    r"\bEurocode\s*\d+\b",
    r"\bEN\s*\d+\b",
    r"\bACI\s*\d+\b",
    r"\bAISC\s*\d+\b",
    r"\bIRC\s*\d+\b",
    r"\bIBC\s*\d+\b",
    r"\bNRM3\b",
    r"\bSMM7\b",
    r"\bCESMM4\b",
    r"\bIS\s*456\b",
    r"\bIS\s*1893\b",
    r"\bIS\s*800\b",
    r"\bIS\s*875\b",
    r"\bIS\s*13827\b",
    r"\bIS\s*13828\b",
    r"\bGB\s*\d+\b",
    r"\bJIS\s*\d+\b",
    r"\bDIN\s*\d+\b",
    r"\bUL\s*\d+\b",
    r"\bCSA\s*\d+\b",
]

GRADE_PATTERNS = [
    r"\bM\d+\b",
    r"\bC\d+\b",
    r"\bFe\d+\b",
    r"\bGrade\s*[A-D]\b",
    r"\bGrade\s*\d+\b",
    r"\bClass\s*[A-Z]\b",
    r"\bClass\s*\d+\b",
    r"\bType\s*[I|II|III|IV|V|VI]\b",
    r"\bType\s*\d+\b",
    r"\bstrength\s*class\b",
    r"\bC30\b",
    r"\bC35\b",
    r"\bC40\b",
    r"\bM20\b",
    r"\bM25\b",
    r"\bM30\b",
    r"\bM35\b",
    r"\bM40\b",
    r"\bFe415\b",
    r"\bFe500\b",
    r"\bFe550\b",
    r"\bFck\s*=\s*\d+\b",
    r"\bfck\b",
]


class EntityMatch(TypedDict):
    text: str
    start: int
    end: int
    label: str


def compile_patterns() -> dict[str, list[re.Pattern]]:
    return {
        "MATERIAL": [re.compile(rf"\b{w}\b", re.IGNORECASE) for w in MATERIALS],
        "ACTION": [re.compile(rf"\b{a}\b", re.IGNORECASE) for a in ACTIONS],
        "UNIT": [re.compile(rf"\b{u}\b", re.IGNORECASE) for u in UNITS],
        "LOCATION": [re.compile(pat, re.IGNORECASE) for pat in LOCATION_PATTERNS],
        "DIMENSION": [re.compile(pat, re.IGNORECASE) for pat in DIMENSION_PATTERNS],
        "STANDARD": [re.compile(pat, re.IGNORECASE) for pat in STANDARD_PATTERNS],
        "GRADE": [re.compile(pat, re.IGNORECASE) for pat in GRADE_PATTERNS],
    }


QUANTITY_PATTERN = re.compile(
    r"\b\d+(?:,\d{3})*(?:\.\d+)?\b" r"|" r"\b\d+\s+\d+/\d+\b" r"|" r"\b\d+/\d+\b" r"|" r"\b\d+\.\d+\b"
)


def extract_quantity_spans(text: str) -> list[tuple[str, int, int]]:
    spans = []
    for match in QUANTITY_PATTERN.finditer(text):
        spans.append((match.group(), match.start(), match.end()))
    return spans


def extract_entities(text: str, patterns: dict[str, list[re.Pattern]]) -> list[EntityMatch]:
    entities: list[EntityMatch] = []

    for label, regexes in patterns.items():
        for regex in regexes:
            for match in regex.finditer(text):
                entities.append(EntityMatch(text=match.group(), start=match.start(), end=match.end(), label=label))

    return entities


def merge_entities(entities: list[EntityMatch]) -> list[EntityMatch]:
    if not entities:
        return []

    entities = sorted(entities, key=lambda e: (e["start"], e["end"]))
    merged: list[EntityMatch] = []
    skip_indices: set[int] = set()

    for i, entity in enumerate(entities):
        if i in skip_indices:
            continue

        span_text = entity["text"]
        start = entity["start"]
        end = entity["end"]
        label = entity["label"]

        j = i + 1
        while j < len(entities):
            if entities[j]["start"] == end or entities[j]["start"] == end + 1:
                span_text += " " + entities[j]["text"]
                end = entities[j]["end"]
                skip_indices.add(j)
                merged.append(EntityMatch(text=span_text, start=start, end=end, label=label))
                break
            elif entities[j]["start"] < end:
                skip_indices.add(j)
                j += 1
            else:
                break

        if j == len(entities) and i not in skip_indices:
            merged.append(entity)

    return merged


def split_into_sentences(text: str) -> list[str]:
    sentence_endings = re.compile(r"(?<=[.!?])\s+")
    raw_sentences = sentence_endings.split(text)

    sentences = []
    for s in raw_sentences:
        s = s.strip()
        if len(s) > 20 and len(s) < 500:
            sentences.append(s)

    return sentences


def generate_bioes_tags(tokens: list[str], entities: list[EntityMatch], text: str) -> list[str]:
    tags: list[str] = ["O"] * len(tokens)

    char_to_token: dict[int, int] = {}
    token_start = 0
    for i, token in enumerate(tokens):
        for c in range(token_start, token_start + len(token)):
            char_to_token[c] = i
        token_start += len(token) + 1

    sorted_entities = sorted(entities, key=lambda e: e["start"])

    for entity in sorted_entities:
        start_token = char_to_token.get(entity["start"])
        end_token = char_to_token.get(entity["end"] - 1)

        if start_token is None or end_token is None:
            continue

        label = entity["label"]
        entity_len = end_token - start_token + 1

        if entity_len == 1:
            tags[start_token] = f"S-{label}"
        else:
            tags[start_token] = f"B-{label}"
            for t in range(start_token + 1, end_token):
                tags[t] = f"I-{label}"
            tags[end_token] = f"E-{label}"

    return tags


def tokenize_for_ner(text: str) -> list[str]:
    tokens_with_spans = list(re.finditer(r"\S+", text))
    return [m.group() for m in tokens_with_spans]


def process_document(text: str, patterns: dict[str, list[re.Pattern]]) -> list[dict]:
    sentences = split_into_sentences(text)
    results: list[dict] = []

    for sentence in sentences:
        entities = extract_entities(sentence, patterns)
        quantities = extract_quantity_spans(sentence)

        for q_text, q_start, q_end in quantities:
            entities.append(EntityMatch(text=q_text, start=q_start, end=q_end, label="QUANTITY"))

        if len(entities) < 2:
            continue

        entities = merge_entities(entities)

        tokens = tokenize_for_ner(sentence)
        tags = generate_bioes_tags(tokens, entities, sentence)

        results.append(
            {
                "sentence": sentence,
                "tokens": tokens,
                "bioes_tags": tags,
                "entities": [
                    {"text": e["text"], "start": e["start"], "end": e["end"], "type": e["label"]} for e in entities
                ],
            }
        )

    return results


def load_source_documents() -> str:
    combined_text = ""

    if PDF_CONTENTS_PATH.exists():
        content = PDF_CONTENTS_PATH.read_text(encoding="utf-8")
        content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)
        content = re.sub(r"\*{2,}", "", content)
        content = re.sub(r"\-{2,}", "", content)
        combined_text += content + "\n"
        print(f"Loaded PDF contents: {len(content)} chars")
    else:
        print(f"PDF contents not found: {PDF_CONTENTS_PATH}")

    if VIDEO_TRANSCRIPTS_PATH.exists():
        content = VIDEO_TRANSCRIPTS_PATH.read_text(encoding="utf-8")
        content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)
        content = re.sub(r"\*{2,}", "", content)
        combined_text += content + "\n"
        print(f"Loaded video transcripts: {len(content)} chars")
    else:
        print(f"Video transcripts not found: {VIDEO_TRANSCRIPTS_PATH}")

    return combined_text


def main() -> dict:
    patterns = compile_patterns()

    print("Loading source documents...")
    text = load_source_documents()

    if not text:
        print("No text loaded!")
        return {"error": "No source documents found"}

    print(f"Total text loaded: {len(text)} chars")
    print("Extracting sentences and entities...")

    annotated_data = process_document(text, patterns)

    print(f"\nExtracted {len(annotated_data)} sentences with entities")

    entity_counts: dict[str, int] = {}
    for item in annotated_data:
        for entity in item["entities"]:
            etype = entity["type"]
            entity_counts[etype] = entity_counts.get(etype, 0) + 1

    print("\nEntity counts by type:")
    for etype, count in sorted(entity_counts.items()):
        print(f"  {etype}: {count}")

    output_data = {
        "metadata": {
            "total_sentences": len(annotated_data),
            "entity_counts": entity_counts,
            "source_files": [str(PDF_CONTENTS_PATH), str(VIDEO_TRANSCRIPTS_PATH)],
            "entity_types": [e.value for e in EntityType],
            "tagging_scheme": "BIOES",
        },
        "annotations": annotated_data,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved annotations to: {OUTPUT_PATH}")

    print("\n" + "=" * 60)
    print("5 EXAMPLE ANNOTATIONS:")
    print("=" * 60)

    for i, item in enumerate(annotated_data[:5]):
        print(f"\n--- Example {i+1} ---")
        print(f"Sentence: {item['sentence'][:120]}...")
        print(f"Tokens: {item['tokens'][:15]}...")
        print(f"Tags: {item['bioes_tags'][:15]}...")
        print(f"Entities: {[(e['text'], e['type']) for e in item['entities']]}")

    return output_data


if __name__ == "__main__":
    main()
