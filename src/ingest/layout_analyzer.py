"""Lightweight document layout and section detection."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from config.constants import SectionType


@dataclass(slots=True)
class LayoutSection:
    section_type: SectionType
    title: str = ""
    content: str = ""
    page_start: int = 1
    page_end: int = 1
    start_offset: int = 0
    end_offset: int = 0
    is_table: bool = False

    @property
    def start(self) -> int:
        return self.start_offset

    @property
    def end(self) -> int:
        return self.end_offset


@dataclass(slots=True)
class LayoutAnalysis:
    sections: list[LayoutSection] = field(default_factory=list)
    is_likely_scanned: bool = False
    page_count: int = 0

    @property
    def total_pages(self) -> int:
        return self.page_count


class LayoutAnalyzer:
    def __init__(self, min_chars_per_page: int = 50) -> None:
        self.min_chars_per_page = min_chars_per_page
        self.section_patterns: dict[SectionType, list[re.Pattern[str]]] = {
            SectionType.SCOPE: [
                re.compile(r"\bSCOPE\s+OF\s+WORK\b", re.IGNORECASE),
                re.compile(r"^\s*SCOPE\b", re.IGNORECASE),
            ],
            SectionType.SPECIFICATIONS: [
                re.compile(r"\bTECHNICAL\s+SPECIFICATIONS?\b", re.IGNORECASE),
                re.compile(r"^\s*SPECIFICATIONS?\b", re.IGNORECASE),
            ],
            SectionType.SCHEDULE_OF_ITEMS: [
                re.compile(r"\bBILL\s+OF\s+QUANTITIES\b", re.IGNORECASE),
                re.compile(r"\bSCHEDULE\s+OF\s+ITEMS\b", re.IGNORECASE),
                re.compile(r"\bBOQ\b", re.IGNORECASE),
            ],
            SectionType.GENERAL: [
                re.compile(r"\bGENERAL\s+TERMS\b", re.IGNORECASE),
                re.compile(r"\bGENERAL\s+CONDITIONS\b", re.IGNORECASE),
            ],
            SectionType.COMMERCIAL: [
                re.compile(r"\bCOMMERCIAL\s+TERMS\b", re.IGNORECASE),
                re.compile(r"\bPAYMENT\s+TERMS\b", re.IGNORECASE),
            ],
            SectionType.DRAWINGS_LIST: [
                re.compile(r"\bLIST\s+OF\s+DRAWINGS\b", re.IGNORECASE),
                re.compile(r"\bDRAWINGS?\s+LIST\b", re.IGNORECASE),
            ],
            SectionType.PREAMBLE: [
                re.compile(r"\bPREAMBLE\b", re.IGNORECASE),
                re.compile(r"\bNOTICE\s+INVITING\s+TENDER\b", re.IGNORECASE),
            ],
        }

    def analyze(self, pages_text: str | list[tuple[int, str]], total_pages: int | None = None) -> LayoutAnalysis:
        pages = self._coerce_pages(pages_text)
        page_count = total_pages if total_pages is not None else len(pages)
        if not pages:
            return LayoutAnalysis(page_count=0)

        sections: list[LayoutSection] = []
        absolute_offset = 0
        for page_number, text in pages:
            lines = text.splitlines() or [text]
            line_offset = 0
            for line in lines:
                stripped = line.strip()
                section_type = self._detect_section_type(stripped)
                if section_type:
                    start = absolute_offset + line_offset + line.find(stripped)
                    sections.append(
                        LayoutSection(
                            section_type=section_type,
                            title=stripped,
                            content="",
                            page_start=page_number,
                            page_end=page_number,
                            start_offset=max(start, 0),
                            end_offset=max(start, 0) + len(stripped),
                            is_table=self._is_table_line(stripped),
                        )
                    )
                line_offset += len(line) + 1
            absolute_offset += len(text) + 1

        sections.sort(key=lambda section: (section.page_start, section.start_offset))
        return LayoutAnalysis(
            sections=sections,
            is_likely_scanned=self._detect_scanned_layout(pages),
            page_count=page_count,
        )

    def _coerce_pages(self, pages_text: str | list[tuple[int, str]]) -> list[tuple[int, str]]:
        if isinstance(pages_text, str):
            return [(1, pages_text)]
        return [(int(page), text or "") for page, text in pages_text]

    def _detect_section_type(self, line: str) -> SectionType | None:
        if not line:
            return None
        for section_type, patterns in self.section_patterns.items():
            if any(pattern.search(line) for pattern in patterns):
                return section_type
        return None

    def _is_table_line(self, line: str) -> bool:
        normalised = line.strip().lower()
        if normalised.count("|") >= 2:
            return True
        if re.search(r"\bitem\s*no\b", normalised):
            return True
        table_terms = {"qty", "quantity", "unit", "rate", "amount"}
        return sum(1 for term in table_terms if re.search(rf"\b{term}\b", normalised)) >= 2

    def _detect_scanned_layout(self, pages: list[tuple[int, str]]) -> bool:
        if not pages:
            return True
        avg_chars = sum(len((text or "").strip()) for _, text in pages) / len(pages)
        return avg_chars < self.min_chars_per_page

    def get_section_type_label(self, section: LayoutSection) -> str:
        return section.section_type.value
