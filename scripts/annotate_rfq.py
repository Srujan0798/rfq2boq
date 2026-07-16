#!/usr/bin/env python3
"""Annotation CLI tool for marking BOQ items in RFQ PDFs/XLSXs.

Reads a PDF or XLSX file, extracts text, and lets you annotate
BOQ items by marking spans as MATERIAL, QUANTITY, UNIT, etc.

Usage:
    python3 scripts/annotate_rfq.py <file_path> [--output <output.json>]
    python3 scripts/annotate_rfq.py data/real_rfqs/additional_real/rfq_building_001.pdf
    python3 scripts/annotate_rfq.py data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx

Output format: JSON with tokens + BIOES tags (matches existing gold format).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest.pdf_extractor import PDFExtractor
from src.ingest.xlsx_parser import XLSXParser

# Entity types from config.constants
ENTITY_TYPES = ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """Extract text from PDF, return list of {page, text, lines}."""
    extractor = PDFExtractor()
    doc = extractor.extract(file_path, max_pages=100)
    pages = []
    for page in doc.pages:
        lines = page.text.split("\n")
        pages.append(
            {
                "page": page.page_number,
                "text": page.text,
                "lines": lines,
            }
        )
    return pages


def extract_text_from_xlsx(file_path: str) -> list[dict]:
    """Extract text from XLSX, return list of {sheet, text, lines}."""
    parser = XLSXParser()
    result = parser.parse(file_path)
    pages = []
    for sheet in result.sheets:
        lines = []
        for row in sheet.rows:
            row_text = " | ".join(str(cell) for cell in row if cell)
            if row_text.strip():
                lines.append(row_text)
        pages.append(
            {
                "page": sheet.name,
                "text": "\n".join(lines),
                "lines": lines,
            }
        )
    return pages


def tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenization."""
    tokens = []
    for word in text.split():
        # Split punctuation from words
        parts = re.findall(r"\w+|[^\w\s]", word)
        tokens.extend(parts)
    return tokens


def annotate_page(page_data: dict) -> list[dict]:
    """Interactive annotation for a single page."""
    annotations = []
    lines = page_data["lines"]
    page_num = page_data["page"]

    print(f"\n{'=' * 70}")
    print(f"PAGE {page_num}")
    print(f"{'=' * 70}")

    for i, line in enumerate(lines):
        if not line.strip():
            continue
        print(f"  [{i:3d}] {line[:100]}")

    print("\nCommands:")
    print("  a <line_num> <entity_type>  — Annotate line as entity")
    print("  s <line_num> <end_line> <entity_type>  — Annotate span of lines")
    print("  d <index>  — Delete annotation")
    print("  l  — List current annotations")
    print("  n  — Next page (finish this page)")
    print("  q  — Quit and save")

    while True:
        try:
            cmd = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not cmd:
            continue

        parts = cmd.split()
        action = parts[0]

        if action == "n":
            break
        elif action == "q":
            return None  # Signal to quit
        elif action == "l":
            for idx, ann in enumerate(annotations):
                print(
                    f"  {idx}: line {ann['start_line']}-{ann['end_line']} "
                    f"as {ann['entity_type']}: {ann['text'][:50]}..."
                )
        elif action == "d" and len(parts) >= 2:
            try:
                idx = int(parts[1])
                if 0 <= idx < len(annotations):
                    removed = annotations.pop(idx)
                    print(f"  Deleted: {removed['entity_type']}: {removed['text'][:30]}...")
            except ValueError:
                print("  Invalid index")
        elif action == "a" and len(parts) >= 3:
            try:
                line_num = int(parts[1])
                entity_type = parts[2].upper()
                if entity_type not in ENTITY_TYPES:
                    print(f"  Invalid entity type. Use: {', '.join(ENTITY_TYPES)}")
                    continue
                if line_num < 0 or line_num >= len(lines):
                    print(f"  Invalid line number (0-{len(lines)-1})")
                    continue
                text = lines[line_num]
                annotations.append(
                    {
                        "start_line": line_num,
                        "end_line": line_num,
                        "entity_type": entity_type,
                        "text": text.strip(),
                    }
                )
                print(f"  Annotated: {entity_type}: {text[:50]}...")
            except ValueError:
                print("  Usage: a <line_num> <entity_type>")
        elif action == "s" and len(parts) >= 4:
            try:
                start = int(parts[1])
                end = int(parts[2])
                entity_type = parts[3].upper()
                if entity_type not in ENTITY_TYPES:
                    print(f"  Invalid entity type. Use: {', '.join(ENTITY_TYPES)}")
                    continue
                if start < 0 or end >= len(lines) or start > end:
                    print(f"  Invalid line range (0-{len(lines)-1})")
                    continue
                text = "\n".join(lines[start : end + 1])
                annotations.append(
                    {
                        "start_line": start,
                        "end_line": end,
                        "entity_type": entity_type,
                        "text": text.strip(),
                    }
                )
                print(f"  Annotated span: {entity_type}: {text[:50]}...")
            except ValueError:
                print("  Usage: s <start_line> <end_line> <entity_type>")
        else:
            print(f"  Unknown command: {cmd}")

    return annotations


def build_bioes_tokens(pages: list[dict], all_annotations: list[dict]) -> dict:
    """Build BIOES-tagged tokens from annotations."""
    all_tokens = []
    all_tags = []
    entities = []

    for page_data in pages:
        page_num = page_data["page"]
        page_annotations = [a for a in all_annotations if a["page"] == page_num]

        for line_idx, line in enumerate(page_data["lines"]):
            if not line.strip():
                continue

            tokens = tokenize(line)
            line_tags = ["O"] * len(tokens)

            # Find annotations that cover this line
            for ann in page_annotations:
                if ann["start_line"] <= line_idx <= ann["end_line"]:
                    # Mark all tokens in this line with the entity type
                    for i in range(len(line_tags)):
                        if line_tags[i] == "O":
                            if i == 0:
                                line_tags[i] = f"B-{ann['entity_type']}"
                            else:
                                line_tags[i] = f"I-{ann['entity_type']}"

            all_tokens.extend(tokens)
            all_tags.extend(line_tags)

    # Convert B/I to proper BIOES
    final_tags = []
    for i, tag in enumerate(all_tags):
        if tag.startswith("B-"):
            # Check if next tag is I- of same type
            if i + 1 < len(all_tags) and all_tags[i + 1] == tag:
                final_tags.append(tag)  # B- stays as B-
            else:
                final_tags.append(tag.replace("B-", "S-"))  # Single token -> S-
        elif tag.startswith("I-"):
            # Check if next tag is I- of same type
            if i + 1 < len(all_tags) and all_tags[i + 1] == tag:
                final_tags.append(tag)  # I- stays as I-
            else:
                final_tags.append(tag.replace("I-", "E-"))  # Last in span -> E-
        else:
            final_tags.append(tag)

    # Extract entity spans
    current_entity = None
    current_start = None
    for i, (token, tag) in enumerate(zip(all_tokens, final_tags, strict=False)):
        if tag.startswith("S-"):
            entity_type = tag[2:]
            entities.append(
                {
                    "text": token,
                    "type": entity_type,
                    "start": i,
                    "end": i + 1,
                    "source": "HUMAN",
                }
            )
        elif tag.startswith("B-"):
            current_entity = tag[2:]
            current_start = i
        elif tag.startswith("E-") and current_entity:
            entities.append(
                {
                    "text": " ".join(all_tokens[current_start : i + 1]),
                    "type": current_entity,
                    "start": current_start,
                    "end": i + 1,
                    "source": "HUMAN",
                }
            )
            current_entity = None
            current_start = None

    return {
        "tokens": all_tokens,
        "ner_tags": final_tags,
        "entities": entities,
    }


def main():
    parser = argparse.ArgumentParser(description="Annotate BOQ items in RFQ files")
    parser.add_argument("file", help="PDF or XLSX file to annotate")
    parser.add_argument("--output", "-o", help="Output JSON path")
    parser.add_argument("--doc-id", help="Document ID for the annotation")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return 1

    # Extract text
    print(f"Extracting text from {file_path}...")
    if file_path.suffix.lower() in (".pdf",):
        pages = extract_text_from_pdf(str(file_path))
    elif file_path.suffix.lower() in (".xlsx", ".xls"):
        pages = extract_text_from_xlsx(str(file_path))
    else:
        print(f"Unsupported file type: {file_path.suffix}")
        return 1

    print(f"Found {len(pages)} pages")

    # Annotate each page
    all_annotations = []
    for page_data in pages:
        result = annotate_page(page_data)
        if result is None:
            # User quit
            break
        for ann in result:
            ann["page"] = page_data["page"]
        all_annotations.extend(result)

    if not all_annotations:
        print("No annotations made.")
        return 0

    # Build BIOES tokens
    bioes_data = build_bioes_tokens(pages, all_annotations)

    # Create output
    doc_id = args.doc_id or file_path.stem
    output = {
        "doc_id": doc_id,
        "source_file": file_path.name,
        "tokens": bioes_data["tokens"],
        "ner_tags": bioes_data["ner_tags"],
        "entities": bioes_data["entities"],
        "relations": [],
        "metadata": {
            "annotator": "human-cli",
            "source": str(file_path),
            "pages": len(pages),
            "annotations": len(all_annotations),
        },
    }

    # Save
    output_path = Path(args.output) if args.output else Path(f"data/real_rfqs/annotations/{doc_id}.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(all_annotations)} annotations to {output_path}")
    print(f"Tokens: {len(bioes_data['tokens'])}, Entities: {len(bioes_data['entities'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
