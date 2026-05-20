"""Table extraction using Camelot for cell-level PDF table extraction.

Requires: pip install camelot-py[cv]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TableCell:
    text: str
    row: int
    col: int
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)


@dataclass
class ExtractedTable:
    page_number: int
    rows: list[list[str]]
    headers: list[str] = field(default_factory=list)
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    extraction_method: str = "auto"
    confidence: float = 1.0

    @property
    def is_header_row(self) -> bool:
        if not self.rows or not self.headers:
            return False
        first_row = self.rows[0]
        header_count = sum(1 for cell in first_row if any(h.lower() in cell.lower() for h in self.headers))
        return header_count >= len(self.headers) // 2


class TableExtractor:
    def __init__(self, flavor: str = "auto"):
        self.flavor = flavor

    def extract(self, file_path: str | Path) -> list[ExtractedTable]:
        tables = []
        try:
            import camelot

            camelot_tables = camelot.read_pdf(str(file_path), pages="all", flavor=self.flavor)
            for camelot_table in camelot_tables:
                page_num = camelot_table.page
                rows = camelot_table.data
                if rows and len(rows) > 1:
                    table = ExtractedTable(
                        page_number=page_num,
                        rows=rows,
                        headers=rows[0] if rows else [],
                        bbox=(0.0, 0.0, 0.0, 0.0),
                        extraction_method=self.flavor,
                        confidence=0.95,
                    )
                    tables.append(table)
        except ImportError:
            logger.warning("camelot-py not installed, falling back to pdfplumber")
            tables = self._fallback_extract(file_path)
        except Exception as e:
            logger.warning(f"Camelot extraction failed: {e}, falling back to pdfplumber")
            tables = self._fallback_extract(file_path)

        return tables

    def _fallback_extract(self, file_path: str | Path) -> list[ExtractedTable]:
        from src.ingest.pdf_extractor import PDFExtractor

        extractor = PDFExtractor()
        raw_tables = extractor.extract_tables(file_path)
        tables = []
        for raw_table in raw_tables:
            table = ExtractedTable(
                page_number=raw_table.page_number,
                rows=raw_table.rows if isinstance(raw_table.rows, list) else [],
                bbox=raw_table.bbox,
                extraction_method="pdfplumber",
                confidence=0.7,
            )
            tables.append(table)
        return tables

    def map_to_boq_rows(self, tables: list[ExtractedTable]) -> list[dict[str, Any]]:
        boq_rows = []
        for table in tables:
            if self._looks_like_boq_table(table):
                rows = table.rows[1:] if self._has_header(table) else table.rows
                for row in rows:
                    if len(row) >= 4:
                        boq_row = self._parse_boq_row(row, table)
                        if boq_row:
                            boq_rows.append(boq_row)
        return boq_rows

    def _looks_like_boq_table(self, table: ExtractedTable) -> bool:
        if not table.rows or len(table.rows) < 2:
            return False
        header_text = " ".join(str(h).lower() for h in table.headers)
        boq_indicators = ["item", "description", "material", "quantity", "unit", "grade", "rate", "amount"]
        score = sum(1 for indicator in boq_indicators if indicator in header_text)
        return score >= 2

    def _has_header(self, table: ExtractedTable) -> bool:
        if not table.headers:
            return False
        header_text = " ".join(str(h).lower() for h in table.headers)
        return "item" in header_text or "description" in header_text or "material" in header_text

    def _parse_boq_row(self, row: list[str], table: ExtractedTable) -> dict[str, Any] | None:
        if len(row) < 3:
            return None
        material = ""
        quantity = ""
        unit = ""
        description = ""
        grade = ""
        location = ""
        standard = ""
        action = "supply"

        try:
            if any(c.isdigit() for c in row[0]):
                material = str(row[1]) if len(row) > 1 else ""
                quantity = str(row[2]) if len(row) > 2 else ""
                unit = str(row[3]) if len(row) > 3 else ""
                description = material
                if len(row) > 4:
                    grade = str(row[4])
                if len(row) > 5:
                    location = str(row[5])
            else:
                for i, cell in enumerate(row):
                    cell_lower = cell.lower().strip()
                    if any(u in cell_lower for u in ["m³", "m2", "kg", "no.", "nos", "rm", "lm"]) and unit == "":
                            unit = cell
                            q_idx = i - 1
                            if q_idx >= 0:
                                quantity = row[q_idx]
                    if i == 0 and cell and not any(c.isdigit() for c in cell):
                        description = cell
                        material = cell
                    if any(str(g).lower() in cell_lower for g in ["m20", "m25", "m30", "fe500", "fe550"]):
                        grade = cell

            return {
                "material": material,
                "quantity": quantity,
                "unit": unit,
                "description": description,
                "grade": grade,
                "location": location,
                "standard": standard,
                "action": action,
            }
        except Exception:
            return None
