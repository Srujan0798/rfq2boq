"""Deduplication logic for BOQ items using Levenshtein similarity."""

from decimal import Decimal
from typing import Any


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def similar_material(m1: str, m2: str, threshold: float = 0.8) -> bool:
    """Check if two material names are similar enough to merge."""
    if not m1 or not m2:
        return False
    m1_lc = m1.lower().strip()
    m2_lc = m2.lower().strip()
    if m1_lc == m2_lc:
        return True
    max_len = max(len(m1_lc), len(m2_lc))
    if max_len == 0:
        return False
    dist = levenshtein_distance(m1_lc, m2_lc)
    similarity = 1 - (dist / max_len)
    return similarity >= threshold


def dedup_boq_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate BOQ items by merging similar materials at same location."""
    if not items:
        return []

    merged = {}
    for item in items:
        key = (
            item.get("material", "").lower().strip(),
            item.get("location", "").lower().strip(),
            item.get("grade", "").lower().strip(),
        )
        if key in merged:
            existing = merged[key]
            try:
                qty = Decimal(str(item.get("quantity", 0)))
                existing_qty = Decimal(str(existing.get("quantity", 0)))
                existing["quantity"] = existing_qty + qty
                existing["warnings"] = list(set((existing.get("warnings") or []) + ["duplicate_merged"]))
                if item.get("confidence", 0) > existing.get("confidence", 0):
                    existing["confidence"] = item.get("confidence", 0)
            except Exception:
                pass
        else:
            merged[key] = dict(item)

    return list(merged.values())
