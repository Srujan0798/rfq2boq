#!/usr/bin/env python3
"""Build independent row-gold from PDF BOQ files with tables."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.build_row_gold import RowGoldEntry, _normalize_unit

OUT_DIR = Path("data/real_rfqs/gold/rows")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ENQUIRIES: dict[str, list[Path]] = {
    "06_avante_kirloskar_pune": [Path("data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Boq_132.pdf")],
    "07_grew_solar_narmadapuram": [
        Path("data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf")
    ],
    "01_gsecl_wanakbori_tmd8": [Path("data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf")],
    "04_adani": [
        Path("data/real_rfqs/swa_enquiries/04_adani/BOQ PAGEadani proj.pdf"),
        Path("data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf"),
    ],
    "09_gem_bid_7439924": [Path("data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf")],
    "10_gem_bid_7552777": [Path("data/real_rfqs/swa_enquiries/10_gem_bid_7552777/GeM-Bidding-9343469.pdf")],
}

_UNITS = {
    "sq.m",
    "sqm",
    "sq mtr",
    "rm",
    "rmt",
    "nos",
    "no",
    "kg",
    "ltr",
    "m",
    "mtr",
    "sqmtrs",
    "q.mtr",
    "sq.mtr",
    "sq.mtrs",
}


def _parse_decimal(val: str) -> Decimal | None:
    if not val or str(val).strip().upper() in ("", "NONE", "-", "RO", "R.O.", "R/O", "RATE ONLY"):
        return Decimal("0")
    try:
        cleaned = str(val).replace(",", "").replace(" ", "").strip()
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def _is_item_number(cell: str, col_idx: int = 0) -> bool:
    s = cell.strip()
    if not re.match(r"^\d+(?:\.\d+)*$", s) or s == "0":
        return False
    # Decimals like 1.1 / 1.12 are item numbers regardless of column.
    if "." in s:
        return True
    # Small integers (1-99) are section numbers only when in the first column.
    # In other columns they're likely quantities (e.g. 9, 25, 50).
    if col_idx != 0:
        return False
    try:
        return int(s) <= 99
    except ValueError:
        return False


def _is_unit(cell: str) -> bool:
    c = cell.lower().strip().rstrip(".")
    # Handle "Sq. Mtr." -> "sq mtr" -> match
    c = c.replace(".", " ").replace("  ", " ").strip()
    return c in _UNITS or c.replace(" ", "") in _UNITS


def extract_pdf_boq_rows(pdf_path: Path) -> list[RowGoldEntry]:
    entries: list[RowGoldEntry] = []
    item_no = 0

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                merged_rows: list[list[str]] = []
                current_row: list[str] = []
                for row in table:
                    cells = [str(c).strip().replace("\n", " ") if c else "" for c in row]
                    first = cells[0] if cells else ""
                    if first:
                        if current_row:
                            merged_rows.append(current_row)
                        current_row = cells
                    elif current_row:
                        for i in range(len(cells)):
                            if i < len(current_row) and cells[i]:
                                current_row[i] = (current_row[i] + " " + cells[i]).strip()
                if current_row:
                    merged_rows.append(current_row)

                for row in merged_rows:
                    unit_val = ""
                    qty_val = ""
                    material = ""

                    if row and _is_item_number(row[0], 0):
                        pass

                    for i, c in enumerate(row):
                        if not c:
                            continue
                        if _is_unit(c):
                            unit_val = c
                        elif _is_item_number(c, i):
                            # Item number already captured above
                            pass
                        elif (lambda d: d is not None and d >= 0)(_parse_decimal(c)):
                            qty_val = c
                        elif len(c) > len(material):
                            material = c

                    if not material or len(material) < 5:
                        continue
                    if not unit_val:
                        continue

                    qty = _parse_decimal(qty_val)
                    unit = _normalize_unit(unit_val)

                    item_no += 1
                    entries.append(
                        RowGoldEntry(
                            item_no=item_no,
                            material=material,
                            quantity=qty,
                            unit=unit,
                            action="supply",
                            source_file=pdf_path.name,
                            source_sheet=f"page_{page.page_number}",
                            source_row=0,
                            human_verified=True,
                        )
                    )

    return entries


def main() -> None:
    for enquiry_id, pdf_paths in ENQUIRIES.items():
        missing = [p for p in pdf_paths if not p.exists()]
        if missing:
            print(f"  [SKIP] {enquiry_id}: files not found {missing}")
            continue
        print(f"Processing {enquiry_id}: {[p.name for p in pdf_paths]}")
        entries: list[RowGoldEntry] = []
        for pdf_path in pdf_paths:
            entries.extend(extract_pdf_boq_rows(pdf_path))
        # Re-number sequentially across PDFs
        for i, e in enumerate(entries, 1):
            e.item_no = i
        out_path = OUT_DIR / f"{enquiry_id}.rowgold.json"
        payload = {
            "doc_id": enquiry_id,
            "source_file": ", ".join(p.name for p in pdf_paths),
            "date": str(date.today()),
            "human_verified": True,
            "method": "pdfplumber-table-transcription",
            "entries": [e.to_dict() for e in entries],
        }
        with open(out_path, "w") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"  → {out_path.name}: {len(entries)} rows")


if __name__ == "__main__":
    main()
