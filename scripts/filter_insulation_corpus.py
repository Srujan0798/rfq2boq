#!/usr/bin/env python3
"""Fast corpus filter: scan PDFs for insulation keywords using pdfplumber (1 page only)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

UNSEEN_DIR = Path("data/real_rfqs/additional_real")
OUTPUT = Path("docs/CORPUS_FILTER.md")

INSULATION_KEYWORDS = [
    "insulation",
    "insulating",
    "insulate",
    "thermal",
    "acoustic",
    "sound",
    "hvac",
    "duct",
    "ductwork",
    "pipe insulation",
    "mineral wool",
    "rock wool",
    "rockwool",
    "glass wool",
    "fiberglass",
    "elastomeric",
    "nitrile",
    "xlpe",
    "foam",
    "polyurethane",
    "foil faced",
    "foil-faced",
    "refractory",
    "ceramic fiber",
    "ceramic wool",
    "calcium silicate",
    "chilled water",
    "cold storage",
    "refrigeration",
    "is 8183",
    "is 9842",
    "astm c553",
]

HVAC_KEYWORDS = [
    "chiller",
    "cooling tower",
    "air handling unit",
    "ahu",
    "fan coil",
    "fcu",
    "vrv",
    "vrf",
    "mechanical",
    "plumbing",
    "fire fighting",
    "sprinkler",
    "pump",
    "valve",
    "damper",
]


def extract_text(pdf_path: Path) -> str:
    try:
        import pdfplumber

        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages[:2]:
                text = page.extract_text()
                if text:
                    return text.lower()
        return ""
    except Exception:
        return ""


def main():
    files = sorted([f for f in UNSEEN_DIR.rglob("*.pdf") if f.stat().st_size > 1000])
    print(f"Scanning {len(files)} PDFs...")

    insulation = []
    hvac = []
    other = []

    for i, pdf_path in enumerate(files, 1):
        rel = pdf_path.relative_to(UNSEEN_DIR)
        text = extract_text(pdf_path)
        ins = sum(1 for kw in INSULATION_KEYWORDS if kw in text)
        hv = sum(1 for kw in HVAC_KEYWORDS if kw in text)

        if ins >= 2:
            insulation.append((rel, ins, hv))
        elif hv >= 2:
            hvac.append((rel, ins, hv))
        else:
            other.append((rel, ins, hv))

        if i % 10 == 0:
            print(f"  [{i}/{len(files)}] done")

    print(f"\nInsulation: {len(insulation)}, HVAC: {len(hvac)}, Other: {len(other)}")

    with open(OUTPUT, "w") as f:
        f.write("# Corpus Filter Report\n\n")
        f.write(f"Scanned: {len(files)} PDFs\n\n")
        f.write("| Category | Count |\n|---|---|\n")
        f.write(f"| Insulation-domain | {len(insulation)} |\n")
        f.write(f"| HVAC adjacent | {len(hvac)} |\n")
        f.write(f"| Other | {len(other)} |\n\n")

        f.write("## Insulation Files\n\n")
        for rel, _ins, _hv in sorted(insulation, key=lambda x: -x[1]):
            f.write(f"- `{rel}` — score={_ins}\n")

        f.write("\n## HVAC Adjacent\n\n")
        for rel, _ins, hv in sorted(hvac, key=lambda x: -x[2]):
            f.write(f"- `{rel}` — score={hv}\n")

    print(f"Report: {OUTPUT}")


if __name__ == "__main__":
    main()
