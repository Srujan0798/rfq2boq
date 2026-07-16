"""Tests for the unified unit normalizer (P3_04).

Covers the typed ``UnitNormalizer`` API, the legacy
``normalize_unit`` wrapper, the ``NormalizedUnit`` dataclass,
``UnitDimension`` enum, the ambiguous-singles rule (per the spec's
§9 gotcha), idempotence, and the dimension-class tagging that
P5_02's invariance tests will rely on.
"""

from __future__ import annotations

import pytest
from src.rules.units import (
    UnitDimension,
    UnitNormalizer,
    is_valid_unit,
    normalize_unit,
    parse_quantity_unit,
    to_float_qty,
)

# Spec §5 verification vector.  These are the bare-minimum mappings
# the spec demands: every Indian-tender variant of area / length /
# volume / count / mass / running-meter must normalize to the same
# canonical.
SPEC_VECTORS: list[tuple[str, str]] = [
    ("Rmt", "rmt"),
    ("R.M.", "rmt"),
    ("SQM", "sqm"),
    ("Sq.Mtr", "sqm"),
    ("M2", "sqm"),
    ("Nos", "nos"),
    ("EA", "nos"),
    ("MT", "mt"),
    ("tonne", "mt"),
    ("Cum", "cum"),
]


class TestSpecVector:
    """Spec §5 explicit vector: every Indian variant → canonical."""

    @pytest.mark.parametrize("raw,expected", SPEC_VECTORS)
    def test_spec_vector(self, raw: str, expected: str) -> None:
        n = UnitNormalizer()
        result = n.normalize(raw)
        assert result.canonical == expected
        assert result.original == raw
        assert not result.is_unknown
        assert not result.is_ambiguous


class TestDimensionClass:
    """P3_04 spec §9: dimension class must be correct on every canonical."""

    @pytest.mark.parametrize(
        "raw,expected_dim",
        [
            ("Sqm", UnitDimension.AREA),
            ("Sq.Mtr", UnitDimension.AREA),
            ("M2", UnitDimension.AREA),
            ("m^2", UnitDimension.AREA),
            ("Rmt", UnitDimension.LENGTH),
            ("rm", UnitDimension.LENGTH),
            ("mm", UnitDimension.LENGTH),
            ("meter", UnitDimension.LENGTH),
            ("metre", UnitDimension.LENGTH),
            ("Cum", UnitDimension.VOLUME),
            ("m3", UnitDimension.VOLUME),
            ("m^3", UnitDimension.VOLUME),
            ("ltr", UnitDimension.CAPACITY),
            ("Nos", UnitDimension.COUNT),
            ("No.", UnitDimension.COUNT),
            ("EA", UnitDimension.COUNT),
            ("kg", UnitDimension.MASS),
            ("MT", UnitDimension.MASS),
            ("tonne", UnitDimension.MASS),
            ("set", UnitDimension.COUNT),
            ("ls", UnitDimension.LUMPSUM),
            ("hr", UnitDimension.TIME),
        ],
    )
    def test_dimension(self, raw: str, expected_dim: UnitDimension) -> None:
        n = UnitNormalizer()
        result = n.normalize(raw)
        assert result.dimension == expected_dim, f"{raw!r} → {result.dimension} (expected {expected_dim})"


class TestIdempotence:
    """normalize(normalize(x)).canonical == normalize(x).canonical."""

    @pytest.mark.parametrize("raw", ["RMT", "SQM", "MT", "tonne", "EA", "Cum", "M2"])
    def test_idempotent(self, raw: str) -> None:
        n = UnitNormalizer()
        first = n.normalize(raw)
        second = n.normalize(first.canonical)
        assert first.canonical == second.canonical
        assert first.dimension == second.dimension


class TestAmbiguousSingles:
    """P3_04 spec §9: bare single-letter tokens are ambiguous → UNKNOWN+flag."""

    @pytest.mark.parametrize("raw", ["M", "T", "L", "A", "V", "W", "m", "t", "l"])
    def test_ambiguous_singles(self, raw: str) -> None:
        n = UnitNormalizer()
        result = n.normalize(raw)
        assert result.is_ambiguous
        assert result.is_unknown
        assert result.dimension == UnitDimension.UNKNOWN
        # canonical is a sentinel "unknown" string so downstream code
        # can still write a value (R1: never silently drop).
        assert result.canonical == "unknown"


class TestUnknownUnit:
    """Unknown inputs are flagged, never silently coerced."""

    def test_garbage_string_is_unknown(self) -> None:
        n = UnitNormalizer()
        result = n.normalize("xyz")
        assert result.is_unknown
        assert not result.is_ambiguous
        assert result.canonical == "xyz"
        assert result.original == "xyz"

    def test_empty_is_unknown(self) -> None:
        n = UnitNormalizer()
        result = n.normalize("")
        assert result.is_unknown
        assert not result.is_ambiguous
        assert result.canonical == ""
        assert result.dimension == UnitDimension.UNKNOWN

    def test_none_is_unknown(self) -> None:
        n = UnitNormalizer()
        result = n.normalize(None)
        assert result.is_unknown
        assert result.canonical == ""

    def test_whitespace_only_is_unknown(self) -> None:
        n = UnitNormalizer()
        result = n.normalize("   ")
        assert result.is_unknown
        assert result.canonical == ""


class TestLegacyBackCompat:
    """The legacy free function ``normalize_unit`` must keep working."""

    def test_legacy_returns_canonical_string(self) -> None:
        assert normalize_unit("RMT") == "rmt"
        assert normalize_unit("SQM") == "sqm"
        assert normalize_unit("MT") == "mt"
        assert normalize_unit("Nos") == "nos"
        assert normalize_unit("Cum") == "cum"

    def test_legacy_empty_returns_no(self) -> None:
        # Legacy behavior: empty input → "no."
        assert normalize_unit("") == "no."
        assert normalize_unit(None) == "no."  # type: ignore[arg-type]

    def test_legacy_unknown_returns_cleaned(self) -> None:
        # Unknown inputs are cleaned and returned as-is (legacy behavior).
        assert normalize_unit("FOO") == "foo"
        assert normalize_unit("foo.") == "foo"


class TestIsValidUnit:
    """``is_valid_unit`` should be permissive (per P3_04) — accepts
    alias-table canonicals (rmt, cum, nos, mt) in addition to the
    frozen CANONICAL_UNITS values, and rejects ambiguous singles."""

    @pytest.mark.parametrize("u", ["m^2", "m^3", "kg", "ltr", "set", "ft^2", "ha", "acre", "no."])
    def test_valid_canonical(self, u: str) -> None:
        assert is_valid_unit(u) is True

    @pytest.mark.parametrize("u", ["rmt", "cum", "nos", "mt"])
    def test_valid_alias_canonical(self, u: str) -> None:
        # These are not in the frozen CANONICAL_UNITS.values() set
        # but are valid per the alias table.
        assert is_valid_unit(u) is True

    @pytest.mark.parametrize("u", ["M", "T", "L", "A"])
    def test_invalid_ambiguous(self, u: str) -> None:
        assert is_valid_unit(u) is False

    @pytest.mark.parametrize("u", ["foo", "???", ""])
    def test_invalid_unknown(self, u: str) -> None:
        assert is_valid_unit(u) is False


class TestQuantityCoercion:
    """``to_float_qty`` and ``parse_quantity_unit`` unchanged behavior."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, None),
            (0, 0.0),
            ("1,200", 1200.0),
            ("270.00", 270.0),
            ("1,234.56", 1234.56),
            ("", None),
            ("abc", None),
        ],
    )
    def test_to_float_qty(self, value, expected: float | None) -> None:
        assert to_float_qty(value) == expected

    def test_parse_quantity_unit(self) -> None:
        qty, unit = parse_quantity_unit("500 sqm")
        assert qty == 500.0
        assert unit == "sqm"

        qty, unit = parse_quantity_unit("1,200 kg")
        assert qty == 1200.0
        assert unit == "kg"

    def test_parse_quantity_unit_with_multiword(self) -> None:
        qty, unit = parse_quantity_unit("12.5 running meter")
        assert qty == 12.5
        assert unit == "rmt"


class TestSingleSourceInvariant:
    """P3_04 acceptance: ONE normalizer; no duplicate tables."""

    def test_no_duplicate_unit_aliases(self) -> None:
        from src.rules.units import UNIT_ALIASES

        # Catch F601 regression: duplicate keys silently overwrite
        # each other in dict literals.
        keys = list(UNIT_ALIASES.keys())
        assert len(keys) == len(set(keys)), f"duplicate alias keys: {keys}"

    def test_legacy_alias_table_gone(self) -> None:
        # The duplicate UNIT_ALIASES table in src/domain/fidelity.py
        # has been removed and replaced with the canonical normalizer.
        from src.domain import fidelity

        assert not hasattr(fidelity, "UNIT_ALIASES"), (
            "fidelity.UNIT_ALIASES should be GONE — the canonical UnitNormalizer in src.rules.units is the only source."
        )
