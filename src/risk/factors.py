"""Individual risk factor calculators for BOQ items."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RiskFactorResult:
    name: str
    score: float
    details: dict[str, Any]


class PriceOutlierFactor:
    def calculate(self, item: Any, norms: dict[str, tuple[float, float]]) -> RiskFactorResult:
        score = 0.0
        details = {}

        if not item.material or not item.quantity:
            return RiskFactorResult(name="price_outlier", score=0.0, details={})

        mat_key = item.material.lower()
        qty = float(item.quantity)

        for key, (norm, sigma) in norms.items():
            if key in mat_key and sigma > 0:
                z_score = abs(norm - qty) / sigma
                if z_score > 3:
                    score = 1.0
                    details = {"z_score": z_score, "norm": norm, "material": key}
                elif z_score > 2:
                    score = 0.8
                    details = {"z_score": z_score, "norm": norm, "material": key}
                elif z_score > 1.5:
                    score = 0.5
                    details = {"z_score": z_score, "norm": norm, "material": key}
                break

        return RiskFactorResult(name="price_outlier", score=score, details=details)


class ScopeAmbiguityFactor:
    def calculate(self, item: Any) -> RiskFactorResult:
        score = 0.0
        details: dict[str, Any] = {"indicators": []}

        if not item.material or len(item.material) < 3:
            score += 0.3
            details["indicators"].append("missing_or_short_material")

        if item.quantity and float(item.quantity) <= 0:
            score += 0.3
            details["indicators"].append("invalid_quantity")

        if not item.unit or item.unit in ("no.", "nos", "na"):
            score += 0.2
            details["indicators"].append("unclear_unit")

        if not item.location:
            score += 0.2
            details["indicators"].append("missing_location")

        score = min(score, 1.0)
        return RiskFactorResult(name="scope_ambiguity", score=score, details=details)


class MissingStandardFactor:
    CONSTRUCTION_MATERIALS = [
        "cement",
        "steel",
        "tmt",
        "brick",
        "block",
        "concrete",
        "aggregate",
        "sand",
        "mortar",
        "tile",
        "paint",
        "glass",
        "pipe",
        "cable",
        "conduit",
        "aluminum",
        "wood",
        "plywood",
    ]

    IS_STANDARDS = ["is", "bis", "irc", "ieee", "astm"]

    def calculate(self, item: Any) -> RiskFactorResult:
        score = 0.0
        details = {}

        is_construction = (
            any(mat in item.material.lower() for mat in self.CONSTRUCTION_MATERIALS) if item.material else False
        )

        if not is_construction:
            return RiskFactorResult(name="missing_standard", score=0.0, details={})

        has_standard = bool(item.standard)
        has_is_ref = any(s in str(item.standard or "").lower() for s in self.IS_STANDARDS) if item.standard else False

        if not has_standard:
            score = 0.9
            details = {"reason": "no_standard_reference"}
        elif not has_is_ref:
            score = 0.5
            details = {"reason": "non_is_standard"}

        return RiskFactorResult(name="missing_standard", score=score, details=details)


class QuantityOutlierFactor:
    def calculate(self, item: Any, historical_stats: dict[str, tuple[float, float]] | None = None) -> RiskFactorResult:
        score = 0.0
        details: dict[str, Any] = {}

        if not item.material or not item.quantity:
            return RiskFactorResult(name="quantity_outlier", score=0.0, details={})

        qty = float(item.quantity)
        if qty <= 0:
            return RiskFactorResult(name="quantity_outlier", score=1.0, details={"reason": "zero_or_negative"})

        mat_key = item.material.lower()
        if historical_stats and mat_key in historical_stats:
            mean_qty, std_qty = historical_stats[mat_key]
            if std_qty > 0:
                z_score = abs(qty - mean_qty) / std_qty
                if z_score > 3:
                    score = 1.0
                elif z_score > 2:
                    score = 0.6
                details = {"z_score": z_score, "mean": mean_qty, "std": std_qty}
        else:
            if qty > 1e6:
                score = 0.7
                details = {"reason": "very_large_quantity"}
            elif qty < 0.001:
                score = 0.5
                details = {"reason": "very_small_quantity"}

        return RiskFactorResult(name="quantity_outlier", score=score, details=details)


class LowConfidenceFactor:
    def calculate(self, item: Any, threshold: float = 0.5) -> RiskFactorResult:
        conf = getattr(item, "confidence", None) or 0.9
        score = 0.0

        if conf < threshold:
            score = 1.0 - (conf / threshold)
            score = max(0.0, min(1.0, score))

        return RiskFactorResult(
            name="low_confidence", score=score, details={"confidence": conf, "threshold": threshold}
        )


class UnknownMaterialFactor:
    KNOWN_MATERIALS = {
        "cement",
        "concrete",
        "steel",
        "sand",
        "aggregate",
        "brick",
        "block",
        "paint",
        "tile",
        "wood",
        "plywood",
        "glass",
        "pipe",
        "cable",
        "aluminum",
        "copper",
        "gi",
        "pvc",
        "cpvc",
        "upvc",
        "tmt",
        "bitumen",
    }

    def calculate(self, item: Any) -> RiskFactorResult:
        score = 0.0
        details = {}

        if not item.material:
            return RiskFactorResult(name="unknown_material", score=0.8, details={"reason": "no_material"})

        mat_lower = item.material.lower()
        is_unknown = not any(km in mat_lower for km in self.KNOWN_MATERIALS)

        if is_unknown:
            score = 0.6
            details = {"material": item.material, "reason": "not_in_known_list"}

        return RiskFactorResult(name="unknown_material", score=score, details=details)


class RiskFactorPipeline:
    WEIGHTS = {
        "price_outlier": 0.30,
        "scope_ambiguity": 0.25,
        "missing_standard": 0.20,
        "quantity_outlier": 0.10,
        "low_confidence": 0.10,
        "unknown_material": 0.05,
    }

    def __init__(self, norms: dict[str, tuple[float, float]] | None = None):
        self.factors: list[Any] = [
            PriceOutlierFactor(),
            ScopeAmbiguityFactor(),
            MissingStandardFactor(),
            QuantityOutlierFactor(),
            LowConfidenceFactor(),
            UnknownMaterialFactor(),
        ]
        self.norms = norms or {}

    def score_item(self, item: Any) -> tuple[float, list[RiskFactorResult]]:
        results = []
        weighted_sum = 0.0

        for factor in self.factors:
            if factor.__class__.__name__ == "PriceOutlierFactor":
                result = factor.calculate(item, self.norms)
            elif factor.__class__.__name__ == "QuantityOutlierFactor":
                result = factor.calculate(item, None)
            else:
                result = factor.calculate(item)
            results.append(result)
            weight = self.WEIGHTS.get(result.name, 0.0)
            weighted_sum += result.score * weight

        total = min(weighted_sum / sum(self.WEIGHTS.values()), 1.0)
        return total, results
