"""Coverage analysis for BOQ completeness."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

WORK_CATEGORIES = {
    "structure": {
        "keywords": [
            "concrete",
            "cement",
            "steel",
            "brick",
            "block",
            "sand",
            "aggregate",
            "mortar",
            " reinforcement",
            " RCC",
        ],
        "weight": 0.25,
    },
    "finishing": {
        "keywords": ["paint", "tile", "flooring", "putty", "plaster", "wood", "plywood", " dado", "skirting", "polish"],
        "weight": 0.20,
    },
    "plumbing": {
        "keywords": ["pipe", "pvc", "cpvc", "upvc", "gi", "plumb", "water", "drain", "sewage", "sanitary", "fixture"],
        "weight": 0.15,
    },
    "electrical": {
        "keywords": ["cable", "conduit", "wire", "switch", "socket", "db", "panel", "light", "fan", "earthing"],
        "weight": 0.15,
    },
    "hvac": {
        "keywords": ["duct", "ac", "air", "ventil", "hvac", "chiller", "cooling", "ventilation"],
        "weight": 0.10,
    },
    "waterproofing": {
        "keywords": ["waterproof", "damp proof", "membrane", " coating", "torching"],
        "weight": 0.10,
    },
    "doors_windows": {
        "keywords": ["door", "window", "ventilator", "frame", "shutter", "glazing", "partition"],
        "weight": 0.05,
    },
}


@dataclass
class CategoryCoverage:
    category: str
    present: bool
    items_found: list[str]
    coverage_fraction: float


@dataclass
class CoverageReport:
    overall_coverage: float
    categories: list[CategoryCoverage]
    missing_categories: list[str]
    low_coverage_categories: list[str]
    recommendations: list[str] = field(default_factory=list)


class CoverageAnalyzer:
    def __init__(self):
        self.categories = WORK_CATEGORIES

    def analyze(self, items: list[Any]) -> CoverageReport:
        category_results = []
        missing = []
        low_coverage = []

        for category, config in self.categories.items():
            result = self._analyze_category(items, category, config["keywords"])
            category_results.append(result)

            if not result.present:
                missing.append(category)
            elif result.coverage_fraction < 0.3:
                low_coverage.append(category)

        overall = sum(r.coverage_fraction * self.categories[r.category]["weight"] for r in category_results)

        recommendations = self._generate_recommendations(missing, low_coverage)

        return CoverageReport(
            overall_coverage=overall,
            categories=category_results,
            missing_categories=missing,
            low_coverage_categories=low_coverage,
            recommendations=recommendations,
        )

    def _analyze_category(
        self,
        items: list[Any],
        category: str,
        keywords: list[str],
    ) -> CategoryCoverage:
        found = []
        for item in items:
            mat = (item.material or "").lower()
            desc = (getattr(item, "description", "") or "").lower()
            combined = mat + " " + desc

            if any(kw.lower() in combined for kw in keywords):
                found.append(item.material or str(item))

        present = len(found) > 0
        fraction = min(len(found) / 3.0, 1.0) if present else 0.0

        return CategoryCoverage(
            category=category,
            present=present,
            items_found=found[:10],
            coverage_fraction=fraction,
        )

    def _generate_recommendations(
        self,
        missing: list[str],
        low_coverage: list[str],
    ) -> list[str]:
        recs = []
        for cat in missing:
            recs.append(f"Missing '{cat}' work category — verify if scope includes {cat}")
        for cat in low_coverage:
            recs.append(f"Low coverage in '{cat}' — may need itemization")
        if not missing and not low_coverage:
            recs.append("BOQ coverage appears complete across major work categories")
        return recs
