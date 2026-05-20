#!/usr/bin/env python3
"""Generate annotations for all 4 real PDFs."""
import json
from pathlib import Path

import pymupdf

RAW = Path("data/real_rfqs/raw")
ANNOTATED = Path("data/real_rfqs/annotated")
ANNOTATED.mkdir(parents=True, exist_ok=True)

def extract_text(pdf_path):
    doc = pymupdf.open(str(pdf_path))
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def create_annotation(pdf_name, text, output_name):
    tokens = text.split()
    # Empty BIOES tags initially - NLP pipeline suggestions not used (slow)
    ner_tags = ["O"] * len(tokens)
    annotation = {
        "doc_id": pdf_name,
        "tokens": tokens,
        "ner_tags": ner_tags,
        "labels": ner_tags,
        "metadata": {
            "source_file": str(RAW / pdf_name),
            "pages_extracted": len(tokens.split("\f")) if "\f" in text else 1,
            "note": "Awaiting human annotation via annotate_helper.py"
        }
    }
    with open(output_name, "w") as f:
        json.dump(annotation, f, indent=2)
    print(f"Created {output_name.name}: {len(tokens)} tokens, {sum(1 for t in ner_tags if t != 'O')} tagged")

real_pdfs = [
    ("cpwd_Guidelines_for_Hassle_Free_Bid_Submission_1778959268.pdf", "cpwd_Guidelines"),
    ("delhi_pwd_Tender_1778958751.pdf", "delhi_pwd_Tender"),
    ("ireps_2724bb1eff78.pdf", "ireps_2724bb1eff78"),
    ("ireps_bc341034058b.pdf", "ireps_bc341034058b"),
]

for pdf_name, base_name in real_pdfs:
    pdf_path = RAW / pdf_name
    out_path = ANNOTATED / f"{base_name}.json"
    if not out_path.exists():
        text = extract_text(pdf_path)
        create_annotation(base_name, text, out_path)
    else:
        print(f"Skipping {out_path.name} (already exists)")

print("\nDone. Annotate with: python scripts/annotate_helper.py interactive <file>")
