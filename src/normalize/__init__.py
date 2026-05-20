"""Normalization module — canonical forms and deduplication."""

from src.normalize.canonical import canonical_dimension, canonical_quantity, canonical_unit, enforce_boq_schema
from src.normalize.dedup import dedup_boq_items, levenshtein_distance, similar_material

__all__ = [
    "canonical_unit",
    "canonical_quantity",
    "canonical_dimension",
    "enforce_boq_schema",
    "dedup_boq_items",
    "similar_material",
    "levenshtein_distance",
]
