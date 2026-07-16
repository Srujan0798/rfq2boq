"""Risk analysis for extracted BOQs."""

from dataclasses import dataclass
from typing import Any


@dataclass
class RiskScore:
    score: float
    factors: list[str]
    item: dict | None = None


class RiskEngine:
    def score_item(self, item: dict, context: dict | None = None) -> RiskScore:
        score = 0.0
        factors = []

        material = item.get("material", "").lower()
        quantity = float(item.get("quantity", 0) or 0)
        grade = item.get("grade", "")
        standard = item.get("standard", [])

        if not standard or (isinstance(standard, list) and len(standard) == 0):
            score += 15
            factors.append("missing_standard")

        unknown_materials = ["unknown", "na", "none", ""]
        if material in unknown_materials or len(material) < 3:
            score += 20
            factors.append("unknown_material")

        if quantity > 10000 or (quantity > 0 and quantity < 0.01):
            score += 10
            factors.append("quantity_outlier")

        if not grade or grade == "":
            score += 10
            factors.append("no_grade")

        desc = item.get("description", item.get("description_raw", ""))
        if len(desc) > 500:
            score += 5
            factors.append("suspiciously_long_description")

        return RiskScore(score=min(score, 100), factors=factors, item=item)

    def score_project(self, boq: list[dict]) -> dict[str, Any]:
        if not boq:
            return {"overall_risk": 0, "high_risk_items": [], "summary": {}}

        scored_items = [self.score_item(item) for item in boq]
        high_risk = [s for s in scored_items if s.score >= 30]
        avg_score = sum(s.score for s in scored_items) / len(scored_items)

        risk_distribution = {
            "low": len([s for s in scored_items if s.score < 15]),
            "medium": len([s for s in scored_items if 15 <= s.score < 30]),
            "high": len([s for s in scored_items if s.score >= 30]),
        }

        return {
            "overall_risk": round(avg_score, 2),
            "high_risk_items": [{"item": s.item, "score": s.score, "factors": s.factors} for s in high_risk],
            "risk_distribution": risk_distribution,
            "total_items": len(boq),
            "high_risk_count": len(high_risk),
        }

    def coverage_analysis(self, boq: list[dict]) -> dict[str, Any]:
        typical_categories = {
            "concrete": ["concrete", "cement", "rcc"],
            "steel": ["steel", "rebar", "tmt"],
            "brickwork": ["brick", "masonry"],
            "plaster": ["plaster", "cement plaster"],
            "flooring": ["flooring", "tile", "granite"],
            "waterproofing": ["waterproofing", "membrane"],
            "plumbing": ["pipe", "gi", "pvc", "plumbing"],
            "electrical": ["wire", "cable", "electrical"],
        }

        found = {cat: False for cat in typical_categories}

        for item in boq:
            mat = item.get("material", "").lower()
            desc = item.get("description", item.get("description_raw", "")).lower()
            combined = mat + " " + desc

            for cat, keywords in typical_categories.items():
                if any(kw in combined for kw in keywords):
                    found[cat] = True

        missing = [cat for cat, present in found.items() if not present]

        return {
            "categories_found": sum(found.values()),
            "total_categories": len(typical_categories),
            "coverage_pct": round(sum(found.values()) / len(typical_categories) * 100, 1),
            "missing_categories": missing,
        }

    def generate_recommendations(self, boq: list[dict]) -> list[str]:
        recommendations = []

        risk_report = self.score_project(boq)

        if risk_report["high_risk_count"] > len(boq) * 0.3:
            recommendations.append(
                f"High proportion of risky items ({risk_report['high_risk_count']}/{len(boq)}). Consider manual review."
            )

        coverage = self.coverage_analysis(boq)
        if coverage["coverage_pct"] < 60:
            recommendations.append(
                f"Low category coverage ({coverage['coverage_pct']}%). Missing: {', '.join(coverage['missing_categories'])}."
            )

        for item in boq:
            mat = item.get("material", "").lower()
            if mat in ["unknown", "na", "none", ""] or len(mat) < 3:
                recommendations.append(
                    f"Item {item.get('item_no', '?')} has unknown material. Add HSN code or material specification."
                )
                break

        missing_grade = sum(1 for item in boq if not item.get("grade"))
        if missing_grade > len(boq) * 0.5:
            recommendations.append(
                f"{missing_grade} items missing grade specification. Add cement grade (M20/M25/etc.) or steel grade (Fe415/Fe500)."
            )

        return recommendations
