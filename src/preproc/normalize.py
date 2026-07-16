"""Text normalization for RFQ documents."""

import re
import unicodedata


def normalize_unicode(text: str) -> str:
    """Apply NFKC Unicode normalization."""
    return unicodedata.normalize("NFKC", text)


def collapse_whitespace(text: str) -> str:
    """Collapse multiple spaces/tabs/newlines into single space."""
    return re.sub(r"[ \t]+", " ", re.sub(r"\s+", " ", text)).strip()


def remove_page_numbers(text: str) -> str:
    """Remove common page number artifacts like 'Page 1 of 5', '1/5', etc."""
    text = re.sub(r"Page\s+\d+\s+(?:of\s+)?\d+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d+\s*/\s*\d+\b", "", text)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    return text


def remove_headers_footers(text: str) -> str:
    """Remove lines that look like document headers/footers."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^(?:Confidential|Proprietary|UNCONTROLLED|DRAFT|REV\s+\d+)", stripped, re.IGNORECASE):
            continue
        if re.match(r"^\s*[-_=]{3,}\s*$", stripped):
            continue
        if len(stripped) < 3:
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def remove_special_artifacts(text: str) -> str:
    """Remove special characters and encoding artifacts."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"[\u200b-\u200f\u2028-\u202f]", "", text)
    text = re.sub(r"&\w+;", "", text)
    text = re.sub(r"%PDF-\d+", "", text)
    text = re.sub(r"^\s*Title:\s*.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r"^\s*Author:\s*.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    return text


def normalize_punctuation(text: str) -> str:
    """Normalize quotes, dashes, and other punctuation."""
    text = re.sub(r"[\u2018\u2019]", "'", text)
    text = re.sub(r"[\u201c\u201d]", '"', text)
    text = re.sub(r"[\u2013\u2014]", "-", text)
    text = re.sub(r"[\u2026]", "...", text)
    return text


def normalize(text: str) -> str:
    """Full normalization pipeline."""
    text = normalize_unicode(text)
    text = remove_special_artifacts(text)
    text = remove_page_numbers(text)
    text = remove_headers_footers(text)
    text = normalize_punctuation(text)
    text = collapse_whitespace(text)
    return text


def normalize_lines(text: str) -> str:
    """Normalize each line while preserving line breaks."""
    lines = text.split("\n")
    normalized = [collapse_whitespace(line) for line in lines]
    return "\n".join(line for line in normalized if line)
