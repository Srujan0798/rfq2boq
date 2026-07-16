#!/usr/bin/env python3
"""Derive truly independent row gold from PDF source using PyMuPDF (NOT pdfplumber).

The pipeline uses pdfplumber for table extraction. This script uses PyMuPDF (fitz)
for text extraction -- a completely different library -- to ensure the gold
is independent of pipeline extraction artifacts.

Output: data/real_rfqs/gold/rows/independent/<enquiry_id>.rowgold.json

Usage:
    python3 scripts/derive_independent_row_gold.py [--enquiry 01_gsecl]
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz  # PyMuPDF
from src.rules.units import normalize_unit

OUT_DIR = Path("data/real_rfqs/gold/rows/independent")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ENQUIRY_DIR = Path("data/real_rfqs/swa_enquiries")

PDF_ENQUIRIES: dict[str, list[str]] = {
    "01_gsecl_wanakbori_tmd8": ["01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf"],
    "04_adani": [
        "04_adani/BOQ PAGEadani proj.pdf",
        "04_adani/BOQ PAGE2adani proj.pdf",
    ],
    "06_avante_kirloskar_pune": ["06_avante_kirloskar_pune/Insulation Boq_132.pdf"],
    "07_grew_solar_narmadapuram": ["07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf"],
    "09_gem_bid_7439924": ["09_gem_bid_7439924/GeM-Bidding-9218026.pdf"],
    "10_gem_bid_7552777": ["10_gem_bid_7552777/GeM-Bidding-9343469.pdf"],
}

# Regex to find BOQ line items: number.xxx, material description, quantity, unit
BOQ_LINE_RE = re.compile(
    r"(?:(?:\d+(?:\.\d+)?)\s+)?"
    r"([A-Za-z][A-Za-z0-9\s,/\-–—&().]+?)"
    r"\s+(?:Sq\.?\s*[mM]\.?|sq\.?\s*[mM]\.?|Sqmtrs?|sqmtrs?|"
    r"sqm|Nos\.|nos\.|Rmt\.|rmt|RMT|kg|mtr|Mtr)"
    r"\s+(\d[\d,.]*)",
    re.IGNORECASE,
)

# Known BOQ action prefixes
ACTION_KWS = [
    "supply", "install", "supply and install", "supply & install",
    "furnish", "provide", "s.i.t.c", "laying", "fixing", "application",
    "supply, installation, testing and commissioning",
    "supply, installation, testing & commissioning",
    "supplying, installing and testing",
    "supply and installation",
    "supply & installation",
]

UNIT_RE = re.compile(r"(Sq\.?\s*[mM]\.?|sq\.?\s*[mM]\.?|Sqmtrs?|sqm|Nos\.|nos\.|Rmt\.|rmt|RMT|kg|mtr|Mtr)", re.IGNORECASE)

QTY_RE = re.compile(r"(\d[\d,.]*)")


def extract_action(desc: str) -> str:
    dl = desc.lower().strip()
    for kw in sorted(ACTION_KWS, key=len, reverse=True):
        if dl.startswith(kw):
            return kw
    return "supply"


def extract_lines_via_pymupdf(pdf_path: Path) -> list[dict]:
    """Extract BOQ line items from PDF using PyMuPDF (fitz) text extraction."""
    items: list[dict] = []
    seen_descriptions: set[str] = set()

    doc = fitz.open(str(pdf_path))
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        lines = text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Skip headers, page numbers, spec text
            if any(
                skip in line.lower()
                for skip in ["page ", "rfq no", "schedule", "description", "unit rate",
                            "offered", "sr. no", "bid number", "bid document", "document no",
                            "specification", "insulation shall", "material shall",
                            "thermal conductivity", "water absorption", "as per"]
            ) and (not any(c.isdigit() for c in line) or len(line) < 10):
                i += 1
                continue

            # Look for patterns like "description <unit> <qty>" or "item_no description <unit> <qty>"
            unit_match = UNIT_RE.search(line)
            if unit_match:
                unit_str = unit_match.group(1)
                unit_pos = unit_match.start()
                before_unit = line[:unit_pos].strip()

                # Find quantity after unit
                desc = before_unit
                after_unit = line[unit_match.end():].strip()
                qty_match = QTY_RE.search(after_unit) if after_unit else None
                if qty_match:
                    qty_str = qty_match.group(1)
                else:
                    # Check if qty is before unit (for "1600 Sq. meter" pattern)
                    before_qty = QTY_RE.findall(before_unit)
                    if before_qty:
                        qty_str = before_qty[-1]
                        desc = before_unit[: before_unit.rfind(qty_str)].strip()
                    else:
                        qty_str = "0"
                        desc = before_unit

                # Clean up description
                desc = desc.strip().rstrip(".,;:")
                if not desc or len(desc) < 5:
                    i += 1
                    continue

                # Skip purely numeric descriptions
                if desc.replace(".", "").replace(",", "").isdigit():
                    i += 1
                    continue

                # Deduplicate
                desc_key = desc.lower()[:60]
                if desc_key in seen_descriptions:
                    i += 1
                    continue
                seen_descriptions.add(desc_key)

                qty = Decimal(qty_str.replace(",", "")) if qty_str else Decimal("0")
                unit = normalize_unit(unit_str)

                items.append({
                    "material": desc,
                    "quantity": str(qty),
                    "unit": unit,
                    "action": extract_action(desc),
                    "source_page": page_num + 1,
                })
            i += 1

    doc.close()
    return items


def extract_gem_items(pdf_path: Path) -> list[dict]:
    """Extract item categories from GeM bid PDFs."""
    items: list[dict] = []
    doc = fitz.open(str(pdf_path))
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()

    # GeM bid documents list items in the "Item Category" field
    # Find the item description section
    item_section = re.search(
        r"(?:Item Category|वस्तु वर्णन|वव(cid:38)(cid:38)ततु ु (cid:39)(cid:39)णेणे ीी).*?\n(.*?)(?=\n\d+\s*/\s*\d+|$)",
        full_text,
        re.DOTALL | re.IGNORECASE,
    )
    if item_section:
        text = item_section.group(1)
        # Split by commas or bullet points
        parts = re.split(r"\s*[,]\s*", text)
        for part in parts:
            part = part.strip().strip(" ,.")
            if part and len(part) > 10 and "cid" not in part:
                qty_match = QTY_RE.search(part)
                qty = Decimal(qty_match.group(1).replace(",", "")) if qty_match else Decimal("0")
                items.append({
                    "material": part,
                    "quantity": str(qty),
                    "unit": "no.",
                    "action": "supply",
                    "source_page": 1,
                })
    else:
        # Fallback: find the bid details section with item names
        lines = full_text.split("\n")
        for line in lines:
            line = line.strip()
            if "Bonded mineral" in line.lower() or "Bonded Mineral" in line:
                qty_match = QTY_RE.search(line)
                qty = Decimal(qty_match.group(1).replace(",", "")) if qty_match else Decimal("0")
                desc = line.strip().rstrip(" ,.")
                if len(desc) > 15:
                    items.append({
                        "material": desc,
                        "quantity": str(qty),
                        "unit": "no.",
                        "action": "supply",
                        "source_page": 1,
                    })

    return items


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Derive independent row gold from PDFs using PyMuPDF")
    parser.add_argument("--enquiry", help="Specific enquiry ID (e.g. 01_gsecl_wanakbori_tmd8)")
    args = parser.parse_args()

    enquiries = PDF_ENQUIRIES
    if args.enquiry:
        if args.enquiry not in PDF_ENQUIRIES:
            print(f"Unknown enquiry: {args.enquiry}")
            print(f"Available: {', '.join(PDF_ENQUIRIES.keys())}")
            return 1
        enquiries = {args.enquiry: PDF_ENQUIRIES[args.enquiry]}

    print("=" * 70)
    print("INDEPENDENT ROW GOLD — PyMuPDF extraction (NOT pdfplumber)")
    print("=" * 70)

    for enquiry_id, pdf_rel_paths in enquiries.items():
        pdf_paths = [ENQUIRY_DIR / p for p in pdf_rel_paths]
        missing = [p for p in pdf_paths if not p.exists()]
        if missing:
            print(f"  [SKIP] {enquiry_id}: missing {missing}")
            continue

        all_items: list[dict] = []
        for pdf_path in pdf_paths:
            items = (
                extract_gem_items(pdf_path)
                if "gem" in enquiry_id.lower()
                else extract_lines_via_pymupdf(pdf_path)
            )
            all_items.extend(items)

        if not all_items:
            print(f"  [WARN] {enquiry_id}: no items extracted")
            continue

        # Build output
        entries = []
        for idx, item in enumerate(all_items, 1):
            entries.append({
                "item_no": idx,
                "material": item["material"],
                "quantity": item["quantity"],
                "unit": item["unit"],
                "action": item["action"],
                "source_file": ", ".join(p.name for p in pdf_paths),
                "source_sheet": f"page_{item.get('source_page', 1)}",
                "source_row": idx,
                "human_verified": False,
                "provenance": "pymupdf-text-extraction",
            })

        payload = {
            "doc_id": enquiry_id,
            "source_file": ", ".join(p.name for p in pdf_paths),
            "date": str(date.today()),
            "human_verified": False,
            "method": "pymupdf-independent-text-extraction",
            "entries": entries,
        }

        out_path = OUT_DIR / f"{enquiry_id}.rowgold.json"
        with open(out_path, "w") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"  {enquiry_id}: {len(entries)} items → {out_path}")

    print("\nDone. Compare with data/real_rfqs/gold/rows/*.rowgold.json to detect drift.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
