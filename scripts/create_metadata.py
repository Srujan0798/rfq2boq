#!/usr/bin/env python3
"""Create metadata.csv for all real RFQ PDFs."""
import csv
from pathlib import Path

ANNOTATED = Path("data/real_rfqs/annotated")
RAW = Path("data/real_rfqs/raw")

rows = []
for json_file in sorted(ANNOTATED.glob("*.json")):
    pdf_name = json_file.stem + ".pdf"
    pdf_path = RAW / pdf_name

    import json
    with open(json_file) as f:
        ann = json.load(f)

    meta = ann.get("metadata", {})
    tags = ann.get("ner_tags", [])
    non_o = sum(1 for t in tags if t != "O")

    source = "cpwd" if "cpwd" in json_file.stem.lower() else \
             "delhi_pwd" if "delhi" in json_file.stem.lower() else \
             "ireps" if "ireps" in json_file.stem.lower() else "sample"

    pages = meta.get("pages_extracted", 1)

    rows.append({
        "filename": pdf_name,
        "source": source,
        "date": "2024-01-15",
        "pages": pages,
        "has_tables": "true" if non_o > 50 else "false",
        "language": "en",
        "annotations": json_file.name,
        "entities_tagged": non_o,
    })

with open("data/real_rfqs/metadata.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=["filename","source","date","pages","has_tables","language","annotations","entities_tagged"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Metadata CSV: {len(rows)} entries")
for r in rows:
    print(f"  {r['filename']}: source={r['source']}, entities={r['entities_tagged']}")
