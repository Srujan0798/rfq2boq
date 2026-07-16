#!/usr/bin/env python3
"""Draft row-level gold extraction for the insulation_hvac BOQ reference PDFs.

ANTI-CHEAT: gold is derived ONLY from the BOQ reference PDFs themselves.
We NEVER run the pipeline on TENDER.pdf and call that gold. The gold is what
the supplier is supposed to quote against (the BOQ).

Inputs (any subset, passed via --pairs):
  data/real_rfqs/raw/insulation_hvac/boq_references/BOQ.pdf
  data/real_rfqs/raw/insulation_hvac/boq_references/BOQ - INSULATION.pdf
  data/real_rfqs/raw/insulation_hvac/boq_references/BOQ PAGE.pdf
  data/real_rfqs/raw/insulation_hvac/boq_references/BOQ PAGE (003).pdf
  data/real_rfqs/raw/insulation_hvac/boq_references/Copy of BOQ.pdf
  data/real_rfqs/raw/insulation_hvac/boq_references/Insulation Boq (1).pdf
  data/real_rfqs/raw/insulation_hvac/boq_references/Insulation Boq (2).pdf
  data/real_rfqs/raw/insulation_hvac/boq_references/BOQ- Insulation_Compliance.pdf
  data/real_rfqs/raw/insulation_hvac/boq_references/47_Pipe Insulation_BOQ Compliance.pdf

Outputs:
  data/real_rfqs/gold/rows/insul_NN_<slug>.rowgold.json

Each row = {item_no, material, quantity, unit, source, source_file, source_page,
            source_table, source_row, human_verified: false}.
Top-level: {doc_id, source_file, date, human_verified, method, gold_source, entries[]}.

Column detection is header-based (sniffs the first contiguous non-data block of
rows for keyword columns). This keeps the script layout-agnostic — no
`if filename ==` hacks. If a header is missing or unrecognisable, we fall back
to the canonical [item=0, material=1, unit=2, qty=3] order used by the original
insul_01/02 pair.

A row is included only if it has both a non-empty material/description AND a
parseable numeric quantity. Section-header rows with no quantity are dropped.
"RO" / "Rate Only" / non-numeric quantity cells are dropped (they carry no
quantity to verify against).

This is DRAFT gold. human_verified is False everywhere. A human must review
before promoting to eval gold (see Lane B1 acceptance criteria).
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pdfplumber

REPO_ROOT = Path(__file__).resolve().parent.parent
BOQ_DIR = REPO_ROOT / "data" / "real_rfqs" / "raw" / "insulation_hvac" / "boq_references"
GOLD_DIR = REPO_ROOT / "data" / "real_rfqs" / "gold" / "rows"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("draft_insulation_gold")


_QTY_WS_RE = re.compile(r"[\s,]+")
_TRAILING_ZEROS_RE = re.compile(r"^0+(?=\d)")
_PURE_NUMERIC_RE = re.compile(r"^\d+(?:\.\d+)?$")


def _normalize_quantity(raw: str | None) -> str | None:
    """Strip spaces/commas from a quantity cell so '2 00.00' -> '200.00'.

    Returns None if the cell is empty or not numeric. '0' is allowed.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    cleaned = _QTY_WS_RE.sub("", s)
    cleaned = cleaned.replace("\u00a0", "")
    if not _PURE_NUMERIC_RE.fullmatch(cleaned):
        return None
    if cleaned.startswith("0") and "." not in cleaned and len(cleaned) > 1:
        cleaned = _TRAILING_ZEROS_RE.sub("", cleaned) or "0"
    return cleaned


def _is_blank_row(cells: list[str | None]) -> bool:
    return all((c is None or str(c).strip() == "") for c in cells)


def _header_block_end(table: list[list[str | None]], max_look: int = 6) -> int:
    """Find the first row index where a data row begins.

    A "data row" is one with at least one pure-numeric cell. The rows above
    (banner + column labels) are treated as header context.

    Returns the number of rows in the leading header block (so callers can
    slice `table[header_end:]` for data).
    """
    for ri, raw_row in enumerate(table[:max_look]):
        if _is_blank_row(raw_row):
            continue
        cells = [str(c).strip() if c is not None else "" for c in raw_row]
        if any(_PURE_NUMERIC_RE.fullmatch(c) for c in cells if c):
            return ri
    return min(len(table), max_look)


_COLUMN_LABEL_KEYWORDS = (
    "qty",
    "quantity",
    "unit",
    "uom",
    "description",
    "material",
    "specification",
    " desc",
    "sr",
    "sl",
    "item",
    "code",
    "remark",
    "rate",
    "amount",
    "est",
    "reqd",
    "dely",
)


def _column_label_score(cell: str) -> int:
    """Score a cell by how column-label-like it is."""
    c = cell.lower()
    return sum(1 for k in _COLUMN_LABEL_KEYWORDS if k in c)


def _merge_header(table: list[list[str | None]], n: int) -> list[str]:
    """Merge the first n rows into a single per-column header string.

    For each column index, pick the cell that most resembles a column label
    (highest keyword score; tiebreak by later position so banner rows that
    appear above the actual header lose to the real header row).

    This handles:
      * Split headers (row0=Sl No/Description/Unit, row1=Revised QTY/wbs/Reply)
        in BOQ- Insulation_Compliance.pdf
      * Banner rows above the header (e.g. "MATERIA\nL / CONSTRUCTION /
        ENGINEERI\nNG" above "MAT.CODE / Sr No / DESCRIPTION / UNIT / CONTRACT
        QTY." in Copy of BOQ.pdf)
    """
    if n <= 0 or not table:
        return []
    max_cols = max((len(r) for r in table[:n]), default=0)
    merged: list[str] = []
    for ci in range(max_cols):
        candidates: list[tuple[int, str]] = []
        for ri in range(n):
            if ci < len(table[ri]) and table[ri][ci] is not None:
                v = str(table[ri][ci]).strip()
                if v:
                    candidates.append((ri, v))
        if not candidates:
            merged.append("")
            continue
        best_idx, best_cell = max(
            candidates,
            key=lambda x: (_column_label_score(x[1]), x[0]),
        )
        merged.append(best_cell)
    return merged


def detect_columns(merged_header: list[str]) -> dict[str, int]:
    """Detect item/material/unit/quantity column indices from a merged header.

    Returns default indices [0,1,2,3] for any column that can't be matched.

    Detection order matters: qty first so that headers containing "Qty" win
    over the item-like "Sr No" pattern; material before item so that
    "Item Description" is classified as material (its dominant keyword).
    """
    item_idx: int | None = None
    mat_idx: int | None = None
    unit_idx: int | None = None
    qty_idx: int | None = None

    for ci, raw in enumerate(merged_header):
        c = raw.lower()
        if qty_idx is None and ("qty" in c or "quantity" in c):
            qty_idx = ci
            continue
        if unit_idx is None and ("unit" in c or c == "uom"):
            unit_idx = ci
            continue
        if mat_idx is None and (
            "description" in c
            or "material" in c
            or " desc" in c
            or "specification" in c
            or "specification of work" in c
        ):
            mat_idx = ci
            continue
        if item_idx is None and (c.startswith("sr") or "sr no" in c or "sl no" in c or "item no" in c):
            item_idx = ci
            continue

    return {
        "item_no": item_idx if item_idx is not None else 0,
        "material": mat_idx if mat_idx is not None else 1,
        "unit": unit_idx if unit_idx is not None else 2,
        "quantity": qty_idx if qty_idx is not None else 3,
    }


@dataclass
class Row:
    item_no: str
    material: str
    quantity: str
    unit: str
    source_page: int
    source_table: int
    source_row: int


def extract_rows(pdf_path: Path) -> tuple[list[Row], dict[str, int]]:
    """Extract (rows, detected_columns) from a BOQ reference PDF."""
    rows: list[Row] = []
    detected_cols: dict[str, int] = {}
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_idx, page in enumerate(pdf.pages, 1):
            tables = page.extract_tables() or []
            for ti, table in enumerate(tables):
                if not table:
                    continue
                header_end = _header_block_end(table)
                merged = _merge_header(table, header_end)
                cols = detect_columns(merged)
                if ti == 0 and page_idx == 1:
                    detected_cols = cols

                max_idx = max(cols["item_no"], cols["material"], cols["unit"], cols["quantity"])
                for ri in range(header_end, len(table)):
                    raw_row = table[ri]
                    if _is_blank_row(raw_row):
                        continue
                    cells = [(str(c).strip() if c is not None else "") for c in raw_row]
                    if len(cells) <= max_idx:
                        continue

                    item_no = cells[cols["item_no"]]
                    material = cells[cols["material"]]
                    unit = cells[cols["unit"]] if cols["unit"] < len(cells) else ""
                    qty_raw = cells[cols["quantity"]] if cols["quantity"] < len(cells) else ""

                    qty = _normalize_quantity(qty_raw)
                    if qty is None:
                        continue

                    if not material:
                        continue

                    material_clean_lower = material.lower().strip()
                    if material_clean_lower.startswith("total"):
                        continue
                    if material_clean_lower.startswith("note"):
                        continue

                    if not item_no:
                        item_no = f"sub_r{ri}"

                    unit_clean = unit.replace("\n", " ").strip()
                    material_clean = " ".join(material.split())

                    rows.append(
                        Row(
                            item_no=item_no,
                            material=material_clean,
                            quantity=qty,
                            unit=unit_clean,
                            source_page=page_idx,
                            source_table=ti,
                            source_row=ri,
                        )
                    )
    return rows, detected_cols


def build_gold(doc_id: str, pdf_path: Path, source_label: str, rows: list[Row], detected_cols: dict[str, int]) -> dict:
    entries: list[dict] = []
    for r in rows:
        entries.append(
            {
                "item_no": r.item_no,
                "material": r.material,
                "quantity": r.quantity,
                "unit": r.unit,
                "source": source_label,
                "source_file": source_label,
                "source_page": r.source_page,
                "source_table": r.source_table,
                "source_row": r.source_row,
                "human_verified": False,
            }
        )
    return {
        "doc_id": doc_id,
        "source_file": source_label,
        "date": datetime.now().date().isoformat(),
        "human_verified": False,
        "method": "pdfplumber-table-transcription (DRAFT — needs human review)",
        "gold_source": str(pdf_path.relative_to(REPO_ROOT)),
        "detected_columns": detected_cols,
        "entries": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pairs",
        nargs="+",
        default=[
            "insul_01_tender:BOQ.pdf",
            "insul_02_swpl:BOQ - INSULATION.pdf",
        ],
        help="doc_id:pdf_filename pairs (relative to boq_references/)",
    )
    parser.add_argument("--boq-dir", type=Path, default=BOQ_DIR)
    parser.add_argument("--gold-dir", type=Path, default=GOLD_DIR)
    args = parser.parse_args()

    args.gold_dir.mkdir(parents=True, exist_ok=True)

    summary: list[dict] = []
    for pair in args.pairs:
        doc_id, fname = pair.split(":", 1)
        pdf_path = args.boq_dir / fname
        if not pdf_path.exists():
            log.error("Missing BOQ PDF: %s", pdf_path)
            return 2
        log.info("[%s] extracting rows from %s", doc_id, pdf_path.name)
        rows, cols = extract_rows(pdf_path)
        gold = build_gold(doc_id, pdf_path, f"boq_references/{fname}", rows, cols)
        out_path = args.gold_dir / f"{doc_id}.rowgold.json"
        out_path.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("  -> %s  rows=%d  cols=%s", out_path, len(rows), cols)
        summary.append(
            {
                "doc_id": doc_id,
                "source_pdf": str(pdf_path.relative_to(REPO_ROOT)),
                "gold_json": str(out_path.relative_to(REPO_ROOT)),
                "row_count": len(rows),
                "detected_columns": cols,
                "first_item": rows[0].item_no if rows else None,
                "last_item": rows[-1].item_no if rows else None,
            }
        )

    summary_path = REPO_ROOT / "data" / "real_rfqs" / "gold" / "rows" / "_insul_draft_summary.json"
    summary_path.write_text(
        json.dumps(
            {"generated_at": datetime.now().isoformat(timespec="seconds"), "pairs": summary},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    log.info("Wrote summary %s", summary_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
