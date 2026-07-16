#!/usr/bin/env python3
"""Generate annotation drafts from extracted RFQ/BOQ files."""

import json
import re
import sys
from pathlib import Path

BATCH_DIR = Path("output/batch_extractions")
ROWGOLD_DIR = Path("data/annotations/cli_drafts/rowgold")
BIOES_DIR = Path("data/annotations/cli_drafts/bioes")
NOTES_DIR = Path("data/annotations/cli_drafts/notes")
DATE = "2026-07-04"


def stem_from_path(p: Path) -> str:
    name = p.name
    if name.endswith(".extracted.json"):
        return name[: -len(".extracted.json")]
    return p.stem


def fix_obvious_typos(text: str) -> str:
    fixes = {
        "accoustic": "acoustic",
        "Acountic": "Acoustic",
        "acountic": "acoustic",
        "Acustic": "Acoustic",
        "acustic": "acoustic",
        "Insulaton": "Insulation",
        "insulaton": "insulation",
        "ductiing": "ducting",
        "insulatione": "insulation",
    }
    for wrong, right in fixes.items():
        text = text.replace(wrong, right)
    return text


def tokenize_material(text: str) -> list[str]:
    """Split material description into tokens."""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    tokens = re.findall(r"\d+(?:\.\d+)?|[A-Za-z]+|[/()\-,.]|[\u0900-\u097F]+", text)
    return tokens


def detect_entity(token: str, prev_token: str | None, next_token: str | None) -> str:
    """Classify a single token into an entity type."""
    t_lower = token.lower()

    if re.match(r"^\d+(\.\d+)?$", token):
        return "QUANTITY"

    units = {
        "sqm", "sq.m", "sqm.", "m", "mm", "cm", "kg", "nos", "no", "ltr",
        "kg/m3", "kg/m", "mtr", "m.", "meter", "meters", "mmthick",
        "kg.", "nos.", "cum", "cu.m", "sqft", "sq.ft", "rmt",
    }
    if t_lower in units or t_lower.rstrip(".") in units:
        return "UNIT"

    location_signals = {"at", "for", "in", "near", "zone", "area", "building", "floor", "level"}
    if t_lower in location_signals and next_token and next_token[0].isupper() and next_token.lower() not in units:
        return "LOCATION"

    if re.match(r"^\d+\s*(mm|cm|m|kg|nos|sqm|ltr)$", token, re.I):
        return "DIMENSION"

    action_words = {"supply", "supplying", "supply.", "install", "installation", "provide", "lay", "erect", "fix"}
    if t_lower in action_words:
        return "ACTION"

    grade_words = {"grade", "type", "class", "is", "bs", "astm", "din", "en"}
    if t_lower in grade_words:
        return "GRADE"

    std_patterns = {"is:", "is ", "bs ", "astm ", "din ", "en ", "iso "}
    for pat in std_patterns:
        if t_lower.startswith(pat):
            return "STANDARD"

    if prev_token and prev_token.lower() in {"thick", "thickness", "size", "dia", "diameter", "width", "length"}:
        return "DIMENSION"

    return "MATERIAL"


def generate_bioes_sentence(entry: dict) -> dict | None:
    """Create a single BIOES sentence from an extraction entry."""
    material = entry.get("material", "").strip()
    if not material:
        return None

    tokens = tokenize_material(material)
    if not tokens:
        return None

    quantity = entry.get("quantity", "")
    unit = entry.get("unit", "")
    grade = entry.get("grade", "")
    location = entry.get("location", "")
    action = entry.get("action", "")

    extra_tokens = []
    if quantity:
        extra_tokens.append(str(quantity))
    if unit:
        extra_tokens.append(unit)
    if grade:
        extra_tokens.extend(tokenize_material(grade))
    if action:
        extra_tokens.append(action)
    if location:
        extra_tokens.extend(location.split())

    all_tokens = tokens + extra_tokens
    tags = []

    for i, tok in enumerate(all_tokens):
        prev = all_tokens[i - 1] if i > 0 else None
        nxt = all_tokens[i + 1] if i < len(all_tokens) - 1 else None

        is_extra = i >= len(tokens)

        if is_extra:
            if tok == str(quantity) or (quantity and tok == str(quantity)):
                tags.append("S-QUANTITY")
            elif unit and tok.lower() == unit.lower():
                tags.append("S-UNIT")
            elif tok.lower() in {"supply", "install", "provide", "lay", "erect", "fix"}:
                tags.append("S-ACTION")
            elif tok == grade:
                tags.append("S-GRADE")
            else:
                tags.append("O")
        else:
            entity = detect_entity(tok, prev, nxt)
            tags.append(f"S-{entity}")

    clean_tokens = []
    clean_tags = []
    for tok, tag in zip(all_tokens, tags, strict=False):
        if tok and tag:
            clean_tokens.append(tok)
            clean_tags.append(tag)

    return {
        "tokens": clean_tokens,
        "ner_tags": clean_tags,
        "labels": clean_tags,
    }


def build_rowgold(source_path: str, entries: list[dict]) -> dict:
    rowgold_entries = []
    for e in entries:
        mat = fix_obvious_typos(e.get("material", ""))
        rowgold_entries.append({
            "item_no": e.get("item_no", ""),
            "material": mat,
            "quantity": e.get("quantity", ""),
            "unit": e.get("unit", ""),
            "grade": e.get("grade", ""),
            "location": e.get("location", ""),
            "action": e.get("action", ""),
        })
    return {
        "source_file": source_path,
        "date": DATE,
        "human_verified": False,
        "method": "machine-assisted-draft-from-extraction",
        "gold_source": source_path,
        "entries": rowgold_entries,
    }


def process_file(fpath: Path) -> tuple[int, int, str]:
    """Process one extracted.json file. Returns (entry_count, bioes_count, note_text)."""
    with open(fpath) as f:
        data = json.load(f)

    stem = stem_from_path(fpath)
    source_path = data.get("source", "")
    entries = data.get("entries", [])

    rowgold = build_rowgold(source_path, entries)
    with open(ROWGOLD_DIR / f"{stem}.rowgold.json", "w") as f:
        json.dump(rowgold, f, indent=2, ensure_ascii=False)

    bioes_sentences = []
    for e in entries:
        sent = generate_bioes_sentence(e)
        if sent:
            bioes_sentences.append(sent)

    bioes_doc = {
        "source_file": source_path,
        "date": DATE,
        "human_verified": False,
        "method": "machine-assisted-draft-from-extraction",
        "sentences": bioes_sentences,
    }
    with open(BIOES_DIR / f"{stem}.bioes.json", "w") as f:
        json.dump(bioes_doc, f, indent=2, ensure_ascii=False)

    unique_materials = len({e.get("material", "") for e in entries if e.get("material")})
    unique_units = len({e.get("unit", "") for e in entries if e.get("unit")})
    has_location = any(e.get("location") for e in entries)
    has_grade = any(e.get("grade") for e in entries)

    note_lines = [
        f"Source: {source_path}",
        f"Extracted entries: {len(entries)}",
        f"BIOES sentences generated: {len(bioes_sentences)}",
        f"Unique material descriptions: {unique_materials}",
        f"Unique units found: {unique_units}",
        f"Has location data: {has_location}",
        f"Has grade data: {has_grade}",
        f"Method: {data.get('method', 'unknown')}",
        f"Generated: {DATE}",
        "Status: DRAFT - requires human review",
    ]
    if len(entries) == 0:
        note_lines.append("NOTE: Zero entries extracted from this file.")
    note_text = "\n".join(note_lines)

    with open(NOTES_DIR / f"{stem}.txt", "w") as f:
        f.write(note_text + "\n")

    return len(entries), len(bioes_sentences), note_text


def main():
    files = sorted(BATCH_DIR.glob("*.extracted.json"))
    if not files:
        print("No .extracted.json files found!")
        sys.exit(1)

    total_entries = 0
    total_bioes = 0

    for fpath in files:
        stem = stem_from_path(fpath)
        entry_count, bioes_count, _ = process_file(fpath)
        total_entries += entry_count
        total_bioes += bioes_count
        print(f"  {stem}: {entry_count} entries, {bioes_count} BIOES sentences")

    done_text = (
        f"Annotation drafts generated successfully.\n"
        f"Files processed: {len(files)}\n"
        f"Total entries: {total_entries}\n"
        f"Total BIOES sentences: {total_bioes}\n"
        f"Generated: {DATE}\n"
    )
    with open(Path("data/annotations/cli_drafts/DONE.txt"), "w") as f:
        f.write(done_text)

    print(f"\nDone: {len(files)} files, {total_entries} entries, {total_bioes} BIOES sentences")


if __name__ == "__main__":
    main()
