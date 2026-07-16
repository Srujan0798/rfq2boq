"""Variance analysis stub (pricing removed per S1 unpriced BOQ scope).

Original rate-variance removed. This module kept as placeholder
for future non-price variance (e.g. quantity anomalies) if needed by risk/conflict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any


@dataclass
class VarianceResult:
    material: str
    extracted_rate: Decimal | None = None
    expected_rate: Decimal | None = None
    variance_pct: float = 0.0
    severity: str = "n/a"
    message: str = "pricing scope removed"


@dataclass
class VarianceReport:
    item_count: int = 0
    rated_count: int = 0
    outlier_count: int = 0
    total_variance_pct: float = 0.0
    flagged_items: list[VarianceResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


class VarianceAnalyzer:
    def __init__(self, pricing_estimator_REMOVED: Any | None = None):
        # pricing_estimator_REMOVED dependency removed (pricing stripped)
        pass

    def analyze_item(self, *a, **k) -> VarianceResult:
        return VarianceResult(material=str(a[0]) if a else "unknown")

    def analyze_boq(self, items: list[Any] | None = None, *a, **k) -> VarianceReport:
        n = len(items) if items else 0
        return VarianceReport(item_count=n, rated_count=0, outlier_count=0)

    def compare_regions(self, *a, **k) -> dict[str, Any]:
        return {"note": "pricing variance removed (unpriced BOQ)"}
