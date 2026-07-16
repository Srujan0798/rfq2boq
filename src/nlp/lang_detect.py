"""Simple language detection for English and Hindi."""


def detect_language(text: str) -> str:
    """
    Detect if text is English, Hindi, or Mixed.
    Uses Devanagari Unicode range detection.
    Returns: 'en', 'hi', or 'mixed'
    """
    if not text:
        return "en"

    devanagari_chars = sum(1 for c in text if "\u0900" <= c <= "\u097f")
    total_chars = len(text.replace(" ", "").replace("\n", ""))

    if total_chars == 0:
        return "en"

    devanagari_ratio = devanagari_chars / total_chars

    if devanagari_ratio > 0.30:
        return "hi"
    elif devanagari_ratio > 0.02:
        return "mixed"
    else:
        return "en"


def is_hindi(text: str) -> bool:
    return detect_language(text) in ("hi", "mixed")


def is_english(text: str) -> bool:
    return detect_language(text) == "en"
