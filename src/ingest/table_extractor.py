"""Table extraction using pdfplumber for cell-level PDF table extraction.

camelot-py was evaluated on PDFs 04/06/07 (2026-06-18): it consistently
failed with 'list index out of range' and fell back to pdfplumber anyway,
while being 4-11x slower with identical row/cell counts.  The dead camelot
code path has been removed.  pdfplumber is the sole extraction backend.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config.settings import settings

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
    def __init__(self) -> None:
        self._section_headers: dict[int, str] = {}
        self._parent_material: str = ""

    def extract(
        self,
        file_path: str | Path,
        max_pages: int | None = None,
        page_numbers: list[int] | None = None,
        timeout_sec: float = 30.0,
    ) -> list[ExtractedTable]:
        def _run():
            return self._fallback_extract(file_path, max_pages=max_pages, page_numbers=page_numbers)

        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(_run)
            try:
                result = fut.result(timeout=timeout_sec)
                return result if isinstance(result, list) else []
            except FutureTimeoutError:
                logger.warning("Table extraction timed out after %.1fs for %s", timeout_sec, file_path)
                fut.cancel()
                return []
            except Exception:
                logger.warning("Table extraction failed for %s", file_path, exc_info=True)
                return []

    def _fallback_extract_with_pages(
        self, file_path: str | Path, max_pages: int | None = None, page_numbers: list[int] | None = None
    ) -> list[ExtractedTable]:
        from src.ingest.pdf_extractor import PDFExtractor

        try:
            extractor = PDFExtractor()
            raw_tables = extractor.extract_tables(file_path, page_numbers=page_numbers)
            tables = []
            for raw_table in raw_tables:
                if max_pages is not None and raw_table.page_number > max_pages:
                    continue
                table = ExtractedTable(
                    page_number=raw_table.page_number,
                    rows=raw_table.rows if isinstance(raw_table.rows, list) else [],
                    bbox=raw_table.bbox,
                    extraction_method="pdfplumber",
                    confidence=settings.TABLE_EXTRACTOR_BASE_CONFIDENCE,
                )
                tables.append(table)
            logger.info("pdfplumber fallback extracted %s tables from %s", len(tables), file_path)
            return tables
        except Exception as exc:
            logger.warning("pdfplumber fallback failed for %s: %s", file_path, exc)
            return []

    def _fallback_extract(
        self, file_path: str | Path, max_pages: int | None = None, page_numbers: list[int] | None = None
    ) -> list[ExtractedTable]:
        from src.ingest.pdf_extractor import PDFExtractor

        try:
            extractor = PDFExtractor()
            raw_tables = extractor.extract_tables(file_path, page_numbers=page_numbers)
            tables = []
            # When explicit page_numbers are given, honour them; otherwise cap at max_pages.
            effective_max = max_pages if page_numbers is None else None
            for raw_table in raw_tables:
                if effective_max is not None and raw_table.page_number > effective_max:
                    continue
                table = ExtractedTable(
                    page_number=raw_table.page_number,
                    rows=raw_table.rows if isinstance(raw_table.rows, list) else [],
                    bbox=raw_table.bbox,
                    extraction_method="pdfplumber",
                    confidence=settings.TABLE_EXTRACTOR_BASE_CONFIDENCE,
                )
                tables.append(table)
            logger.info("pdfplumber fallback extracted %s tables from %s", len(tables), file_path)
            return tables
        except Exception as exc:
            logger.warning("pdfplumber fallback failed for %s: %s", file_path, exc)
            return []

    def extract_from_split_quantity_pdf(
        self,
        file_path: str | Path,
        max_pages: int | None = None,
        page_numbers: list[int] | None = None,
    ) -> list[ExtractedTable]:
        """Extract BOQ tables from PDFs where quantities are split across lines
        (e.g. GeM tenders where the PDF renders each digit of a quantity on
        its own visual line). Uses the position-aware extractor to reconstruct
        the table cells.
        """
        from src.ingest.pdf_extractor import PDFExtractor

        pe = PDFExtractor()
        extracted: list[ExtractedTable] = []
        # Determine which pages to scan
        try:
            import fitz

            with fitz.open(str(file_path)) as doc:
                page_count = len(doc)
        except Exception:
            page_count = max_pages or 0
        limit = min(page_count, max_pages) if max_pages else page_count
        for p in range(1, limit + 1):
            if page_numbers and p not in page_numbers:
                continue
            rows = pe.extract_boq_rows_from_split_quantity_page(file_path, p)
            if not rows:
                continue
            # Build a 2-column "table" from rows: [Material, Quantity]
            table_rows: list[list[str]] = []
            for r in rows:
                material = r.get("material", "")
                qty = r.get("quantity")
                table_rows.append([material, str(qty) if qty is not None else ""])
            if not table_rows:
                continue
            extracted.append(
                ExtractedTable(
                    page_number=p,
                    rows=table_rows,
                    headers=["Material", "Quantity"],
                    bbox=(0.0, 0.0, 0.0, 0.0),
                    extraction_method="position_aware_split_qty",
                    confidence=settings.TABLE_EXTRACTOR_HIGH_CONFIDENCE,
                )
            )
        return extracted

    def extract_column_aware(
        self,
        file_path: str | Path,
        max_pages: int | None = None,
        page_numbers: list[int] | None = None,
        y_tolerance: float = 6.0,
        confidence_floor: float = 0.5,
    ) -> list[ExtractedTable]:
        """Extract BOQ tables using column-aware cell-by-cell assembly.

        Uses ``PDFExtractor.extract_column_aware_tables`` which detects
        vertical column bands from ruling-line edges and word x-edge
        histograms, then clusters words into row envelopes and assigns
        each word to a band.

        Returns empty list when columns are unreliable (low confidence,
        fewer than 2 bands) so the pipeline can fall back to the
        existing text-line path.
        """
        from src.ingest.pdf_extractor import PDFExtractor

        try:
            extractor = PDFExtractor()
            raw_tables = extractor.extract_column_aware_tables(
                file_path,
                page_numbers=page_numbers,
                y_tolerance=y_tolerance,
                confidence_floor=confidence_floor,
            )
            tables: list[ExtractedTable] = []
            for raw_table in raw_tables:
                if max_pages is not None and raw_table.page_number > max_pages:
                    continue
                table = ExtractedTable(
                    page_number=raw_table.page_number,
                    rows=raw_table.rows if isinstance(raw_table.rows, list) else [],
                    bbox=raw_table.bbox,
                    extraction_method="column_aware",
                    confidence=settings.TABLE_EXTRACTOR_HIGH_CONFIDENCE,
                )
                tables.append(table)
            logger.info("Column-aware extraction: %s tables from %s", len(tables), file_path)
            return tables
        except Exception as exc:
            logger.debug("Column-aware extraction failed for %s: %s", file_path, exc)
            return []

    def map_to_boq_rows(self, tables: list[ExtractedTable]) -> list[dict[str, Any]]:
        boq_rows = []

        for _t_idx, table in enumerate(tables):
            if self._looks_like_boq_table(table):
                rows = table.rows[1:] if self._has_header(table) else table.rows
                pending_header = ""
                for _row_idx, row in enumerate(rows):
                    if len(row) >= 3:
                        # Check if this row is a parent item (integer item number, has description, no qty/unit in qty/unit columns)
                        row_text = " ".join(str(c) for c in row if c)
                        item_num_match = re.match(r"^\s*(\d+)(?:\.\d+)?\s*", row_text)
                        is_parent_item = False
                        if item_num_match:
                            first_token = item_num_match.group(0).strip().split()[0]
                            # Parent items have integer numbers (1, 2, 3) not decimals (1.1, 1.2)
                            # Check for qty/unit in the expected columns (last two columns typically)
                            has_qty_in_qty_col = False
                            has_unit_in_unit_col = False
                            if len(row) >= 4:
                                # Quantity typically in last column, unit in second-to-last
                                has_qty_in_qty_col = self._cell_is_quantity(str(row[-1])) if row[-1] else False
                                has_unit_in_unit_col = self._cell_is_unit(str(row[-2])) if row[-2] else False
                            elif len(row) == 3:
                                has_qty_in_qty_col = self._cell_is_quantity(str(row[-1])) if row[-1] else False
                                has_unit_in_unit_col = self._cell_is_unit(str(row[-2])) if row[-2] else False

                            if (
                                "." not in first_token
                                and len(row_text) > 80
                                and not has_qty_in_qty_col
                                and not has_unit_in_unit_col
                            ):
                                is_parent_item = True

                        result = self._parse_boq_row(row, table)
                        if result is None:
                            if is_parent_item:
                                if len(row) > 1 and row[1]:
                                    raw = str(row[1]).strip().replace("\n", " ")
                                    self._parent_material = self._extract_shared_material(raw) or raw
                                continue
                            # Check if this row is a section header (short text, no qty/unit).
                            # Also accept SUPPLY/RETURN pipe section labels that include a
                            # temperature number (e.g. "SUPPLY PIPES @ 19 DEG C AT LOWER FLOOR")
                            # — without this, identical supply/return size lines collapse in dedup.
                            text_no_item = re.sub(r"^\d+(?:\.\d+)?\s*", "", row_text).strip()
                            is_pipe_section = bool(
                                re.search(
                                    r"\b(supply|return)\b.*\b(pipe|pipes|piping)\b",
                                    text_no_item,
                                    re.IGNORECASE,
                                )
                                or re.search(
                                    r"\b(terrace|condensate|lower floor|exposed)\b",
                                    text_no_item,
                                    re.IGNORECASE,
                                )
                            )
                            if (
                                len(text_no_item) < 100
                                and (
                                    is_pipe_section
                                    or (
                                        len(row_text) < 80
                                        and not re.search(
                                            r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b",
                                            text_no_item,
                                        )
                                    )
                                )
                            ):
                                pending_header = text_no_item.strip()
                            continue
                        # Prepend section header only when the material is a
                        # generic continuation (no dimension prefix, no trade
                        # keyword at start) — e.g. "ACOUSTIC LINING" before
                        # "Supply,InstallationandTestingof...".
                        dim_prefix = re.compile(r"^\d+\s*mm\s*(thick|dia)", re.IGNORECASE)
                        # If this is a child item (decimal item number like 1.1, 1.2) with dimension header,
                        # use the parent's material description instead
                        is_child_item = False
                        if item_num_match and "." in item_num_match.group(0).strip().split()[0]:
                            is_child_item = True

                        # Section labels that distinguish otherwise-identical size lines
                        # (e.g. SUPPLY vs RETURN pipes with the same dia/qty on one page).
                        section_label_re = re.compile(
                            r"\b(supply|return|terrace|condensate|indoor|outdoor)\b",
                            re.IGNORECASE,
                        )

                        def _apply_context(row_dict: dict[str, Any]) -> dict[str, Any]:
                            mat = row_dict.get("material", "") or ""
                            concise_parent = (
                                self._parent_material
                                if self._parent_material
                                and len(self._parent_material) < 80
                                and not any(
                                    kw in self._parent_material.lower()
                                    for kw in {"supply", "installation", "commissioning", "testing"}
                                )
                                else ""
                            )
                            if is_child_item and concise_parent and dim_prefix.search(mat):
                                row_dict["material"] = f"{concise_parent} {mat}"
                                row_dict["description"] = row_dict["material"]
                                return row_dict
                            if (
                                pending_header
                                and pending_header.lower() not in mat.lower()
                            ):
                                # Always attach distinguishing supply/return section labels
                                # even on pure diameter lines (Copy of BOQ R1).
                                if section_label_re.search(pending_header) and (
                                    dim_prefix.search(mat)
                                    or re.match(
                                        r"^\d+\s*mm\b",
                                        mat,
                                        re.IGNORECASE,
                                    )
                                ):
                                    # Compact label: first meaningful token group
                                    label = re.sub(r"\s+", " ", pending_header).strip()
                                    if len(label) > 48:
                                        label = label[:48].rstrip()
                                    row_dict["material"] = f"{label}: {mat}"
                                    row_dict["description"] = row_dict["material"]
                                elif not dim_prefix.search(mat):
                                    row_dict["material"] = f"{pending_header} {mat}"
                                    row_dict["description"] = row_dict["material"]
                            return row_dict

                        if isinstance(result, list):
                            for r in result:
                                _apply_context(r)
                            boq_rows.extend(result)
                        else:
                            _apply_context(result)
                            boq_rows.append(result)
                        # Keep supply/return/terrace section labels sticky so every
                        # subsequent size line in the section gets the same prefix
                        # (dedup must not collapse SUPPLY vs RETURN identical diams).
                        # Other one-shot pending headers still clear after first use.
                        if not (
                            pending_header
                            and section_label_re.search(pending_header)
                        ):
                            pending_header = ""
        return boq_rows

    # A technical-compliance-checklist table ("Sl.No | Details | Specification |
    # Bidder Reply") is structurally NOT a BOQ table: its spec column routinely
    # states real units (density in kg/m3, water absorption in %) as a
    # *requirement*, not a quantity -- which fools the per-row qty+unit
    # heuristic below into inventing fake BOQ rows out of "Comply"/"Noted"
    # reply cells. Reject on the checklist's header SHAPE before any row
    # logic runs, rather than loosen the row heuristic itself (which sacred-10
    # fidelity depends on). Found empirically 2026-07-05 on a real, previously
    # untested Specification-2 document.
    _CHECKLIST_HEADER_SCAN_ROWS = 6

    def _looks_like_compliance_checklist(self, table: ExtractedTable) -> bool:
        for row in table.rows[: self._CHECKLIST_HEADER_SCAN_ROWS]:
            row_text = " ".join(str(c).lower() for c in row if c)
            has_spec_col = "specification" in row_text or "tce spec" in row_text
            has_reply_col = any(k in row_text for k in ("bidder reply", "reply", "compliance", "remarks"))
            has_sl_no = "sl.no" in row_text or "sl. no" in row_text
            if has_spec_col and has_reply_col and has_sl_no:
                return True
        return False

    def _looks_like_boq_table(self, table: ExtractedTable) -> bool:
        # Position-aware tables are pre-validated
        if table.extraction_method == "position_aware_split_qty":
            return len(table.rows) >= 1
        if not table.rows or len(table.rows) < 2:
            return False

        if self._looks_like_compliance_checklist(table):
            return False

        # Check explicit headers
        header_text = " ".join(str(h).lower() for h in table.headers)
        boq_indicators = [
            "item",
            "description",
            "material",
            "quantity",
            "unit",
            "grade",
            "rate",
            "amount",
            "sr.",
            "no.",
            "qty",
            "total",
        ]
        header_score = sum(1 for indicator in boq_indicators if indicator in header_text)
        if header_score >= 2:
            return True

        # Check first row for header-like content
        if table.rows:
            first_row_text = " ".join(str(c).lower() for c in table.rows[0] if c)
            header_score = sum(1 for indicator in boq_indicators if indicator in first_row_text)
            if header_score >= 2:
                return True

        # Check data rows for BOQ-like structure (item number + quantity + unit)
        boq_row_count = 0
        for row in table.rows[1:]:
            if self._is_boq_data_row(row):
                boq_row_count += 1

        return boq_row_count >= 1

    def _is_boq_data_row(self, row: list[str]) -> bool:
        """Check if a row looks like a BOQ data row (has quantity + unit, item optional)."""
        if len(row) < 3:
            return False
        row_text = " ".join(str(c) for c in row if c)
        has_item = bool(re.search(r"^\d+(?:\.\d+)?\s", row_text))
        has_qty = bool(re.search(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", row_text))
        has_unit = any(self._cell_is_unit(str(c)) for c in row if c)
        # Classic BOQ row: item number + qty + unit
        if has_item and has_qty and has_unit:
            return True
        # Some PDFs put the item number in a preceding header row and the
        # description/qty/unit in a continuation row (e.g. 'ACOUSTIC LINING')
        return bool(has_qty and has_unit and len(row_text) > 20)

    def _find_section_header(self, text: str) -> str:
        lines = text.split("\n")
        for line in reversed(lines):
            stripped = line.strip()
            if not stripped:
                continue
            if (
                stripped.isupper()
                and len(stripped) > 5
                and not re.search(r"schedule|bill|annexure|nit|notice|boq|item|abstract", stripped, re.IGNORECASE)
            ):
                return stripped.title()
        return ""

    def _has_header(self, table: ExtractedTable) -> bool:
        if not table.rows:
            return False
        first_row = table.rows[0]
        first_row_text = " ".join(str(h).lower() for h in first_row if h)
        # Header rows are short; a 500-char description containing "material"
        # is not a header.
        if len(first_row_text) > 120:
            return False
        # If the first cell looks like an item number, this is a data row
        # (e.g. "12 ACOUSTIC LINING"), not a header row.
        if first_row and first_row[0] is not None and self._cell_is_item_number(str(first_row[0]).strip()):
            return False
        # Trust explicit headers only when they look like real headers.
        if table.headers and table.headers != table.rows[0]:
            return True
        return (
            "item" in first_row_text
            or "description" in first_row_text
            or "material" in first_row_text
            or "sr." in first_row_text
        )

    def _cell_is_unit(self, cell: str) -> bool:
        """Check if a cell is a construction unit (not a dimension containing a unit)."""
        c = cell.lower().strip().rstrip(".")  # strip trailing period for "Rmt.", "Nos."

        # A pure unit cell is short and consists mostly of the unit
        if len(c) > 25:
            return False

        # Reject cells that are clearly dimensions/descriptions (contain numbers + unit in same cell)
        # e.g., "500 mm dia", "13 mm thk", "25mm thick", "300 MM" (size token, not UOM).
        # "thk" is a common BOQ abbreviation for thickness and must not fall through
        # to the bare "mm" unit keyword (that swap yields material=Sq.M unit="13 mm thk").
        if re.search(
            r"\d+\s*(mm|cm|m|ft|inch|in)\s*(dia|diameter|thick|thk|wide|depth|length|size)",
            c,
        ):
            return False
        # Bare size tokens: "300 MM", "50mm", "13 mm" — dimension material, not a UOM cell.
        if re.fullmatch(r"\d+(\.\d+)?\s*(mm|cm|m|ft|inch|in)", c):
            return False
        # Any digit + mm/cm with extra words is a size/desc fragment, not a pure unit.
        if re.search(r"\d", c) and re.search(r"\b(mm|cm)\b", c) and not re.fullmatch(
            r"(mm|cm)", c
        ):
            return False

        unit_keywords = [
            "sqm",
            "sq.m",
            "sq. mtr",
            "sq meter",
            "square meter",
            "mtr",
            "kg",
            "nos",
            "no",
            "rm",
            "m³",
            "cum",
            "ltr",
            "m2",
            "m3",
            "sq.mtr",
            "rmt",
            "lm",
            "m²",
            "sqmtrs",
            "sq. mtrs",
            "sqmtr",
            "mtrs",
            "rmtr",
            "m",
            "sqft",
            "sq.ft",
            "sft",
            "cft",
            "cu.ft",
            "ea",
            "each",
            "hr",
            "hrs",
            "hour",
            "hours",
            "day",
            "days",
            "running metre",
            "running meter",
            "r.mtr",
            "rmt",
            "ft",
            "mm",
            "cm",
            "bags",
            "bag",
        ]
        return any(re.search(r"\b" + re.escape(u) + r"\b", c) for u in unit_keywords)

    def _cell_is_quantity(self, cell: str) -> bool:
        """Check if a cell contains a numeric quantity or a rate-only marker."""
        s = cell.strip().replace(" ", "").replace(",", "")
        if s.upper() in ("RO", "R.O.", "R/O", "R.O", "RATEONLY", "RATE-ONLY"):
            return True
        try:
            float(s)
            return True
        except ValueError:
            return False

    def _cell_is_item_number(self, cell: str) -> bool:
        """Check if a cell is an item number."""
        s = cell.strip()
        # Match integers, decimals, and numbers with trailing period (1., 2.)
        if not re.match(r"^\d+(?:\.\d*)?$", s):
            return False
        if s == "0" or s == "0.":
            return False
        return not ("." not in s and int(s) > 99)

    def _extract_shared_material(self, parent_text: str) -> str:
        """Extract a concise shared material description from a parent BOQ row.

        For parent descriptions like the Adani chilled-water BOQ:
          "Supply, installation, testing & commissioning of thermally insulated
           MS Class C (heavy) chilled water piping as per IS1239... The insulation
           shall be closed cell nitrile rubber insulation class O..."
        Returns e.g. ``"MS chilled water pipe insulation nitrile rubber"``.

        The heuristic looks for pipe material (MS, GI, …), pipe description
        (chilled water pipe), and insulation type (nitrile rubber, PUF, …).
        """
        if not parent_text:
            return ""

        m = re.search(r"\b(MS|GI|CI|HDPE|PVC|copper|steel|mild\s+steel)\b", parent_text, re.IGNORECASE)
        pipe_mat = m.group(1).upper() if m else ""
        if pipe_mat == "MILD STEEL":
            pipe_mat = "MS"

        pipe_desc = ""
        m = re.search(r"chilled\s+water\s+(?:pipe|piping)", parent_text, re.IGNORECASE)
        if m:
            pipe_desc = "chilled water pipe"

        ins_type = ""
        m = re.search(
            r"insulation\s+shall\s+be\s+(?:closed\s+cell\s+)?(\w+(?:\s+\w+)*?)(?:\s+insulation|\s+class|\s+density|\s+with|\s+\.)",
            parent_text,
            re.IGNORECASE,
        )
        if m:
            raw = m.group(1).strip()
            if re.search(r"nitrile\s+rubber", raw, re.IGNORECASE):
                ins_type = "nitrile rubber"
            elif re.search(r"\bPUF\b", raw, re.IGNORECASE):
                ins_type = "PUF"
            elif re.search(r"elastomeric", raw, re.IGNORECASE):
                ins_type = "elastomeric"
            else:
                ins_type = raw

        if not pipe_mat or (not pipe_desc and not ins_type):
            return ""
        parts = [p for p in [pipe_mat, pipe_desc or "pipe", "insulation", ins_type] if p]
        return " ".join(parts) if parts else ""

    def _split_dimension_lines(self, material: str) -> list[str]:
        """Split a material cell into multiple materials when it contains
        dimension lines like ``500 mm dia\\n400 mm dia`` or space-joined
        ``32 mm Dia 40 mm Dia 50 mm Dia`` (column-aware row merges).
        Returns a single-item list if no dimension lines are detected.
        """
        if not material or not material.strip():
            return [material]
        # Newline-separated dimension lines (classic merged PDF cells).
        if "\n" in material:
            lines = [ln.strip() for ln in material.split("\n") if ln.strip()]
            if len(lines) > 1:
                dim_re = re.compile(r"\d+\s*mm\s+(?:dia|diameter|thick|thk)\b", re.IGNORECASE)
                if all(dim_re.search(ln) for ln in lines):
                    return lines
        # Space-joined multi-diameter tokens from column-band row collapse.
        # e.g. "32 mm Dia 40 mm Dia 50 mm Dia" or "50 mm Dia 65 mm Dia".
        # Only split repeated *diameter* tokens — never "65 mm dia (19 mm thickness)"
        # which is a single pipe line (dia + insulation thickness in parentheses).
        space_dia_re = re.compile(
            r"\d+(?:\.\d+)?\s*mm\s*(?:dia\.?|diameter)",
            re.IGNORECASE,
        )
        parts = space_dia_re.findall(material)
        if len(parts) >= 2:
            # Only split when the cell is essentially just these diameter tokens
            # (no long prose description that happens to mention two sizes).
            remainder = space_dia_re.sub(" ", material)
            # Drop parenthetical thickness specs and separators from remainder check.
            remainder = re.sub(r"\([^)]*\)", " ", remainder)
            remainder = re.sub(r"[\s,;/|]+", "", remainder)
            if len(remainder) <= 8:
                return [p.strip() for p in parts]
        return [material]

    def _parse_boq_row(self, row: list[str], table: ExtractedTable) -> dict[str, Any] | list[dict[str, Any]] | None:
        # Special path: position-aware split-quantity table has 2 cols [Material, Quantity]
        if table.extraction_method == "position_aware_split_qty" and len(row) >= 2:
            material = str(row[0]).strip()
            quantity = str(row[1]).strip()
            if not material or not quantity:
                return None
            # Heuristic: if material mentions "Sq meter" / "Mattress" / "M3" use sqm; if "Rmt" use rmt; else "nos"
            mat_lower = material.lower()
            if (
                "sq meter" in mat_lower
                or "sqm" in mat_lower
                or "m2" in mat_lower
                or "m³" in mat_lower
                or "m3" in mat_lower
            ):
                unit = "sqm"
            elif "rmt" in mat_lower or "running" in mat_lower:
                unit = "rmt"
            elif "kg" in mat_lower:
                unit = "kg"
            else:
                unit = "nos"
            return {
                "material": material,
                "quantity": quantity,
                "unit": unit,
                "grade": "",
                "location": "",
                "standard": "",
                "action": "supply",
                "description": material,
                "source_table_page": table.page_number,
                "extraction_method": table.extraction_method,
            }
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
            grade_keywords = ["m20", "m25", "m30", "fe500", "fe550", "fe415"]

            # Strategy 1: Find unit and quantity by cell content
            unit_idx = -1
            qty_idx = -1
            item_idx = -1

            _EXCEL_ERRORS = {"#REF!", "#N/A", "#VALUE!", "#DIV/0!", "#NAME?", "#NULL!", "#NUM!", "#GETTING_DATA"}

            for i, cell in enumerate(row):
                cell_str = str(cell).strip().replace("\n", " ").replace("  ", " ")
                if not cell_str:
                    continue
                if any(err in cell_str for err in _EXCEL_ERRORS):
                    continue
                # Item numbers are almost always in the first column — detect first
                if i == 0 and self._cell_is_item_number(cell_str) and item_idx == -1:
                    item_idx = i
                elif self._cell_is_unit(cell_str) and unit_idx == -1:
                    unit_idx = i
                elif (
                    self._cell_is_quantity(cell_str)
                    and qty_idx == -1
                    and not (i == 0 and self._cell_is_item_number(cell_str))
                ):
                    qty_idx = i
                elif self._cell_is_item_number(cell_str) and item_idx == -1:
                    item_idx = i

            # Strategy 2: If we found unit and qty, material is the best remaining cell.
            # Prefer the longest non-item cell that appears before the quantity column;
            # fallback to any longest non-item cell if nothing precedes the quantity.
            raw_material_cell = ""
            # Compliance-form noise: WBS tag "insulation", bidder-reply cells, etc.
            # Prefer real description/size cells over these when choosing material.
            _MATERIAL_NOISE = frozenset(
                {
                    "insulation",
                    "noted",
                    "complies",
                    "comply",
                    "compy",
                    "yes",
                    "no",
                    "na",
                    "n/a",
                    "nil",
                    "ok",
                    "as per",
                }
            )
            if unit_idx != -1 and qty_idx != -1:
                remaining = [
                    (i, str(cell).strip().replace("\n", " ").replace("  ", " "))
                    for i, cell in enumerate(row)
                    if i not in (unit_idx, qty_idx) and str(cell).strip()
                ]
                if remaining:
                    # Skip item number cells and grade-keyword cells for material
                    grade_keywords = ["m20", "m25", "m30", "fe500", "fe550", "fe415"]
                    non_item = [
                        (i, c)
                        for i, c in remaining
                        if not self._cell_is_item_number(c)
                        and not any(g in c.lower() for g in grade_keywords)
                        and c.lower().strip() not in _MATERIAL_NOISE
                    ]
                    if non_item:
                        # Prefer cells before the quantity column (material usually comes first)
                        before_qty = [(i, c) for i, c in non_item if i < qty_idx]
                        if before_qty:
                            # Prefer size/thickness tokens over short generic tags when both present.
                            def _mat_score(pair: tuple[int, str]) -> tuple[int, int]:
                                text = pair[1]
                                is_size = 1 if re.search(
                                    r"\d+\s*mm\s*(dia|diameter|thick|thk)?",
                                    text,
                                    re.IGNORECASE,
                                ) else 0
                                return (is_size, len(text))

                            chosen = max(before_qty, key=_mat_score)
                        else:
                            chosen = max(non_item, key=lambda x: len(x[1]))
                        material = chosen[1]
                        raw_material_cell = str(row[chosen[0]])
                    else:
                        # Only item-number/grade/noise cells remain — not a real data row
                        return None
                quantity = str(row[qty_idx]).strip().replace("\n", " ")
                unit = str(row[unit_idx]).strip().replace("\n", " ")
            else:
                # Fallback: heuristic position-based parsing
                for i, cell in enumerate(row):
                    cell_str = str(cell).strip().replace("\n", " ").replace("  ", " ")
                    if not cell_str:
                        continue
                    if any(err in cell_str for err in _EXCEL_ERRORS):
                        continue
                    if self._cell_is_unit(cell_str) and unit == "":
                        unit = cell_str
                        if i > 0 and self._cell_is_quantity(str(row[i - 1]).strip().replace("\n", " ")):
                            quantity = str(row[i - 1]).strip().replace("\n", " ")
                    elif (
                        not material
                        and len(cell_str) >= 8
                        and not self._cell_is_unit(cell_str)
                        and not self._cell_is_quantity(cell_str)
                        and not self._cell_is_item_number(cell_str)
                        or i == 0
                        and cell_str
                        and not any(c.isdigit() for c in cell_str)
                    ):
                        description = cell_str
                        material = cell_str
                    elif any(g in cell_str.lower() for g in grade_keywords):
                        grade = cell_str

            description = material
            if not material:
                return None

            quantity = quantity.strip().replace(" ", "").replace(",", "")
            unit = unit.strip()
            description = description.strip()

            qty_val = 0.0
            is_rate_only = False
            if quantity.upper() in ("RO", "R.O.", "R/O", "RATEONLY"):
                qty_val = 0.0
                is_rate_only = True
            else:
                with suppress(ValueError):
                    qty_val = float(quantity) if quantity else 0.0

            # Check any cell for RO marker (some tables have RO in quantity column
            # that wasn't detected as numeric)
            if not is_rate_only:
                for c in row:
                    if str(c).strip().upper() in ("RO", "R.O.", "R/O"):
                        is_rate_only = True
                        break

            # Skip rows with no unit and no quantity (likely headers or description rows)
            if unit == "" and qty_val == 0.0 and not is_rate_only:
                return None
            if is_rate_only:
                material = re.sub(r"\s*\bR\s*/\s*O\b", "", material, flags=re.IGNORECASE).strip()

            # Treat 0-qty rows with a real unit as rate-only items so BoqRow.validate()
            # does not reject them downstream. These are common in real BOQ tables
            # (e.g., Adani item 1.1 "500 mm dia" listed without a quantity in the
            # gold-standard rowgold).
            if qty_val == 0.0 and unit != "" and not is_rate_only:
                is_rate_only = True

            # Variable confidence
            confidence = 0.70
            if item_idx >= 0 or (row and self._cell_is_item_number(str(row[0]))):
                confidence += 0.10
            if unit_idx != -1:
                confidence += 0.10
            if qty_val > 0:
                confidence += 0.10
            if unit_idx == -1 or qty_idx == -1:
                confidence -= 0.10
            if qty_val == 0:
                confidence -= 0.10
            confidence = max(0.50, min(0.95, round(confidence, 2)))

            # Infer material from section headers
            if re.match(r"^\d+\s*mm\s*thick$", material.strip(), re.IGNORECASE):
                header = self._section_headers.get(table.page_number, "")
                if header:
                    material = f"{header} {material}"
                    description = material

            # Detect dimension-only material (e.g. "500 mm dia", "350 mm dia")
            dimension = ""
            if re.match(r"^\d+\s*mm\s*(?:dia|diameter|thick|wide)\s*$", material.strip(), re.IGNORECASE):
                dimension = material.strip()

            # Split multi-line dimension cells (e.g. "500 mm dia\n400 mm dia") into
            # separate BOQ rows so each dimension gets its own quantity.
            dim_split = self._split_dimension_lines(raw_material_cell or material)
            if len(dim_split) > 1:
                return [
                    {
                        "material": m,
                        "quantity": qty_val,
                        "unit": unit,
                        "description": m,
                        "grade": grade,
                        "location": location,
                        "standard": standard,
                        "action": action,
                        "rate_only": is_rate_only,
                        "confidence": confidence,
                        "source_table_page": table.page_number,
                        "extraction_method": table.extraction_method,
                        "dimension": m,
                    }
                    for m in dim_split
                ]

            return {
                "material": material,
                "quantity": qty_val,
                "unit": unit,
                "description": description,
                "grade": grade,
                "location": location,
                "standard": standard,
                "action": action,
                "rate_only": is_rate_only,
                "confidence": confidence,
                "source_table_page": table.page_number,
                "extraction_method": table.extraction_method,
                "dimension": dimension,
            }
        except Exception:
            return None
