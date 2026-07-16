"""Structure-aware PDF extraction — extract document outline and route to BOQ sections.

Multi-range routing (P3_01, R4):
    Real Indian tender PDFs often have BOQ in multiple disjoint locations
    — a Schedule-B in the main body, a Schedule of Quantities in an
    Annexure, and a Per-item Consignee table at the end. Returning a single
    best range (the legacy ``get_page_range_for_boq`` API) loses any of
    those that aren't the highest-scored. ``find_boq_ranges`` therefore
    scores every candidate section, applies a precision gate, merges
    overlapping/adjacent ranges, and follows explicit Annexure references.

Scoring gate:
    Each section is scored on three orthogonal features (see
    ``_score_section`` for weights):
      - heading_score (0..1): strong BOQ keywords ("bill of quantities",
        "schedule-b", "boq schedule", ...) plus medium keywords ("qty",
        "schedule of items", ...).  Schedule of Rates is a NEGATIVE
        signal (priced-only section is out of scope per task 9).
      - qty_unit_density (0..1): ratio of qty+unit pairs in the section
        heading's page text to the page's text length. A real BOQ page
        has many pairs; a spec page has none.
      - table_density (0..1): fraction of lines that look like table
        rows (multiple short aligned cells, or contain `|` separators).
        Real BOQ pages have tabular rows; spec pages have paragraphs.
    Total score = heading*0.5 + qty_unit*0.3 + table*0.2
    Threshold = 0.50 — tuned on TRAIN/DEV PDFs, see
    ``results/structure_eval/STRUCTURE_EVAL.md``.
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

logger = logging.getLogger(__name__)


@dataclass
class DocumentSection:
    """A section in a PDF document."""

    title: str
    level: int
    page_number: int
    section_number: str = ""
    keywords: list[str] = field(default_factory=list)
    text_preview: str = ""
    is_boq_likely: bool = False
    confidence: float = 0.0


@dataclass
class PageRange:
    """A contiguous page range flagged as BOQ-bearing.

    Attributes:
        start_page: 1-based inclusive start page.
        end_page: 1-based inclusive end page (start_page <= end_page).
        score: Final combined score (0..1). Higher = more likely BOQ.
        heading: Heading text of the section that triggered the range.
        source_section_page: 1-based page where the heading was found.
        features: Dict of named feature scores that produced ``score``.
        annexures_followed: Names of annexures pulled in by reference
            follow (e.g. ``["Annexure-1"]``).
    """

    start_page: int
    end_page: int
    score: float
    heading: str
    source_section_page: int
    features: dict[str, float] = field(default_factory=dict)
    annexures_followed: list[str] = field(default_factory=list)

    @property
    def page_count(self) -> int:
        return self.end_page - self.start_page + 1

    def to_dict(self) -> dict:
        return {
            "start_page": self.start_page,
            "end_page": self.end_page,
            "score": self.score,
            "heading": self.heading,
            "source_section_page": self.source_section_page,
            "features": dict(self.features),
            "annexures_followed": list(self.annexures_followed),
        }


class DocumentStructureExtractor:
    """Extract hierarchical structure from PDF and identify BOQ-containing sections."""

    # Strong BOQ indicators — these almost certainly mean BOQ content
    STRONG_BOQ_KEYWORDS = frozenset(
        {
            "bill of quantities",
            "boq",
            "schedule of quantities",
            "schedule of rates",
            "schedule a",
            "schedule b",
            "price schedule",
            "rate schedule",
            "schedule of works",
        }
    )

    # Medium BOQ indicators
    MEDIUM_BOQ_KEYWORDS = frozenset(
        {
            "quantity",
            "quantities",
            "qty",
            "qty.",
            "item no",
            "item no.",
            "sr. no",
            "s. no",
            "unit price",
            "unit rate",
            "lump sum",
            "total amount",
            "supply and installation",
            "scope of work",
            "description of work",
            "description",
        }
    )

    # Strong keywords usable for PAGE-RANGE EXTRACTION SCORING only
    # (``_score_section`` / ``find_boq_ranges``). This excludes the bare
    # "boq" token from ``STRONG_BOQ_KEYWORDS``: that 3-letter token alone
    # is too generic — it matches boilerplate portal form labels like
    # "BOQ Detail Document" that repeat once per consignee/delivery
    # entry in GeM bid PDFs (see 09_gem_bid_7439924), not real section
    # headings. Recognizing those as *headings* (via
    # ``_is_heading_line_fast``/``_is_heading_line``) is correct and
    # needed for structure-completeness reporting (they ARE BOQ-related
    # markers), but letting a bare "boq" match drive the extraction
    # scorer caused every one of those repeated labels to independently
    # anchor a page range, merging into one giant range and pulling in
    # ~9 extra non-BOQ consignee-table rows (regression caught by
    # scripts/audit_fidelity_per_doc.py). Multi-word strong phrases
    # ("bill of quantities", "schedule of quantities", "schedule a/b",
    # ...) remain unambiguous real headings and still count.
    STRONG_BOQ_KEYWORDS_FOR_SCORING = frozenset(
        {
            "bill of quantities",
            "schedule of quantities",
            "schedule of rates",
            "schedule a",
            "schedule b",
            "price schedule",
            "rate schedule",
            "schedule of works",
        }
    )

    # Weak BOQ indicators
    WEAK_BOQ_KEYWORDS = frozenset(
        {
            "technical specification",
            "annexure",
            "annex",
            "appendix",
            "scope",
            "supply",
            "installation",
            "erection",
        }
    )

    # Explicit heading patterns — these are unambiguous headings
    HEADING_PATTERNS = [
        re.compile(r"^\s*Schedule[\s\-]*[A-Z][\s\-]*", re.IGNORECASE),  # Schedule A, SCHEDULE-B
        re.compile(r"^\s*Annexure[\s\-]*\d*", re.IGNORECASE),  # Annexure 1
        re.compile(r"^\s*Appendix[\s\-]*\d*", re.IGNORECASE),  # Appendix 1
        re.compile(r"^\s*Section[\s\-]*\d+", re.IGNORECASE),  # Section 1
        re.compile(r"^\s*Part[\s\-]*\d+", re.IGNORECASE),  # Part 1
        re.compile(r"^\s*Chapter[\s\-]*\d+", re.IGNORECASE),  # Chapter 1
        re.compile(r"^\s*\d+\s*\.\s*\d+\s*\.\s*[A-Z]", re.IGNORECASE),  # 1.1. Subsection
        re.compile(r"^\s*[A-Z]\s*\.\s*\d+\s*\.\s*[A-Z]", re.IGNORECASE),  # A.1. Subsection
        re.compile(r"^\s*[IVX]+\s*\.\s*[A-Z]", re.IGNORECASE),  # I. Introduction
    ]

    # Section number patterns
    SECTION_NUMBER_RE = re.compile(
        r"^\s*(\d+(?:\.\d+)*)\s*[\.\-\)]\s*",
    )

    # Rejection: body-text verbs (ALL CAPS body sentences, not headings)
    _BODY_VERBS = frozenset(
        {
            "shall",
            "must",
            "will",
            "may",
            "can",
            "should",
            "would",
            "is",
            "are",
            "was",
            "were",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
        }
    )

    # Rejection: common body-text / spec paragraph markers (not just verbs)
    _BODY_MARKERS = frozenset(
        {
            "refer",
            "clause",
            "section",
            "figure",
            "table",
            "annexure",
            "appendix",
            "chapter",
            "para",
            "note",
            "notes",
            "below",
            "above",
            "respectively",
            "hereinafter",
            "aforesaid",
            "aforementioned",
            "vide",
            "pursuant",
        }
    )

    # Rejection: price/currency patterns
    _PRICE_RE = re.compile(r"[₹\$€£@]\s*\d+|\d+\s*[₹\$€£]|per\s+(sqm|kg|tonne|m3|cum|nos|rmt|m)", re.IGNORECASE)

    # Rejection: dimension patterns (table content, not headings)
    _DIMENSION_RE = re.compile(
        r"\d+\s*(mm|cm|m|ft|inch|kg|sqm|cum|nos|rmt)\s+(dia|thick|wide|deep|length)", re.IGNORECASE
    )

    # Rejection: common false-positive start patterns
    _BODY_START = re.compile(
        r"^\s*(note[:\s]|notes[:\s]|nb[:\s]|ref[:\s]|reference[:\s]"
        r"|to,|from,|subject[:\s]|re:|cc:|attn|encl)",
        re.IGNORECASE,
    )

    def __init__(self):
        self.sections: list[DocumentSection] = []

    def extract_structure(self, pdf_path: str | Path) -> list[DocumentSection]:
        """Extract document structure from PDF.

        Tries PyMuPDF fast scan first, falls back to pdfplumber for
        font-size analysis if fast scan finds nothing.

        Wrapped with a 30-second timeout to prevent hangs on large or
        complex PDFs (e.g. GeM tenders with embedded fonts).
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")

        def _run() -> list[DocumentSection]:
            # Try fast PyMuPDF scan first
            sections = self._extract_structure_fast(path)
            if sections:
                self.sections = sections
                return sections

            # Fall back to pdfplumber for detailed font-size analysis
            sections = self._extract_structure_pdfplumber(path)
            self.sections = sections
            return sections

        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(_run)
            try:
                return cast(list[DocumentSection], fut.result(timeout=30.0))
            except FutureTimeoutError:
                logger.warning("Document structure extraction timed out (30s) for %s", path)
                fut.cancel()
                self.sections = []
                return []
            except Exception:
                logger.warning("Document structure extraction failed for %s", path, exc_info=True)
                self.sections = []
                return []

    def _extract_structure_fast(self, path: Path) -> list[DocumentSection]:
        """Fast structure extraction using PyMuPDF.

        ~5-10x faster than pdfplumber for large documents.
        Uses regex-based heading detection without font-size analysis.
        Capped at 100 sections to prevent noise on spec-heavy PDFs.
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return []

        sections: list[DocumentSection] = []
        MAX_SECTIONS = 100

        with fitz.open(str(path)) as doc:
            # Track running headers: identical heading text appearing on
            # consecutive pages is likely a page header, not a real section.
            last_heading_text: str = ""
            last_heading_page: int = 0
            running_header_count: int = 0
            MAX_RUNNING_HEADER = 3  # same heading on 3+ consecutive pages = header

            for page_num in range(1, len(doc) + 1):
                page = doc[page_num - 1]
                text = page.get_text()
                if not text:
                    continue

                lines = text.splitlines()
                for line_text in lines[:30]:  # First 30 lines per page
                    line_text = line_text.strip()
                    if not line_text or len(line_text) < 5:
                        continue
                    if len(line_text) > 100:
                        continue

                    # Fast heading detection: regex patterns only
                    is_heading = self._is_heading_line_fast(line_text)
                    if not is_heading:
                        continue

                    # ---- Running header dedup ----
                    # If same heading text appears on consecutive pages,
                    # it's a running page header, not a real section.
                    normalized = line_text.strip().upper()
                    if normalized == last_heading_text and page_num == last_heading_page + 1:
                        running_header_count += 1
                        if running_header_count >= MAX_RUNNING_HEADER:
                            continue  # skip this running header
                    else:
                        running_header_count = 0
                    last_heading_text = normalized
                    last_heading_page = page_num

                    section_num = self._extract_section_number(line_text)
                    level = self._determine_level(line_text, section_num)

                    line_lower = line_text.lower()
                    strong_kw = [k for k in self.STRONG_BOQ_KEYWORDS if k in line_lower]
                    medium_kw = [k for k in self.MEDIUM_BOQ_KEYWORDS if k in line_lower]
                    weak_kw = [k for k in self.WEAK_BOQ_KEYWORDS if k in line_lower]

                    schedule_letter = re.search(r"schedule\s*[\-]?\s*[a-z]\b", line_lower)
                    schedule_word = re.search(r"schedule\s+of", line_lower)
                    annexure_match = re.search(r"annexure\s*[\-]?\s*\d*", line_lower)
                    appendix_match = re.search(r"appendix\s*[\-]?\s*\d*", line_lower)
                    boost = 0.0
                    if schedule_letter:
                        boost = 0.6
                    elif schedule_word:
                        boost = 0.3
                    elif annexure_match or appendix_match:
                        boost = 0.2

                    is_boq = bool(strong_kw or medium_kw or boost > 0)
                    confidence = len(strong_kw) * 0.5 + len(medium_kw) * 0.2 + len(weak_kw) * 0.05 + boost
                    confidence = min(confidence, 1.0)

                    all_kw = strong_kw + medium_kw + weak_kw

                    section = DocumentSection(
                        title=line_text[:100],
                        level=level,
                        page_number=page_num,
                        section_number=section_num,
                        keywords=all_kw,
                        text_preview="",
                        is_boq_likely=is_boq,
                        confidence=confidence,
                    )
                    sections.append(section)
                    if len(sections) >= MAX_SECTIONS:
                        logger.debug("Reached max sections (%d) for %s, stopping fast scan", MAX_SECTIONS, path)
                        return sections

        return sections

    def _extract_structure_pdfplumber(self, path: Path) -> list[DocumentSection]:
        """Detailed structure extraction using pdfplumber with font-size analysis."""
        import pdfplumber

        sections: list[DocumentSection] = []

        with pdfplumber.open(str(path)) as pdf:
            # Track running headers for dedup
            last_heading_text: str = ""
            last_heading_page: int = 0
            running_header_count: int = 0
            MAX_SECTIONS = 100

            for page_num, page in enumerate(pdf.pages, start=1):
                words = page.extract_words()
                if not words:
                    continue

                font_sizes = []
                for w in words:
                    if "height" in w:
                        font_sizes.append(w["height"])
                if not font_sizes:
                    continue
                median_size = sorted(font_sizes)[len(font_sizes) // 2]
                threshold_size = median_size * 1.2

                lines = self._group_words_into_lines(words)

                for line_words in lines[:25]:
                    line_text = " ".join(w["text"] for w in line_words).strip()
                    if not line_text or len(line_text) < 5:
                        continue

                    is_heading = self._is_heading_line(line_text, line_words, threshold_size)
                    if not is_heading:
                        continue

                    # ---- Running header dedup ----
                    normalized = line_text.strip().upper()
                    if normalized == last_heading_text and page_num == last_heading_page + 1:
                        running_header_count += 1
                        if running_header_count >= 3:
                            continue
                    else:
                        running_header_count = 0
                    last_heading_text = normalized
                    last_heading_page = page_num

                    section_num = self._extract_section_number(line_text)
                    level = self._determine_level(line_text, section_num)

                    line_lower = line_text.lower()
                    strong_kw = [k for k in self.STRONG_BOQ_KEYWORDS if k in line_lower]
                    medium_kw = [k for k in self.MEDIUM_BOQ_KEYWORDS if k in line_lower]
                    weak_kw = [k for k in self.WEAK_BOQ_KEYWORDS if k in line_lower]

                    schedule_letter = re.search(r"schedule\s*[\-]?\s*[a-z]\b", line_lower)
                    schedule_word = re.search(r"schedule\s+of", line_lower)
                    annexure_match = re.search(r"annexure\s*[\-]?\s*\d*", line_lower)
                    appendix_match = re.search(r"appendix\s*[\-]?\s*\d*", line_lower)
                    boost = 0.0
                    if schedule_letter:
                        boost = 0.6
                    elif schedule_word:
                        boost = 0.3
                    elif annexure_match or appendix_match:
                        boost = 0.2

                    is_boq = bool(strong_kw or medium_kw or boost > 0)
                    confidence = len(strong_kw) * 0.5 + len(medium_kw) * 0.2 + len(weak_kw) * 0.05 + boost
                    confidence = min(confidence, 1.0)

                    all_kw = strong_kw + medium_kw + weak_kw

                    section = DocumentSection(
                        title=line_text[:100],
                        level=level,
                        page_number=page_num,
                        section_number=section_num,
                        keywords=all_kw,
                        text_preview="",
                        is_boq_likely=is_boq,
                        confidence=confidence,
                    )
                    sections.append(section)
                    if len(sections) >= MAX_SECTIONS:
                        logger.debug(
                            "Reached max sections (%d) for %s (pdfplumber), stopping",
                            MAX_SECTIONS,
                            path,
                        )
                        return sections

        return sections

    def _is_heading_line_fast(self, text: str) -> bool:
        """Fast heading check without font-size analysis (for PyMuPDF path).

        A line is a heading only if it has unambiguous heading signals:
        explicit heading patterns, ALL CAPS, or a section number combined
        with heading-like text (ALL CAPS, BOQ keyword, or short line).
        Bare section numbers in long body-text sentences are rejected.

        Tightened to reduce false positives that cause 1000+ "sections"
        on large PDFs (e.g. GSECL 29MB spec document).
        """
        if len(text) > 80:
            return False
        if len(text) < 8:
            return False

        # ---- Global rejection: patterns that never make a heading ----
        text_lower = text.lower().strip()
        # Price/rate lines (₹ 500, @ Rs. 200, per sqm)
        if self._PRICE_RE.search(text):
            return False
        # Dimension spec lines (table content, not headings)
        if self._DIMENSION_RE.search(text):
            return False
        # Annotation / letter-header start patterns
        if self._BODY_START.match(text):
            return False
        # Body-text verbs in ALL CAPS lines → sentence, not heading
        if text.isupper():
            words = set(text_lower.split())
            if words & self._BODY_VERBS:
                return False
            # Body-text markers in ALL CAPS → spec reference, not heading
            if words & self._BODY_MARKERS:
                return False

        # Reject lines that end with common body-text suffixes
        text_stripped = text.strip()
        if text_stripped.endswith((":", ";", ",", ".", "/", "&", "-")):
            return False
        # Reject lines with excessive punctuation (>20% non-alpha)
        alpha_chars = [c for c in text_stripped if c.isalpha()]
        non_alpha_pct = 1.0 - (len(alpha_chars) / max(len(text_stripped), 1))
        if non_alpha_pct > 0.35:
            return False

        for pattern in self.HEADING_PATTERNS:
            if pattern.match(text):
                return True

        if self.SECTION_NUMBER_RE.match(text):
            after_num = self.SECTION_NUMBER_RE.sub("", text).strip()
            if len(after_num) > 5:
                after_lower = after_num.lower()
                alpha = [c for c in after_num if c.isalpha()]
                # Must have some actual text, not just numbers/symbols
                if len(alpha) < 3:
                    return False
                # ALL CAPS after the number → real heading
                if sum(1 for c in alpha if c.isupper()) / len(alpha) > 0.8:
                    return True
                # Contains a BOQ keyword → likely heading
                if any(kw in after_lower for kw in self.STRONG_BOQ_KEYWORDS | self.MEDIUM_BOQ_KEYWORDS):
                    return True
                # Short, concise line with Title Case → real heading
                if len(text) <= 35 and alpha and alpha[0].isupper():
                    return True
            # Section number without heading-like signals → body text
            return False

        # Short label-like line carrying a strong BOQ keyword (e.g. GeM
        # portal form labels like "BOQ Detail Document") — these are not
        # ALL CAPS and have no section number, but the strong keyword plus
        # short length (already passed the punctuation/length gates above)
        # is enough signal on its own. Without this, portal-style Title
        # Case labels are silently dropped and BOQ sections in GeM bids
        # go undetected (see test_boq_section_capture_completeness.py).
        if len(text) <= 50 and any(kw in text_lower for kw in self.STRONG_BOQ_KEYWORDS):
            return True

        # ALL CAPS heading without section number
        alpha = [c for c in text if c.isalpha()]
        if len(alpha) < 12:  # increased from 10
            return False
        if len(text) > 36:  # reduced from 48 — longer ALL CAPS lines are usually body text
            return False
        # Must have very high uppercase ratio (92%+)
        uppercase_ratio = sum(1 for c in alpha if c.isupper()) / len(alpha)
        if uppercase_ratio <= 0.92:
            return False
        # Final check: no body-text markers in the line
        words = set(text_lower.split())
        return not bool(words & self._BODY_MARKERS)

    def find_boq_sections(self) -> list[DocumentSection]:
        """Return sections most likely to contain BOQ data."""
        if not self.sections:
            return []

        boq_sections = [s for s in self.sections if s.is_boq_likely or s.confidence > 0.15]
        boq_sections.sort(key=lambda s: (-s.confidence, s.page_number))
        return boq_sections

    def get_page_range_for_boq(self) -> tuple[int, int] | None:
        """Return (start_page, end_page) for BOQ sections.

        Focuses on the highest-confidence section(s) rather than spanning
        the entire document. This avoids extracting 50+ pages when weak
        signals are scattered throughout.

        .. deprecated::
            Kept for backward compatibility. New callers should use
            :meth:`find_boq_ranges` which returns *all* BOQ ranges and
            preserves R1 (no silent range drop) for multi-annexure
            tenders. This method returns the highest-scored range only.
        """
        boq = self.find_boq_sections()
        if not boq:
            return None

        # Only consider high-confidence sections (confidence >= 0.3)
        high_conf = [s for s in boq if s.confidence >= 0.3]
        if not high_conf:
            # No high-confidence sections — fall back to top 2
            high_conf = boq[:2]

        if not high_conf:
            return None

        # Dedup by page number — multiple headings on the same page don't
        # expand the range.
        pages = sorted({s.page_number for s in high_conf})

        if len(pages) == 1:
            # Single high-confidence page — extract it + 5 pages after
            p = pages[0]
            return (max(1, p - 1), p + 5)

        # Multiple pages — check if they're clustered
        span = pages[-1] - pages[0]

        if span <= 10:
            # Clustered sections — extract the cluster + margin
            return (max(1, pages[0] - 1), pages[-1] + 2)

        # Scattered sections — use only the highest-confidence one
        # (prefer first in confidence order, then earliest page)
        best = high_conf[0]
        p = best.page_number
        return (max(1, p - 1), p + 5)

    # ------------------------------------------------------------------
    # Multi-range routing (P3_01, R4)
    # ------------------------------------------------------------------

    # Score threshold for promoting a section to a BOQ candidate.
    # Tuned on the TRAIN/DEV eval set in
    # ``results/structure_eval/STRUCTURE_EVAL.md``; the same threshold
    # is used in the scoring gate and exposed in tests for traceability.
    BOQ_RANGE_SCORE_THRESHOLD: float = 0.45

    # How many pages to extend a candidate range beyond its source
    # heading (forward + backward) when no other candidate is nearby.
    SINGLE_RANGE_MARGIN: int = 5
    BACKWARD_MARGIN: int = 1

    # Maximum page-span of a single range (defensive: prevents
    # pathological cases from ever returning "extract the whole 800-page
    # tender"). Ranges larger than this get clipped to
    # ``[start, start + MAX_RANGE_SPAN]``.
    MAX_RANGE_SPAN: int = 50

    # Real-world qty+unit keywords observed in the corpus (covers
    # multi-line broken cases like "Sq\nmeter", abbreviated variants,
    # and unit names sometimes spelled across two lines by PDF text
    # extraction). Kept as a class-level frozenset so the regex can be
    # compiled once.
    _QTY_UNITS: tuple[str, ...] = (
        "cum",
        "cu\\.m",
        "cu\\.? m",
        "kg",
        "kgs",
        "sq",
        "sq\\.",
        "sqm",
        "sq\\.m",
        "sq\\.mtr",
        "sq mtr",
        "sq m",
        "sq mtrs",
        "sqmtrs",
        "sq meter",
        "sq meters",
        "sq metre",
        "sq metres",
        "m2",
        "m²",
        "m3",
        "m³",
        "nos",
        "no\\.",
        "nos\\.",
        "num",
        "rmt",
        "rm",
        "lm",
        "r\\.m",
        "m",  # bare "m" — could be a length; require word-boundary match
        "each",
        "set",
        "lot",
        "tonne",
        "ton",
        "mt",
        "pcs",
        "pc",
        "pair",
        "bag",
        "bundle",
        "coil",
        "roll",
        "box",
        "can",
        "hr",
        "hour",
        "day",
        "sft",
        "cft",
        "ft2",
        "ft3",
        "mm",
        "cm",
    )
    _QTY_UNITS_RE = re.compile(
        r"\b(\d+(?:[,\d]{0,7})(?:\.\d+)?)\s*(?:" + "|".join(_QTY_UNITS) + r")\b",
        re.IGNORECASE,
    )
    # Multi-line qty+unit pattern: a line that is just a number, then
    # in the next 1-4 lines a unit keyword. PDF text extraction often
    # splits a single cell "1600\nSq\nmeter" into 3 separate lines, so
    # scanning the surrounding lines catches the unit.
    _ML_QTY_RE = re.compile(r"^\s*(\d{1,7}(?:[,\d]{0,7})(?:\.\d+)?)\s*$")
    _ML_UNIT_RE = re.compile(r"\b(" + "|".join(_QTY_UNITS) + r")\b", re.IGNORECASE)
    # Table header words that signal a real BOQ table.
    _HEADER_WORDS: tuple[str, ...] = (
        "sr.",
        "s.no",
        "s. no",
        "sr.no",
        "item no",
        "item no.",
        "sl.no",
        "description of work",
        "description of item",
        "description",
        "qty",
        "qty.",
        "quantity",
        "unit",
        "rate",
        "amount",
    )
    # Row-index pattern: "1.", "2.", "1)", "(1)", etc. — one per data row.
    _ROW_IDX_RE = re.compile(r"^\s*\(?\d{1,3}\)?[.)]\s")

    # Cached page text keyed by (path, page_number_1_indexed).
    # Lets _score_section and the annexure-follow pass share one read.
    # This is set in __init__ rather than as a dataclass field so it's
    # a real instance attribute (Field descriptors don't support
    # ``in`` checks).
    _page_text_cache: dict = None  # type: ignore[assignment]

    def _get_page_text(self, pdf_path: Path, page_number: int) -> str:
        """Return the text of a single page (1-indexed), cached.

        Uses PyMuPDF for speed. ``page_number`` is 1-indexed (matches
        ``DocumentSection.page_number`` contract and is what pipeline
        callers see). PyMuPDF is 0-indexed internally; this method
        applies the boundary safely and returns "" on out-of-range.
        """
        if self._page_text_cache is None:
            self._page_text_cache = {}
        key = (str(pdf_path), page_number)
        if key in self._page_text_cache:
            return str(self._page_text_cache[key])
        try:
            import fitz  # PyMuPDF

            with fitz.open(str(pdf_path)) as doc:
                text = "" if page_number < 1 or page_number > len(doc) else doc[page_number - 1].get_text()
        except Exception:
            logger.debug("Failed to read page %d of %s", page_number, pdf_path, exc_info=True)
            text = ""
        self._page_text_cache[key] = text
        return text

    def _annexure_follow_targets(self, text: str) -> list[str]:
        """Extract annexure/appendix identifiers referenced in ``text``.

        Used by ``find_boq_ranges`` to widen a range to cover an
        annexure explicitly named in the body text (e.g. "see Annexure-B
        for schedule of quantities"). Returns lowercase identifiers
        suitable for matching against section titles.
        """
        if not text:
            return []
        pat = re.compile(r"\b(annexure|appendix)\s*[-:]?\s*([a-z0-9]+)\b", re.IGNORECASE)
        return [f"{m.group(1).lower()}-{m.group(2).lower()}" for m in pat.finditer(text)]

    def _heading_matches_annexure(self, heading: str) -> str | None:
        """If ``heading`` is an explicit annexure/appendix heading, return
        its lowercase identifier (e.g. ``"annexure-1"``); else None."""
        m = re.match(r"^\s*(annexure|appendix)\s*[-:]?\s*([a-z0-9]+)\b", heading, re.IGNORECASE)
        if not m:
            return None
        return f"{m.group(1).lower()}-{m.group(2).lower()}"

    def _score_section(self, section: DocumentSection, page_text: str) -> tuple[float, dict[str, float]]:
        """Return (combined_score, feature_dict) for ``section``.

        ``combined_score`` is in [0, 1]. ``feature_dict`` records the
        individual feature values for transparency (and is also reported
        in the PageRange dataclass so callers can audit the routing).
        """
        title_lower = section.title.lower()

        # ---- heading score (0..1) ----
        # Uses STRONG_BOQ_KEYWORDS_FOR_SCORING (not the full
        # STRONG_BOQ_KEYWORDS set) — see its docstring: the bare "boq"
        # token is excluded here to avoid over-triggering page-range
        # extraction on repeated boilerplate form labels.
        strong_hits = sum(1 for k in self.STRONG_BOQ_KEYWORDS_FOR_SCORING if k in title_lower)
        medium_hits = sum(1 for k in self.MEDIUM_BOQ_KEYWORDS if k in title_lower)
        # Schedule of Rates is a NEGATIVE signal — priced-only sections
        # are out of scope (unpriced BOQ only) and would inflate
        # candidate counts without contributing rows.
        sor_signal = 1.0 if "schedule of rates" in title_lower else 0.0
        # "schedule" alone is weak; "schedule a/b/c" is strong.
        schedule_letter = 1.0 if re.search(r"schedule\s*[-]?\s*[a-z]\b", title_lower) else 0.0
        schedule_word = 1.0 if re.search(r"\bschedule\s+of\b", title_lower) else 0.0
        annexure_word = 1.0 if re.search(r"\b(annexure|appendix)\s*[-:]?\s*[a-z0-9]+", title_lower) else 0.0

        heading_score = min(
            1.0,
            0.45 * strong_hits
            + 0.20 * medium_hits * 0.2
            + 0.30 * schedule_letter
            + 0.15 * schedule_word
            + 0.10 * annexure_word
            - 0.50 * sor_signal,
        )
        heading_score = max(0.0, heading_score)

        # ---- qty/unit density on the section's page text ----
        # Count numeric+unit pairs (e.g. "500 kg", "100 sqm", "10 nos").
        # Also count multi-line pairs where the number and unit are on
        # adjacent lines (because PDF text extraction splits cells).
        qty_unit_count = 0
        ml_qty_count = 0
        qty_unit_density = 0.0
        row_count = 0
        header_signal = 0.0
        table_density = 0.0

        if page_text:
            # Standard inline pairs: "1600 Sq meter" or "3200 Sq"
            inline_pairs = self._QTY_UNITS_RE.findall(page_text)
            qty_unit_count = len(inline_pairs)
            # Multi-line pairs: a line that is just a number, followed
            # within 4 lines by a unit keyword.
            lines = page_text.splitlines()
            for i, line in enumerate(lines):
                stripped = line.strip()
                if not stripped:
                    continue
                if self._ML_QTY_RE.match(stripped):
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if self._ML_UNIT_RE.search(lines[j]):
                            ml_qty_count += 1
                            break
            total_pairs = qty_unit_count + ml_qty_count
            # Saturation at 15 pairs to prevent double-density from huge tables dominating.
            qty_unit_density = min(1.0, total_pairs / 15.0)

            # ---- table density ----
            # Heuristic: count real BOQ table signals on the page.
            non_empty_lines = [ln for ln in lines if ln.strip()]
            if non_empty_lines:
                # Row-index patterns: "1.", "2.", "1)", "(2)" at line start
                row_count = sum(1 for ln in non_empty_lines if self._ROW_IDX_RE.match(ln))
                # Header detection: look for table header words in the first
                # few lines (BOQ tables have a header row).
                first_ten = " ".join(non_empty_lines[:10]).lower()
                header_signal = sum(2 if hw in first_ten else 0 for hw in self._HEADER_WORDS)
                # Table density: row_count normalized to page length.
                # Real BOQ pages have 3+ row indices.
                table_density = min(1.0, row_count / max(1, len(non_empty_lines)) * 5.0)

        combined = 0.0 if heading_score < 0.10 else 0.5 * heading_score + 0.3 * qty_unit_density + 0.2 * table_density
        features = {
            "heading": round(heading_score, 3),
            "qty_unit_density": round(qty_unit_density, 3),
            "qty_unit_count": float(qty_unit_count),
            "ml_qty_count": float(ml_qty_count),
            "table_density": round(table_density, 3),
            "row_count": float(row_count),
            "header_signal": float(header_signal),
        }
        return round(combined, 3), features

    def find_boq_ranges(
        self,
        pdf_path: str | Path | None = None,
        threshold: float | None = None,
    ) -> list[PageRange]:
        """Return ALL BOQ-bearing page ranges in the document, scored + merged.

        The legacy single-range API ``get_page_range_for_boq`` picks the
        highest-scored section only. This method returns *every* section
        whose combined score exceeds ``threshold`` (default
        :attr:`BOQ_RANGE_SCORE_THRESHOLD`), expanded to a page range,
        with overlapping/adjacent ranges merged and explicit Annexure
        references followed.

        Contract:
          * Returns ``[]`` if no section scores above the threshold —
            the caller MUST then fall back to full-document extraction
            (R1: never let routing lose data).
          * Returned ranges are non-overlapping and sorted by start.
          * Each range's ``start_page`` and ``end_page`` are 1-indexed
            and inclusive; the caller can iterate ``range(r.start_page,
            r.end_page + 1)`` directly.

        Args:
            pdf_path: Optional PDF path. If supplied, page text is read
                for feature scoring (qty/unit + table density) and
                annexure-follow. If None, only the (already extracted)
                ``self.sections`` are used and feature scores that
                require page text are 0.0.
            threshold: Override the default score threshold.
        """
        if not self.sections:
            return []
        thr = self.BOQ_RANGE_SCORE_THRESHOLD if threshold is None else threshold

        # Reset per-call page-text cache so back-to-back calls on the
        # same document don't grow unbounded.
        self._page_text_cache = {}
        pdf_path_obj = Path(pdf_path) if pdf_path is not None else None

        # 1) Score every section
        scored: list[tuple[DocumentSection, float, dict[str, float]]] = []
        for sec in self.sections:
            page_text = self._get_page_text(pdf_path_obj, sec.page_number) if pdf_path_obj is not None else ""
            combined, features = self._score_section(sec, page_text)
            if combined >= thr:
                scored.append((sec, combined, features))

        if not scored:
            return []

        # 2) For each scored section, build an initial PageRange.
        raw_ranges: list[PageRange] = []
        for sec, score, features in scored:
            start = max(1, sec.page_number - self.BACKWARD_MARGIN)
            end = sec.page_number + self.SINGLE_RANGE_MARGIN
            # Cap range span defensively
            if end - start + 1 > self.MAX_RANGE_SPAN:
                end = start + self.MAX_RANGE_SPAN - 1
            raw_ranges.append(
                PageRange(
                    start_page=start,
                    end_page=end,
                    score=score,
                    heading=sec.title,
                    source_section_page=sec.page_number,
                    features=features,
                )
            )

        # 3) Follow annexure references: if a section's PAGE text
        # mentions "Annexure-X" / "Appendix-X" and the document has a
        # section whose title matches that identifier, pull that
        # section's range in. This is the R4 follow rule.
        if pdf_path_obj is not None:
            annexure_sections: dict[str, DocumentSection] = {}
            for sec in self.sections:
                ident = self._heading_matches_annexure(sec.title)
                if ident:
                    annexure_sections.setdefault(ident, sec)

            if annexure_sections:
                for r in raw_ranges:
                    matched_sec: DocumentSection | None = next((s for s, _, _ in scored if s.page_number == r.source_section_page), None)
                    if matched_sec is None:
                        continue
                    page_text = self._get_page_text(pdf_path_obj, matched_sec.page_number)
                    refs = self._annexure_follow_targets(page_text)
                    for ref in refs:
                        target = annexure_sections.get(ref)
                        if target is None:
                            continue
                        # Add a range for the referenced annexure
                        new_start = max(1, target.page_number - self.BACKWARD_MARGIN)
                        new_end = target.page_number + self.SINGLE_RANGE_MARGIN
                        if new_end - new_start + 1 > self.MAX_RANGE_SPAN:
                            new_end = new_start + self.MAX_RANGE_SPAN - 1
                        raw_ranges.append(
                            PageRange(
                                start_page=new_start,
                                end_page=new_end,
                                score=max(0.0, r.score * 0.7),  # weaker — derived, not primary
                                heading=target.title,
                                source_section_page=target.page_number,
                                features={"annexure_follow": 1.0},
                                annexures_followed=[ref],
                            )
                        )
                        if ref not in r.annexures_followed:
                            r.annexures_followed.append(ref)

        # 4) Merge overlapping / adjacent ranges (gap <= 2).
        raw_ranges.sort(key=lambda r: (r.start_page, -r.score))
        merged: list[PageRange] = []
        for r in raw_ranges:
            if merged and r.start_page <= merged[-1].end_page + 2:
                last = merged[-1]
                new_start = min(last.start_page, r.start_page)
                new_end = max(last.end_page, r.end_page)
                new_score = max(last.score, r.score)
                new_heading = last.heading if last.score >= r.score else r.heading
                new_features = {**last.features, **r.features}
                new_annexures = list(dict.fromkeys(last.annexures_followed + r.annexures_followed))
                merged[-1] = PageRange(
                    start_page=new_start,
                    end_page=new_end,
                    score=new_score,
                    heading=new_heading,
                    source_section_page=last.source_section_page,
                    features=new_features,
                    annexures_followed=new_annexures,
                )
            else:
                merged.append(r)

        merged.sort(key=lambda r: r.start_page)
        # Final clip of any range still exceeding MAX_RANGE_SPAN
        for r in merged:
            if r.end_page - r.start_page + 1 > self.MAX_RANGE_SPAN:
                r.end_page = r.start_page + self.MAX_RANGE_SPAN - 1
        return merged

    def _group_words_into_lines(self, words: list[dict]) -> list[list[dict]]:
        """Group pdfplumber words into lines by y-position."""
        if not words:
            return []

        # Sort by y-position (top), then x-position
        sorted_words = sorted(words, key=lambda w: (w.get("top", 0), w.get("x0", 0)))

        lines: list[list[dict]] = []
        current_line: list[dict] = []
        current_y = None
        y_threshold = 3  # pixels

        for w in sorted_words:
            y = w.get("top", 0)
            if current_y is None or abs(y - current_y) <= y_threshold:
                current_line.append(w)
                current_y = y
            else:
                if current_line:
                    lines.append(current_line)
                current_line = [w]
                current_y = y

        if current_line:
            lines.append(current_line)

        # Sort words within each line by x-position
        for line in lines:
            line.sort(key=lambda w: w.get("x0", 0))

        return lines

    def _is_heading_line(self, text: str, words: list[dict], threshold_size: float) -> bool:
        """Check if a line is a document heading.

        Same tightening as _is_heading_line_fast: section numbers alone are
        not enough — require heading-like signals (ALL CAPS, BOQ keyword,
        short line, or larger font size).

        Also applies body-text rejection rules from _is_heading_line_fast.
        """
        if len(text) > 80:
            return False
        if len(text) < 8:
            return False

        text_lower = text.lower().strip()

        # Reject lines ending with body-text suffixes
        text_stripped = text.strip()
        if text_stripped.endswith((":", ";", ",", ".", "/", "&", "-")):
            return False
        # Reject lines with excessive punctuation
        alpha_chars = [c for c in text_stripped if c.isalpha()]
        non_alpha_pct = 1.0 - (len(alpha_chars) / max(len(text_stripped), 1))
        if non_alpha_pct > 0.35:
            return False

        # Check explicit heading patterns first
        for pattern in self.HEADING_PATTERNS:
            if pattern.match(text):
                return True

        # Check section number — require heading-like remainder
        if self.SECTION_NUMBER_RE.match(text):
            after_num = self.SECTION_NUMBER_RE.sub("", text).strip()
            if len(after_num) > 5:
                after_lower = after_num.lower()
                alpha = [c for c in after_num if c.isalpha()]
                # Must have some actual text, not just numbers/symbols
                if len(alpha) < 3:
                    return False
                if sum(1 for c in alpha if c.isupper()) / len(alpha) > 0.8:
                    return True
                if any(kw in after_lower for kw in self.STRONG_BOQ_KEYWORDS | self.MEDIUM_BOQ_KEYWORDS):
                    return True
                if len(text) <= 35 and alpha and alpha[0].isupper():
                    return True
                # Font-size boost: larger-than-median text with section number
                sizes = [w.get("height", 0) for w in words if "height" in w]
                if sizes and max(sizes) >= threshold_size and len(text) < 60:
                    return True
            # Section number without any heading signal → body text
            return False

        # Check font size — heading should be larger than median
        sizes = [w.get("height", 0) for w in words if "height" in w]
        if sizes and max(sizes) >= threshold_size and len(text) < 60:
            return True

        # Short label-like line carrying a strong BOQ keyword (e.g. GeM
        # portal form labels like "BOQ Detail Document") — see matching
        # comment in _is_heading_line_fast for rationale.
        if len(text) <= 50 and any(kw in text_lower for kw in self.STRONG_BOQ_KEYWORDS):
            return True

        # ALL CAPS heading (strict: 92%+ uppercase, at least 12 chars, max 36 chars)
        alpha = [c for c in text if c.isalpha()]
        if len(alpha) < 12:
            return False
        if len(text) > 36:
            return False
        uppercase_ratio = sum(1 for c in alpha if c.isupper()) / len(alpha)
        if uppercase_ratio <= 0.92:
            return False
        text_words = set(text_lower.split())
        return not bool(text_words & self._BODY_MARKERS)

    def _extract_section_number(self, line: str) -> str:
        """Extract section number from a line."""
        match = self.SECTION_NUMBER_RE.match(line)
        if match:
            return match.group(1).strip()
        return ""

    def _determine_level(self, line: str, section_num: str) -> int:
        """Determine heading level."""
        if not section_num:
            if line.isupper():
                return 1
            return 2
        dots = section_num.count(".")
        return dots + 1
