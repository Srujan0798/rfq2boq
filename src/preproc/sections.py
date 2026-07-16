"""Section classification for RFQ documents."""

import re
from enum import Enum

from config.constants import SectionType

SECTION_KEYWORDS: dict[SectionType, list[str]] = {
    SectionType.PREAMBLE: [
        "preamble",
        "general description",
        "scope of work",
        "project description",
        "introduction",
        "background",
        "scope",
        "general",
        "project overview",
    ],
    SectionType.SCOPE: [
        "scope of work",
        "scope of the work",
        "scope",
        "work scope",
        "scope item",
        "schedule of items",
        "bill of quantities",
        "boq",
        "item description",
        "description of items",
        "schedule",
        "bill of materials",
    ],
    SectionType.SCHEDULE_OF_ITEMS: [
        "schedule of items",
        "schedule of rates",
        "bill of quantities",
        "boq",
        "item schedule",
        "price schedule",
        "rate schedule",
        "quantity schedule",
    ],
    SectionType.SPECIFICATIONS: [
        "specification",
        "specifications",
        "technical specification",
        "tech spec",
        "material specification",
        "workmanship",
        "quality requirement",
        "acceptance criteria",
        "standard",
        "standards",
        "codes",
        "code of practice",
    ],
    SectionType.DRAWINGS_LIST: [
        "drawing",
        "drawings",
        "drawing list",
        "list of drawings",
        "drawing numbers",
        "architectural drawings",
        "structural drawings",
        "plans",
        "sketches",
    ],
    SectionType.COMMERCIAL: [
        "commercial",
        "payment terms",
        "price",
        "rates",
        "cost",
        "bid",
        "tender",
        "quoted price",
        " lumpsum",
        "basis of pricing",
        "taxes",
        "gst",
        "terms of payment",
        "validity of tender",
        "bank guarantee",
        "safety goggle",
        "safety helmet",
        "insurance",
        "penalty",
        "liquidated damages",
        "performance security",
    ],
    SectionType.GENERAL: [
        "general terms",
        "general conditions",
        "terms and conditions",
        "t&c",
        "condition of contract",
        "general",
        "miscellaneous",
        "others",
        "note",
        "notes",
    ],
}

SECTION_PATTERNS: dict[SectionType, list[re.Pattern]] = {
    st: [re.compile(r"\b" + kw + r"\b", re.IGNORECASE) for kw in kws] for st, kws in SECTION_KEYWORDS.items()
}

HEADING_PATTERN = re.compile(r"^(\d+\.\d*\s*|[\w\s]+:)\s*(.*)$", re.MULTILINE)


def classify_section(title: str, content: str = "") -> SectionType:
    """Classify a section based on its title and optional content."""
    text = (title + " " + content).lower()

    scores: dict[SectionType, float] = {st: 0.0 for st in SectionType}

    for st, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(title):
                scores[st] += 3.0
            if pattern.search(text):
                scores[st] += 1.0

    if scores[SectionType.PREAMBLE] > 0 and "scope" in text and "work" in text:
        scores[SectionType.SCOPE] += 1.5
    if "bill of quantities" in text or "boq" in text:
        scores[SectionType.SCHEDULE_OF_ITEMS] += 2.0
        scores[SectionType.SCOPE] += 0.5
    if re.search(r"\d+\.\d+\s*mm|\d+\.\d+\s*cm", text):
        scores[SectionType.SPECIFICATIONS] += 0.5

    best_score = max(scores.values())
    if best_score == 0:
        return SectionType.GENERAL

    for st in SectionType:
        if scores[st] == best_score:
            return st

    return SectionType.GENERAL


def extract_sections(text: str) -> list[dict]:
    """Extract sections from document text."""
    lines = text.split("\n")
    sections = []
    current_title = ""
    current_lines: list[str] = []

    def flush():
        nonlocal current_title, current_lines
        if current_title or current_lines:
            content = "\n".join(current_lines).strip()
            section_type = classify_section(current_title, content)
            sections.append(
                {
                    "title": current_title.strip(),
                    "type": section_type,
                    "content": content,
                    "line_count": len(current_lines),
                }
            )
            current_title = ""
            current_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        is_heading = False
        if re.match(r"^\d+\.\d+\s+[A-Z]", stripped) or re.match(r"^[A-Z][A-Z\s]{5,}:", stripped):
            is_heading = True

        if is_heading and len(stripped) < 100:
            flush()
            current_title = stripped
            current_lines = []
        else:
            current_lines.append(line)

    flush()
    return sections


def get_section_type_name(section_type: SectionType) -> str:
    return section_type.name


class PageSectionType(Enum):
    UNKNOWN = "UNKNOWN"
    BOQ = "BOQ"
    FRONT_MATTER = "FRONT_MATTER"
    TECHNICAL_SPEC = "TECHNICAL_SPEC"
    GENERAL_CONDITIONS = "GENERAL_CONDITIONS"
    ANNEXURE = "ANNEXURE"
    COMMERCIAL = "COMMERCIAL"


def _get_markers():
    return {
        "BOQ": [
            "bill of quantities",
            "boq schedule",
            "schedule of quantities",
            "abstract of quantities",
            "schedule of items",
        ],
        "FRONT_MATTER": [
            "notice inviting tender",
            "nit - notice",
            "instructions to bidders",
            "emd details",
            "eligibility criteria",
            "schedule a - eligibility criteria",
        ],
        "TECHNICAL_SPEC": ["technical specifications", "technical specification"],
        "GENERAL_CONDITIONS": ["general conditions of contract"],
        "ANNEXURE": ["annexure"],
        "COMMERCIAL": [
            "validity of tender",
            "safety goggles",
            "ppe requirements",
            "insurance",
            "penalty",
            "liquidated damages",
            "bank guarantee",
        ],
    }


class SectionClassifier:
    def __init__(self):
        self.markers = _get_markers()

    def classify_page(self, text: str, page_idx: int) -> PageSectionType:
        if not text.strip():
            return PageSectionType.UNKNOWN

        lower_text = text.lower()
        lines = [line.strip().lower() for line in text.split("\n") if line.strip()]
        if not lines:
            return PageSectionType.UNKNOWN

        first_lines = " ".join(lines[:3])

        for m in self.markers["BOQ"]:
            if m in first_lines:
                return PageSectionType.BOQ

        for m in self.markers["COMMERCIAL"]:
            if m in lower_text:
                return PageSectionType.COMMERCIAL

        for m in self.markers["FRONT_MATTER"]:
            if m in first_lines:
                return PageSectionType.FRONT_MATTER

        for m in self.markers["TECHNICAL_SPEC"]:
            if m in first_lines:
                return PageSectionType.TECHNICAL_SPEC

        for m in self.markers["GENERAL_CONDITIONS"]:
            if m in first_lines:
                return PageSectionType.GENERAL_CONDITIONS

        for m in self.markers["ANNEXURE"]:
            if m in first_lines:
                return PageSectionType.ANNEXURE

        import re

        row_pattern = re.compile(r"\d+\.\d+\s+.*?\s+\d+\s+(cum|kg|sqm|m3|nos|sq|m|rm|ft)", re.IGNORECASE)
        matches = len(row_pattern.findall(text))
        if matches >= 3:
            return PageSectionType.BOQ

        return PageSectionType.UNKNOWN

    def _has_quantity_unit_pairs(self, text: str) -> bool:
        """Check if text has at least 3 quantity-unit pairs (secondary BOQ heuristic).

        Improved for PDF: searches full text (not limited to first 1000) to catch BOQ tables in real tenders.
        """
        if not text or len(text) == 0:
            return False
        import re

        # Use full page text for PDF improvement (qty-unit pairs can be anywhere in BOQ tables; original 1000-char window was limiting for real tenders)
        window = text
        # Quantity (int or decimal) followed by common construction unit
        pattern = re.compile(
            r"\b(\d+(?:\.\d+)?)\s*(cum|kg|sqm|m3|nos|sq|m|rm|ft|kg/m3|mm|cm|m|each|set|pair|lot)\b", re.IGNORECASE
        )
        matches = list(pattern.finditer(window))
        # >=3 distinct matches signals BOQ-like page
        return len(matches) >= 3

    def find_boq_pages(self, pages: list[str]) -> list[int]:
        if not pages:
            return []

        boq_pages: list[int] = []
        boq_keywords = ("bill of quantities", "schedule of items", "boq", "bill of quantity")

        for i, text in enumerate(pages):
            text_lower = text.lower()
            # Strong keyword signal for BOQ pages (helps long PDFs like 01 GSECL where BOQ is in specific sections)
            if any(kw in text_lower for kw in boq_keywords):
                boq_pages.append(i)
                continue

            if self.classify_page(text, i) == PageSectionType.BOQ:
                boq_pages.append(i)
                continue

            if len(text) > 0 and self._has_quantity_unit_pairs(text):
                # Use full text for C2 on PDF (not just first 1000) to catch BOQ tables anywhere
                boq_pages.append(i)

        if boq_pages:
            # Return exact candidate pages (sorted unique), not forced contiguous range.
            # This avoids including non-BOQ pages between sparse triggers and focuses extraction.
            return sorted(set(boq_pages))

        return list(range(len(pages)))


# ---------------------------------------------------------------------------
# SmartSectionClassifier — structural text analysis for BOQ page detection
# ---------------------------------------------------------------------------


class SmartSectionClassifier:
    """Classify PDF pages using structural text analysis.

    A true BOQ page must have:
      1. Multiple lines with BOTH item numbers AND quantity-unit pairs
      2. Short, consistent row lengths (not paragraphs)
      3. Either BOQ keywords OR clear table headers

    Spec pages are rejected because:
      - Their "item numbers" are section numbers (02.02, 9.2.2.1) not row indices
      - Lines are paragraphs, not tabular rows
      - Quantity-unit pairs are scattered in explanatory text
    """

    BOQ_KEYWORDS = [
        "bill of quantities",
        "schedule of quantities",
        "schedule of items",
        "boq",
        "bill of quantity",
        "abstract of quantities",
        "item schedule",
        "quantity schedule",
        "schedule of rates",
        "detailed estimate",
        "schedule of works",
        "price schedule",
        "schedule-b",
    ]

    SPEC_KEYWORDS = [
        "technical specification",
        "specification",
        "workmanship",
        "quality requirement",
        "acceptance criteria",
        "code of practice",
        "general conditions",
        "terms and conditions",
        "validity of tender",
        "bank guarantee",
        "insurance",
        "liquidated damages",
        "penalty",
        "safety",
        "ppe",
        "scope of work",
        "general description",
        "measurement formula",
        "formula -a",
        "measurement are indicated",
    ]

    STRONG_BOQ_HEADERS = [
        "item no",
        "item no.",
        "item number",
        "s.no",
        "s.no.",
        "sr.no",
        "description of item",
        "description of work",
        "material description",
        "quantity",
        "qty",
        "rate",
        "amount",
        "abstract",
    ]
    # "unit" is excluded from simple substring matching because it false-positives on
    # "Unit No. 8", "Turbine Unit", etc. We require "unit" to appear as a table header
    # (bounded by word boundaries and not followed by "no").
    _UNIT_HEADER_RE = re.compile(r"\bunit\b(?!\s*no)", re.IGNORECASE)

    BOQ_UNITS = [
        "cum",
        "kg",
        "sqm",
        "m3",
        "nos",
        "sq",
        "m",
        "rm",
        "ft",
        "kg/m3",
        "mm",
        "cm",
        "each",
        "set",
        "pair",
        "lot",
        "no.",
        "rmt",
        "lm",
        "sft",
        "cft",
        "ft3",
        "ft2",
        "m2",
        "m²",
        "running meter",
        "running metre",
        "sq.m",
        "sq.mtr",
    ]

    def __init__(self):
        self.qty_unit_pattern = re.compile(
            r"\b(\d+(?:\.\d+)?)\s*(" + "|".join(re.escape(u) for u in self.BOQ_UNITS) + r")\b",
            re.IGNORECASE,
        )
        self.spec_section_pattern = re.compile(r"^\d+\.\d+(?:\.\d+)+[\.\s]")
        self.simple_number_pattern = re.compile(r"^(\d+)[\.\)\s]")

    def _is_boq_row(self, line: str) -> bool:
        line = line.strip()
        if len(line) > 250 or len(line) < 15:
            return False
        if self.spec_section_pattern.match(line):
            return False
        if not self.simple_number_pattern.match(line):
            return False
        return bool(self.qty_unit_pattern.search(line))

    def _is_spec_section_line(self, line: str) -> bool:
        return bool(self.spec_section_pattern.match(line.strip()))

    def _multi_line_qty_unit_pairs(self, lines: list[str]) -> int:
        """Count qty→unit pairs split across consecutive short lines (common in PDF text extraction)."""
        count = 0
        unit_re = re.compile(r"\b(" + "|".join(re.escape(u) for u in self.BOQ_UNITS) + r")\b", re.IGNORECASE)
        for i, line in enumerate(lines):
            # Line looks like a standalone quantity: item number + number, or just a number
            if not re.match(r"^(?:\d+[\.\)]\s*)?\d+(?:,\d{3})*(?:\.\d+)?\s*$", line):
                continue
            # Look at next 5 lines for a unit, combining adjacent short lines
            # because PDF text extraction often splits "Sq meter" into ["Sq", "meter"].
            for j in range(i + 1, min(i + 6, len(lines))):
                combined = " ".join(lines[i + 1 : j + 1])
                if unit_re.search(combined):
                    count += 1
                    break
        return count

    def analyse_page(self, text: str) -> dict:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            return {"is_boq": False, "score": 0.0, "reason": "empty"}

        text_lower = text.lower()
        boq_rows = sum(1 for l in lines if self._is_boq_row(l))
        multi_line_pairs = self._multi_line_qty_unit_pairs(lines)
        spec_sections = sum(1 for l in lines if self._is_spec_section_line(l))
        first_lines_lower = " ".join(lines[:8]).lower()
        header_score = sum(2 for h in self.STRONG_BOQ_HEADERS if h in first_lines_lower)
        if self._UNIT_HEADER_RE.search(first_lines_lower):
            header_score += 2
        boq_kw_score = sum(1.5 for kw in self.BOQ_KEYWORDS if kw in text_lower)
        spec_kw_score = sum(1 for kw in self.SPEC_KEYWORDS if kw in text_lower)
        total_lines = len(lines)
        paragraph_lines = sum(1 for l in lines if len(l) > 300)
        qty_unit_anywhere = len(self.qty_unit_pattern.findall(text))

        score = 0.0
        reasons = []

        if boq_rows >= 5:
            score += 8.0
            reasons.append(f"many_boq_rows({boq_rows})")
        elif boq_rows >= 3:
            score += 5.0
            reasons.append(f"boq_rows({boq_rows})")
        elif boq_rows >= 1:
            score += 1.0
            reasons.append(f"few_boq_rows({boq_rows})")

        if multi_line_pairs >= 3:
            score += 4.0
            reasons.append(f"multi_line_pairs({multi_line_pairs})")
        elif multi_line_pairs >= 1:
            score += 1.5
            reasons.append(f"multi_line_pairs({multi_line_pairs})")

        if header_score >= 4:
            score += 4.0
            reasons.append(f"strong_headers({header_score})")
        elif header_score >= 2:
            score += 2.0
            reasons.append(f"headers({header_score})")

        if boq_kw_score >= 3:
            score += 3.0
            reasons.append(f"boq_kw({boq_kw_score})")
        elif boq_kw_score >= 1.5:
            score += 1.0
            reasons.append(f"boq_kw({boq_kw_score})")

        # Strong signal: explicit schedule-b / schedule of items header combined
        # with tabular quantity lines (e.g. GSECL Schedule-B on page 61).
        if "schedule-b" in text_lower and multi_line_pairs + boq_rows >= 1:
            score += 3.0
            reasons.append("schedule_b_qty")

        if spec_sections >= 3:
            score -= 3.0
            reasons.append(f"spec_sections({spec_sections})")
        elif spec_sections >= 1:
            score -= 1.0
            reasons.append(f"spec_sections({spec_sections})")

        if spec_kw_score >= 4 and boq_rows < 3:
            score -= 2.0
            reasons.append(f"spec_heavy({spec_kw_score})")

        if paragraph_lines > total_lines * 0.4 and boq_rows < 3:
            score -= 1.5
            reasons.append("paragraph_heavy")

        if qty_unit_anywhere < 2:
            score -= 1.0
            reasons.append("few_qty_units")

        is_boq = (
            (boq_rows >= 3)
            or (score >= 5.0 and (boq_rows >= 1 or multi_line_pairs >= 2))
            or (header_score >= 4 and boq_kw_score >= 1.5)
        )

        return {
            "is_boq": is_boq,
            "score": score,
            "reasons": reasons,
            "boq_rows": boq_rows,
            "spec_sections": spec_sections,
            "paragraph_lines": paragraph_lines,
            "total_lines": total_lines,
            "header_score": header_score,
            "boq_kw_score": boq_kw_score,
            "spec_kw_score": spec_kw_score,
            "qty_unit_anywhere": qty_unit_anywhere,
            "multi_line_pairs": multi_line_pairs,
        }

    def find_boq_pages(self, pages: list[str]) -> list[int]:
        if not pages:
            return []

        boq_pages: list[int] = []
        analyses: list[dict] = []

        for i, text in enumerate(pages):
            analysis = self.analyse_page(text)
            analyses.append(analysis)
            if analysis["is_boq"]:
                boq_pages.append(i)

        if boq_pages:
            expanded = set(boq_pages)
            for p in boq_pages:
                for offset in (-1, 1):
                    adj = p + offset
                    if 0 <= adj < len(pages):
                        adj_a = analyses[adj]
                        # A blank/whitespace-only adjacent page short-circuits in
                        # analyse_page() to a minimal dict without these keys
                        # (see the `if not lines:` early return above) -- treat
                        # it as having zero BOQ signal rather than crashing.
                        if adj_a.get("boq_rows", 0) >= 1 or adj_a.get("header_score", 0) >= 2:
                            expanded.add(adj)
            return sorted(expanded)

        for i, analysis in enumerate(analyses):
            if (
                analysis.get("qty_unit_anywhere", 0) >= 5
                and analysis.get("paragraph_lines", 0) < analysis.get("total_lines", 1) * 0.2
                and analysis.get("spec_sections", 0) < 2
            ):
                boq_pages.append(i)

        if boq_pages:
            return sorted(set(boq_pages))

        # Fallback: pages with explicit "schedule-b" or "schedule of items" headers
        # and tabular content (item numbers + quantities) are BOQ pages even if
        # the classifier missed them due to interleaved text (e.g. GSECL page 61).
        for i, text in enumerate(pages):
            text_lower = text.lower()
            if "schedule-b" not in text_lower and "schedule of items" not in text_lower:
                continue
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            has_item_numbers = any(re.match(r"^\d+[\.\)]\s+", l) for l in lines)
            has_quantities = any(re.match(r"^\d+(?:,\d{3})*(?:\.\d+)?\s*$", l) for l in lines)
            if has_item_numbers and has_quantities:
                boq_pages.append(i)

        if boq_pages:
            return sorted(set(boq_pages))

        if len(pages) <= 5:
            return list(range(len(pages)))
        return []
