"""Pricing Variance & Risk Engine for BOQ Analysis."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.domain.models import BoqRow

logger = logging.getLogger(__name__)

MATERIAL_PRICE_NORMS: dict[str, tuple[float, float]] = {
    "cement": (6.5, 0.8),
    "opc": (6.5, 0.8),
    "ppc": (5.8, 0.7),
    "m20": (6.0, 0.9),
    "m25": (6.5, 1.0),
    "m30": (7.0, 1.2),
    "m35": (7.5, 1.3),
    "steel": (65.0, 8.0),
    "tmt": (68.0, 8.0),
    "fe415": (62.0, 7.0),
    "fe500": (65.0, 8.0),
    "fe550": (68.0, 8.5),
    "sand": (45.0, 5.0),
    "aggregate": (55.0, 6.0),
    "brick": (6.5, 0.8),
    "block": (35.0, 4.0),
    "plywood": (45.0, 5.0),
    "glass": (220.0, 25.0),
    "pain": (120.0, 15.0),
    "paint": (120.0, 15.0),
    " conduit": (15.0, 2.0),
    "cable": (12.0, 1.5),
    "pipe": (8.0, 1.0),
    "cpvc": (12.0, 1.5),
    "upvc": (10.0, 1.2),
    "gi": (14.0, 1.8),
    "aluminum": (190.0, 22.0),
    "tile": (35.0, 4.5),
    "flooring": (85.0, 10.0),
}


@dataclass
class RiskFlag:
    flag_type: str
    severity: str
    item_ref: int
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ItemRiskScore:
    item_no: int
    material: str
    price_outlier_score: float = 0.0
    scope_ambiguity_score: float = 0.0
    missing_standard_score: float = 0.0
    coverage_score: float = 0.0
    total_risk_score: float = 0.0
    flags: list[RiskFlag] = field(default_factory=list)


@dataclass
class ProjectRiskReport:
    item_scores: list[ItemRiskScore]
    aggregate_risk_score: float
    high_risk_items: int
    flagged_items: int
    coverage_percentage: float
    warnings: list[str] = field(default_factory=list)


class RiskEngine:
    def __init__(self, norms_path: str | Path | None = None):
        self._norms = MATERIAL_PRICE_NORMS.copy()
        if norms_path and Path(norms_path).exists():
            self._load_norms(norms_path)

    def _load_norms(self, norms_path: Path) -> None:
        try:
            with open(norms_path) as f:
                data = json.load(f)
                for mat, stats in data.get("norms", {}).items():
                    if isinstance(stats, (list, tuple)) and len(stats) >= 2:
                        self._norms[mat.lower()] = (float(stats[0]), float(stats[1]))
        except Exception as e:
            logger.warning(f"Could not load norms: {e}")

    def analyze(self, items: list[BoqRow]) -> ProjectRiskReport:
        item_scores = []
        all_flags = []

        for item in items:
            score = self._score_item(item)
            item_scores.append(score)
            all_flags.extend(score.flags)

        aggregate = self._aggregate_risk(item_scores) if item_scores else 0.0
        high_risk = sum(1 for s in item_scores if s.total_risk_score > 0.7)
        flagged = sum(1 for s in item_scores if s.flags)
        coverage = self._compute_coverage(items)

        warnings = []
        if aggregate > 0.6:
            warnings.append(f"High aggregate risk: {aggregate:.1%}")
        if high_risk > len(items) * 0.2:
            warnings.append(f"Many high-risk items: {high_risk}/{len(items)}")
        if coverage < 0.5:
            warnings.append(f"Low coverage: {coverage:.1%} of work types missing")

        return ProjectRiskReport(
            item_scores=item_scores,
            aggregate_risk_score=aggregate,
            high_risk_items=high_risk,
            flagged_items=flagged,
            coverage_percentage=coverage,
            warnings=warnings,
        )

    def _score_item(self, item: BoqRow) -> ItemRiskScore:
        score = ItemRiskScore(
            item_no=item.item_no,
            material=item.material,
        )
        score.price_outlier_score = self._price_outlier(item)
        score.scope_ambiguity_score = self._scope_ambiguity(item)
        score.missing_standard_score = self._missing_standard(item)
        score.coverage_score = self._coverage(item)
        score.total_risk_score = (
            score.price_outlier_score * 0.35
            + score.scope_ambiguity_score * 0.25
            + score.missing_standard_score * 0.25
            + score.coverage_score * 0.15
        )

        if score.price_outlier_score > 0.7:
            score.flags.append(RiskFlag(
                flag_type="PRICE_OUTLIER",
                severity="HIGH",
                item_ref=item.item_no,
                message="Price more than 2σ from market norm",
                details={"material": item.material},
            ))
        if score.scope_ambiguity_score > 0.5:
            score.flags.append(RiskFlag(
                flag_type="SCOPE_AMBIGUITY",
                severity="MEDIUM",
                item_ref=item.item_no,
                message="Multiple plausible entity type interpretations",
                details={"material": item.material},
            ))
        if score.missing_standard_score > 0.8:
            score.flags.append(RiskFlag(
                flag_type="MISSING_STANDARD",
                severity="HIGH",
                item_ref=item.item_no,
                message="Material without IS standard reference",
                details={"material": item.material},
            ))

        return score

    def _price_outlier(self, item: BoqRow) -> float:
        mat_key = item.material.lower() if item.material else ""
        for key, (norm, sigma) in self._norms.items():
            if key in mat_key:
                qty = float(item.quantity or 0)
                if qty > 0:
                    z_score = abs(norm - qty) / sigma if sigma > 0 else 0.0
                    if z_score > 3:
                        return 1.0
                    elif z_score > 2:
                        return 0.8
                    elif z_score > 1.5:
                        return 0.5
        return 0.0

    def _scope_ambiguity(self, item: BoqRow) -> float:
        ambiguity_indicators = 0
        if not item.material:
            ambiguity_indicators += 1
        if item.material and len(item.material) < 3:
            ambiguity_indicators += 1
        if item.quantity and float(item.quantity) <= 0:
            ambiguity_indicators += 1
        if not item.unit or item.unit in ("no.", "nos"):
            ambiguity_indicators += 1
        if not item.location:
            ambiguity_indicators += 1
        return min(ambiguity_indicators / 3.0, 1.0)

    def _missing_standard(self, item: BoqRow) -> float:
        construction_materials = [
            "cement", "steel", "tmt", "brick", "block", "concrete",
            "aggregate", "sand", "mortar", "tile", "paint", "glass",
            "pipe", "cable", "conduit", "aluminum", "wood", "plywood",
        ]
        has_standard = bool(item.standard)
        has_is_ref = any("is" in str(s).lower() for s in item.standard) if item.standard else False
        mat_is_construction = any(mat in item.material.lower() for mat in construction_materials) if item.material else False

        if mat_is_construction and not has_standard:
            return 0.9
        elif mat_is_construction and not has_is_ref:
            return 0.5
        return 0.0

    def _coverage(self, item: BoqRow) -> float:
        score = 0.0
        if item.material:
            score += 0.3
        if item.quantity and float(item.quantity) > 0:
            score += 0.3
        if item.unit and item.unit != "no.":
            score += 0.2
        if item.grade or item.standard:
            score += 0.2
        return score

    def _compute_coverage(self, items: list[BoqRow]) -> float:
        work_types = set()
        for item in items:
            if item.material:
                work_types.add(self._categorize_work(item.material))
        len(work_types)
        expected_categories = {"structure", "finishing", "mep", "hvac", "electrical", "plumbing"}
        covered = len(work_types.intersection(expected_categories))
        return covered / len(expected_categories) if expected_categories else 0.0

    def _categorize_work(self, material: str) -> str:
        mat = material.lower()
        if any(t in mat for t in ["concrete", "cement", "steel", "brick", "block", "sand", "aggregate"]):
            return "structure"
        elif any(t in mat for t in ["paint", "tile", "flooring", "putty", "plaster", "wood", "plywood"]):
            return "finishing"
        elif any(t in mat for t in ["pipe", "pvc", "cpvc", "upvc", "gi", "plumb"]):
            return "plumbing"
        elif any(t in mat for t in ["cable", "conduit", "wire", "switch", "socket", "electrical"]):
            return "electrical"
        elif any(t in mat for t in ["duct", "ac", "air", "ventil", "hvac", "chiller"]):
            return "hvac"
        return "general"

    def _aggregate_risk(self, item_scores: list[ItemRiskScore]) -> float:
        if not item_scores:
            return 0.0
        weighted = sum(s.total_risk_score for s in item_scores) / len(item_scores)
        max_risk = max((s.total_risk_score for s in item_scores), default=0.0)
        return weighted * 0.7 + max_risk * 0.3
