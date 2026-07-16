#!/usr/bin/env python3
"""Intake script for new tender PDFs/XLSXs.

Usage:
    python3 scripts/intake_tender.py <path> [--source SOURCE] [--client CLIENT]

Path may be a single file or a directory (scanned recursively for .pdf/.xlsx/.xls).
Each file is:
  1. Deduplicated by SHA-256 against data/real_rfqs/INTAKE_MANIFEST.csv
  2. Copied to data/incoming/ (if not already there)
  3. Run through the pipeline to produce a DRAFT annotation
  4. Recorded in the manifest with provenance

Draft annotations are NEVER auto-marked human_verified.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


INTAKE_DIR = Path("data/incoming")
ANNOTATIONS_DRAFT_DIR = Path("data/annotations/draft")
MANIFEST_PATH = Path("data/real_rfqs/INTAKE_MANIFEST.csv")


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: Path) -> set[str]:
    """Load existing SHA-256 hashes from manifest."""
    if not path.exists():
        return set()
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return {row["sha256"] for row in reader if row.get("sha256")}


def append_manifest(path: Path, row: dict[str, str]) -> None:
    """Append a row to the manifest CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sha256",
        "filename",
        "doc_id",
        "source",
        "client",
        "date",
        "pages",
        "draft_entities",
        "status",
        "annotator",
        "review_date",
    ]
    exists = path.exists()
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in fieldnames})


def tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenization."""
    tokens = []
    for word in text.split():
        parts = re.findall(r"\w+|[^\w\s]", word)
        tokens.extend(parts)
    return tokens


def _normalize_entity_type(typ: object) -> str:
    """Return upper-case entity type string, handling Enum, str, etc."""
    if typ is None:
        return "MATERIAL"
    if hasattr(typ, "value"):
        val = typ.value
        return str(val).upper() if val else "MATERIAL"
    s = str(typ).strip()
    # strip possible "EntityType.FOO" or module prefix
    if "." in s:
        s = s.rsplit(".", 1)[-1]
    return s.upper() or "MATERIAL"


def _find_span_for_text(tokens: list[str], search_text: str) -> tuple[int, int] | None:
    """Locate the token span for a search phrase (best-effort, first match)."""
    if not search_text or not tokens:
        return None
    search_tokens = tokenize(search_text)
    if not search_tokens:
        return None
    n = len(search_tokens)
    for i in range(len(tokens) - n + 1):
        if tokens[i : i + n] == search_tokens:
            return (i, i + n)
    return None


def _suggest_entities(text: str) -> list[dict]:
    """Suggest entity spans using simple gazetteer + regex heuristics.

    This is a DRAFT pre-annotation — every span must be reviewed.
    """
    entities: list[dict] = []
    tokens = tokenize(text)

    # Quantity heuristic: standalone numbers
    qty_re = re.compile(r"^[\d,]+(?:\.\d+)?$")
    # Unit heuristic: known unit strings
    from config.constants import CANONICAL_UNITS

    unit_set = set(CANONICAL_UNITS.keys())
    # Dimension heuristic: e.g. "100mm", "25 mm dia"
    dim_re = re.compile(r"\b\d+\s*mm\b|\b\d+\s*mm\s+dia\b|\b\d+\s*mm\s*thick\b", re.IGNORECASE)

    i = 0
    while i < len(tokens):
        tok = tokens[i]

        # DIMENSION
        dim_match = dim_re.match(tok)
        if dim_match:
            j = i + 1
            while j < len(tokens) and tokens[j].lower() in {"dia", "thick", "x", "mm"}:
                j += 1
            entities.append(
                {
                    "text": " ".join(tokens[i:j]),
                    "type": "DIMENSION",
                    "start": i,
                    "end": j,
                    "source": "AUTO",
                }
            )
            i = j
            continue

        # QUANTITY
        if qty_re.match(tok.replace(",", "")):
            entities.append(
                {
                    "text": tok,
                    "type": "QUANTITY",
                    "start": i,
                    "end": i + 1,
                    "source": "AUTO",
                }
            )
            i += 1
            continue

        # UNIT
        if tok.lower() in unit_set or tok.lower().rstrip(".") in unit_set:
            entities.append(
                {
                    "text": tok,
                    "type": "UNIT",
                    "start": i,
                    "end": i + 1,
                    "source": "AUTO",
                }
            )
            i += 1
            continue

        i += 1

    return entities


def _entities_to_bioes(tokens: list[str], entities: list[dict]) -> list[str]:
    """Convert entity spans to BIOES tags."""
    tags = ["O"] * len(tokens)
    for ent in entities:
        s, e = ent["start"], ent["end"]
        if s >= len(tags) or e > len(tags):
            continue
        typ = ent["type"]
        length = e - s
        if length == 1:
            tags[s] = f"S-{typ}"
        else:
            tags[s] = f"B-{typ}"
            for k in range(s + 1, e - 1):
                tags[k] = f"I-{typ}"
            tags[e - 1] = f"E-{typ}"
    return tags


def _pipeline_extract(file_path: Path) -> dict:
    """Run the pipeline on a file and return raw text + draft entities."""
    from src.pipeline import Pipeline

    pipeline = Pipeline()
    result = pipeline.run(str(file_path))

    # Build a simple text representation from BOQ items + pages
    lines: list[str] = []
    for item in result.boq_items:
        lines.append(f"{item.material} {item.quantity} {item.unit}")
    text = "\n".join(lines)

    tokens = tokenize(text)
    # Use both pipeline NER entities (relocated if needed) and heuristic suggesters.
    # CRITICAL: only include entities whose (start, end) are valid token indices for *this* tokens list.
    # Pipeline spans come from full-doc text; we relocate by text match when possible.
    entities: list[dict] = []
    seen_spans: set[tuple[int, int]] = set()

    # Add pipeline entities if available (filter/relocate spans to summary tokens)
    for ent in getattr(result, "entities", []):
        raw_text = getattr(ent, "text", "") or ""
        s = getattr(ent, "start", 0)
        e = getattr(ent, "end", 0)
        typ = _normalize_entity_type(getattr(ent, "type", "MATERIAL"))

        # If original indices are valid for our token list, use them; else try relocate
        if not (0 <= s < e <= len(tokens)):
            found = _find_span_for_text(tokens, raw_text)
            if found:
                s, e = found
            else:
                continue  # cannot map reliably; skip (prevents OOB garbage in draft)
        span = (s, e)
        if span in seen_spans:
            continue
        seen_spans.add(span)
        entities.append(
            {
                "text": raw_text,
                "type": typ,
                "start": s,
                "end": e,
                "source": "AUTO",
            }
        )

    # Add heuristic suggestions for text not already covered
    suggested = _suggest_entities(text)
    for ent in suggested:
        span = (ent["start"], ent["end"])
        if span not in seen_spans:
            seen_spans.add(span)
            entities.append(ent)

    # Sort by start position
    entities.sort(key=lambda e: (e["start"], e["end"]))
    ner_tags = _entities_to_bioes(tokens, entities)

    return {
        "tokens": tokens,
        "ner_tags": ner_tags,
        "entities": entities,
        "relations": [],
        "text": text,
        "boq_item_count": len(result.boq_items),
        "pages_processed": result.metadata.pages_processed if result.metadata else 0,
    }


def process_file(
    file_path: Path,
    existing_shas: set[str],
    source: str,
    client: str,
) -> dict | None:
    """Process a single file: dedup, run pipeline, save draft."""
    sha = sha256_file(file_path)
    if sha in existing_shas:
        print(f"  SKIP (duplicate): {file_path.name}")
        return None

    print(f"  Processing: {file_path.name}")

    # Copy to incoming dir
    dest = INTAKE_DIR / file_path.name
    INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        shutil.copy2(file_path, dest)

    # Run pipeline
    extracted = _pipeline_extract(dest)

    # Build doc_id
    doc_id = dest.stem
    safe_doc_id = re.sub(r"[^\w\-]", "_", doc_id)[:80]

    # Save draft annotation
    ANNOTATIONS_DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    draft_path = ANNOTATIONS_DRAFT_DIR / f"{safe_doc_id}.json"
    annotation = {
        "doc_id": safe_doc_id,
        "source_file": dest.name,
        "sha256": sha,
        "tokens": extracted["tokens"],
        "ner_tags": extracted["ner_tags"],
        "entities": extracted["entities"],
        "relations": extracted["relations"],
        "metadata": {
            "status": "draft-needs-review",
            "annotator": "auto-pipeline",
            "date": datetime.now(UTC).isoformat(),
            "source": source,
            "client": client,
            "pages_processed": extracted["pages_processed"],
            "boq_items": extracted["boq_item_count"],
            "provenance": {
                "original_path": str(file_path),
                "incoming_path": str(dest),
            },
        },
    }
    with open(draft_path, "w") as f:
        json.dump(annotation, f, indent=2)

    # Record in manifest
    manifest_row = {
        "sha256": sha,
        "filename": dest.name,
        "doc_id": safe_doc_id,
        "source": source,
        "client": client,
        "date": datetime.now(UTC).isoformat(),
        "pages": str(extracted["pages_processed"]),
        "draft_entities": str(len(extracted["entities"])),
        "status": "draft-needs-review",
        "annotator": "auto-pipeline",
        "review_date": "",
    }
    append_manifest(MANIFEST_PATH, manifest_row)

    print(f"    → Draft saved: {draft_path}")
    print(f"    → Entities: {len(extracted['entities'])}, BOQ items: {extracted['boq_item_count']}")
    return manifest_row


def main() -> int:
    parser = argparse.ArgumentParser(description="Intake tender PDFs/XLSXs")
    parser.add_argument("path", help="File or directory to intake")
    parser.add_argument("--source", default="unknown", help="Source of the tender (e.g. 'sales', 'jineth')")
    parser.add_argument("--client", default="unknown", help="Client name")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"Path not found: {target}")
        return 1

    existing_shas = load_manifest(MANIFEST_PATH)
    print(f"Manifest has {len(existing_shas)} existing entries")

    files: list[Path] = []
    if target.is_dir():
        for ext in ("*.pdf", "*.xlsx", "*.xls"):
            files.extend(target.rglob(ext))
    else:
        if target.suffix.lower() in (".pdf", ".xlsx", ".xls"):
            files.append(target)
        else:
            print(f"Unsupported file type: {target.suffix}")
            return 1

    if not files:
        print("No PDF/XLSX files found.")
        return 0

    print(f"Found {len(files)} file(s) to process")
    processed = 0
    skipped = 0
    for f in sorted(files):
        result = process_file(f, existing_shas, args.source, args.client)
        if result:
            processed += 1
            existing_shas.add(result["sha256"])
        else:
            skipped += 1

    print(f"\nDone: {processed} processed, {skipped} skipped (duplicates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
