"""Canonical form enforcement and unit normalization for BOQ items."""

from decimal import Decimal
from typing import Any

UNIT_ALIASES = {
    "sq.m": "m²", "sqm": "m²", "sq.m.": "m²", "square meter": "m²", "square meters": "m²",
    "cum": "m³", "cu.m": "m³", "cu.m.": "m³", "cubic meter": "m³", "cubic meters": "m³",
    "rmt": "rm", "running meter": "rm", "R.m": "rm", "rm": "rm", "lm": "rm",
    "nos": "no.", "no.": "no.", "nos.": "no.", "each": "no.", "ea": "no.",
    "kg": "kg", "kgs": "kg",
    "t": "t", "tonne": "t", "MT": "t", "tonnes": "t",
    "ls": "ls", "lumpsum": "ls", "lump-sum": "ls",
    "l": "L", "liters": "L", "litres": "L",
}


def canonical_unit(unit: str | None) -> str | None:
    """Normalize unit string to canonical form."""
    if not unit:
        return None
    u = unit.lower().strip()
    return UNIT_ALIASES.get(u, unit)


def canonical_quantity(qty: Any) -> Decimal:
    """Normalize quantity to Decimal."""
    if qty is None:
        return Decimal("0")
    if isinstance(qty, Decimal):
        return qty
    try:
        return Decimal(str(qty).replace(",", "").strip())
    except Exception:
        return Decimal("0")


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
