"""Entity-level matchers for the Z1 honest PDF eval.

This module re-exports the row-level matcher from `boq_matcher.py` for
backward compatibility, and exposes the new asymmetric material matcher
for the Z1 eval.

The asymmetric matcher is the fix for the gold-is-short-phrase / pred-is-
long-sentence problem documented in `results/diagnosis_pdf.md`. It does
NOT lower the threshold below 0.6 — it adds two new signals above the
0.6 threshold: containment (≥80% of gold tokens present in pred) and
substring (gold phrase literally appears in pred).
"""

from __future__ import annotations

from src.eval.boq_matcher import (
    MatchResult,
    format_match_report,
    match_boq_rows,
)
from src.eval.material_matcher import (
    containment_score,
    jaccard_score,
    match_material,
    match_materials_asymmetric,
    sequence_score,
    substring_score,
)

__all__ = [
    "MatchResult",
    "format_match_report",
    "match_boq_rows",
    "containment_score",
    "jaccard_score",
    "match_material",
    "match_materials_asymmetric",
    "sequence_score",
    "substring_score",
]
