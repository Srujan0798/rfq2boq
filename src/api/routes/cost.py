"""Cost estimation API routes."""

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException
from src.domain.cost_estimator import CostEstimator
from src.domain.variance import VarianceAnalyzer

router = APIRouter(prefix="/v1/cost", tags=["cost-estimation"])


_cost_estimator_cache: CostEstimator | None = None


def get_cost_estimator() -> CostEstimator:
    global _cost_estimator_cache
    if _cost_estimator_cache is None:
        _cost_estimator_cache = CostEstimator()
    return _cost_estimator_cache


@router.get("/rates/{material}")
async def get_rate(material: str, unit: str = "nos", region: str = "cpwd_delhi") -> dict[str, Any]:
    estimator = get_cost_estimator()
    entry = estimator.lookup_rate(material, unit, region)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"No rate found for {material} ({unit}) in {region}")
    return {
        "material": entry.material,
        "unit": entry.unit,
        "rate": float(entry.rate),
        "region": entry.region,
        "year": entry.year,
        "source": entry.source,
        "remarks": entry.remarks,
    }


@router.get("/rates/{material}/variance")
async def get_rate_variance(material: str, unit: str = "nos") -> dict[str, Any]:
    estimator = get_cost_estimator()
    variance_data = estimator.get_rate_variance(material, unit)
    if not variance_data:
        raise HTTPException(status_code=404, detail=f"No variance data for {material} ({unit})")
    return variance_data


@router.get("/regions")
async def list_regions() -> list[str]:
    estimator = get_cost_estimator()
    regions = set()
    for entry in estimator._rates:
        regions.add(entry.region)
    return sorted(regions)


@router.post("/analyze")
async def analyze_variance(
    items: list[dict[str, Any]],
    region: str = "cpwd_delhi",
) -> dict[str, Any]:
    estimator = get_cost_estimator()
    analyzer = VarianceAnalyzer(estimator)
    estimates = []
    for item in items:
        from src.domain.cost_estimator import ItemEstimate
        est = ItemEstimate(
            item_no=item.get("item_no", 1),
            material=item.get("material", ""),
            quantity=Decimal(str(item.get("quantity", 0))),
            unit=item.get("unit", "nos"),
            rate=Decimal(str(item["rate"])) if item.get("rate") else None,
            amount=Decimal("0"),
            source=None,
            confidence=0.5,
        )
        estimates.append(est)
    report = analyzer.analyze_boq(estimates, region)
    return {
        "item_count": report.item_count,
        "rated_count": report.rated_count,
        "outlier_count": report.outlier_count,
        "total_variance_pct": report.total_variance_pct,
        "flagged_items": [
            {
                "material": f.material,
                "extracted_rate": float(f.extracted_rate) if f.extracted_rate else None,
                "expected_rate": float(f.expected_rate) if f.expected_rate else None,
                "variance_pct": f.variance_pct,
                "severity": f.severity,
                "message": f.message,
            }
            for f in report.flagged_items
        ],
        "summary": report.summary,
    }


@router.get("/estimate")
async def estimate_total(
    material: str,
    quantity: float,
    unit: str = "nos",
    region: str = "cpwd_delhi",
) -> dict[str, Any]:
    estimator = get_cost_estimator()
    rate_entry = estimator.lookup_rate(material, unit, region)
    if rate_entry is None:
        raise HTTPException(status_code=404, detail=f"No rate found for {material} ({unit}) in {region}")
    amount = Decimal(str(quantity)) * rate_entry.rate
    subtotal = amount
    tax_rate = subtotal * Decimal("0.18")
    total = subtotal + tax_rate
    return {
        "material": material,
        "quantity": quantity,
        "unit": unit,
        "rate": float(rate_entry.rate),
        "amount": float(amount),
        "subtotal": float(subtotal),
        "tax": float(tax_rate),
        "total": float(total),
        "region": region,
        "source": rate_entry.source,
    }
