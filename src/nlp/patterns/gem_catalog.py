"""GeM (Government e-Marketplace) product catalog integration for NER.

This module loads SWA's authoritative GeM product catalog (ingested verbatim
into ``data/ontology/gem_catalog.json`` by ``scripts/ingest_gem_catalog.py``)
and exposes a closed-vocabulary gazetteer for MATERIAL entity recognition and
validation.

R2 — the catalog is the single authoritative reference. There are NO
hard-coded product strings in this module: every entry comes from the JSON,
which is byte-for-byte identical to ``resources/PUBLISH PRODUCT.xlsx``
(SWA's sacred, read-only workbook).

Matching is exact-after-normalization only. Normalization is limited to:
  - case folding
  - whitespace collapse (handles doubled spaces and trailing form-feeds)
  - common OCR artifacts: ``0``/``O`` swaps within alphanumeric tokens

No paraphrase / fuzzy / edit-distance expansion is performed: the entire
point of R2 is exact standardized vocabulary.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Catalog JSON loading
# ---------------------------------------------------------------------------

_CATALOG_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "ontology" / "gem_catalog.json"


class GemProduct:
    """One verbatim product row from the GeM catalog."""

    __slots__ = ("row_no", "name", "product_id", "normalized_name")

    def __init__(self, row_no: int, name: str, product_id: str, normalized_name: str) -> None:
        self.row_no = row_no
        self.name = name
        self.product_id = product_id
        self.normalized_name = normalized_name

    def to_dict(self) -> dict[str, Any]:
        return {"row_no": self.row_no, "name": self.name, "product_id": self.product_id}

    def __repr__(self) -> str:
        return f"GemProduct(row_no={self.row_no}, name={self.name!r}, product_id={self.product_id!r})"


def _normalize(text: str) -> str:
    """Normalize a material string for exact-match comparison.

    Limited, deterministic cleanup only — no fuzzy expansion:
      * lowercase
      * collapse all whitespace runs (spaces, tabs, form-feeds, NBSPs) to a
        single space and strip ends (handles doubled spaces and trailing
        form-feed chars observed in GeM OCR artifacts)
      * swap ``0`` <-> ``O`` within alphanumeric tokens (common OCR artifact)
    """
    if not text:
        return ""
    t = text.lower()
    # Collapse any whitespace (incl. form-feed \x0c and NBSP \xa0) to single space.
    t = re.sub(r"\s+", " ", t, flags=re.UNICODE)
    t = t.replace("\xa0", " ")
    t = re.sub(r"\s+", " ", t).strip()

    # OCR 0/O swap: treat '0' and 'O' as interchangeable inside tokens.
    # (e.g. "F0AM TAPE" -> "FOAM TAPE", "IS: 9842" unaffected since digits stay).
    def _swap(token: str) -> str:
        # Only swap when the token mixes letters and 0/O ambiguity; leave pure
        # numeric tokens (quantities, ids) untouched.
        if not token:
            return token
        has_letter = any(c.isalpha() and c not in "oO" for c in token)
        has_zero = "0" in token
        if has_letter and has_zero:
            return token.replace("0", "o")
        return token

    return " ".join(_swap(tok) for tok in t.split(" "))


@lru_cache(maxsize=1)
def _load_catalog() -> tuple[dict[str, GemProduct], list[GemProduct], dict[str, str]]:
    """Load the catalog JSON once, returning:
    - products_by_name: keyed by verbatim product name -> GemProduct (first row wins for dup names)
    - products_in_order: list of all GemProduct rows in source order
    - normalized_index: normalized_name -> verbatim product name (for exact-after-norm lookup)
    """
    if not _CATALOG_PATH.exists():
        raise FileNotFoundError(f"GeM catalog JSON not found: {_CATALOG_PATH}")
    data = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    products_by_name: dict[str, GemProduct] = {}
    products_in_order: list[GemProduct] = []
    normalized_index: dict[str, str] = {}
    for row in data.get("products", []):
        name = row.get("name", "")
        product_id = row.get("product_id", "")
        row_no = int(row.get("row_no", 0))
        norm = _normalize(name)
        gp = GemProduct(row_no=row_no, name=name, product_id=product_id, normalized_name=norm)
        products_in_order.append(gp)
        # First row wins for duplicate names (preserves source-order precedence).
        products_by_name.setdefault(name, gp)
        normalized_index.setdefault(norm, name)
    return products_by_name, products_in_order, normalized_index


def get_gem_materials() -> dict[str, GemProduct]:
    """Return the GeM catalog keyed by verbatim product name.

    The dict contains one entry per unique product name (first source row wins
    for duplicate names like the four 'Preformed Fibrous Pipe Sections ...').
    """
    return _load_catalog()[0]


def get_gem_products_in_order() -> list[GemProduct]:
    """Return all GeM product rows in source-row order (no deduplication)."""
    return _load_catalog()[1]


def get_provenance() -> dict[str, Any]:
    """Return the ``_provenance`` block from the catalog JSON."""
    if not _CATALOG_PATH.exists():
        raise FileNotFoundError(f"GeM catalog JSON not found: {_CATALOG_PATH}")
    data: dict[str, Any] = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    prov = data.get("_provenance", {})
    return prov if isinstance(prov, dict) else {}


def is_gem_material(text: str) -> bool:
    """Return True iff ``text`` matches a GeM catalog product exactly
    (after the limited normalization defined in ``_normalize``).

    No fuzzy / paraphrase expansion is performed.
    """
    if not text or not text.strip():
        return False
    _, _, normalized_index = _load_catalog()
    return _normalize(text) in normalized_index


# ---------------------------------------------------------------------------
# Backward-compatible list symbol consumed by src.nlp.patterns.dictionary
# ---------------------------------------------------------------------------


def _catalog_names() -> list[str]:
    """Return the verbatim product names of every catalog row (in source order,
    with duplicates preserved) for downstream gazetteer wiring."""
    return [p.name for p in get_gem_products_in_order()]


# Lazily-populated catalog list. Kept as a function call result (not a module
# constant) so re-running the ingest script and re-importing reflects the new
# catalog without needing a process restart in long-lived shells. Callers that
# imported the old hard-coded list symbol get a live list object.
class _DefaultCatalogProxy(list):  # type: ignore[misc]
    """List subclass that lazily fills itself from the JSON catalog on first
    access to ``len()`` / iteration / indexing, so callers see the real
    catalog without any hard-coded strings in this module."""

    def __init__(self) -> None:
        super().__init__()
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        for name in _catalog_names():
            super().append(name)
        self._loaded = True

    def __len__(self) -> int:  # type: ignore[override]
        self._ensure_loaded()
        return super().__len__()

    def __iter__(self):
        self._ensure_loaded()
        return super().__iter__()

    def __contains__(self, item: object) -> bool:  # type: ignore[override]
        self._ensure_loaded()
        return super().__contains__(item)

    def __getitem__(self, index):  # type: ignore[override]
        self._ensure_loaded()
        return super().__getitem__(index)

    def copy(self) -> list[str]:  # type: ignore[override]
        self._ensure_loaded()
        return list(self)


DEFAULT_GEM_CATALOG: list[str] = _DefaultCatalogProxy()


# ---------------------------------------------------------------------------
# Gazetteer (phrase matcher) — kept for backward compatibility with
# src.nlp.pipeline which constructs GeMCatalogGazetteer() for MATERIAL spans.
# ---------------------------------------------------------------------------


class GeMCatalogGazetteer:
    """Gazetteer that extracts MATERIAL entities by matching against the GeM catalog.

    Uses only the JSON-loaded catalog (no hard-coded strings). Matches are
    exact-after-normalization; overlapping matches are resolved by keeping the
    longest span.
    """

    def __init__(self, catalog_path: str | Path | None = None) -> None:
        if catalog_path is not None:
            # Caller-provided path (test seam / override) — load eagerly.
            data = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
            self.catalog: list[str] = [p.get("name", "") for p in data.get("products", []) if p.get("name")]
        else:
            self.catalog = list(_catalog_names())

        self._normalized: list[str] = [_normalize(p) for p in self.catalog]
        self._catalog_set: set[str] = set(self._normalized)
        # Map normalized -> verbatim catalog name (first wins for dups).
        self._norm_to_name: dict[str, str] = {}
        for name in self.catalog:
            self._norm_to_name.setdefault(_normalize(name), name)

    def extract_materials(self, text: str) -> list[dict]:
        """Extract MATERIAL entities from text using catalog matches.

        Returns a list of dicts with keys: text, type, start, end, confidence, source.
        """
        if not text:
            return []
        entities: list[dict] = []
        # We scan the *original* text but match against normalized catalog entries
        # using word-boundary regex on the normalized form is unsafe for span
        # reporting (positions differ). Instead, do a case-insensitive literal
        # search per catalog name on the original text, with whitespace-flexible
        # regex so doubled spaces still match.
        for original_name in self.catalog:
            norm_name = _normalize(original_name)
            if not norm_name:
                continue
            # Build a whitespace-flexible, escaped regex from the catalog name tokens.
            tokens = re.escape(norm_name).split(r"\ ")
            pattern = r"(?<![A-Za-z0-9])" + r"\s+".join(tokens) + r"(?![A-Za-z0-9])"
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                start = match.start()
                end = match.end()
                entities.append(
                    {
                        "text": text[start:end],
                        "type": "MATERIAL",
                        "start": start,
                        "end": end,
                        "confidence": 0.95,
                        "source": "swa_gem_catalog",
                        "gem_product_name": original_name,
                    }
                )
        return self._remove_overlapping(entities)

    @staticmethod
    def _remove_overlapping(entities: list[dict]) -> list[dict]:
        """Remove overlapping entity matches, keeping the longest."""
        if not entities:
            return []
        sorted_entities = sorted(entities, key=lambda e: (e["start"], -(e["end"] - e["start"])))
        kept: list[dict] = []
        for e in sorted_entities:
            overlaps = any(not (e["end"] <= k["start"] or e["start"] >= k["end"]) for k in kept)
            if not overlaps:
                kept.append(e)
        return kept

    def is_in_catalog(self, text: str) -> bool:
        """Check if a text string matches any catalog entry (normalized exact)."""
        if not text or not text.strip():
            return False
        return _normalize(text) in self._catalog_set


def extract_gem_catalog_entities(text: str) -> list[dict]:
    """Convenience function: extract MATERIAL entities using the default catalog."""
    return GeMCatalogGazetteer().extract_materials(text)


def validate_gem_extraction(text: str, threshold: float = 0.85) -> bool:
    """Return True iff ``text`` exactly matches a GeM catalog product after
    normalization. The ``threshold`` argument is accepted for backward
    compatibility but ignored — R2 mandates exact standardized vocabulary,
    no fuzzy matching.

    (The authoritative validator used by the pipeline lives in
    ``src.rules.gem_validation`` and operates on lists of materials with
    GeM-doc detection; this helper remains for direct callers.)
    """
    del threshold  # unused — exact matching only per R2
    return is_gem_material(text)
