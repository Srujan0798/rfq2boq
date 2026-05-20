"""Regex patterns for entity extraction."""

import re

STANDARD_PATTERNS = [
    (r"IS\s*\d+(?::\d+)?", "STANDARD"),
    (r"ASTM\s+[A-Z]\d+(?:\s*\([^)]+\))?", "STANDARD"),
    (r"BS\s*EN\s*\d+(?::\d+)?", "STANDARD"),
    (r"ACI\s*\d+", "STANDARD"),
    (r"EN\s*\d+(?::\d+)?", "STANDARD"),
]

QUANTITY_PATTERNS = [
    (r"\d{1,3}(?:,\d{3})+(?:\.\d+)?", "QUANTITY"),
    (r"\d+\.\d+", "QUANTITY"),
    (r"\b\d+\b", "QUANTITY"),
]

DIMENSION_PATTERNS = [
    (r"\b\d{2,}\s*mm\b", "DIMENSION"),
    (r"\b\d{2,}\s*cm\b", "DIMENSION"),
    (r"\b\d{2,}\s*m\b", "DIMENSION"),
    (r"\d+\s*mm\s*(?:dia|diameter)\b", "DIMENSION"),
    (r"\d+\s*cm\s*(?:dia|diameter)\b", "DIMENSION"),
    (r"\d+\s*m\s*(?:x\s*\d+\s*m)?(?:\s*(?:long|wide|high))?", "DIMENSION"),
    (r"Ø\s*\d+\s*mm", "DIMENSION"),
    (r"\d+\s*mm\s*x\s*\d+\s*mm", "DIMENSION"),
]

GRADE_PATTERNS = [
    (r"M\d{1,2}\b", "GRADE"),
    (r"Fe\d{3}\b", "GRADE"),
    (r"Grade\s+[A-C]\b", "GRADE"),
    (r"Grade\s+\d+\b", "GRADE"),
    (r"Class\s+[A-C]\b", "GRADE"),
    (r"Class\s+\d+\b", "GRADE"),
]

ACTION_PATTERNS = [
    (r"\b(supply|install|provide|lay|erect|apply|fix|construct|build|pour|cast|fabricate)\b", "ACTION"),
]

MATERIAL_PATTERNS = [
    (r"\bwet mix macadam\b", "MATERIAL"),
    (r"\btack coat\b", "MATERIAL"),
    (r"\bbituminous concrete\b", "MATERIAL"),
    (r"\bgranular sub[- ]base(?:\s+type\s+[A-Z])?\b", "MATERIAL"),
    (r"\bprime coat\b", "MATERIAL"),
    (r"\baggregate base course\b", "MATERIAL"),
    (r"\bdry lean concrete\b", "MATERIAL"),
    (r"\belastomeric bearing[sd]?\b", "MATERIAL"),
    (r"\bpre[- ]stressed steel\b", "MATERIAL"),
    (r"\breinforcement steel\b", "MATERIAL"),
    (r"\bms structural steel\b", "MATERIAL"),
    (r"\bshotcrete\b", "MATERIAL"),
    (r"\bexpansion joint[sd]?\b", "MATERIAL"),
    (r"\brock anchor\b", "MATERIAL"),
    (r"\brcc pipe\b", "MATERIAL"),
    (r"\bfirst class brickwork\b", "MATERIAL"),
    (r"\bgranite flooring\b", "MATERIAL"),
    (r"\bplywood flush door\b", "MATERIAL"),
    (r"\bceramic floor tile[sd]?\b", "MATERIAL"),
    (r"\bcpvc pipe[sd]?\b", "MATERIAL"),
    (r"\bg[i]? pipe[sd]?\b", "MATERIAL"),
    (r"\bpvc conduit\b", "MATERIAL"),
    (r"\bupvc pipe[sd]?\b", "MATERIAL"),
    (r"\bgi conduit\b", "MATERIAL"),
    (r"\belectric wire\b", "MATERIAL"),
    (r"\bcopper cable\b", "MATERIAL"),
    (r"\baluminium cable\b", "MATERIAL"),
    (r"\bball valve\b", "MATERIAL"),
    (r"\bwater meter\b", "MATERIAL"),
    (r"\bdb box\b", "MATERIAL"),
    (r"\bair breaker\b", "MATERIAL"),
    (r"\bfire alarm call point\b", "MATERIAL"),
    (r"\bsanitary ware\b", "MATERIAL"),
    (r"\bsewage pump\b", "MATERIAL"),
    (r"\bpressure boosting\b", "MATERIAL"),
    (r"\bfrp tank\b", "MATERIAL"),
    (r"\bled panel light\b", "MATERIAL"),
    (r"\bceiling fan\b", "MATERIAL"),
    (r"\baluminum window[sd]?\b", "MATERIAL"),
    (r"\bearth electrode\b", "MATERIAL"),
    (r"\btmt (?:steel )?bar[sd]?\b", "MATERIAL"),
    (r"\btmt steel\b", "MATERIAL"),
    (r"\btmt bar[sd]?\b", "MATERIAL"),
    (r"\bstructural steel\b", "MATERIAL"),
    (r"\bstainless steel\b", "MATERIAL"),
    (r"\bmild steel\b", "MATERIAL"),
    (r"\bgalvanized steel\b", "MATERIAL"),
    (r"\bbeam\b", "MATERIAL"),
    (r"\bcolumn\b", "MATERIAL"),
    (r"\bslab\b", "MATERIAL"),
]


def extract_regex_entities(text: str) -> list[dict]:
    """Extract entities using regex patterns."""
    entities = []

    def add_entity(ent: dict):
        for existing in entities:
            overlaps = (
                existing["start"] <= ent["start"] < existing["end"]
                or existing["start"] < ent["end"] <= existing["end"]
            )
            if overlaps and existing["type"] == ent["type"]:
                if ent["text"] in existing["text"]:
                    return
                if existing["text"] in ent["text"]:
                    existing["text"] = ent["text"]
                    existing["start"] = ent["start"]
                    existing["end"] = ent["end"]
                    return
        entities.append(ent)

    for pattern, label in STANDARD_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            add_entity({
                "text": match.group(0),
                "type": label,
                "start": match.start(),
                "end": match.end(),
                "confidence": 0.95,
                "source": "regex",
            })

    for pattern, label in QUANTITY_PATTERNS:
        for match in re.finditer(pattern, text):
            text_val = match.group(0)
            if text_val and len(text_val) > 1:
                existing_in_range = [e for e in entities
                    if (e["start"] <= match.start() < e["end"] or
                        e["start"] < match.end() <= e["end"])]
                blocked_types = {"STANDARD", "GRADE", "DIMENSION"}
                if not any(e.get("type") in blocked_types | {label} for e in existing_in_range):
                    add_entity({
                        "text": text_val,
                        "type": label,
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.90,
                        "source": "regex",
                    })

    for pattern, label in DIMENSION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            match_text = match.group(0)
            existing_in_range = [e for e in entities
                if (e["start"] <= match.start() < e["end"] or
                    e["start"] < match.end() <= e["end"])]
            if not any(e.get("type") == label for e in existing_in_range):
                add_entity({
                    "text": match_text,
                    "type": label,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.92,
                    "source": "regex",
                })

    for pattern, label in GRADE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            match_text = match.group(0)
            existing_in_range = [e for e in entities
                if (e["start"] <= match.start() < e["end"] or
                    e["start"] < match.end() <= e["end"])]
            if not any(e.get("type") == label for e in existing_in_range):
                add_entity({
                    "text": match_text,
                    "type": label,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.93,
                    "source": "regex",
                })

    for pattern, label in ACTION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            match_text = match.group(0)
            existing_in_range = [e for e in entities
                if (e["start"] <= match.start() < e["end"] or
                    e["start"] < match.end() <= e["end"])]
            if not any(e.get("type") == label for e in existing_in_range):
                add_entity({
                    "text": match_text,
                    "type": label,
                    "start": match.start(),
                    "end": match.end(),
                    "confidence": 0.94,
                    "source": "regex",
                })

    entities.sort(key=lambda x: x["start"])
    return entities
