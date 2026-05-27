#!/usr/bin/env python3
"""Build `data/real_rfqs/annotations/manifest.csv` from on-disk PDFs + manifest.json stats."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

RAW_DIR = Path("data/real_rfqs/raw")
META_PATH = RAW_DIR.parent / "manifest.json"
OUT_PATH = Path("data/real_rfqs/annotations/manifest.csv")


def _iter_pdf_paths(raw_dir: Path) -> list[Path]:
    paths: list[Path] = []
    paths.extend(raw_dir.glob("*.pdf"))
    for sub in sorted(raw_dir.iterdir()):
        if sub.is_dir():
            paths.extend(sorted(sub.glob("*.pdf")))
    return sorted(paths, key=lambda p: str(p.relative_to(raw_dir)))


def main() -> None:
    if not META_PATH.exists():
        print(f"Missing {META_PATH} — run: python scripts/collect_real_rfqs.py")
        sys.exit(1)

    with open(META_PATH, encoding="utf-8") as f:
        meta = json.load(f)
    by_basename = {entry["filename"]: entry for entry in meta.get("files", [])}

    rows: list[dict[str, str | float | bool]] = []
    for pdf_path in _iter_pdf_paths(RAW_DIR):
        if pdf_path.name in ("manifest.json", "metadata.json"):
            continue
        rel = pdf_path.relative_to(RAW_DIR).as_posix()
        base = pdf_path.name
        fi = by_basename.get(base, {})
        is_real = bool(fi.get("is_real", False))
        cat = fi.get("category", "unknown")
        source = cat if is_real else "synthetic"

        h = hashlib.sha256()
        with open(pdf_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        s = pdf_path.stat()

        rows.append({
            "filename": rel,
            "source": source,
            "file_size_kb": round(s.st_size / 1024, 1),
            "sha256": h.hexdigest(),
            "pages": fi.get("pages", 0),
            "chars": fi.get("chars", 0),
            "is_real": is_real,
            "is_scanned": fi.get("is_scanned", False),
        })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["filename", "source", "file_size_kb", "sha256", "pages", "chars", "is_real", "is_scanned"],
        )
        writer.writeheader()
        writer.writerows(rows)

    real = sum(1 for r in rows if r["is_real"])
    print(f"{OUT_PATH}: {len(rows)} PDFs ({real} real), saved")


if __name__ == "__main__":
    main()
