"""Construction-aware sentence splitting."""

import re

NO_SPLIT_BEFORE = [
    re.compile(r"\bIS\s*\d+", re.IGNORECASE),
    re.compile(r"\bNo\.\s*\d+"),
    re.compile(r"\bSr\.\s*\d+"),
    re.compile(r"\bFig\.\s*\d+"),
    re.compile(r"\bCl\.\s*\d+"),
    re.compile(r"\bClause\s+\d+", re.IGNORECASE),
    re.compile(r"\bSection\s+\d+", re.IGNORECASE),
    re.compile(r"\bArticle\s+\d+", re.IGNORECASE),
    re.compile(r"\bItem\s+\d+", re.IGNORECASE),
    re.compile(r"\bASTM\s+\w+\s*\d+", re.IGNORECASE),
    re.compile(r"\bBS\s+\d+", re.IGNORECASE),
    re.compile(r"\bEN\s+\d+", re.IGNORECASE),
    re.compile(r"\bISO\s+\d+", re.IGNORECASE),
]


DECIMAL_NUM = re.compile(r"\b\d+\.\d+\b")


SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")


def _in_no_split_zone(pos: int, text: str) -> bool:
    for pat in NO_SPLIT_BEFORE:
        for m in pat.finditer(text):
            if m.start() <= pos < m.end() + 2:
                return True
    return False


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences, preserving construction references.

    Does NOT split on:
    - "IS 456", "No. 123", "Fig. 1", "Cl. 4.2", decimal numbers like "1.5"
    """
    if not text or not text.strip():
        return []

    sentences = []
    prev_end = 0

    for m in SPLIT_RE.finditer(text):
        split_pos = m.start()
        if _in_no_split_zone(split_pos, text):
            continue
        if DECIMAL_NUM.search(text[prev_end:split_pos]):
            continue
        sent = text[prev_end:split_pos].strip()
        if sent:
            sentences.append(sent)
        prev_end = m.end()

    final = text[prev_end:].strip()
    if final:
        sentences.append(final)

    return [s for s in sentences if s]


def sentence_split(text: str) -> list[str]:
    """Alias for split_into_sentences."""
    return split_into_sentences(text)


def split_sentences(text: str) -> list[str]:
    """Alias for split_into_sentences."""
    return split_into_sentences(text)
