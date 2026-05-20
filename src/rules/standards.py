"""Standards validation rules."""

import re

STANDARD_PATTERNS = [
    (re.compile(r"IS\s*[:.]?\s*(\d+)(?:\s*[:.]\s*(\d+))?", re.IGNORECASE), "IS"),
    (re.compile(r"ASTM\s+([A-Z])\s*(\d+)", re.IGNORECASE), "ASTM"),
    (re.compile(r"BS\s*EN\s*(\d+)", re.IGNORECASE), "BS EN"),
    (re.compile(r"BS\s*:\s*EN\s*(\d+)", re.IGNORECASE), "BS EN"),
    (re.compile(r"ACI\s*(\d+)", re.IGNORECASE), "ACI"),
    (re.compile(r"EN\s*(\d+)", re.IGNORECASE), "EN"),
    (re.compile(r"ISO\s*(\d+)", re.IGNORECASE), "ISO"),
]


def validate_standard(text: str) -> dict | None:
    """Validate and parse standard notation."""
    text = text.strip()

    for pattern, body in STANDARD_PATTERNS:
        match = pattern.search(text)
        if match:
            result = {
                "body": body,
                "number": match.group(1) if match.lastindex >= 1 else "",
                "year": match.group(2) if match.lastindex >= 2 and match.group(2) else "",
            }
            return result

    return None


def normalize_standard(text: str) -> str:
    """Normalize standard notation to canonical form."""
    parsed = validate_standard(text)
    if parsed:
        body = parsed["body"]
        number = parsed["number"]
        year = parsed["year"]
        if year:
            return f"{body} {number}:{year}"
        return f"{body} {number}"

    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"is(\d+)", r"IS \1", text, flags=re.IGNORECASE)
    text = re.sub(r"astm([A-Z])", r"ASTM \1", text, flags=re.IGNORECASE)
    text = re.sub(r"bsen(\d+)", r"BS EN \1", text, flags=re.IGNORECASE)

    return text


def is_recognized_standard(text: str) -> bool:
    """Check if text is a recognized standard."""
    return validate_standard(text) is not None


def get_standard_body(text: str) -> str | None:
    """Extract standard body (IS, ASTM, BS EN, etc.) from text."""
    parsed = validate_standard(text)
    if parsed:
        return parsed["body"]
    return None
