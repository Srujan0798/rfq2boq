"""Recommendation generator from risk analysis."""

from __future__ import annotations

from typing import Any

from src.risk.engine import ProjectRiskReport


class RecommendationGenerator:
    def generate(self, report: ProjectRiskReport) -> list[dict[str, Any]]:
        recs = []

        if report.aggregate_risk_score > 0.6:
            recs.append({
                "priority": "HIGH",
                "category": "overall",
                "message": "High aggregate risk detected — review entire BOQ before bidding",
                "action": "manual_review",
                "items_affected": sum(1 for s in report.item_scores if s.total_risk_score > 0.5),
            })

        high_risk_items = [s for s in report.item_scores if s.total_risk_score > 0.7]
        for score in high_risk_items[:5]:
            for flag in score.flags:
                recs.append({
                    "priority": "HIGH",
                    "category": flag.flag_type,
                    "message": flag.message,
                    "action": self._action_for_flag(flag.flag_type),
                    "item_ref": flag.item_ref,
                    "material": score.material,
                })

        if report.coverage_percentage < 0.5:
            recs.append({
                "priority": "MEDIUM",
                "category": "coverage",
                "message": f"Low BOQ coverage ({report.coverage_percentage:.0%}) — major work categories may be missing",
                "action": "verify_scope",
            })

        flagged_count = sum(1 for s in report.item_scores if s.flags)
        if flagged_count > len(report.item_scores) * 0.3:
            recs.append({
                "priority": "MEDIUM",
                "category": "flag_rate",
                "message": f"{flagged_count}/{len(report.item_scores)} items flagged — high error rate",
                "action": "quality_check",
            })

        price_outliers = [s for s in report.item_scores if any(f.flag_type == "PRICE_OUTLIER" for f in s.flags)]
        if price_outliers:
            recs.append({
                "priority": "MEDIUM",
                "category": "price_outlier",
                "message": f"{len(price_outliers)} items with outlier pricing — verify market rates",
                "action": "rate_verification",
                "items_affected": [s.item_no for s in price_outliers],
            })

        return recs

    @staticmethod
    def _action_for_flag(flag_type: str) -> str:
        actions = {
            "PRICE_OUTLIER": "rate_verification",
            "SCOPE_AMBIGUITY": "clarify_with_client",
            "MISSING_STANDARD": "add_standard_reference",
            "QUANTITY_OUTLIER": "verify_measurements",
            "LOW_CONFIDENCE": "request_review",
            "UNKNOWN_MATERIAL": "verify_material_name",
        }
        return actions.get(flag_type, "manual_review")
