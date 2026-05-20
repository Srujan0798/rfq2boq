"""Cost estimation engine for BOQ items using schedule of rates.

Estimates costs for BOQ items based on region-specific rates from CPWD,
DSR, and MSR schedules. Supports outlier detection for bid analysis.

DSR 2023 is loaded as primary source (data/rates/cpwd_dsr_2023.json),
with existing stub files (rates_cpwd.json, rates_dsr.json, etc.) as fallback.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from src.domain.models import BoqRow

DSR_2023_FILE = "cpwd_dsr_2023.json"


@dataclass
class RateEntry:
    material: str
    unit: str
    rate: Decimal
    region: str
    year: int
    source: str
    remarks: str = ""


@dataclass
class CostEstimate:
    rate: Decimal | None
    amount: Decimal
    source: str
    confidence: float
    remarks: str = ""


@dataclass
class ItemEstimate:
    item_no: int
    material: str
    quantity: Decimal
    unit: str
    rate: Decimal | None
    amount: Decimal
    source: str | None
    confidence: float
    remarks: str = ""


@dataclass
class TotalEstimate:
    subtotal: Decimal
    taxes: Decimal
    total: Decimal
    breakdown: dict[str, Decimal] = field(default_factory=dict)
    flagged_items: list[ItemEstimate] = field(default_factory=list)


def _levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


class CostEstimator:
    def __init__(self, rates_dir: str | Path | None = None):
        self.rates_dir = Path(rates_dir) if rates_dir else Path(__file__).parent.parent.parent / "data" / "rates"
        self._rates: list[RateEntry] = []
        self._material_index: dict[str, list[RateEntry]] = {}
        self._dsr_index: list[RateEntry] = []
        self._dsr_description_index: list[tuple[str, RateEntry]] = []
        self._load_rates()

    def _load_rates(self) -> None:
        if not self.rates_dir.exists():
            return
        dsr_path = self.rates_dir / DSR_2023_FILE
        if dsr_path.exists():
            self._load_dsr_2023(dsr_path)
        for rate_file in self.rates_dir.glob("rates_*.json"):
            if rate_file.name == DSR_2023_FILE:
                continue
            with open(rate_file, encoding="utf-8") as f:
                data = json.load(f)
            region = data.get("region", rate_file.stem)
            year = data.get("year", 2024)
            source = data.get("source", rate_file.stem)
            for item in data.get("items", []):
                entry = RateEntry(
                    material=item["material"].lower(),
                    unit=item["unit"],
                    rate=Decimal(str(item["rate"])),
                    region=region,
                    year=year,
                    source=source,
                    remarks=item.get("remarks", ""),
                )
                self._rates.append(entry)
                key = entry.material
                if key not in self._material_index:
                    self._material_index[key] = []
                self._material_index[key].append(entry)

    def _load_dsr_2023(self, path: Path) -> None:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        region = data.get("region", "delhi")
        source = data.get("source", "CPWD DSR 2023")
        for item in data.get("items", []):
            desc = item.get("description", "")
            entry = RateEntry(
                material=desc.lower(),
                unit=item.get("unit", ""),
                rate=Decimal(str(item.get("rate_inr", item.get("rate", 0)))),
                region=region,
                year=item.get("year", 2023),
                source=source,
                remarks=item.get("chapter", ""),
            )
            self._dsr_index.append(entry)
            self._dsr_description_index.append((desc.lower(), entry))

    def lookup_rate(
        self,
        material: str,
        unit: str | None = None,
        region: str | None = None,
        grade: str | None = None,
    ) -> RateEntry | None:
        key = material.lower().strip()

        for desc_lower, entry in self._dsr_description_index:
            if key in desc_lower or desc_lower in key:
                return entry

        tokens = key.split()
        if len(tokens) >= 2 and len(key) >= 5:
            for desc_lower, entry in self._dsr_description_index:
                desc_tokens = desc_lower.split()
                matches = sum(1 for tok in tokens if tok in desc_tokens)
                if matches >= 2:
                    return entry

        fuzzy_candidates: list[tuple[int, RateEntry]] = []
        for desc_lower, entry in self._dsr_description_index:
            dist = _levenshtein_distance(key, desc_lower)
            if dist <= 3 and len(key) >= 5:
                fuzzy_candidates.append((dist, entry))
        if fuzzy_candidates:
            fuzzy_candidates.sort(key=lambda x: x[0])
            best = fuzzy_candidates[0][1]
            best.remarks = best.remarks + " [fuzzy]" if best.remarks else "[fuzzy]"
            return best

        candidates = self._material_index.get(key, [])
        if not candidates:
            for mat_key, entries in self._material_index.items():
                if key in mat_key or mat_key in key:
                    candidates.extend(entries)
        if not candidates:
            return None

        if region:
            region_lower = region.lower()
            for entry in candidates:
                if region_lower in entry.region or entry.region in region_lower:
                    return entry
        return candidates[0]

    def estimate_item(self, boq_row: BoqRow, region: str | None = None) -> ItemEstimate:
        rate_entry = self.lookup_rate(boq_row.material, boq_row.unit, region, boq_row.grade)
        rate = rate_entry.rate if rate_entry else None
        amount = (boq_row.quantity * rate) if rate else Decimal("0")
        source = rate_entry.source if rate_entry else None
        confidence = 0.9 if rate_entry else 0.0

        return ItemEstimate(
            item_no=boq_row.item_no,
            material=boq_row.material,
            quantity=boq_row.quantity,
            unit=boq_row.unit,
            rate=rate,
            amount=amount,
            source=source,
            confidence=confidence,
            remarks=rate_entry.remarks if rate_entry else "",
        )

    def estimate_total(
        self,
        boq_items: list[BoqRow],
        region: str | None = None,
        tax_rate: float = 0.18,
    ) -> TotalEstimate:
        item_estimates: list[ItemEstimate] = []
        subtotal = Decimal("0")

        for row in boq_items:
            est = self.estimate_item(row, region)
            item_estimates.append(est)
            subtotal += est.amount

        taxes = subtotal * Decimal(str(tax_rate))
        total = subtotal + taxes

        flagged = self.flag_outliers(item_estimates)

        return TotalEstimate(
            subtotal=subtotal,
            taxes=taxes,
            total=total,
            breakdown={"subtotal": subtotal, "CGST": taxes / 2, "SGST": taxes / 2, "total": total},
            flagged_items=flagged,
        )

    def flag_outliers(self, items: list[ItemEstimate]) -> list[ItemEstimate]:
        rated_items = [i for i in items if i.rate is not None and i.rate > 0]
        if len(rated_items) < 3:
            return []

        rates = [float(i.rate) for i in rated_items]
        mean_rate = sum(rates) / len(rates)
        variance = sum((r - mean_rate) ** 2 for r in rates) / len(rates)
        std_dev = variance ** 0.5

        if std_dev == 0:
            return []

        flagged = []
        for item in rated_items:
            z_score = abs(float(item.rate) - mean_rate) / std_dev
            if z_score > 2:
                flagged.append(item)
        return flagged

    def get_rate_variance(self, material: str, unit: str) -> dict[str, Any]:
        key = material.lower().strip()
        candidates: list[RateEntry] = []
        for desc_lower, entry in self._dsr_description_index:
            if key in desc_lower or desc_lower in key:
                candidates.append(entry)
        if not candidates:
            candidates = self._material_index.get(key, [])
        if not candidates:
            return {}

        rates = [float(e.rate) for e in candidates]
        if not rates:
            return {}

        mean_rate = sum(rates) / len(rates)
        min_rate = min(rates)
        max_rate = max(rates)

        return {
            "material": material,
            "unit": unit,
            "count": len(rates),
            "mean": round(mean_rate, 2),
            "min": min_rate,
            "max": max_rate,
            "variance": round(max_rate - min_rate, 2),
            "regions": [e.region for e in candidates],
        }
