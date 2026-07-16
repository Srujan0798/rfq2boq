"""Text cleaning and sentence segmentation for RFQ documents."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass(slots=True)
class Sentence:
    text: str
    start: int
    end: int
    page: int = 1


@dataclass(slots=True)
class PreprocessedText:
    cleaned_text: str
    sentences: list[Sentence] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return self.cleaned_text


class TextPreprocessor:
    def __init__(self) -> None:
        self.smart_quotes = {
            "\u201c": '"',
            "\u201d": '"',
            "\u2018": "'",
            "\u2019": "'",
            "\u201e": '"',
            "\u2032": "'",
            "\u2033": '"',
        }
        self.unit_replacements = {
            "sq.m": "sqm",
            "sq. m": "sqm",
            "sq m": "sqm",
            "cu.m": "cum",
            "cu. m": "cum",
            "cu m": "cum",
        }
        self.abbreviations = {
            "TMT": "thermo mechanically treated",
            "RCC": "reinforced cement concrete",
            "GI": "galvanized iron",
            "MS": "mild steel",
            "SS": "stainless steel",
        }

    def clean(self, text: str) -> str:
        text = unicodedata.normalize("NFKC", text or "")
        for source, target in self.smart_quotes.items():
            text = text.replace(source, target)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", text)
        text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
        text = self.remove_page_numbers(text)
        for source, target in self.unit_replacements.items():
            text = re.sub(rf"\b{re.escape(source)}\b", target, text, flags=re.IGNORECASE)
        return self.normalize_whitespace(text)

    def normalize_whitespace(self, text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

    def normalize(self, text: str) -> str:
        return self.clean(text)

    def remove_page_numbers(self, text: str) -> str:
        text = re.sub(r"(?im)^\s*page\s+\d+\s*$", "", text)
        text = re.sub(r"(?m)^\s*-\s*\d+\s*-\s*$", "", text)
        # Standalone numeric lines are usually copied PDF page artefacts.
        text = re.sub(r"(?m)^\s*\d+\s*$", "", text)
        return text

    def remove_headers(self, text: str, patterns: list[str]) -> str:
        for pattern in patterns:
            text = re.sub(pattern, "", text, flags=re.MULTILINE | re.IGNORECASE)
        return text

    def remove_footers(self, text: str, patterns: list[str]) -> str:
        for pattern in patterns:
            text = re.sub(pattern, "", text, flags=re.MULTILINE | re.IGNORECASE)
        return text

    def expand_abbreviations(self, text: str) -> str:
        for abbr, expansion in self.abbreviations.items():
            text = re.sub(rf"\b{abbr}\b", expansion, text, flags=re.IGNORECASE)
        return text

    def segment_sentences(self, text: str, page: int = 1) -> list[Sentence]:
        if not text:
            return []

        sentences: list[Sentence] = []
        try:
            from src.preproc.sentence import split_into_sentences

            fragments = split_into_sentences(text)
        except Exception:
            fragments = []

        if fragments:
            search_from = 0
            for fragment in fragments:
                start = text.find(fragment, search_from)
                if start < 0:
                    start = search_from
                end = start + len(fragment)
                sentences.append(Sentence(text=fragment, start=start, end=end, page=page))
                search_from = end
            return sentences

        start = 0
        for match in re.finditer(r"[.!?](?:\s+|$)", text):
            end = match.end()
            fragment = text[start:end].strip()
            if fragment:
                offset = text.find(fragment, start, end)
                sentences.append(Sentence(text=fragment, start=offset, end=offset + len(fragment), page=page))
            start = end

        if start < len(text):
            fragment = text[start:].strip()
            if fragment:
                offset = text.find(fragment, start)
                sentences.append(Sentence(text=fragment, start=offset, end=offset + len(fragment), page=page))

        return sentences or [Sentence(text=text.strip(), start=0, end=len(text.strip()), page=page)]

    def preprocess(self, text: str, page: int = 1) -> PreprocessedText:
        cleaned = self.clean(text)
        return PreprocessedText(cleaned_text=cleaned, sentences=self.segment_sentences(cleaned, page=page))
