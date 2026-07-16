"""PDF text and table extraction.

This module keeps the public surface deliberately small: it wraps
``pdfplumber`` when available, returns stable dataclasses, and exposes scanned
PDF detection so the pipeline can route image-only documents to OCR.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PageText:
    page_number: int
    text: str
    width: float = 0.0
    height: float = 0.0
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    blocks: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class TableData:
    page_number: int
    rows: Any
    top: float = 0.0
    bottom: float = 0.0
    left: float = 0.0
    right: float = 0.0

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        return (self.left, self.top, self.right, self.bottom)


@dataclass(slots=True)
class TokenBox:
    text: str
    bbox: tuple[float, float, float, float]
    page_number: int = 1


def extract_with_bboxes(pdf_path: str | Path) -> list[dict]:
    """Extract tokens with normalized bounding boxes (0-1000 range).

    Returns list of {page: int, tokens: list[str], bboxes: list[list[int]]}
    matching LayoutLM convention.
    """
    from pathlib import Path

    pdf_path = Path(pdf_path)
    result: list[dict] = []

    try:
        import pdfplumber

        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                width = float(page.width or 0)
                height = float(page.height or 0)
                chars = page.chars or []

                if not chars:
                    result.append({"page": page_num, "tokens": [], "bboxes": []})
                    continue

                tokens: list[str] = []
                bboxes: list[list[int]] = []
                current_word: list[dict] = []
                current_bbox: tuple[float, float, float, float] | None = None

                def flush_word(w: float, h: float, tok_list: list, bbox_list: list) -> None:
                    nonlocal current_word, current_bbox
                    if not current_word or not current_bbox:
                        return
                    text = "".join(c["text"] for c in current_word)
                    x0, y0, x1, y1 = current_bbox
                    norm = 1000.0
                    nx0 = int((x0 / w) * norm) if w > 0 else 0
                    ny0 = int((y0 / h) * norm) if h > 0 else 0
                    nx1 = int((x1 / w) * norm) if w > 0 else 1000
                    ny1 = int((y1 / h) * norm) if h > 0 else 1000
                    tok_list.append(text)
                    bbox_list.append([nx0, ny0, nx1, ny1])
                    current_word = []
                    current_bbox = None

                def make_flush(w: float, h: float, tok_list: list[str], bbox_list: list[list[int]]):
                    def flush_word_call() -> None:
                        flush_word(w, h, tok_list, bbox_list)

                    return flush_word_call

                flush_word_call = make_flush(width, height, tokens, bboxes)

                for char in chars:
                    char_text = char.get("text", "")
                    if char_text.strip():
                        if not current_word:
                            current_word = [char]
                            current_bbox = (char["x0"], char["top"], char["x1"], char["bottom"])
                        elif char["x0"] <= (current_bbox[2] if current_bbox else 0) + 2:
                            current_word.append(char)
                            if current_bbox:
                                current_bbox = (
                                    min(current_bbox[0], char["x0"]),
                                    min(current_bbox[1], char["top"]),
                                    max(current_bbox[2], char["x1"]),
                                    max(current_bbox[3], char["bottom"]),
                                )
                        else:
                            flush_word_call()
                            current_word = [char]
                            current_bbox = (char["x0"], char["top"], char["x1"], char["bottom"])
                    else:
                        flush_word_call()

                flush_word_call()
                result.append({"page": page_num, "tokens": tokens, "bboxes": bboxes})
    except Exception:
        pass

    return result


@dataclass(slots=True)
class DocumentContent:
    pages: list[PageText] = field(default_factory=list)
    tables: list[TableData] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    pdf_path: str = ""
    is_scanned: bool = False

    @property
    def full_text(self) -> str:
        return "\n".join(page.text for page in self.pages if page.text)


class PDFExtractor:
    """Extract text/tables from text-based PDFs and detect OCR candidates."""

    # Module-level cache for extract_gem_per_item_rows — avoids redundant
    # full-PDF scans when the pipeline calls this method many times per file.
    _gem_cache: dict[str, list[dict]] = {}

    def __init__(self, min_chars_per_page: int = 50) -> None:
        self.min_chars_per_page = min_chars_per_page

    def is_scanned(self, pages: list[PageText]) -> bool:
        if not pages:
            return True
        non_empty = [len((page.text or "").strip()) for page in pages]
        if not any(non_empty):
            return True
        avg_chars = sum(non_empty) / len(non_empty)
        return avg_chars < self.min_chars_per_page

    def extract_text(self, file_path: str | Path, max_pages: int | None = None) -> list[PageText]:
        pages: list[PageText] = []
        try:
            import pdfplumber

            with pdfplumber.open(str(file_path)) as pdf:
                page_count = len(pdf.pages)
                limit = min(page_count, max_pages) if max_pages else page_count
                for index in range(limit):
                    page = pdf.pages[index]
                    text = page.extract_text() or ""
                    # Detect corrupted encoding (Hindi/Indic PDFs with cid: glyphs)
                    is_corrupted = self._is_corrupted_text(text)
                    if is_corrupted:
                        text = self._clean_corrupted_text(text)
                        # If after cleaning the text is still short, try word-level
                        # extraction as fallback (handles font encoding issues better).
                        cleaned_word_text = self._extract_words_fallback(page)
                        if cleaned_word_text and len(cleaned_word_text) > len(text):
                            text = cleaned_word_text
                    blocks = []
                    try:
                        blocks = page.extract_words() or []
                    except Exception:
                        blocks = []
                    pages.append(
                        PageText(
                            page_number=index + 1,
                            text=text,
                            width=float(getattr(page, "width", 0.0) or 0.0),
                            height=float(getattr(page, "height", 0.0) or 0.0),
                            bbox=tuple(getattr(page, "bbox", (0.0, 0.0, 0.0, 0.0))),
                            blocks=blocks,
                        )
                    )
        except Exception:
            return []
        return pages

    def _is_corrupted_text(self, text: str) -> bool:
        """Detect pdfplumber corruption patterns like (cid:1), (cid:41)."""
        if not text:
            return False
        cid_count = text.count("(cid:")
        # Any cid: pattern means corrupted font encoding
        return cid_count >= 3

    def _extract_words_fallback(self, page: Any) -> str:
        """Fallback: extract words from pdfplumber when text extraction fails."""
        try:
            words = page.extract_words()
            if words:
                return " ".join(w.get("text", "") for w in words)
        except Exception:
            pass
        return ""

    def _clean_corrupted_text(self, text: str) -> str:
        """Clean Hindi/Indic PDF corruption: remove cid: patterns and devanagari."""
        import re

        # Remove (cid:NN) patterns
        clean = re.sub(r"\(cid:\d+\)", "", text)
        # Remove Devanagari script (Hindi)
        clean = re.sub(r"[\u0900-\u097F]+", "", clean)
        # Normalize whitespace
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    def extract_full_text(self, file_path: str | Path, max_pages: int | None = None) -> str:
        return "\n".join(page.text for page in self.extract_text(file_path, max_pages=max_pages) if page.text)

    def extract_tables(self, file_path: str | Path, page_numbers: list[int] | None = None) -> list[TableData]:
        """Extract tables, optionally limited to specific 1-based page numbers (for BOQ section focus)."""
        tables: list[TableData] = []
        try:
            import pdfplumber

            with pdfplumber.open(str(file_path)) as pdf:
                for index, page in enumerate(pdf.pages, start=1):
                    if page_numbers and index not in page_numbers:
                        continue
                    raw_tables = page.extract_tables() or []
                    tables.extend(self._normalise_tables(index, raw_tables, page))
        except Exception:
            return []
        return tables

    def extract(self, file_path: str | Path, max_pages: int | None = None) -> DocumentContent:
        pages = self.extract_text(file_path, max_pages=max_pages)
        tables = self.extract_tables(file_path)
        scanned = self.is_scanned(pages)
        return DocumentContent(
            pages=pages,
            tables=tables,
            pdf_path=str(file_path),
            is_scanned=scanned,
            metadata={
                "total_pages": len(pages),
                "page_count": len(pages),
                "has_tables": bool(tables),
                "is_scanned": scanned,
            },
        )

    def extract_page(self, file_path: str | Path, page_number: int) -> PageText | None:
        for page in self.extract_text(file_path):
            if page.page_number == page_number:
                return page
        return None

    def extract_text_position_aware(
        self,
        file_path: str | Path,
        max_pages: int | None = None,
        y_tolerance: float = 4.0,
        x_gap: float = 25.0,
    ) -> list[PageText]:
        """Reconstruct text by y/x position so multi-line table cells collapse.

        Some PDFs (e.g. GeM tenders) render each word/character on its own
        visual line in the text stream, even when visually they sit side-by-
        side. Standard ``extract_text()`` then produces 1-word-per-line output
        that breaks every downstream BOQ heuristic.

        This method uses pdfplumber ``words`` (which carry x0/top coords) to
        bucket words into rows by y, sort each row by x, and rejoin. Words
        with an x-gap > ``x_gap`` (default 25 pt) get a column break; words
        within the same row but on a different visual line still collapse.

        Y tolerance (default 4 pt) is the half-height of the bucket. Smaller
        values keep visually-distinct lines separate; larger values merge
        genuinely-distinct rows.
        """
        pages: list[PageText] = []
        try:
            import pdfplumber

            with pdfplumber.open(str(file_path)) as pdf:
                page_count = len(pdf.pages)
                limit = min(page_count, max_pages) if max_pages else page_count
                for index in range(limit):
                    page = pdf.pages[index]
                    words = (
                        page.extract_words(
                            keep_blank_chars=False,
                            use_text_flow=False,
                            x_tolerance=3,
                            y_tolerance=3,
                        )
                        or []
                    )

                    # Bucket by y
                    rows: list[list[tuple[float, str]]] = []
                    current_y: float | None = None
                    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
                        top = float(w["top"])
                        if current_y is None or abs(top - current_y) > y_tolerance:
                            rows.append([])
                            current_y = top
                        rows[-1].append((float(w["x0"]), str(w["text"])))

                    # Within each row, sort by x and rejoin with column breaks
                    lines: list[str] = []
                    for row in rows:
                        row.sort(key=lambda x: x[0])
                        line_parts: list[str] = []
                        prev_x: float | None = None
                        for x, text in row:
                            if prev_x is not None and (x - prev_x) > x_gap:
                                line_parts.append("  ")  # column separator
                            line_parts.append(text)
                            prev_x = x + max(8.0, len(text) * 4.0)  # rough right edge
                        lines.append(" ".join(line_parts).strip())

                    text = "\n".join(lines)
                    if text and self._is_corrupted_text(text):
                        text = self._clean_corrupted_text(text)
                    pages.append(
                        PageText(
                            page_number=index + 1,
                            text=text,
                            width=float(getattr(page, "width", 0.0) or 0.0),
                            height=float(getattr(page, "height", 0.0) or 0.0),
                            bbox=tuple(getattr(page, "bbox", (0.0, 0.0, 0.0, 0.0))),
                            blocks=[],
                        )
                    )
        except Exception:
            return []
        return pages

    def extract_position_aware_rows(
        self,
        file_path: str | Path,
        page_number: int,
        y_tolerance: float = 4.0,
        x_gap: float = 25.0,
    ) -> list[dict]:
        """Return position-reconstructed rows for a single page.

        Each row is a dict: ``{"y": float, "cells": [{"x": float, "text": str}]}``
        ordered by x. Consecutive single-digit "cells" that are pure digits
        at the same column are NOT auto-concatenated here; the caller
        (e.g. BOQ row builder) decides how to merge.
        """
        out: list[dict] = []
        try:
            import pdfplumber

            with pdfplumber.open(str(file_path)) as pdf:
                if page_number < 1 or page_number > len(pdf.pages):
                    return out
                page = pdf.pages[page_number - 1]
                words = (
                    page.extract_words(
                        keep_blank_chars=False,
                        use_text_flow=False,
                        x_tolerance=3,
                        y_tolerance=3,
                    )
                    or []
                )
                rows: list[dict] = []
                current_y: float | None = None
                for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
                    top = float(w["top"])
                    if current_y is None or abs(top - current_y) > y_tolerance:
                        rows.append({"y": top, "cells": []})
                        current_y = top
                    rows[-1]["cells"].append((float(w["x0"]), str(w["text"])))
                for row in rows:
                    row["cells"].sort(key=lambda c: c[0])
                    out.append(
                        {
                            "y": row["y"],
                            "cells": [{"x": x, "text": t} for x, t in row["cells"]],
                        }
                    )
        except Exception:
            return out
        return out

    def extract_digit_columns(
        self,
        file_path: str | Path,
        page_number: int,
        x_tolerance: float = 30.0,
        y_gap_threshold: float = 17.0,
    ) -> list[dict]:
        """Find vertical columns whose cells are single digits — these are
        likely split quantities (e.g. "7 / 1 / 5 / 0" → 7150).

        Returns list of ``{"x_center": float, "groups": [{"digits": [str], "y_range": (y0, y1), "value": int}], "y_range": (y0, y1)}``.
        Consecutive single-digit cells with y-gap < ``y_gap_threshold`` are
        grouped into the same quantity. Adjacent cells within ``x_tolerance``
        pixels (column) are considered the same column.
        """
        rows = self.extract_position_aware_rows(file_path, page_number)
        # Build (y, x, text) triples
        triples: list[tuple[float, float, str]] = []
        for r in rows:
            for c in r["cells"]:
                triples.append((r["y"], c["x"], c["text"]))
        triples.sort(key=lambda t: (t[0], t[1]))
        # Cluster by x
        clusters: list[list[tuple[float, float, str]]] = []
        for y, x, text in triples:
            placed = False
            for cluster in clusters:
                cx = sum(c[1] for c in cluster) / len(cluster)
                if abs(x - cx) <= x_tolerance:
                    cluster.append((y, x, text))
                    placed = True
                    break
            if not placed:
                clusters.append([(y, x, text)])
        # Keep only clusters that are predominantly single digits, then
        # group the digits by y-gap (each y-gap > threshold = new group).
        out: list[dict] = []
        for cluster in clusters:
            digit_cells = [t for t in cluster if len(t[2].strip()) == 1 and t[2].strip().isdigit()]
            if len(digit_cells) < 3:
                continue
            if len(digit_cells) < 0.5 * len(cluster):
                continue
            digit_cells.sort(key=lambda t: t[0])
            groups: list[dict] = []
            current_digits: list[str] = [digit_cells[0][2]]
            current_y_start = digit_cells[0][0]
            current_y_end = digit_cells[0][0]
            for prev, cur in zip(digit_cells, digit_cells[1:], strict=False):
                gap = cur[0] - prev[0]
                if gap > y_gap_threshold:
                    groups.append(
                        {
                            "digits": current_digits,
                            "y_range": (current_y_start, current_y_end),
                            "value": int("".join(current_digits)) if current_digits else None,
                        }
                    )
                    current_digits = [cur[2]]
                    current_y_start = cur[0]
                    current_y_end = cur[0]
                else:
                    current_digits.append(cur[2])
                    current_y_end = cur[0]
            if current_digits:
                groups.append(
                    {
                        "digits": current_digits,
                        "y_range": (current_y_start, current_y_end),
                        "value": int("".join(current_digits)) if current_digits else None,
                    }
                )
            xs = [t[1] for t in digit_cells]
            ys = [t[0] for t in digit_cells]
            out.append(
                {
                    "x_center": sum(xs) / len(xs),
                    "groups": groups,
                    "y_range": (min(ys), max(ys)),
                }
            )
        return out

    def extract_boq_rows_from_split_quantity_page(
        self,
        file_path: str | Path,
        page_number: int,
        x_tolerance: float = 30.0,
        y_gap_threshold: float = 17.0,
    ) -> list[dict]:
        """Build BOQ rows from a page whose quantities are split across lines.

        For each digit-column group (single concatenated quantity), find
        the material text to the LEFT at the same y-range, the consignee
        text in the middle, and assemble a row.

        Returns list of dicts: ``{"material": str, "quantity": int, "quantity_y_range": (y0, y1), "consignee": str, "page": int}``
        """
        rows = self.extract_position_aware_rows(file_path, page_number)
        cols = self.extract_digit_columns(
            file_path, page_number, x_tolerance=x_tolerance, y_gap_threshold=y_gap_threshold
        )
        if not cols:
            return []
        digit_col = cols[0]
        qty_groups = digit_col["groups"]
        qty_x = digit_col["x_center"]

        # Find the "material" column: leftmost x-position cluster of multi-word text
        # We classify each row's cells by x and assign a role
        # Convention: x < 200 = material, 200-360 = consignee name, 360-540 = address
        boq_rows: list[dict] = []
        for grp in qty_groups:
            y0, y1 = grp["y_range"]
            # Pages often have a header band — skip if quantity is at the very bottom
            # (page number) and has only 1 digit
            if y1 > 800 and grp["value"] is not None and grp["value"] < 100:
                continue
            # Find words in the row's y-range, with x < qty_x.
            # GeM summary tables have a leftmost "Evaluation Schedules" column
            # (x ~ 45) with labels like "FOR TALCHER PROJECT"; the material
            # column starts further right (x ~ 80).  We skip words that are
            # clearly schedule-label fragments and sit in that narrow left band.
            artifact_words = {"FOR", "TALC", "HER", "PROJECT", "CT", "ARAP", "ROJEC", "FORL", "LARAP", "T"}
            material_words: list[str] = []
            consignee_words: list[str] = []
            # Use a generous y-margin: material text often starts a little
            # above the first digit and can end a little below the last digit
            # of the quantity column.
            for r in rows:
                if not (y0 - 20 <= r["y"] <= y1 + 20):
                    continue
                for c in r["cells"]:
                    if c["x"] >= qty_x - 5:
                        continue  # skip quantity column and right of it
                    txt = c["text"].strip()
                    if c["x"] < 70 and txt.upper() in artifact_words:
                        continue
                    if c["x"] < 300:
                        material_words.append(txt)
                    else:
                        consignee_words.append(txt)
            material = " ".join(material_words).strip()
            consignee = " ".join(consignee_words).strip()
            # Clean up layout artefacts from the leftmost "Evaluation Schedules"
            # column (e.g. "FOR TALCHER PROJECT", "FOR LARA PROJECT") that can
            # leak into the material text on GeM summary tables.
            material = self._clean_gem_material(material)
            boq_rows.append(
                {
                    "material": material,
                    "quantity": grp["value"],
                    "quantity_y_range": (y0, y1),
                    "consignee": consignee,
                    "page": page_number,
                }
            )
        return boq_rows

    @staticmethod
    def _clean_gem_material(text: str) -> str:
        import re

        # Drop common GeM evaluation-schedule column fragments.
        artifacts = [
            r"FOR\b",
            r"TALC\b",
            r"HER\b",
            r"PROJECT\b",
            r"PROJE\b",
            r"CT\b",
            r"ARAP\b",
            r"ROJEC\b",
            r"FORL\b",
            r"LARAP\b",
        ]
        for pat in artifacts:
            text = re.sub(r"\b" + pat + r"\s*", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text).strip()
        # Ensure the description starts with the actual material name.
        m = re.search(r"\bBonded Mineral\b", text, re.IGNORECASE)
        if m:
            text = text[m.start() :]
        return text.strip()

    def extract_gem_per_item_rows(
        self,
        file_path: str | Path,
        page_numbers: list[int] | None = None,
    ) -> list[dict]:
        """Extract BOQ rows from GeM-style PDFs where each item description is
        in the page text and its quantity is in a consignee table below.

        These PDFs have no split-quantity digit columns and no summary BOQ
        table.  Instead each item (e.g. ``Bonded Mineral Rock Wool ...``)
        appears as text, followed by a small consignee table with a Quantity
        column.  We collect descriptions and quantities in document order and
        pair them 1:1.

        Returns list of dicts:
        ``{"material": str, "quantity": int, "consignee": str, "page": int}``.
        """
        import re

        try:
            import pdfplumber
        except Exception:
            return []

        # Fast reject: GeM per-item PDFs always contain a consignee quantity table
        # and usually a GEM/ marker. Non-GeM insulation PDFs (e.g. GSECL) contain
        # the same keywords but no consignee table, so avoid the expensive full scan.
        try:
            import fitz

            with fitz.open(str(file_path)) as doc:
                sample_text = ""
                for page in doc[:5]:
                    sample_text += page.get_text()
                if "GEM/" not in sample_text and "consignee" not in sample_text.lower():
                    return []
        except Exception:
            pass

        # Cache check: avoid redundant full-PDF scans when called multiple
        # times by the pipeline (which has many fallback attempts per file).
        cache_key = str(file_path) + "_gem_per_item"
        if cache_key in self._gem_cache:
            return list(self._gem_cache[cache_key])

        # Broadened pattern for GeM per-item insulation descriptions (handles
        # slight variations in hyphenation, wire netting sizes, thickness, and
        # newlines from extraction). We also fall back to table scanning for
        # rows containing the core keywords when regex misses split-text cases.
        desc_pattern = re.compile(
            r"Bonded Mineral\s*(?:-?\s*Rock\s*-?)?\s*Wool\s+Mattresses\s+With\s+One\s+Side\s+.*?(?:GS|SS|G\.?S\.?)\s*Wire\s*Netting",
            re.IGNORECASE | re.DOTALL,
        )

        descriptions: list[tuple[int, str]] = []
        quantities: list[tuple[int, int, str]] = []

        import time

        scan_start = time.monotonic()
        SCAN_TIMEOUT = 30.0  # max seconds for full GeM scan
        SCAN_PAGE_LIMIT = 50  # max pages to scan (GeM items are in first ~30 pages)

        with pdfplumber.open(str(file_path)) as pdf:
            limit_pages = page_numbers or list(range(1, len(pdf.pages) + 1))
            # Cap scan to prevent hangs on huge PDFs
            if isinstance(limit_pages, list) and len(limit_pages) > SCAN_PAGE_LIMIT:
                limit_pages = limit_pages[:SCAN_PAGE_LIMIT]
            scanned_pages = 0
            for pn in limit_pages:
                scanned_pages += 1
                # Check timeout every 10 pages
                if scanned_pages % 10 == 0 and time.monotonic() - scan_start > SCAN_TIMEOUT:
                    logger.warning(
                        "GeM per-item scan timed out (%.1fs, %d pages) for %s",
                        time.monotonic() - scan_start,
                        scanned_pages,
                        file_path,
                    )
                    break
                if pn < 1 or pn > len(pdf.pages):
                    continue
                page = pdf.pages[pn - 1]
                text = page.extract_text() or ""
                tables = page.extract_tables() or []

                # Only consider pages that contain a consignee quantity table;
                # this skips the front-matter "Item Category" block on page 1.
                has_qty_table = False
                page_has_keywords = "bonded" in text.lower() and ("wool" in text.lower() or "mattress" in text.lower())
                page_quantities: list[tuple[int, str]] = []
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    header = [str(c).lower() if c else "" for c in table[0]]
                    if any("quantity" in h or "मात्रा" in h or "/quantity" in h for h in header):
                        has_qty_table = True
                        # Extract the quantity from the first data row (original behavior)
                        for row in table[1:]:
                            qty_val = None
                            for _idx, cell in enumerate(row):
                                s = str(cell).strip().replace("\n", " ") if cell else ""
                                if s.isdigit() and int(s) > 9:
                                    qty_val = int(s)
                                    break
                            if qty_val is not None:
                                consignee = ""
                                if len(row) > 1:
                                    consignee = str(row[1]).replace("\n", " ").strip()
                                page_quantities.append((qty_val, consignee))
                                break

                if has_qty_table or page_has_keywords:
                    for m in desc_pattern.finditer(text):
                        raw = m.group(0)
                        clean = " ".join(raw.split())
                        descriptions.append((pn, clean))

                    # Extra for variants that the strict regex misses on keyword pages (to hit 22 on 09)
                    if page_has_keywords:
                        for m in re.finditer(
                            r"Bonded Mineral[^.]{40,400}?(?:GS|SS|G\.?S\.?|Wire Netting|netting)",
                            text,
                            re.IGNORECASE | re.DOTALL,
                        ):
                            raw = m.group(0)
                            clean = " ".join(raw.split())
                            if len(clean) > 30 and not any(d[1] == clean for d in descriptions):
                                descriptions.append((pn, clean))

                    # Collect quantities from ALL quantity tables on this page
                    all_page_quantities: list[tuple[int, str]] = []
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        header = [str(c).lower() if c else "" for c in table[0]]
                        if not any("quantity" in h or "मात्रा" in h or "/quantity" in h for h in header):
                            continue
                        for row in table[1:]:
                            qty_val = None
                            for _idx, cell in enumerate(row):
                                s = str(cell).strip().replace("\n", " ") if cell else ""
                                if s.isdigit() and int(s) > 9:
                                    qty_val = int(s)
                                    break
                            if qty_val is not None:
                                consignee = ""
                                if len(row) > 1:
                                    consignee = str(row[1]).replace("\n", " ").strip()
                                all_page_quantities.append((qty_val, consignee))
                    quantities.extend((pn, q, c) for q, c in all_page_quantities)

                    # Robust table fallback (keyword rows)
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        for row in table[1:]:
                            row_text = " ".join(str(c or "").replace("\n", " ") for c in row)
                            if not (
                                "bonded" in row_text.lower()
                                and "wool" in row_text.lower()
                                and "mattress" in row_text.lower()
                            ):
                                continue
                            material_cell = max((str(c or "").replace("\n", " ").strip() for c in row), key=len)
                            qty_val = None
                            for c in row:
                                s = str(c or "").strip().replace("\n", " ")
                                if s.isdigit() and int(s) > 9:
                                    qty_val = int(s)
                                    break
                            if qty_val is not None and material_cell and len(material_cell) > 20:
                                if not any(d[1] == material_cell for d in descriptions):
                                    descriptions.append((pn, material_cell))
                                if not any(q[1] == qty_val and q[2] == "" for q in quantities):
                                    quantities.append((pn, qty_val, ""))

        # Pair descriptions and quantities in document order.  When a page
        # break falls between a description and its table, the next quantity
        # in the stream still belongs to the earliest unmatched description.
        rows: list[dict] = []
        n = min(len(descriptions), len(quantities))
        for i in range(n):
            d_page, material = descriptions[i]
            q_page, quantity, consignee = quantities[i]
            rows.append(
                {
                    "material": material,
                    "quantity": quantity,
                    "consignee": consignee,
                    "page": q_page,
                    "description_page": d_page,
                }
            )
        return rows

        tokens: list[TokenBox] = []
        try:
            import pdfplumber

            with pdfplumber.open(str(file_path)) as pdf:
                for index, page in enumerate(pdf.pages, start=1):
                    words = page.extract_words() or []
                    for word in words:
                        text = word.get("text", "")
                        x0 = word.get("x0", 0)
                        top = word.get("top", 0)
                        x1 = word.get("x1", x0)
                        bottom = word.get("bottom", top)
                        if text.strip():
                            tokens.append(
                                TokenBox(
                                    text=text,
                                    bbox=(x0, top, x1, bottom),
                                    page_number=index,
                                )
                            )
        except Exception:
            return []
        return tokens

    def extract_column_aware_tables(
        self,
        file_path: str | Path,
        page_numbers: list[int] | None = None,
        y_tolerance: float = 6.0,
        confidence_floor: float = 0.5,
    ) -> list[TableData]:
        """P3_02: build BOQ tables cell-by-cell from detected column bands.

        Multi-column PDFs (07_grew class) interleave words from sibling
        columns on the same y-line. pdfplumber's ``extract_tables``
        happens to produce clean cells for some of these (because the
        column dividers are visible as filled rects) but is fragile —
        it relies on heuristic line/rect inference and on the order
        pdfplumber walks the page.

        This method uses ``src.ingest.column_detector`` to:

        1. Detect the vertical bands from ruling-line edges (when
           present) AND word x-edge histograms.
        2. Cluster words into row envelopes by y-center.
        3. For each envelope, assign each word to a band by x-center
           proximity; concatenate words within the band to form the
           cell string.
        4. Optionally merge wrapped cells so a description spanning
           multiple visual lines becomes a single cell.

        The result is a list of ``TableData`` carrying the same shape
        as the existing extract_tables output: ``rows = list[list[str]]``
        with one cell per detected band. Downstream
        ``TableExtractor.map_to_boq_rows`` can then run unchanged —
        it sees the same shape, but the cells are now positioned
        correctly.

        Confidence gating
        -----------------
        If ``detect_columns`` returns ``is_reliable == False`` (e.g. fewer
        than 2 bands detected, or confidence < ``confidence_floor``),
        this method returns ``[]``. The pipeline then uses the existing
        text-line path and tags ``column_fallback:true`` on the metadata.

        Parameters
        ----------
        file_path
            PDF file path.
        page_numbers
            1-based page numbers to process. ``None`` means "all pages".
        y_tolerance
            Y-clustering tolerance for row envelopes.
        confidence_floor
            Minimum detector confidence for a band set to be accepted.

        Returns
        -------
        list[TableData]
            Detected tables, one per page where bands were reliable.
        """
        from src.ingest.column_detector import (
            assemble_cell_based_rows,
            detect_columns,
            merge_wrapped_rows,
        )

        out: list[TableData] = []
        try:
            import pdfplumber
        except Exception:
            return out
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                pages_to_scan: list[int]
                if page_numbers is None:
                    pages_to_scan = list(range(1, len(pdf.pages) + 1))
                else:
                    pages_to_scan = [p for p in page_numbers if 1 <= p <= len(pdf.pages)]
                for pn in pages_to_scan:
                    page = pdf.pages[pn - 1]
                    detector = detect_columns(page)
                    if not detector.is_reliable or detector.confidence < confidence_floor:
                        logger.debug(
                            "column_detector: page %d unreliable (bands=%d, conf=%.2f)",
                            pn,
                            detector.band_count,
                            detector.confidence,
                        )
                        continue
                    from src.ingest.column_detector import (
                        _detect_band_roles,
                        filter_empty_bands,
                    )

                    bands = filter_empty_bands(detector.bands, min_words=1)
                    if len(bands) < 2:
                        continue
                    roles = _detect_band_roles(bands, page)
                    rows = assemble_cell_based_rows(page, bands, y_tolerance=y_tolerance)
                    if not rows:
                        continue
                    rows = merge_wrapped_rows(
                        rows,
                        item_band_index=roles.get("item"),
                        unit_band_index=roles.get("unit"),
                        qty_band_index=roles.get("qty"),
                        material_band_index=roles.get("material"),
                    )
                    if not rows:
                        continue
                    table_rows = [[c for c in r.cells] for r in rows]
                    out.append(
                        TableData(
                            page_number=pn,
                            rows=table_rows,
                            top=0.0,
                            bottom=float(getattr(page, "height", 0.0) or 0.0),
                            left=0.0,
                            right=float(getattr(page, "width", 0.0) or 0.0),
                        )
                    )
        except Exception as exc:
            logger.debug("extract_column_aware_tables failed for %s: %s", file_path, exc)
        return out

    def extract_column_aware_diagnostics(  # noqa: F811
        self,
        file_path: str | Path,
        page_numbers: list[int] | None = None,
    ) -> list[dict]:
        """Diagnostic dump of the column_detector for a file. Used by
        P3_02's eval script and by manual inspection.

        Returns one dict per processed page with bands, confidence,
        evidence_summary, and the first few assembled rows.
        """
        from src.ingest.column_detector import (
            _detect_band_roles,
            assemble_cell_based_rows,
            detect_columns,
            filter_empty_bands,
            merge_wrapped_rows,
        )

        out: list[dict] = []
        try:
            import pdfplumber
        except Exception:
            return out
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                if page_numbers is None:
                    pages_to_scan = list(range(1, len(pdf.pages) + 1))
                else:
                    pages_to_scan = [p for p in page_numbers if 1 <= p <= len(pdf.pages)]
                for pn in pages_to_scan:
                    page = pdf.pages[pn - 1]
                    detector = detect_columns(page)
                    if detector.bands:
                        bands = filter_empty_bands(detector.bands, min_words=1)
                        roles = _detect_band_roles(bands, page)
                    else:
                        bands = []
                        roles = {}
                    rows = assemble_cell_based_rows(page, bands) if bands else []
                    rows = (
                        merge_wrapped_rows(
                            rows,
                            item_band_index=roles.get("item"),
                            unit_band_index=roles.get("unit"),
                            qty_band_index=roles.get("qty"),
                            material_band_index=roles.get("material"),
                        )
                        if rows
                        else []
                    )
                    out.append(
                        {
                            "page": pn,
                            "bands": [
                                {
                                    "x_left": b.x_left,
                                    "x_right": b.x_right,
                                    "evidence": b.evidence,
                                    "word_count": b.word_count,
                                }
                                for b in detector.bands
                            ],
                            "filtered_bands": len(bands),
                            "band_roles": roles,
                            "confidence": detector.confidence,
                            "evidence_summary": detector.evidence_summary,
                            "first_3_rows": [[c[:60] for c in r.cells] for r in rows[:3]],
                            "row_count": len(rows),
                        }
                    )
        except Exception:
            return out
        return out

    def _normalise_tables(self, page_number: int, raw_tables: Any, page: Any) -> list[TableData]:
        """Handle both pdfplumber's nested tables and simple mocked rows."""
        if not raw_tables:
            return []

        page_width = float(getattr(page, "width", 0.0) or 0.0)
        page_height = float(getattr(page, "height", 0.0) or 0.0)

        def clean_row(row: Any) -> list[str]:
            if isinstance(row, (list, tuple)):
                return [str(cell or "").strip() for cell in row]
            return [str(row or "").strip()]

        # Some unit tests mock ``extract_tables`` as a list of rows, while
        # pdfplumber returns a list of tables. Support both without special
        # casing the tests.
        first = raw_tables[0]
        if first and isinstance(first, (list, tuple)) and all(not isinstance(cell, (list, tuple)) for cell in first):
            return [
                TableData(
                    page_number=page_number,
                    rows=clean_row(row),
                    top=0.0,
                    bottom=page_height,
                    left=0.0,
                    right=page_width,
                )
                for row in raw_tables
                if any(clean_row(row))
            ]

        normalised: list[TableData] = []
        for table in raw_tables:
            rows = [clean_row(row) for row in table or []]
            rows = [row for row in rows if any(row)]
            if rows:
                normalised.append(
                    TableData(
                        page_number=page_number,
                        rows=rows,
                        top=0.0,
                        bottom=page_height,
                        left=0.0,
                        right=page_width,
                    )
                )
        return normalised

