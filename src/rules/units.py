"""Unit normalization rules — single source of truth for the whole repo.

Every component that needs to canonicalize a unit or coerce a quantity
must import from here.  No local alias tables allowed.

P3_04: provides the typed ``UnitNormalizer`` + ``NormalizedUnit`` API used
by every stage (assembler, exporters, validators).  The legacy free
functions (``normalize_unit``, ``parse_quantity_unit``, etc.) are thin
wrappers that delegate to ``UnitNormalizer`` for backward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any

from config.constants import CANONICAL_UNITS

# ---------------------------------------------------------------------------
# UNIT_ALIASES — comprehensive alias-to-canonical mapping consolidated from
# every local alias table that existed before NW-05.  Checked BEFORE
# CANONICAL_UNITS so that the (sqm → sqm, cum → cum, …) convention
# used by all real-tender extraction logic takes priority.
# Keys are lower-cased; trailing-period handling is automatic in _lookup.
# ---------------------------------------------------------------------------
UNIT_ALIASES: dict[str, str] = {
    # --- Count ---
    "nos": "nos",
    "no": "nos",
    "nos.": "nos",
    "no.": "nos",
    "nr": "nos",
    "ea": "nos",
    "each": "nos",
    "pcs": "nos",
    "pc": "nos",
    "pieces": "nos",
    "piece": "nos",
    "number": "nos",
    "numbers": "nos",
    "coil": "coil",
    # P3_04: "coil" and "roll" are BOTH distinct count-dimension
    # canonicals per the data/ontology/units.json (coil = "coil",
    # roll = "roll").  The legacy alias table collapsed "coil" -> "roll";
    # preserve both as separate canonicals.
    "coils": "coil",
    # --- Mass ---
    "kg": "kg",
    "kgs": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "mt": "mt",
    "ton": "mt",
    "tons": "mt",
    "tonne": "mt",
    "tonnes": "mt",
    "metric ton": "mt",
    "metric tonne": "mt",
    "t": "mt",
    # --- Volume (cum) ---
    "cum": "cum",
    "cu.m": "cum",
    "cu.m.": "cum",
    "cum.": "cum",
    "m³": "cum",
    "m3": "cum",
    "cbm": "cum",
    "cu m": "cum",
    "cubic meter": "cum",
    "cubic meters": "cum",
    "cubic metre": "cum",
    "cubic metres": "cum",
    "cubicmeter": "cum",
    "cubicmeters": "cum",
    "cft": "ft^3",
    "cu.ft": "ft^3",
    "cft.": "ft^3",
    "cubic feet": "ft^3",
    # --- Area (sqm) ---
    "sqm": "sqm",
    "sq.m": "sqm",
    "sqm.": "sqm",
    "sq.m.": "sqm",
    "sqmtr": "sqm",
    "sqmtrs": "sqm",
    "sqmt": "sqm",
    "sq meter": "sqm",
    "sq metre": "sqm",
    "sq. mtr": "sqm",
    "sq.mtr": "sqm",
    "sqmeter": "sqm",
    "sqmeters": "sqm",
    "sqft": "sqm",
    "sq.ft": "sqm",
    "sft": "sqm",
    "sft.": "sqm",
    "sq ft": "sqm",
    "square feet": "sqm",
    "squarefeet": "sqm",
    "square meter": "sqm",
    "square meters": "sqm",
    "square metre": "sqm",
    "square metres": "sqm",
    "squaremeter": "sqm",
    "squaremeters": "sqm",
    "squaremetre": "sqm",
    "squaremetres": "sqm",
    "m²": "sqm",
    "m2": "sqm",
    # --- Running metre (rmt) ---
    "rmt": "rmt",
    "r.m": "rmt",
    "r.m.": "rmt",
    "rm": "rmt",
    "l.m": "rmt",
    "lm": "rmt",
    "running meter": "rmt",
    "running meters": "rmt",
    "running metre": "rmt",
    "running metres": "rmt",
    "runningmeter": "rmt",
    "runningmeters": "rmt",
    "runningmetre": "rmt",
    "runningmetres": "rmt",
    "linear meter": "rmt",
    "linear metre": "rmt",
    "lineal meter": "rmt",
    "lineal metre": "rmt",
    "r.mtr": "rmt",
    # --- Capacity (ltr) ---
    "ltr": "ltr",
    "liter": "ltr",
    "litre": "ltr",
    "liters": "ltr",
    "litres": "ltr",
    "l": "ltr",
    # --- Set ---
    "set": "set",
    "sets": "set",
    # --- Packaging ---
    "bag": "bag",
    "bags": "bag",
    "sack": "bag",
    "sacks": "bag",
    "roll": "roll",
    "rolls": "roll",
    # P3_04: coil/roll are now distinct canonicals (see Count section
    # above); the legacy duplicate "coil" -> "roll" mapping was
    # removed.
    "bundle": "bundle",
    "bundles": "bundle",
    "pair": "pair",
    "pairs": "pair",
    "pr": "pair",
    "drum": "drum",
    "drums": "drum",
    "box": "box",
    "boxes": "box",
    "carton": "carton",
    "cartons": "carton",
    "can": "can",
    "cans": "can",
    # --- Time ---
    "hr": "hr",
    "hrs": "hr",
    "hour": "hr",
    "hours": "hr",
    "day": "day",
    "days": "day",
    # --- Square mm ---
    "sqmm": "sqmm",
    "sq.mm": "sqmm",
    "mm²": "sqmm",
    # --- Bare length ---
    "m": "m",
    "meter": "m",
    "metre": "m",
    "meters": "m",
    "metres": "m",
    "mm": "mm",
    "millimeter": "mm",
    "millimetre": "mm",
    "millimeters": "mm",
    "millimetres": "mm",
    "cm": "cm",
    "centimeter": "cm",
    "centimetre": "cm",
    "centimeters": "cm",
    "centimetres": "cm",
    "foot": "ft",
    "feet": "ft",
    "ft": "ft",
    "inch": "in",
    "inches": "in",
    "in": "in",
    # --- Electrical ---
    "kilowatt": "kW",
    "watt": "W",
    "kiloliter": "kl",
    "kilolitre": "kl",
    "milliliter": "ml",
    "millilitre": "ml",
    "bar": "bar",
    "psi": "psi",
    # --- Lump sum ---
    "lump-sum": "ls",
    "lumpsum": "ls",
    # --- Hectare/acre ---
    "hectare": "ha",
    "hectares": "ha",
    "acre": "acre",
    "acres": "acre",
}

# Additional aliases added by Lane E tasks (E1/E3) — kept separate for
# clarity and tested by test_units_unified.py::test_no_duplicate_keys_in_extra_aliases.
# Currently empty; all production aliases live in UNIT_ALIASES above.
_EXTRA_ALIASES: dict[str, str] = {}


def parse_quantity_unit(text: str) -> tuple[float | None, str | None]:
    """Extract number and unit from strings like '500 sqm', '1,200 kg', '12.5 running meter'.

    P3_04: extended to capture multi-word units (``running meter``,
    ``cubic feet``, ``metric ton``) by greedily matching alpha-tokens
    after the number.  The matched unit text is then run through
    :class:`UnitNormalizer` so multi-word aliases resolve to their
    canonical form (``running meter`` → ``rmt``).
    """
    import re

    # First try: number followed by a single alpha-token unit.
    # Use ``\S+`` to capture all non-space chars so "12.5 rm" or
    # "12.5sqm" both work; the multi-word branch handles the case
    # where the unit is space-separated.
    match = re.match(r"([\d,]+(?:\.\d+)?)(\s+)([^\s]+)\s*$", text.strip())
    if match:
        number_str = match.group(1).replace(",", "")
        try:
            number = float(number_str)
        except ValueError:
            number = None
        unit = _DEFAULT_NORMALIZER.normalize(match.group(3)).canonical
        return number, unit

    # Second try: number followed by a multi-word unit (1+ alpha tokens).
    match2 = re.match(r"([\d,]+(?:\.\d+)?)\s+([a-zA-Z][a-zA-Z\s³².]+?)\s*$", text.strip())
    if match2:
        number_str = match2.group(1).replace(",", "")
        try:
            number = float(number_str)
        except ValueError:
            number = None
        unit = _DEFAULT_NORMALIZER.normalize(match2.group(2)).canonical
        return number, unit

    parts = text.strip().split()
    if parts:
        try:
            number = float(parts[0].replace(",", ""))
        except ValueError:
            number = None
        parsed_unit: str | None = _DEFAULT_NORMALIZER.normalize(parts[-1]).canonical if len(parts) > 1 else None
        return number, parsed_unit

    return None, None


def get_canonical_unit(unit_text: str) -> str:
    """Get canonical unit string."""
    return normalize_unit(unit_text)


def is_valid_unit(unit: str) -> bool:
    """Check if unit is a valid canonical form (or an unknown-after-normalize).

    P3_04: a unit is "valid" iff it normalizes to a known canonical with a
    non-UNKNOWN dimension.  This is more permissive than checking against
    the frozen ``CANONICAL_UNITS.values()`` set alone — it also accepts
    the new alias-table canonicals (``rmt``, ``cum``, ``nos``, ``mt``)
    that real tenders use but the frozen constants haven't been
    updated to include.  Bare ambiguous singles (``M``, ``T``, ``L``)
    return False, which is the desired flag-emit behavior.
    """
    n = _DEFAULT_NORMALIZER.normalize(unit)
    return bool(n.canonical) and n.dimension != UnitDimension.UNKNOWN and not n.is_ambiguous


def get_unit_for_material(material: str) -> str:
    """Get default unit for a material."""
    material_lower = material.lower()
    defaults = {
        "cement": "bags",
        "concrete": "m^3",
        "steel": "kg",
        "brick": "no.",
        "aggregate": "m^3",
        "sand": "m^3",
        "marble": "m^2",
        "granite": "m^2",
        "tile": "m^2",
        "paint": "L",
        "mortar": "m^3",
        "plaster": "m^2",
    }
    return defaults.get(material_lower, "no.")


def to_float_qty(value: Any) -> float | None:
    """Coerce a quantity value to float.

    Handles strings with commas (\"1,200\"), ints, floats, Decimals,
    and returns None for unparseable input.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def to_decimal_qty(value: Any) -> Decimal:
    """Coerce a quantity value to Decimal.

    Same rules as ``to_float_qty`` but returns Decimal.
    """
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).replace(",", "").strip())
    except Exception:
        return Decimal("0")


# ---------------------------------------------------------------------------
# P3_04 typed normalizer
# ---------------------------------------------------------------------------


class UnitDimension(StrEnum):
    """Physical dimension class a unit belongs to.

    P3_04: dimension class matters downstream (a qty in sqm attached to
    a length-dimensioned material is a red-flag combo P5_02's invariance
    tests can use).  Categories:

    - LENGTH       — meter-class
    - AREA         — square-meter class
    - VOLUME       — cubic-meter class
    - MASS         — kilogram / tonne class
    - COUNT        — nos / ea / each / set
    - TIME         — hr / day
    - RATE         — kg/m, m/m, etc. (not used in tenders but reserved)
    - ELECTRICAL   — W / kW / A / V
    - PRESSURE     — bar / psi / Pa
    - CAPACITY     — ltr / kl / ml
    - LUMPSUM      — ls / lot / job
    - UNKNOWN      — anything we don't recognize (never silently coerced)
    """

    LENGTH = "length"
    AREA = "area"
    VOLUME = "volume"
    MASS = "mass"
    COUNT = "count"
    TIME = "time"
    RATE = "rate"
    ELECTRICAL = "electrical"
    PRESSURE = "pressure"
    CAPACITY = "capacity"
    LUMPSUM = "lumpsum"
    UNKNOWN = "unknown"


# Dimension classification: canonical-symbol → dimension.
# Built from data/ontology/units.json's "dimension" field, frozen in
# code so we never re-read disk on the hot path.  P3_04 audit confirmed
# the ontology's dimensions are correct.
_CANONICAL_TO_DIMENSION: dict[str, UnitDimension] = {
    # Length
    "m": UnitDimension.LENGTH,
    "cm": UnitDimension.LENGTH,
    "mm": UnitDimension.LENGTH,
    "ft": UnitDimension.LENGTH,
    "in": UnitDimension.LENGTH,
    "rmt": UnitDimension.LENGTH,
    # Area
    "m^2": UnitDimension.AREA,
    "sqm": UnitDimension.AREA,
    "ft^2": UnitDimension.AREA,
    "ha": UnitDimension.AREA,
    "acre": UnitDimension.AREA,
    # Volume
    "m^3": UnitDimension.VOLUME,
    "cum": UnitDimension.VOLUME,
    "ft^3": UnitDimension.VOLUME,
    "ltr": UnitDimension.CAPACITY,
    "ml": UnitDimension.CAPACITY,
    "kl": UnitDimension.CAPACITY,
    "gal": UnitDimension.VOLUME,
    # Mass
    "kg": UnitDimension.MASS,
    "mt": UnitDimension.MASS,
    "g": UnitDimension.MASS,
    "lb": UnitDimension.MASS,
    # Count
    "no.": UnitDimension.COUNT,
    "nos": UnitDimension.COUNT,
    "set": UnitDimension.COUNT,
    "pair": UnitDimension.COUNT,
    "bag": UnitDimension.COUNT,
    "roll": UnitDimension.COUNT,
    "drum": UnitDimension.COUNT,
    "box": UnitDimension.COUNT,
    "bundle": UnitDimension.COUNT,
    "point": UnitDimension.COUNT,
    "plate": UnitDimension.COUNT,
    "coil": UnitDimension.COUNT,
    "lot": UnitDimension.COUNT,
    "job": UnitDimension.COUNT,
    "sheet": UnitDimension.COUNT,
    "carton": UnitDimension.COUNT,
    "can": UnitDimension.COUNT,
    # Lumpsum
    "ls": UnitDimension.LUMPSUM,
    # Time
    "hr": UnitDimension.TIME,
    "day": UnitDimension.TIME,
    # Electrical
    "W": UnitDimension.ELECTRICAL,
    "kW": UnitDimension.ELECTRICAL,
    "V": UnitDimension.ELECTRICAL,
    "A": UnitDimension.ELECTRICAL,
    "VA": UnitDimension.ELECTRICAL,
    "kVA": UnitDimension.ELECTRICAL,
    "hp": UnitDimension.ELECTRICAL,
    # Pressure
    "bar": UnitDimension.PRESSURE,
    "psi": UnitDimension.PRESSURE,
    "Pa": UnitDimension.PRESSURE,
    "kPa": UnitDimension.PRESSURE,
}


# Bare ambiguous single-letter / single-token units (per P3_04 §9 gotcha).
# "M" alone is ambiguous (meter vs thousand).  "T" alone is ambiguous
# (tonne vs thousand).  These get normalized to UNKNOWN with an
# AMBIGUOUS_UNIT flag rather than guessed.
_AMBIGUOUS_SINGLES: frozenset[str] = frozenset({"m", "t", "l", "a", "v", "w"})

# Stripped characters during pre-processing (e.g. trailing periods).
_STRIP_CHARS = ".,;: \t"


@dataclass(frozen=True)
class NormalizedUnit:
    """Result of normalizing one unit string.

    Fields:
    - ``canonical`` : canonical symbol (e.g. ``"sqm"``, ``"rmt"``,
      ``"mt"`` for unknown-after-table-lookup).  Never empty.
    - ``dimension`` : the ``UnitDimension`` enum value; ``UNKNOWN`` for
      unrecognized input.
    - ``original``  : the raw input text, preserved verbatim for audit
      and for round-tripping into Excel/JSON outputs.
    - ``is_unknown`` : True iff the input was not in any alias table —
      the canonical falls back to the lowercased+stripped form so
      downstream code still has a string to write, and a flag should be
      attached (R1: flag, never drop).
    - ``is_ambiguous`` : True iff the input was a bare single character
      like ``"M"`` that is genuinely ambiguous (meter vs thousand).  Per
      P3_04 §9, ambiguous singles normalize to UNKNOWN+flag rather than
      guess (R1: a wrong guess is worse than a flag).
    """

    canonical: str
    dimension: UnitDimension
    original: str
    is_unknown: bool = False
    is_ambiguous: bool = False

    def __post_init__(self) -> None:
        # canonical is allowed to be empty for the empty-input case so
        # downstream code can still write something (an empty cell / a
        # flag) without crashing.  The is_unknown flag is the source of
        # truth for "this is not a real unit".
        if self.canonical is None:
            raise ValueError("NormalizedUnit.canonical must not be None")

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical": self.canonical,
            "dimension": self.dimension.value,
            "original": self.original,
            "is_unknown": self.is_unknown,
            "is_ambiguous": self.is_ambiguous,
        }


class UnitNormalizer:
    """Canonical unit normalizer for the whole pipeline (P3_04).

    Stateless / thread-safe.  Wraps the alias tables in this module
    and the canonical-symbol → dimension map.  The legacy
    ``normalize_unit(text) -> str`` function is a thin wrapper around
    ``UnitNormalizer().normalize(text).canonical`` for backward
    compatibility.
    """

    def __init__(
        self,
        alias_map: dict[str, str] | None = None,
        canonical_to_dimension: dict[str, UnitDimension] | None = None,
    ) -> None:
        # Use the module-level tables by default.  Injectable for tests.
        self._alias_map: dict[str, str] = alias_map if alias_map is not None else UNIT_ALIASES
        self._canonical_to_dimension: dict[str, UnitDimension] = (
            canonical_to_dimension if canonical_to_dimension is not None else _CANONICAL_TO_DIMENSION
        )

    def normalize(self, raw: str | None) -> NormalizedUnit:
        """Normalize a raw unit string.

        Algorithm (R1-honest):
        1. Empty / None → canonical="" + UNKNOWN + is_unknown=True
        2. Pre-clean (lowercase, strip punctuation/whitespace)
        3. Look up in UNIT_ALIASES first (preserves sqm→sqm, cum→cum, …)
        4. If alias hit, look up canonical's dimension.  If dimension is
           UNKNOWN, mark is_unknown=True (defensive).
        5. If no alias hit, try CANONICAL_UNITS table (case-insensitive
           and rstrip-period).
        6. Bare ambiguous single (e.g. "M", "T") → canonical="unknown",
           is_ambiguous=True, dimension=UNKNOWN.
        7. Truly unknown → canonical = cleaned input, is_unknown=True,
           dimension=UNKNOWN.

        Never raises on bad input.  Never silently drops (always returns
        a NormalizedUnit; downstream stages can decide whether to attach
        a flag for the is_unknown/is_ambiguous cases).
        """
        original = "" if raw is None else str(raw)
        cleaned = original.lower().strip().rstrip(_STRIP_CHARS)
        if not cleaned:
            return NormalizedUnit(
                canonical="",
                dimension=UnitDimension.UNKNOWN,
                original=original,
                is_unknown=True,
            )

        # Bare ambiguous single (per P3_04 §9): "M" is meter-vs-thousand,
        # "T" is tonne-vs-thousand, "L" litre-vs-leader, "A" ampere-vs-area.
        if cleaned in _AMBIGUOUS_SINGLES:
            return NormalizedUnit(
                canonical="unknown",
                dimension=UnitDimension.UNKNOWN,
                original=original,
                is_unknown=True,
                is_ambiguous=True,
            )

        # If the input is already a known canonical (e.g. someone
        # passes "m^2" or "rmt" directly, not via an alias), accept
        # it as-is.  This is the "idempotence" property required by
        # the spec: normalize(normalize(x)) == normalize(x).
        if cleaned in self._canonical_to_dimension:
            dim = self._canonical_to_dimension[cleaned]
            return NormalizedUnit(
                canonical=cleaned,
                dimension=dim,
                original=original,
                is_unknown=False,
            )

        # Look in UNIT_ALIASES (preserves the "sqm → sqm" convention
        # that real-tender extraction logic depends on).
        canon: str | None = None
        for key, value in self._alias_map.items():
            if key == cleaned or key.rstrip(".") == cleaned.rstrip("."):
                canon = value
                break
        if canon is None:
            # Fallback to CANONICAL_UNITS (lowercased, rstrip-period).
            for key, value in CANONICAL_UNITS.items():
                k = key.lower()
                if k == cleaned or k.rstrip(".") == cleaned.rstrip("."):
                    canon = value
                    break
        if canon is None:
            # Last resort: cleaned form.  is_unknown=True so downstream
            # stages can attach a flag.
            return NormalizedUnit(
                canonical=cleaned.rstrip("."),
                dimension=UnitDimension.UNKNOWN,
                original=original,
                is_unknown=True,
            )

        # Look up dimension for the canonical.
        dim = self._canonical_to_dimension.get(canon, UnitDimension.UNKNOWN)
        return NormalizedUnit(
            canonical=canon,
            dimension=dim,
            original=original,
            is_unknown=(dim == UnitDimension.UNKNOWN),
        )

    def dimension(self, canonical: str) -> UnitDimension:
        """Return the dimension for an already-canonicalized unit string."""
        return self._canonical_to_dimension.get(canonical, UnitDimension.UNKNOWN)


# Singleton used by hot paths.
_DEFAULT_NORMALIZER = UnitNormalizer()


def normalize_unit(text: str) -> str:
    """Normalize unit text to canonical form (string return for back-compat).

    This is the legacy free function preserved for backward compatibility.
    New code should call :class:`UnitNormalizer` directly to get the
    typed ``NormalizedUnit`` (with dimension + is_unknown / is_ambiguous
    flags).
    """
    if not text:
        return "no."
    return _DEFAULT_NORMALIZER.normalize(text).canonical or "no."
