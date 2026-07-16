"""Canonical form enforcement and unit normalization for BOQ items."""

from decimal import Decimal
from typing import Any

from src.rules.units import normalize_unit as _normalize_unit
from src.rules.units import to_decimal_qty


def canonical_unit(unit: str | None) -> str | None:
    """Normalize unit string to canonical form."""
    if not unit:
        return None
    return _normalize_unit(unit)


def canonical_quantity(qty: Any) -> Decimal:
    """Normalize quantity to Decimal."""
    return to_decimal_qty(qty)


def canonical_dimension(dim_str: str | None) -> str | None:
    """Normalize dimension string."""
    if not dim_str:
        return None
    d = dim_str.strip()
    d = d.replace("mm thk", "mm")
    d = d.replace("MM Thk", "mm")
    d = d.replace("x", " x ")
    return d


def enforce_boq_schema(item: dict[str, Any]) -> dict[str, Any]:
    """Ensure BOQ item conforms to schema v1."""
    canonical = {
        "item_no": item.get("item_no", 0),
        "material": item.get("material", "").strip(),
        "grade": item.get("grade", "") or "",
        "quantity": canonical_quantity(item.get("quantity")),
        "unit": canonical_unit(item.get("unit")),
        "action": item.get("action", "") or "",
        "location": item.get("location", "") or "",
        "standard": item.get("standard", []) or [],
        "dimensions": item.get("dimensions", []) or [],
        "description_raw": item.get("description_raw", "") or "",
        "confidence": float(item.get("confidence", 0.0)),
        "warnings": item.get("warnings", []) or [],
    }
    return canonical
