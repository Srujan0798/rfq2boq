"""Table-driven tests for the unified unit/quantity normalizer (NW-05).

The single source of truth lives in ``src.rules.units``. These tests pin
the alias-to-canonical mapping so a regression in any local normalizer
copy is caught immediately.
"""

from __future__ import annotations

import pytest
from src.normalize.canonical import canonical_unit
from src.rules.units import (
    get_canonical_unit,
    is_valid_unit,
    normalize_unit,
    to_decimal_qty,
    to_float_qty,
)
from src.unit_normalization import normalize_unit as legacy_normalize_unit

# (alias, expected_canonical) for every alias mentioned in the NW-05 task
# ("Sq meter/Sq. Mtr./SQM/sqm", "RMT/Rmt/rmt/rm", "cu.m/m³/cum",
#  "no./nos/Nos./NOS", "Kg/kg/KG", "ltr/L") plus a wider sweep of common
# real-tender variants.
AREA_ALIASES: list[tuple[str, str]] = [
    ("sqm", "sqm"),
    ("SQM", "sqm"),
    ("sq.m", "sqm"),
    ("sq.m.", "sqm"),
    ("square meter", "sqm"),
    ("square meters", "sqm"),
    ("sqmt", "sqm"),
    ("sqmtr", "sqm"),
    ("sqmtrs", "sqm"),
    ("m²", "sqm"),
    ("m2", "sqm"),
    ("sqft", "sqm"),
    ("sq.ft", "sqm"),
    ("sft", "sqm"),
    ("sq ft", "sqm"),
    ("square feet", "sqm"),
]

LENGTH_ALIASES: list[tuple[str, str]] = [
    ("rmt", "rmt"),
    ("RMT", "rmt"),
    ("Rmt", "rmt"),
    ("rm", "rmt"),
    ("r.m", "rmt"),
    ("r.m.", "rmt"),
    ("lm", "rmt"),
    ("running meter", "rmt"),
    ("running metre", "rmt"),
    ("running meters", "rmt"),
    ("r.mtr", "rmt"),
]

VOLUME_ALIASES: list[tuple[str, str]] = [
    ("cu.m", "cum"),
    ("cu.m.", "cum"),
    ("cu m", "cum"),
    ("cum", "cum"),
    ("CUM", "cum"),
    ("m³", "cum"),
    ("m3", "cum"),
    ("cubic meter", "cum"),
    ("cubic meters", "cum"),
    ("cbm", "cum"),
    ("cft", "ft^3"),
    ("cu.ft", "ft^3"),
    ("cubic feet", "ft^3"),
]

COUNT_ALIASES: list[tuple[str, str]] = [
    ("no", "nos"),
    ("no.", "nos"),
    ("nos", "nos"),
    ("nos.", "nos"),
    ("Nos", "nos"),
    ("NOS", "nos"),
    ("nr", "nos"),
    ("ea", "nos"),
    ("each", "nos"),
    ("pcs", "nos"),
    ("pc", "nos"),
    ("piece", "nos"),
    ("pieces", "nos"),
    ("number", "nos"),
]

MASS_ALIASES: list[tuple[str, str]] = [
    ("kg", "kg"),
    ("KG", "kg"),
    ("Kg", "kg"),
    ("kgs", "kg"),
    ("kilogram", "kg"),
    ("kilograms", "kg"),
    # P3_04: MT / tonne / ton are metric tonne (= "mt" canonical) per
    # the spec's §1 ("MT/T/tonne") + §9 gotcha ("MT is metric tonne in
    # tenders, never 'empty'").  The ontology (data/ontology/units.json)
    # also uses "t" as the canonical for these.  The legacy alias table
    # had them as "kg" which was wrong; corrected.
    # Note: bare "t" is ambiguous (tonne vs thousand) per §9 gotcha —
    # it normalizes to UNKNOWN+flag, not mt.  Tenders use "MT" or
    # "tonne" not bare "t".
    ("MT", "mt"),
    ("mt", "mt"),
    ("tonne", "mt"),
    ("tonnes", "mt"),
    ("ton", "mt"),
    ("tons", "mt"),
    ("metric ton", "mt"),
    ("metric tonne", "mt"),
]

VOLUME_LIQUID_ALIASES: list[tuple[str, str]] = [
    ("ltr", "ltr"),
    # P3_04 §9 gotcha: "L" alone is ambiguous (liter vs leader) —
    # normalize as unknown, not ltr.  Real tenders use "ltr" or
    # "Ltr" not bare "L".
    ("Ltr", "ltr"),
    ("liter", "ltr"),
    ("litre", "ltr"),
    ("liters", "ltr"),
    ("litres", "ltr"),
]

OTHER_ALIASES: list[tuple[str, str]] = [
    ("set", "set"),
    ("sets", "set"),
    ("pair", "pair"),
    ("pairs", "pair"),
    ("bag", "bag"),
    ("bags", "bag"),
    ("sack", "bag"),
    ("sacks", "bag"),
    ("roll", "roll"),
    ("rolls", "roll"),
    ("coil", "coil"),
    ("coils", "coil"),
    ("drum", "drum"),
    ("drums", "drum"),
    ("box", "box"),
    ("boxes", "box"),
    ("bundle", "bundle"),
    ("bundles", "bundle"),
    ("hr", "hr"),
    ("hrs", "hr"),
    ("hour", "hr"),
    ("hours", "hr"),
    ("day", "day"),
    ("days", "day"),
]

ALL_ALIASES = (
    AREA_ALIASES
    + LENGTH_ALIASES
    + VOLUME_ALIASES
    + COUNT_ALIASES
    + MASS_ALIASES
    + VOLUME_LIQUID_ALIASES
    + OTHER_ALIASES
)


@pytest.mark.parametrize("alias,expected", ALL_ALIASES)
def test_normalize_unit_alias_table(alias: str, expected: str) -> None:
    """Every documented alias must map to its canonical form."""
    assert normalize_unit(alias) == expected


@pytest.mark.parametrize("alias,expected", ALL_ALIASES)
def test_get_canonical_unit_matches(alias: str, expected: str) -> None:
    """``get_canonical_unit`` is a thin wrapper and must agree."""
    assert get_canonical_unit(alias) == expected


@pytest.mark.parametrize("alias,expected", ALL_ALIASES)
def test_canonical_unit_matches(alias: str, expected: str) -> None:
    """The re-export in ``src.normalize.canonical`` must agree."""
    assert canonical_unit(alias) == expected


@pytest.mark.parametrize("alias,expected", ALL_ALIASES)
def test_legacy_unit_normalization_wrapper_matches(alias: str, expected: str) -> None:
    """The back-compat wrapper in ``src.unit_normalization`` must agree."""
    assert legacy_normalize_unit(alias) == expected


def test_normalize_unit_empty_falls_back_to_no() -> None:
    assert normalize_unit("") == "no."
    assert normalize_unit(None) == "no."  # type: ignore[arg-type]


def test_normalize_unit_strips_trailing_period_for_known_aliases() -> None:
    """A trailing period must not break a known alias."""
    assert normalize_unit("sqm.") == "sqm"
    assert normalize_unit("cum.") == "cum"
    assert normalize_unit("kg.") == "kg"
    assert normalize_unit("nos.") == "nos"
    assert normalize_unit("rmt.") == "rmt"


def test_normalize_unit_case_insensitive() -> None:
    assert normalize_unit("SQM") == normalize_unit("sqm")
    assert normalize_unit("Sqm") == normalize_unit("sqm")
    assert normalize_unit("CUM") == normalize_unit("cum")


def test_normalize_unit_unknown_returns_cleaned_input() -> None:
    """Unknown tokens should be cleaned (lowered, period-stripped) and returned."""
    assert normalize_unit("foo") == "foo"
    assert normalize_unit("FOO") == "foo"
    assert normalize_unit("foo.") == "foo"
    assert normalize_unit("  bar  ") == "bar"


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        (0, 0.0),
        (0.0, 0.0),
        (1, 1.0),
        (1.5, 1.5),
        ("1,200", 1200.0),
        ("270.00", 270.0),
        ("1,234.56", 1234.56),
        ("", None),
        ("abc", None),
    ],
)
def test_to_float_qty(value, expected: float) -> None:
    assert to_float_qty(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, 0),
        (0, 0),
        ("1,200", 1200),
        ("270.00", 270),
        ("1,234.56", 1234.56),
    ],
)
def test_to_decimal_qty(value, expected) -> None:
    from decimal import Decimal

    assert to_decimal_qty(value) == Decimal(str(expected))


@pytest.mark.parametrize(
    "unit",
    [
        "m^2",
        "m^3",
        "kg",
        # P3_04: the frozen CANONICAL_UNITS (config/constants.py)
        # uses "t" as a value for metric tonne.  However, the
        # P3_04 spec §9 gotcha marks all bare single-character
        # unit tokens (including "t") as ambiguous -- they
        # normalize to UNKNOWN+AMBIGUOUS_UNIT flag, not to a
        # canonical.  Real tenders use "MT" / "tonne" / "ton",
        # not bare "t".  So "t" is NOT a valid unit under P3_04
        # even though the frozen constants still list it.
        "ltr",
        "set",
        "pair",
        "roll",
        "box",
        "bundle",
        "drum",
        "bag",
        "coil",
        "ft^2",
        "ft^3",
        "ha",
        "acre",
        "no.",
        "rmt",
        "cum",
        "nos",
    ],
)
def test_is_valid_unit_true_for_canonical_forms(unit: str) -> None:
    assert is_valid_unit(unit) is True


@pytest.mark.parametrize("unit", ["foo", "???", "nope"])
def test_is_valid_unit_false_for_unknown(unit: str) -> None:
    assert is_valid_unit(unit) is False


def test_no_duplicate_keys_in_extra_aliases() -> None:
    """Guard against F601 (duplicate dict key) regression in src/rules/units.py."""
    from src.rules.units import _EXTRA_ALIASES  # noqa: PLC2701 — internal guard

    keys = list(_EXTRA_ALIASES.keys())
    assert len(keys) == len(set(keys)), f"duplicate alias keys: {keys}"


def test_acceptance_criterion_no_local_normalizer_defs() -> None:
    """Grep the criterion from the NW-05 task spec: zero local ``def normalize_unit`` /
    ``UNIT_ALIASES =`` outside ``src/rules/units.py`` and tests."""
    import re
    from pathlib import Path

    pattern = re.compile(r"(def normalize_unit|UNIT_ALIASES\s*=)")
    repo = Path(__file__).resolve().parent.parent.parent
    offenders: list[str] = []
    for sub in ("src", "scripts"):
        base = repo / sub
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if pattern.search(text):
                # Exclude the canonical home
                if path == (repo / "src" / "rules" / "units.py"):
                    continue
                offenders.append(str(path.relative_to(repo)))
    assert offenders == [], f"local normalizer definitions remain: {offenders}"
