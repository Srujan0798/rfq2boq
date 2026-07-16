"""Extract canonical material noun phrases from long pipeline-output sentences.

The pattern engine and table extractor sometimes return full BOQ row sentences
(e.g. "Supply & application of 100 mm thick lightly bonded Mineral Wool
mattresses, hooks, retainer plates ... per Schedule-A, General terms &
conditions and Instruction of Engineer In-charge.").

Human gold annotations, by contrast, contain just the material noun phrase
(e.g. "Mineral Wool mattresses hooks retainer plates casing supports wires
etc. on plain area pipes valves bends vessels etc. per Schedule").

This module extracts the canonical material phrase from a long sentence by
stripping:

  1. Action prefixes (Supply & application of, Providing and fixing,
     Supply installation testing commissioning, etc.)
  2. Specification prefixes (X mm thick, density Y kg/m3, lightly bonded)
  3. Reference suffixes (as per Schedule-A, of as per Schedule, as per
     instruction of Engineer In-charge, per terms and conditions)

It is intentionally conservative: prefer to keep more text over splitting
into a wrong phrase. Determinism is required — same input must always
return same output (used in eval).
"""

from __future__ import annotations

import re

# Action prefixes (lowercase first match wins; we match case-insensitively
# against the start of the sentence).
_ACTION_PREFIXES = [
    r"supply\s*(?:&|and)\s*application\s+of\s+",
    r"supply\s*,?\s*installation\s*,?\s*testing\s*,?\s*and\s+commissioning\s+of\s+",
    r"supply\s+installation\s+testing\s+commissioning\s+of\s+",
    r"supply\s*,?\s*installation\s+of\s+",
    r"supply\s+and\s+installation\s+of\s+",
    r"testing\s+and\s+commissioning\s+of\s+",
    r"supplying\s+and\s+fixing\s+",
    r"supplying\s+and\s+applying\s+",
    r"providing\s+and\s+fixing\s+",
    r"providing\s+and\s+supplying\s+",
    r"providing\s*,?\s*supplying\s*,?\s*and\s+fixing\s+",
    r"providing\s+and\s+installation\s+of\s+",
    r"providing\s+and\s+laying\s+",
    r"fabrication\s*,?\s*supplying\s+and\s+installation\s+of\s+",
    r"supplying\s+",
    r"providing\s+",
    r"supply\s+",
    r"providing\s+&?\s+",
    r"supplyinstallationof\s+",
    r"supplyandinstallationof\s+",
    r"testingandcommissioningof\s+",
    r"supply,?\s*installation\s*and\s*testing\s*of",
]

# Reference suffixes — strip from the end. Match case-insensitive.
_REFERENCE_SUFFIXES = [
    r"\s+of\s+as\s+per\s+schedule[\-\s]?[a-z0-9]*\.?.*$",
    r"\s+as\s+per\s+schedule[\-\s]?[a-z0-9]*\.?.*$",
    r"\s+per\s+schedule[\-\s]?[a-z0-9]*\.?.*$",
    r"\s+as\s+per\s+instruction\s+of\s+engineer\s+in[\-\s]?charge.*$",
    r"\s+as\s+per\s+instructions?\s+of\s+(?:the\s+)?(?:site\s+)?(?:engineer|supervisor).*$",
    r"\s+as\s+per\s+general\s+terms?\s+(&|and)\s+conditions?.*$",
    r"\s+as\s+per\s+terms?\s+(&|and)\s+conditions?.*$",
    r"\s+general\s+terms?\s+(&|and)\s+conditions?\s+and\s+instructions?.*$",
    r"\s+of\s+general\s+terms?\s+(&|and)\s+conditions?.*$",
    r"\s+as\s+per\s+approved\s+guidelines.*$",
    r"\s+as\s+per\s+specifications?.*$",
    r"\s+as\s+per\s+drawings?.*$",
    r"\s+as\s+per\s+direction\s+of\s+engineer.*$",
    r"\s+as\s+per\s+site\s+conditions?.*$",
    r"\s+as\s+directed\s+by\s+engineer.*$",
    r"\s+including\s+adhesive\s+required\s+for\s+insulation\s+application.*$",
    r"\s+with\s+all\s+accessories.*$",
    r"\s+complete\s+in\s+all\s+respects?.*$",
    r"\s+per\s+schedule\s*$",
    r"\s+etc\.?\s*$",
]

# Specification prefixes to strip from the front of the material phrase
# (e.g. "100 mm thick lightly bonded Mineral Wool" -> "Mineral Wool").
_SPEC_PREFIXES = [
    r"^\s*\d+(?:\.\d+)?\s*(?:mm|cm|m|inch|in)\s+thick\s+",
    r"^\s*\d+(?:\.\d+)?\s*(?:mm|cm|m|inch|in)\s+dia(?:meter)?\s+",
    r"^\s*lightly\s+(?:resin\s+)?bonded\s+",
    r"^\s*resin\s+bonded\s+",
    r"^\s*self\s+",
    r"^\s*type\s+[a-z0-9\-]+\s+",
    r"^\s*grade\s+[a-z0-9\-]+\s+",
    r"^\s*first\s+layer\s+of\s+",
    r"^\s*second\s+layer\s+of\s+",
    r"^\s*closed\s+cell\s+",
    r"^\s*open\s+cell\s+",
    r"^\s*density\s+\d+\s*(?:to\s+\d+\s*)?(?:kg|g|lb)/(?:m[23]|cubic\s*m(?:eter|etre)?)\s+",
    r"^\s*having\s+density\s+.*?\s+kg/(?:m[23]|cubic\s*m(?:eter|etre)?)\s+",
    r"^\s*with\s+minimum\s+(?:stc|nrc|density)\s+.*?\s+d[bp]?\s+",
    r"^\s*fm\s+approved\s+",
    r"^\s*armaflex\s+",
]

_TRAILING_SPEC = [
    r"\s+of\s+(?:[\d\.]+\s*)?mm\s+thickness\s*$",
    r"\s+having\s+density\s+.*$",
    r"\s+density\s+.*$",
    r"\s+with\s+.*$",
    r"\s+on\s+\d+(?:\.\d+)?\s*NB\s+(?:to|/|-)\s+.*$",
]

# Tokens that mark where a unit/quantity starts; everything from this token
# onward is dropped from the material phrase. We keep dimensions like
# "300 mm dia" because gold for 04_adani expects them.
_DIMENSION_TOKENS_BEFORE_UNIT = re.compile(
    r"\s+\d+(?:\.\d+)?\s*(?:mm|cm|m|kg|g|ton|tonne|ltr|liter|litre)\s*$",
    re.IGNORECASE,
)


def _strip_action_prefix(text: str) -> str:
    lower = text.lower()
    for pattern in _ACTION_PREFIXES:
        m = re.match(pattern, lower)
        if m:
            return text[m.end() :]
    return text


def _strip_reference_suffix(text: str) -> str:
    lower = text.lower()
    for pattern in _REFERENCE_SUFFIXES:
        m = re.search(pattern, lower)
        if m and m.start() > 0:
            return text[: m.start()]
    return text


def _strip_spec_prefix(text: str) -> str:
    """Strip specification prefixes conservatively.

    For short dimension items like "300 mm dia pipes", stripping the
    dimension leaves just "pipes" which is too short to be a canonical
    material phrase. We only apply a spec strip if the result is still
    a meaningful phrase (>= 15 chars after stripping).
    """
    original = text
    out = text
    changed = True
    iterations = 0
    while changed and iterations < 5:
        changed = False
        for pattern in _SPEC_PREFIXES:
            new = re.sub(pattern, "", out, count=1, flags=re.IGNORECASE)
            if new != out and len(new.strip()) >= 15:
                out = new
                changed = True
                break
        iterations += 1
    if len(out.strip()) < 15:
        return original
    return out


def _strip_trailing_spec(text: str) -> str:
    out = text
    changed = True
    iterations = 0
    while changed and iterations < 5:
        changed = False
        for pattern in _TRAILING_SPEC:
            new = re.sub(pattern, "", out, count=1, flags=re.IGNORECASE)
            if new != out:
                out = new
                changed = True
                break
        iterations += 1
    return out


def _truncate_long_material(text: str) -> str:
    """Truncate material strings longer than 200 characters."""
    if len(text) <= 200:
        return text
    # Try to truncate at first sentence boundary (period, semicolon)
    m = re.search(r"[.;]", text)
    if m:
        truncated = text[:m.start()]
        if len(truncated) >= 15:  # ensure we don't truncate too short
            return truncated
    # If no sentence boundary, try to truncate at first known suffix
    for pattern in _REFERENCE_SUFFIXES:
        m = re.search(pattern, text.lower())
        if m and m.start() > 0:
            truncated = text[:m.start()]
            if len(truncated) >= 15:
                return truncated
    # If still too long, truncate at 200 chars
    return text[:200]


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" ,.;:-")


def extract_canonical_material(sentence: str) -> str:
    """Extract the canonical material noun phrase from a long BOQ-row sentence.

    Conservative: returns the stripped sentence. Does NOT split on commas
    (splitting is too aggressive and breaks legitimate compound materials
    like "hooks, retainer plates, casing supports, wires etc.").

    Same input always returns the same output. No external state, no LLM.
    """
    if not sentence or not sentence.strip():
        return ""

    text = sentence.strip()
    text = _strip_action_prefix(text)
    text = _strip_reference_suffix(text)
    text = _strip_spec_prefix(text)
    text = _strip_trailing_spec(text)
    text = _truncate_long_material(text)
    text = _normalize_whitespace(text)
    return text


def extract_canonical_material_batch(sentences: list[str]) -> list[str]:
    """Batch wrapper. Same length as input, deterministic."""
    return [extract_canonical_material(s) for s in sentences]
