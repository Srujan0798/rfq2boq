"""Variance analysis for extracted BOQ rates against historical norms.

Compares extracted rates against historical norms and flags suspiciously
low/high quotes that may indicate bid issues or extraction errors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from src.domain.cost_estimator import CostEstimator, ItemEstimate


@dataclass
class VarianceResult:
    material: str
    extracted_rate: Decimal | None
    expected_rate: Decimal | None
    variance_pct: float
    severity: str
    message: str


@dataclass
class VarianceReport:
    item_count: int
    rated_count: int
    outlier_count: int
    total_variance_pct: float
    flagged_items: list[VarianceResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


class VarianceAnalyzer:
    def __init__(self, cost_estimator: CostEstimator | None = None):
        self.cost_estimator = cost_estimator or CostEstimator()

    def analyze_item(
        self,
        material: str,
        unit: str,
        extracted_rate: Decimal | None,
        region: str | None = None,
    ) -> VarianceResult:
        rate_entry = self.cost_estimator.lookup_rate(material, unit, region)
        expected_rate = rate_entry.rate if rate_entry else None

        if extracted_rate is None or expected_rate is None or expected_rate == 0:
            severity = "unknown"
            variance_pct = 0.0
            message = "Cannot compute variance: missing rate data"
        else:
            variance_pct = float((extracted_rate - expected_rate) / expected_rate * 100)
            abs_variance = abs(variance_pct)
            if abs_variance > 50:
                severity = "critical"
                message = f"Rate is {abs_variance:.1f}% away from expected — possible extraction error"
            elif abs_variance > 25:
                severity = "high"
                message = f"Rate is {abs_variance:.1f}% away from expected — review recommended"
            elif abs_variance > 10:
                severity = "medium"
                message = f"Rate is {abs_variance:.1f}% away from expected"
            else:
                severity = "low"
                message = f"Rate within normal range ({abs_variance:.1f}% variance)"

        return VarianceResult(
            material=material,
            extracted_rate=extracted_rate,
            expected_rate=expected_rate,
            variance_pct=variance_pct,
            severity=severity,
            message=message,
        )

    def analyze_boq(
        self,
        items: list[ItemEstimate],
        region: str | None = None,
    ) -> VarianceReport:
        flagged: list[VarianceResult] = []
        variances: list[float] = []

        for item in items:
            if item.rate is None:
                continue
            result = self.analyze_item(item.material, item.unit, item.rate, region)
            if result.severity in ("critical", "high"):
                flagged.append(result)
            if result.variance_pct != 0:
                variances.append(result.variance_pct)

        total_variance_pct = sum(variances) / len(variances) if variances else 0.0

        return VarianceReport(
            item_count=len(items),
            rated_count=len([i for i in items if i.rate is not None]),
            outlier_count=len(flagged),
            total_variance_pct=round(total_variance_pct, 2),
            flagged_items=flagged,
            summary={
                "critical_count": len([f for f in flagged if f.severity == "critical"]),
                "high_count": len([f for f in flagged if f.severity == "high"]),
                "medium_count": len([f for f in flagged if f.severity == "medium"]),
                "low_count": len([f for f in flagged if f.severity == "low"]),
            },
        )

    def compare_regions(
        self,
        material: str,
        unit: str,
    ) -> dict[str, Any]:
        variance_data = self.cost_estimator.get_rate_variance(material, unit)
        return variance_data
