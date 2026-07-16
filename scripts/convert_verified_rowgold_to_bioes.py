#!/usr/bin/env python3
"""Convert verified rowgold files into BIOES NER training sentences.

Reads rowgold JSONs from data/real_rfqs/gold/rows/ where both the top-level
human_verified flag and the per-entry human_verified flag are true.

Each rowgold entry becomes one sentence record with tokens + BIOES ner_tags.
The sentence is built canonically as:
    [action] [material description] [quantity] [unit]
where tokens are tagged according to the verified field they came from.

Output: data/annotations/verified_from_rowgold/bioes/<doc_id>_<idx>.json
Also optionally mirrors to data/annotations/verified/ for downstream trainers.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


ROWGOLD_DIR = Path("data/real_rfqs/gold/rows")
OUTPUT_DIR = Path("data/annotations/verified_from_rowgold/bioes")
VERIFIED_MIRROR_DIR = Path("data/annotations/verified")

# Fields we accept as verified truth.
ENTITY_FIELDS = {"ACTION", "MATERIAL", "QUANTITY", "UNIT"}


def _tokenise(text: str) -> list[str]:
    """Whitespace tokeniser; preserves attached punctuation."""
    return text.strip().split()


def _field_to_bioes(tokens: list[str], entity_type: str) -> list[str]:
    """Tag all tokens in a field segment with BIOES tags for entity_type."""
    if not tokens:
        return []
    if len(tokens) == 1:
        return [f"S-{entity_type}"]
    tags = [f"B-{entity_type}"]
    for _ in tokens[1:-1]:
        tags.append(f"I-{entity_type}")
    tags.append(f"E-{entity_type}")
    return tags


def _normalise_action(action: object) -> str | None:
    """Return a clean action string or None."""
    if action is None:
        return None
    s = str(action).strip().lower()
    if not s or s == "none":
        return None
    return s


def _normalise_quantity(qty: object) -> str | None:
    """Return quantity as a string token or None if empty."""
    if qty is None:
        return None
    s = str(qty).strip().replace(",", "")
    if s == "" or s.lower() == "none":
        return None
    # Keep numeric-ish values including decimals.
    return s


def _normalise_unit(unit: object) -> str | None:
    """Return unit string or None if empty."""
    if unit is None:
        return None
    s = str(unit).strip()
    if s == "" or s.lower() == "none":
        return None
    return s


def _build_record(doc_id: str, source_file: str, rowgold_file: str, idx: int, entry: dict) -> dict | None:
    """Build one BIOES sentence record from a rowgold entry."""
    material_raw = entry.get("material")
    if not material_raw or not str(material_raw).strip():
        return None

    action = _normalise_action(entry.get("action"))
    qty = _normalise_quantity(entry.get("quantity"))
    unit = _normalise_unit(entry.get("unit"))

    tokens: list[str] = []
    tags: list[str] = []

    if action:
        act_tokens = _tokenise(action)
        tokens.extend(act_tokens)
        tags.extend(_field_to_bioes(act_tokens, "ACTION"))

    mat_tokens = _tokenise(str(material_raw))
    tokens.extend(mat_tokens)
    tags.extend(_field_to_bioes(mat_tokens, "MATERIAL"))

    if qty:
        qty_tokens = _tokenise(qty)
        tokens.extend(qty_tokens)
        tags.extend(_field_to_bioes(qty_tokens, "QUANTITY"))

    if unit:
        unit_tokens = _tokenise(unit)
        tokens.extend(unit_tokens)
        tags.extend(_field_to_bioes(unit_tokens, "UNIT"))

    if len(tokens) != len(tags):
        return None
    if not tokens:
        return None

    return {
        "doc_id": f"{doc_id}_{idx:03d}",
        "source_file": source_file,
        "tokens": tokens,
        "ner_tags": tags,
        "metadata": {
            "status": "human_verified",
            "source": "rowgold",
            "rowgold_file": rowgold_file,
            "row_idx": idx,
            "action": action,
            "quantity": qty,
            "unit": unit,
        },
    }


def convert_rowgold(rowgold_path: Path) -> list[dict]:
    """Convert one rowgold file into BIOES sentence records."""
    data = json.loads(rowgold_path.read_text())
    if not data.get("human_verified", False):
        return []

    doc_id = data.get("doc_id", rowgold_path.stem.replace(".rowgold", ""))
    source_file = data.get("source_file", "")
    records: list[dict] = []
    for idx, entry in enumerate(data.get("entries", [])):
        if not entry.get("human_verified", False):
            continue
        rec = _build_record(doc_id, source_file, rowgold_path.name, idx, entry)
        if rec:
            records.append(rec)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert verified rowgold to BIOES")
    parser.add_argument("--mirror-to-verified", action="store_true", help="Also write files to data/annotations/verified/")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Output directory")
    args = parser.parse_args()

    if not ROWGOLD_DIR.exists():
        print(f"ERROR: rowgold directory not found: {ROWGOLD_DIR}", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.mirror_to_verified:
        VERIFIED_MIRROR_DIR.mkdir(parents=True, exist_ok=True)

    all_records: list[dict] = []
    docs_with_records: set[str] = set()
    for path in sorted(ROWGOLD_DIR.glob("*.rowgold.json")):
        records = convert_rowgold(path)
        if records:
            all_records.extend(records)
            docs_with_records.add(path.name)
        for rec in records:
            out_path = args.output_dir / f"{rec['doc_id']}.json"
            out_path.write_text(json.dumps(rec, indent=2))
            if args.mirror_to_verified:
                mirror_path = VERIFIED_MIRROR_DIR / f"rowgold_{rec['doc_id']}.json"
                mirror_path.write_text(json.dumps(rec, indent=2))

    print(f"Verified rowgold files processed: {len(docs_with_records)}")
    print(f"Verified sentences written: {len(all_records)}")
    print(f"Output directory: {args.output_dir}")
    if args.mirror_to_verified:
        print(f"Mirrored to: {VERIFIED_MIRROR_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
