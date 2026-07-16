"""Closed-catalog matcher — matches BOQ material lines against SWA's GeM catalog.

Unlike open NER (14% F1 on PDFs), this is a constrained matching problem:
we have ~19 GeM catalog items (13 unique products) and need to match each
BOQ line to one of them (or flag it as unmatched).

Matching strategy (cascading, best-score-wins):
  1. Exact match (normalized) — confidence 1.0
  2. Alias exact match — confidence 0.98
  3. Token overlap (Jaccard) — confidence scaled by overlap ratio
  4. Substring / keyword containment — confidence 0.85
  5. Edit distance (Levenshtein) — confidence scaled by similarity

Thresholds are configurable. Unmatched items are never silently dropped.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config.settings import settings

# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def _normalize(text: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation at boundaries."""
    t = text.lower().strip()
    t = re.sub(r"[^\w\s/\-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _tokenize(text: str) -> list[str]:
    """Split normalized text into tokens (words)."""
    return _normalize(text).split()


def _jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity between two token sets."""
    if not a and not b:
        return 0.0
    inter = a & b
    union = a | b
    return len(inter) / len(union) if union else 0.0


def _levenshtein_ratio(a: str, b: str) -> float:
    """Levenshtein edit-distance similarity (0..1)."""
    if a == b:
        return 1.0
    len_a, len_b = len(a), len(b)
    if len_a == 0 or len_b == 0:
        return 0.0
    # Optimized for short strings (< 100 chars)
    prev = list(range(len_b + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + cost))
        prev = curr
    dist = prev[len_b]
    max_len = max(len_a, len_b)
    return 1.0 - (dist / max_len)


# ---------------------------------------------------------------------------
# Match result
# ---------------------------------------------------------------------------


@dataclass
class CatalogMatch:
    """Result of matching one BOQ line against the GeM catalog."""

    input_text: str
    gem_id: str | None = None
    gem_name: str | None = None
    matched_alias: str | None = None
    confidence: float = 0.0
    method: str = "none"  # exact / alias_exact / token_overlap / substring / edit_distance / none
    is_unmatched: bool = True
    material: str | None = None  # catalog material field
    standards: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_text": self.input_text,
            "gem_id": self.gem_id,
            "gem_name": self.gem_name,
            "matched_alias": self.matched_alias,
            "confidence": round(self.confidence, 4),
            "method": self.method,
            "is_unmatched": self.is_unmatched,
            "material": self.material,
            "standards": self.standards,
        }


# ---------------------------------------------------------------------------
# Catalog matcher
# ---------------------------------------------------------------------------


class CatalogMatcher:
    """Match BOQ material lines against SWA's GeM catalog.

    Parameters
    ----------
    catalog_path : path to swa_gem_catalog_full.json
    ontology_path : path to insulation_materials.json (optional, for enrichment)
    exact_threshold : minimum confidence for exact matches (default 1.0)
    token_threshold : minimum Jaccard score for token-overlap match (default 0.3)
    substring_threshold : minimum token coverage for substring match (default 0.5)
    edit_threshold : minimum Levenshtein ratio for edit-distance match (default 0.7)
    """

    def __init__(
        self,
        catalog_path: str | Path | None = None,
        ontology_path: str | Path | None = None,
        exact_threshold: float = 1.0,
        token_threshold: float = 0.3,
        substring_threshold: float = 0.5,
        edit_threshold: float = 0.7,
    ) -> None:
        self.exact_threshold = exact_threshold
        self.token_threshold = token_threshold
        self.substring_threshold = substring_threshold
        self.edit_threshold = edit_threshold

        self._catalog: list[dict[str, Any]] = []
        self._normalized_index: dict[str, dict[str, Any]] = {}  # normalized_name -> product
        self._alias_index: dict[str, dict[str, Any]] = {}  # normalized_alias -> product
        self._ontology: dict[str, Any] = {}

        self._load_catalog(catalog_path)
        self._load_ontology(ontology_path)

    # -- loaders --

    def _load_catalog(self, catalog_path: str | Path | None) -> None:
        if catalog_path is None:
            catalog_path = (
                Path(__file__).resolve().parent.parent.parent / "data" / "real_rfqs" / "swa_gem_catalog_full.json"
            )
        path = Path(catalog_path)
        if not path.exists():
            raise FileNotFoundError(f"GeM catalog not found: {path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        products = data.get("products", [])
        self._catalog = products

        # Build lookup indices
        for product in products:
            name = product.get("name", "")
            norm_name = _normalize(name)
            aliases = product.get("aliases", [])

            entry = {
                "gem_id": product.get("gem_id", ""),
                "name": name,
                "material": product.get("material", ""),
                "standards": product.get("standards", []),
                "aliases": aliases,
            }
            self._normalized_index[norm_name] = entry
            for alias in aliases:
                norm_alias = _normalize(alias)
                if norm_alias not in self._alias_index:
                    self._alias_index[norm_alias] = entry

    def _load_ontology(self, ontology_path: str | Path | None) -> None:
        if ontology_path is None:
            ontology_path = (
                Path(__file__).resolve().parent.parent.parent / "data" / "ontology" / "insulation_materials.json"
            )
        path = Path(ontology_path)
        if path.exists():
            self._ontology = json.loads(path.read_text(encoding="utf-8"))
        else:
            self._ontology = {}

    # -- public API --

    @property
    def catalog_size(self) -> int:
        return len(self._catalog)

    @property
    def unique_products(self) -> int:
        return len(self._normalized_index)

    def match(self, text: str) -> CatalogMatch:
        """Match a single BOQ material line against the catalog.

        Returns a CatalogMatch with the best match found (or unmatched=True).
        """
        norm = _normalize(text)
        tokens = set(_tokenize(text))

        # 1. Exact match on product name
        if norm in self._normalized_index:
            entry = self._normalized_index[norm]
            return CatalogMatch(
                input_text=text,
                gem_id=entry["gem_id"],
                gem_name=entry["name"],
                matched_alias=entry["name"],
                confidence=1.0,
                method="exact",
                is_unmatched=False,
                material=entry["material"],
                standards=entry["standards"],
            )

        # 2. Exact match on alias
        if norm in self._alias_index:
            entry = self._alias_index[norm]
            return CatalogMatch(
                input_text=text,
                gem_id=entry["gem_id"],
                gem_name=entry["name"],
                matched_alias=norm,
                confidence=settings.CATALOG_EXACT_MATCH_CONFIDENCE,
                method="alias_exact",
                is_unmatched=False,
                material=entry["material"],
                standards=entry["standards"],
            )

        # 3. Token overlap (Jaccard) — find best match
        best_token_match: CatalogMatch | None = None
        best_token_score = 0.0

        for norm_alias, entry in self._alias_index.items():
            alias_tokens = set(norm_alias.split())
            score = _jaccard(tokens, alias_tokens)
            if score > best_token_score and score >= self.token_threshold:
                best_token_score = score
                # Scale confidence: 0.3 -> 0.6, 1.0 -> 0.95
                conf = 0.6 + 0.35 * ((score - self.token_threshold) / (1.0 - self.token_threshold))
                best_token_match = CatalogMatch(
                    input_text=text,
                    gem_id=entry["gem_id"],
                    gem_name=entry["name"],
                    matched_alias=norm_alias,
                    confidence=min(conf, 0.95),
                    method="token_overlap",
                    is_unmatched=False,
                    material=entry["material"],
                    standards=entry["standards"],
                )

        # 4. Substring / keyword containment
        best_sub_match: CatalogMatch | None = None
        best_sub_score = 0.0

        for norm_alias, entry in self._alias_index.items():
            alias_tokens = set(norm_alias.split())
            if not alias_tokens:
                continue
            # How many alias tokens appear in the input?
            overlap = alias_tokens & tokens
            coverage = len(overlap) / len(alias_tokens)
            if coverage >= self.substring_threshold and coverage > best_sub_score:
                best_sub_score = coverage
                conf = 0.7 + 0.15 * ((coverage - self.substring_threshold) / (1.0 - self.substring_threshold))
                best_sub_match = CatalogMatch(
                    input_text=text,
                    gem_id=entry["gem_id"],
                    gem_name=entry["name"],
                    matched_alias=norm_alias,
                    confidence=min(conf, 0.85),
                    method="substring",
                    is_unmatched=False,
                    material=entry["material"],
                    standards=entry["standards"],
                )

        # 5. Edit distance (Levenshtein) — only on short-ish inputs
        best_edit_match: CatalogMatch | None = None
        best_edit_score = 0.0

        if len(norm) <= 100:
            for norm_alias, entry in self._alias_index.items():
                # Compare against the alias directly (both normalized)
                ratio = _levenshtein_ratio(norm, norm_alias)
                if ratio > best_edit_score and ratio >= self.edit_threshold:
                    best_edit_score = ratio
                    # Scale confidence: 0.7 -> 0.6, 1.0 -> 0.9
                    conf = 0.6 + 0.3 * ((ratio - self.edit_threshold) / (1.0 - self.edit_threshold))
                    best_edit_match = CatalogMatch(
                        input_text=text,
                        gem_id=entry["gem_id"],
                        gem_name=entry["name"],
                        matched_alias=norm_alias,
                        confidence=min(conf, 0.90),
                        method="edit_distance",
                        is_unmatched=False,
                        material=entry["material"],
                        standards=entry["standards"],
                    )

        # Pick the best among token_overlap, substring, edit_distance
        candidates: list[CatalogMatch] = [c for c in (best_token_match, best_sub_match, best_edit_match) if c is not None]
        if candidates:
            best = max(candidates, key=lambda c: c.confidence)
            return best

        # No match found
        return CatalogMatch(
            input_text=text,
            is_unmatched=True,
            confidence=0.0,
            method="none",
        )

    def match_batch(self, texts: list[str]) -> list[CatalogMatch]:
        """Match a batch of BOQ material lines."""
        return [self.match(t) for t in texts]

    def get_catalog_summary(self) -> list[dict[str, Any]]:
        """Return a summary of all catalog entries."""
        seen: set[str] = set()
        summary = []
        for product in self._catalog:
            name = product.get("name", "")
            if name in seen:
                continue
            seen.add(name)
            summary.append(
                {
                    "gem_id": product.get("gem_id", ""),
                    "name": name,
                    "material": product.get("material", ""),
                    "aliases": product.get("aliases", []),
                    "standards": product.get("standards", []),
                }
            )
        return summary
