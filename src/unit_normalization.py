"""Unit and dimension normalization utilities."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

UNIT_MAP = {
    "cu.m": "m³",
    "cu m": "m³",
    "cum": "m³",
    "m3": "m³",
    "m³": "m³",
    "cubic meter": "m³",
    "cubic metre": "m³",
    "cubic meters": "m³",
    "cubic metres": "m³",
    "sq.m": "m²",
    "sq m": "m²",
    "sqm": "m²",
    "m2": "m²",
    "m²": "m²",
    "square meter": "m²",
    "square metre": "m²",
    "square meters": "m²",
    "square metres": "m²",
    "kg": "kg",
    "kgs": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "nos": "no.",
    "nos.": "no.",
    "no": "no.",
    "no.": "no.",
    "each": "no.",
    "ea": "no.",
    "rm": "rm",
    "r.m.": "rm",
    "running meter": "rm",
    "running metre": "rm",
    "ls": "ls",
    "l.s.": "ls",
    "lumpsum": "ls",
}


def normalize_unit(text: str) -> str:
    """Normalize unit text to presentation form used by legacy outputs."""
    key = re.sub(r"\s+", " ", (text or "").strip().lower())
    return UNIT_MAP.get(key, (text or "").strip())


def normalize_dimension(text: str) -> str:
    value = (text or "").strip()
    value = re.sub(r"\b(thick|thickness|wide|width|dia|diameter)\b\.?", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"(\d+(?:\.\d+)?)\s*(mm|cm|m)\b", r"\1\2", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*[x×]\s*", " x ", value)
    return value.strip()


def parse_dimension(text: str) -> dict[str, float] | None:
    """Parse common construction dimensions into metres."""
    value = normalize_dimension(text)
    if not value:
        return None

    compound = re.match(
        r"(?P<length>\d+(?:\.\d+)?)\s*(?P<lu>mm|cm|m)\s*[x×]\s*"
        r"(?P<width>\d+(?:\.\d+)?)\s*(?P<wu>mm|cm|m)\b",
        value,
        flags=re.IGNORECASE,
    )
    if compound:
        return {
            "length": _to_metres(compound.group("length"), compound.group("lu")),
            "width": _to_metres(compound.group("width"), compound.group("wu")),
        }

    single = re.match(r"(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>mm|cm|m)\b", value, flags=re.IGNORECASE)
    if single:
        return {"thickness": _to_metres(single.group("num"), single.group("unit"))}

    return None


def calculate_quantity(*args: Any) -> float | tuple[float, str]:
    """Parse quantities.

    Supports the newer ``calculate_quantity("1,200")`` form and the legacy
    integration-test form ``calculate_quantity(text, qty, unit, dimension)``.
    """
    if len(args) >= 3:
        quantity = _to_float(args[1])
        return quantity, str(args[2])
    if not args:
        return 0.0
    return _to_float(args[0])


def _to_float(value: Any) -> float:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0


def _to_metres(number: str | Decimal, unit: str) -> float:
    value = float(number)
    unit = unit.lower()
    if unit == "mm":
        return value / 1000.0
    if unit == "cm":
        return value / 100.0
    return value
