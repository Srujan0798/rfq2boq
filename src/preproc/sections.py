"""Section classification for RFQ documents."""

import re

from config.constants import SectionType

SECTION_KEYWORDS: dict[SectionType, list[str]] = {
    SectionType.PREAMBLE: [
        "preamble", "general description", "scope of work", "project description",
        "introduction", "background", "scope", "general", "project overview",
    ],
    SectionType.SCOPE: [
        "scope of work", "scope of the work", "scope", "work scope", "scope item",
        "schedule of items", "bill of quantities", "boq", "item description",
        "description of items", "schedule", "bill of materials",
    ],
    SectionType.SCHEDULE_OF_ITEMS: [
        "schedule of items", "schedule of rates", "bill of quantities", "boq",
        "item schedule", "price schedule", "rate schedule", "quantity schedule",
    ],
    SectionType.SPECIFICATIONS: [
        "specification", "specifications", "technical specification", "tech spec",
        "material specification", "workmanship", "quality requirement",
        "acceptance criteria", "standard", "standards", "codes", "code of practice",
    ],
    SectionType.DRAWINGS_LIST: [
        "drawing", "drawings", "drawing list", "list of drawings", "drawing numbers",
        "architectural drawings", "structural drawings", "plans", "sketches",
    ],
    SectionType.COMMERCIAL: [
        "commercial", "payment terms", "price", "rates", "cost", "bid", "tender",
        "quoted price", " lumpsum", "basis of pricing", "taxes", "gst", "terms of payment",
    ],
    SectionType.GENERAL: [
        "general terms", "general conditions", "terms and conditions", "t&c",
        "condition of contract", "general", "miscellaneous", "others", "note", "notes",
    ],
}

SECTION_PATTERNS: dict[SectionType, list[re.Pattern]] = {
    st: [re.compile(r"\b" + kw + r"\b", re.IGNORECASE) for kw in kws]
    for st, kws in SECTION_KEYWORDS.items()
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
            sections.append({
                "title": current_title.strip(),
                "type": section_type,
                "content": content,
                "line_count": len(current_lines),
            })
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
