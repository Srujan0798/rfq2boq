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
    "insulation",
    "waterproofing",
    "membrane",
    "cladding",
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
    "HYSD",
    "deformed bar",
    "plain bar",
    "readymix concrete",
    "precast",
    "prestressed",
    "structural steel",
    "buckstay",
    "curtain wall",
    "CAC",
    "HVAC",
    "electrical conduit",
    "GI pipe",
    "CPVC pipe",
    "UPVC pipe",
    "SW pipe",
    "GC pipe",
    "BWG",
    "SWG",
    "armour",
    "stranded wire",
    "solid wire",
    "busbar",
    "MDB",
    "DB",
    "MCB",
    "RCCB",
    "ELCB",
    "switch",
    "socket",
    "fan",
    "light",
    "luminaire",
    "bracket",
    "cleat",
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
    "provide",
    "deliver",
    "transport",
    "handle",
    "store",
    "stack",
    "hoist",
    "lift",
    "embed",
    "patch",
    "rake",
    "repoint",
    "hack",
    "roughcast",
    "render",
    "screed",
    "trowel",
    "float",
    "polish",
    "grind",
    "hone",
]

UNITS = [
    "kg",
    "kilogram",
    "kilograms",
    "meter",
    "meters",
    "metre",
    "metres",
    "m2",
    "sqm",
    "sq.m",
    "square meter",
    "square metres",
    "m^2",
    "m3",
    "cum",
    "cu.m",
    "cubic meter",
    "cubic metres",
    "m^3",
    "ft2",
    "sft",
    "sq.ft",
    "square foot",
    "square feet",
    "ft^2",
    "ft3",
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
    "cumec",
    "mec",
    "lps",
    "gpm",
    "lpm",
]

LOCATION_PATTERNS = [
    r"\bground\s*floor\b",
    r"\bfirst\s*floor\b",
    r"\bsecond\s*floor\b",
    r"\bthird\s*floor\b",
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
    r"\bliving\s*room\b",
    r"\bdining\s*room\b",
    r"\bhall\b",
    r"\bcorrider\b",
    r"\bstaircase\b",
    r"\bstairway\b",
    r"\bbalcony\b",
    r"\bveranda\b",
    r"\bporch\b",
    r"\bgarage\b",
    r"\bstore\s*room\b",
    r"\butility\b",
    r"\bplant\s*room\b",
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
    r"\broom\s+no\.?\s*\d+\b",
    r"\bzone\s*[A-Z]\b",
    r"\barea\s*\d+\b",
]

DIMENSION_PATTERNS = [
    r"\d+\s*mm\s*(?:thick|diame)?ter?\b",
    r"\d+\s*cm\s*(?:thick|long|wide)?\b",
    r"\d+\s*m\s*(?:long|wide|high|thick)?\b",
    r"\d+\s*ft\s*(?:long|wide|high|thick)?\b",
    r"\d+\s*in(?:ch)?(?:es)?\b",
    r"\d+\s*[xX\xd7]\s*\d+\s*(?:mm|cm|m|ft|in)\b",
    r"\d+\s*[xX\xd7]\s*\d+\s*[xX\xd7]\s*\d+\s*(?:mm|cm|m|ft|in)\b",
    r"\d+\.\d+\s*(?:mm|cm|m|ft|in)\b",
    r"\xd8\s*\d+\s*mm\b",
    r"phi\s*\d+\s*mm\b",
    r"\d+\s*mm\s*rod\b",
    r"\d+\s*mm\s*bar\b",
    r"\d+\s*mm\s*pipe\b",
    r"\d+\s*mm\s*wire\b",
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

SYNTHETIC_TRAINING_SENTENCES = [
    "Supply 500 kg cement for the foundation at ground floor.",
    "Install 200 nos of TMT steel bars of 12mm diameter in the column.",
    "Pour 25 cubic meters of M20 grade concrete for the ground floor slab.",
    "Lay 1000 bricks of Class A quality for the external wall at first floor.",
    "Apply 50 kg of waterproofing compound on the roof terrace.",
    "Fix 500 meters of PVC pipe of 110mm diameter for drainage at basement.",
    "Construct a beam of size 300mm x 450mm using M25 grade concrete.",
    "Install 100 square meters of drywall panel in the bedroom on second floor.",
    "Supply and install 50 pieces of aluminum windows of dimension 1200mm x 1500mm.",
    "Lay 200 bags of cement for the foundation footing at block A.",
    "Place 15 cubic meters of readymix concrete C30 grade for the column.",
    "Fix reinforcement steel mesh of 8mm bars at 150mm spacing in the slab.",
    "Apply 2 coats of primer on the internal wall surface before painting.",
    "Install electrical conduit of 25mm diameter using GI pipe throughout.",
    "Supply 1000 kilograms of structural steel Fe500 for the framework.",
    "Cast 10 cubic meters of M30 concrete for the foundation raft.",
    "Lay 500 meters of cable of size 2.5 sqmm for electrical wiring.",
    "Fix 200 numbers of ceiling fans of 1200mm sweep in all rooms.",
    "Apply waterproofing membrane of 2mm thickness on the roof area.",
    "Construct brick wall of 200mm thickness using M20 mortar mix.",
    "Install copper wire of 4 sqmm for main electrical distribution board.",
    "Place 100 cubic meters of plain cement concrete M25 for the flooring.",
    "Lay 50 bags of cement plastering mix on the bathroom walls.",
    "Supply and install 500 pieces of ceramic floor tiles of 600mm x 600mm.",
    "Fix 150 meters of UPVC pipe of 75mm diameter for soil and waste system.",
    "Apply bitumen primer at the rate of 0.5 liters per square meter on roof.",
    "Install TMT reinforcement bars of 16mm diameter in the beam at ground floor.",
    "Pour 30 cubic meters of Fe415 grade concrete for the pile foundation.",
    "Lay 1000 kilograms of coarse aggregate of 20mm nominal size for concrete.",
    "Fix 200 square meters of glass panel of 6mm thickness for the facade.",
]


class EntityMatch(TypedDict):
    text: str
    start: int
    end: int
    label: str


PDF_CONTENTS_PATH = Path("/Users/srujansai/Desktop/rfq2boq/docs/historical/research/COMPLETE_PDF_CONTENTS.md")
VIDEO_TRANSCRIPTS_PATH = Path("/Users/srujansai/Desktop/rfq2boq/docs/historical/research/VIDEO_TRANSCRIPTS.md")
OUTPUT_PATH = Path("/Users/srujansai/Desktop/rfq2boq/data/nerAnnotations.json")
SCRIPT_PATH = Path("/Users/srujansai/Desktop/rfq2boq/resources/ner_training_data.py")


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
    r"\b\d{1,3}(,\d{3})+\b" r"|" r"\b\d+\.\d+\b" r"|" r"\b\d+/\d+\b" r"|" r"\b\d+\s+\d+/\d+\b" r"|" r"\b\d+\b"
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
                entity = EntityMatch(text=match.group(), start=match.start(), end=match.end(), label=label)
                entities.append(entity)

    entities = sorted(entities, key=lambda e: (e["start"], -e["end"]))
    filtered: list[EntityMatch] = []
    skip_indices: set[int] = set()

    for i, entity in enumerate(entities):
        if i in skip_indices:
            continue

        should_skip = False
        for j in range(i + 1, len(entities)):
            if j in skip_indices:
                continue
            next_entity = entities[j]
            if next_entity["start"] >= entity["start"] and next_entity["end"] <= entity["end"]:
                if entity["label"] == "ACTION" and next_entity["label"] in ("QUANTITY", "UNIT", "MATERIAL"):
                    skip_indices.add(j)
                    should_skip = True

        if not should_skip:
            filtered.append(entity)

    return filtered


def merge_overlapping_entities(entities: list[EntityMatch]) -> list[EntityMatch]:
    if not entities:
        return []

    entities = sorted(entities, key=lambda e: (e["start"], -e["end"]))
    merged: list[EntityMatch] = []
    skip_indices: set[int] = set()

    for i, entity in enumerate(entities):
        if i in skip_indices:
            continue

        current = EntityMatch(text=entity["text"], start=entity["start"], end=entity["end"], label=entity["label"])

        j = i + 1
        while j < len(entities):
            if j in skip_indices:
                j += 1
                continue

            next_entity = entities[j]
            if next_entity["start"] > current["end"] + 1:
                break

            if next_entity["start"] == current["end"] or next_entity["start"] == current["end"] + 1:
                current["text"] += " " + next_entity["text"]
                current["end"] = next_entity["end"]
                skip_indices.add(j)

            j += 1

        merged.append(current)

    return merged


def split_into_sentences(text: str) -> list[str]:
    sentence_endings = re.compile(r"(?<=[.!?])\s+")
    raw_sentences = sentence_endings.split(text)

    sentences = []
    for s in raw_sentences:
        s = s.strip()
        if len(s) > 30 and len(s) < 400:
            sentences.append(s)

    return sentences


def is_construction_context(text_lower: str) -> bool:
    construction_keywords = [
        "cement",
        "concrete",
        "steel",
        "brick",
        "mortar",
        "beam",
        "column",
        "slab",
        "foundation",
        "reinforcement",
        "aggregate",
        "sand",
        "bitumen",
        "asphalt",
        "construction",
        "building",
        "structural",
        "erection",
        "installation",
        "qty",
        "quantity",
        "unit",
        "meter",
        "sqm",
        "cum",
        "nos",
        "BOQ",
        "RFQ",
        "tender",
        "schedule",
        "item",
        "rate",
        "cost",
        "labour",
        "material",
        "work",
        "civil",
        "architectural",
        "structural",
        "M20",
        "M25",
        "M30",
        "Fe500",
        "IS 456",
        "IS 800",
        "floor",
        "wall",
        "brick",
        "tile",
        "pipe",
        "wire",
        "cable",
        "electrical",
        "plumbing",
        "painting",
        "plastering",
        "waterproofing",
        "drainage",
        "sanitary",
    ]
    score = sum(1 for kw in construction_keywords if kw in text_lower)
    return score >= 1


def is_valid_material_context(entity_text: str, context: str) -> bool:
    invalid_contexts = [
        "science foundation",
        "national science foundation",
        "industry foundation classes",
        "research foundation",
        "building foundation classes",
        "IFC",
        "concrete core",
        "reinforcement shall",
    ]
    context_lower = context.lower()
    for ic in invalid_contexts:
        if ic in context_lower:
            combined = f"{entity_text} {context}".lower()
            if combined.count(ic) > context_lower.count(ic):
                return False
    return True


def remove_duplicate_entity_spans(entities: list[EntityMatch]) -> list[EntityMatch]:
    if not entities:
        return []

    entities = sorted(entities, key=lambda e: (e["start"], -e["end"]))
    result: list[EntityMatch] = []
    last_start = -1
    last_end = -1

    for entity in entities:
        if entity["start"] == last_start and entity["end"] == last_end:
            continue
        result.append(entity)
        last_start = entity["start"]
        last_end = entity["end"]

    return result


def resolve_entity_overlaps(entities: list[EntityMatch]) -> list[EntityMatch]:
    if not entities:
        return []

    entities = sorted(entities, key=lambda e: (e["start"], -e["end"]))
    resolved: list[EntityMatch] = []
    skip_indices: set[int] = set()

    for i, entity in enumerate(entities):
        if i in skip_indices:
            continue

        if entity["label"] in ("MATERIAL", "LOCATION", "STANDARD"):
            for j in range(i + 1, len(entities)):
                if j in skip_indices:
                    continue
                next_e = entities[j]
                if next_e["start"] < entity["end"] and next_e["end"] > entity["start"]:
                    if next_e["label"] in ("QUANTITY", "UNIT"):
                        skip_indices.add(j)
                    elif next_e["label"] == entity["label"]:
                        if (
                            next_e["start"] >= entity["start"]
                            and next_e["end"] <= entity["end"]
                            or next_e["start"] > entity["start"]
                        ):
                            skip_indices.add(j)
                    elif next_e["label"] in ("LOCATION", "MATERIAL", "STANDARD"):
                        skip_indices.add(j)

        resolved.append(entity)

    return resolved


def split_multitoken_entities(entities: list[EntityMatch]) -> list[EntityMatch]:
    result: list[EntityMatch] = []

    for entity in entities:
        if entity["label"] == "ACTION" and " " in entity["text"]:
            words = entity["text"].split()
            first_word = words[0]
            result.append(
                EntityMatch(
                    text=first_word, start=entity["start"], end=entity["start"] + len(first_word), label="ACTION"
                )
            )
            if len(words) > 1:
                rest = " ".join(words[1:])
                rest_start = entity["start"] + len(first_word) + 1
                result.append(EntityMatch(text=rest, start=rest_start, end=rest_start + len(rest), label="QUANTITY"))
        else:
            result.append(entity)

    return result


def tokenize_for_ner(text: str) -> list[str]:
    tokens_with_spans = list(re.finditer(r"\S+", text))
    return [m.group() for m in tokens_with_spans]


def generate_bioes_tags(tokens: list[str], entities: list[EntityMatch], text: str) -> list[str]:
    tags: list[str] = ["O"] * len(tokens)

    char_to_token: dict[int, int] = {}
    token_start = 0
    for i, token in enumerate(tokens):
        for c in range(token_start, token_start + len(token)):
            char_to_token[c] = i
        token_start += len(token)
        if token_start < len(text):
            token_start += 1

    sorted_entities = sorted(entities, key=lambda e: (e["start"], -e["end"]))

    processed_ranges: list[tuple[int, int]] = []

    for entity in sorted_entities:
        start_token = char_to_token.get(entity["start"])
        end_token = char_to_token.get(entity["end"] - 1)

        if start_token is None or end_token is None:
            continue

        label = entity["label"]
        entity_len = end_token - start_token + 1

        overlapping = False
        for pr in processed_ranges:
            if not (end_token < pr[0] or start_token > pr[1]):
                overlapping = True
                break

        if overlapping:
            continue

        if entity_len == 1:
            tags[start_token] = f"S-{label}"
        else:
            tags[start_token] = f"B-{label}"
            for t in range(start_token + 1, end_token):
                tags[t] = f"I-{label}"
            tags[end_token] = f"E-{label}"

        processed_ranges.append((start_token, end_token))

    return tags


def process_sentence(
    sentence: str, patterns: dict[str, list[re.Pattern]], validate_context: bool = True
) -> dict | None:
    text_lower = sentence.lower()

    if validate_context and not is_construction_context(text_lower):
        return None

    entities = extract_entities(sentence, patterns)
    quantities = extract_quantity_spans(sentence)

    for q_text, q_start, q_end in quantities:
        entities.append(EntityMatch(text=q_text, start=q_start, end=q_end, label="QUANTITY"))

    if validate_context:
        valid_entities = []
        for e in entities:
            if e["label"] == "MATERIAL" and not is_valid_material_context(e["text"], sentence):
                continue
            valid_entities.append(e)
        entities = valid_entities

    if len(entities) < 2:
        return None

    entities = resolve_entity_overlaps(entities)
    entities = remove_duplicate_entity_spans(entities)

    if len(entities) < 2:
        return None

    tokens = tokenize_for_ner(sentence)
    tags = generate_bioes_tags(tokens, entities, sentence)

    return {
        "sentence": sentence,
        "tokens": tokens,
        "bioes_tags": tags,
        "entities": [{"text": e["text"], "start": e["start"], "end": e["end"], "type": e["label"]} for e in entities],
    }


def process_document(text: str, patterns: dict[str, list[re.Pattern]]) -> list[dict]:
    sentences = split_into_sentences(text)
    results: list[dict] = []

    for sentence in sentences:
        result = process_sentence(sentence, patterns, validate_context=True)
        if result:
            results.append(result)

    return results


def process_synthetic_sentences(patterns: dict[str, list[re.Pattern]]) -> list[dict]:
    results: list[dict] = []
    for sentence in SYNTHETIC_TRAINING_SENTENCES:
        result = process_sentence(sentence, patterns, validate_context=False)
        if result:
            results.append(result)
    return results


def load_source_documents() -> str:
    combined_text = ""

    if PDF_CONTENTS_PATH.exists():
        content = PDF_CONTENTS_PATH.read_text(encoding="utf-8")
        content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)
        content = re.sub(r"\*{2,}", "", content)
        content = re.sub(r"\-{3,}", "", content)
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

    print("\nProcessing synthetic construction sentences...")
    synthetic_data = process_synthetic_sentences(patterns)
    print(f"Extracted {len(synthetic_data)} synthetic sentences")

    if text:
        print("\nProcessing document sentences...")
        document_data = process_document(text, patterns)
        print(f"Extracted {len(document_data)} document sentences")
    else:
        document_data = []

    annotated_data = synthetic_data + document_data

    print(f"\nTotal: {len(annotated_data)} sentences with entities")

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
            "source_files": [str(PDF_CONTENTS_PATH), str(VIDEO_TRANSCRIPTS_PATH), "synthetic_construction_sentences"],
            "entity_types": ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"],
            "tagging_scheme": "BIOES",
        },
        "annotations": annotated_data,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved annotations to: {OUTPUT_PATH}")

    SCRIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SCRIPT_PATH.write_text(Path(__file__).read_text(), encoding="utf-8")
    print(f"Saved script to: {SCRIPT_PATH}")

    print("\n" + "=" * 60)
    print("5 EXAMPLE ANNOTATIONS:")
    print("=" * 60)

    for i, item in enumerate(annotated_data[:5]):
        print(f"\n--- Example {i+1} ---")
        print(f"Sentence: {item['sentence'][:120]}")
        print(f"Tokens: {item['tokens'][:12]}")
        print(f"Tags: {item['bioes_tags'][:12]}")
        print(f"Entities: {[(e['text'], e['type']) for e in item['entities']]}")

    return output_data


if __name__ == "__main__":
    main()
