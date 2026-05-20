#!/usr/bin/env python3
import csv
import hashlib
import json
from pathlib import Path

raw_dir = Path("data/real_rfqs/raw")
with open(raw_dir.parent / "manifest.json") as f:
    m = json.load(f)
file_list = m["files"]

rows = []
for pdf_path in sorted(raw_dir.glob("*.pdf")):
    if pdf_path.name in ("manifest.json", "metadata.json"):
        continue
    s = pdf_path.stat()
    h = hashlib.sha256()
    with open(pdf_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)

    fi = next((f for f in file_list if f["filename"] == pdf_path.name), {})
    rows.append({
        "filename": pdf_path.name,
        "source": fi.get("category", "unknown"),
        "file_size_kb": round(s.st_size / 1024, 1),
        "sha256": h.hexdigest(),
        "pages": fi.get("pages", 0),
        "chars": fi.get("chars", 0),
        "is_real": fi.get("is_real", False),
        "is_scanned": fi.get("is_scanned", False),
    })

with open(raw_dir / "manifest.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["filename", "source", "file_size_kb", "sha256", "pages", "chars", "is_real", "is_scanned"],
    )
    writer.writeheader()
    writer.writerows(rows)

real = sum(1 for r in rows if r["is_real"])
print(f"manifest.csv: {len(rows)} PDFs ({real} real), saved")
