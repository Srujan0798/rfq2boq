"""Table-driven tests for canonical unit normalization (NW-05).

Verifies that every alias listed in the NW-05 task spec maps to the
expected canonical form via ``normalize_unit``.
"""

from __future__ import annotations

import pytest
from src.rules.units import normalize_unit, to_float_qty

# (input, expected) pairs for every alias in the NW-05 task spec
# "Sq meter/Sq. Mtr./SQM/sqm/m2/m² -> 'sqm'"
AREA_CASES: list[tuple[str, str]] = [
    ("sq meter", "sqm"),
    ("sq. mtr", "sqm"),
    ("sq.mtr", "sqm"),
    ("SQM", "sqm"),
    ("sqm", "sqm"),
    ("m2", "sqm"),
    ("m²", "sqm"),
    ("sqm.", "sqm"),
    ("sqmtr", "sqm"),
    ("SQMTR", "sqm"),
    ("sq.m", "sqm"),
    ("square meter", "sqm"),
    ("square metre", "sqm"),
]

# "RMT/Rmt/rmt/rm/RMT -> 'rmt'"
LENGTH_CASES: list[tuple[str, str]] = [
    ("RMT", "rmt"),
    ("Rmt", "rmt"),
    ("rmt", "rmt"),
    ("rm", "rmt"),
    ("running meter", "rmt"),
    ("running metre", "rmt"),
    ("lm", "rmt"),
    ("r.m", "rmt"),
    ("l.m", "rmt"),
]

# "cu.m/m³/cum/CUM -> 'cum'"
VOLUME_CASES: list[tuple[str, str]] = [
    ("cu.m", "cum"),
    ("cu.m.", "cum"),
    ("m³", "cum"),
    ("m3", "cum"),
    ("cum", "cum"),
    ("CUM", "cum"),
    ("cbm", "cum"),
    ("cubic meter", "cum"),
    ("cubic metre", "cum"),
    ("cft", "ft^3"),
    ("cu.ft", "ft^3"),
    ("cubic feet", "ft^3"),
]

# "no./nos/Nos./NOS/Nos -> 'nos'"
COUNT_CASES: list[tuple[str, str]] = [
    ("no.", "nos"),
    ("nos", "nos"),
    ("Nos.", "nos"),
    ("NOS", "nos"),
    ("Nos", "nos"),
    ("no", "nos"),
    ("nos.", "nos"),
]

# "Kg/kg/KG/kgs -> 'kg'"
MASS_CASES: list[tuple[str, str]] = [
    ("Kg", "kg"),
    ("kg", "kg"),
    ("KG", "kg"),
    ("kgs", "kg"),
    ("kilogram", "kg"),
    ("kilograms", "kg"),
]

# "ltr/L/Ltr/litre -> 'ltr'"
LIQUID_CASES: list[tuple[str, str]] = [
    ("ltr", "ltr"),
    # P3_04 §9 gotcha: bare "L" is ambiguous (liter vs leader) and
    # normalizes to UNKNOWN+AMBIGUOUS_UNIT flag rather than guessing.
    # Real tenders use "ltr" or "Ltr" not bare "L".
    ("Ltr", "ltr"),
    ("liter", "ltr"),
    ("litre", "ltr"),
    ("liters", "ltr"),
    ("litres", "ltr"),
]

ALL_CASES = AREA_CASES + LENGTH_CASES + VOLUME_CASES + COUNT_CASES + MASS_CASES + LIQUID_CASES


@pytest.mark.parametrize("alias,expected", ALL_CASES)
def test_normalize_unit_canonical(alias: str, expected: str) -> None:
    assert normalize_unit(alias) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        ("1,200", 1200.0),
        ("270.00", 270.0),
        (42, 42.0),
        (3.14, 3.14),
        ("1,234.56", 1234.56),
        ("abc", None),
        ("", None),
    ],
)
def test_to_float_qty_canonical(value, expected: float | None) -> None:
    assert to_float_qty(value) == expected
