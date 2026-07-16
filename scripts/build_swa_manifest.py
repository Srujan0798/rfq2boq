#!/usr/bin/env python3
"""Build data/real_rfqs/swa_enquiries/manifest.csv from the filesystem.

The manifest catalogs every real source file in the 10 SWA enquiry folders,
with id, client, filename, type, and SHA256. It is regenerated from disk on
each run so the hashes and sizes always match the actual files.

Run from repo root:
    python3 scripts/build_swa_manifest.py
"""

from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SWA_DIR = REPO_ROOT / "data" / "real_rfqs" / "swa_enquiries"
MANIFEST_CSV = SWA_DIR / "manifest.csv"

CLIENT_MAP: dict[str, str] = {
    "01_gsecl_wanakbori_tmd8": "GSECL Wanakbori",
    "02_isro_vssc": "ISRO VSSC",
    "03_zydus_matoda_osd": "Zydus Pharma Matoda",
    "04_adani": "Adani",
    "05_zydus_animal_pharmez": "Zydus Animal Health",
    "06_avante_kirloskar_pune": "Avante Spaces / Kirloskar Pune",
    "07_grew_solar_narmadapuram": "Grew Solar Narmadapuram",
    "08_sael": "SAEL",
    "09_gem_bid_7439924": "GeM Bid 7439924",
    "10_gem_bid_7552777": "GeM Bid 7552777",
}

SKIP_BASENAMES = {"manifest.csv", "MANIFEST.md", "README.md", "README.txt"}
SOURCE_EXTS = {".pdf", ".xlsx", ".docx"}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for eid in sorted(os.listdir(SWA_DIR)):
        sub = SWA_DIR / eid
        if not sub.is_dir():
            continue
        client = CLIENT_MAP.get(eid, eid)
        for entry in sorted(sub.iterdir()):
            if not entry.is_file():
                continue
            if entry.name in SKIP_BASENAMES:
                continue
            ext = entry.suffix.lower()
            if ext not in SOURCE_EXTS:
                continue
            rows.append(
                {
                    "id": eid,
                    "client": client,
                    "filename": entry.name,
                    "type": ext.lstrip("."),
                    "SHA": sha256_of(entry),
                }
            )
    return rows


def main() -> None:
    rows = collect_rows()
    with open(MANIFEST_CSV, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "client", "filename", "type", "SHA"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"manifest.csv: {len(rows)} entries, written to {MANIFEST_CSV.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
