"""Tests for BoqRow model (E3/E4: rate_only flag, validation, serialization)."""

from __future__ import annotations

from decimal import Decimal

from src.domain.models import BoqRow


class TestBoqRowRateOnly:
    def test_rate_only_default_false(self) -> None:
        row = BoqRow(material="Cement", quantity=Decimal("100"), unit="kg")
        assert row.rate_only is False

    def test_rate_only_flag_set(self) -> None:
        row = BoqRow(material="Item", quantity=Decimal("0"), unit="Sqm.", rate_only=True)
        assert row.rate_only is True

    def test_rate_only_serialization(self) -> None:
        row = BoqRow(material="Item", quantity=Decimal("0"), unit="Sqm.", rate_only=True)
        d = row.model_dump(mode="json")
        assert d["rate_only"] is True

    def test_rate_only_deserialization(self) -> None:
        row = BoqRow(**{"material": "Item", "quantity": 0, "unit": "Sqm.", "rate_only": True})
        assert row.rate_only is True

    def test_backward_compat_no_rate_only_field(self) -> None:
        row = BoqRow(**{"material": "Item", "quantity": 100, "unit": "kg"})
        assert row.rate_only is False


class TestBoqRowValidation:
    def test_valid_row_no_errors(self) -> None:
        row = BoqRow(material="Cement", quantity=Decimal("100"), unit="kg")
        errors = row.validate()
        assert errors == []

    def test_empty_material_error(self) -> None:
        row = BoqRow(material="", quantity=Decimal("100"), unit="kg")
        errors = row.validate()
        assert any("material is empty" in e for e in errors)

    def test_whitespace_material_error(self) -> None:
        row = BoqRow(material="   ", quantity=Decimal("100"), unit="kg")
        errors = row.validate()
        assert any("material is empty" in e for e in errors)

    def test_empty_unit_error(self) -> None:
        row = BoqRow(material="Cement", quantity=Decimal("100"), unit="")
        errors = row.validate()
        assert any("unit is empty" in e for e in errors)

    def test_negative_quantity_error(self) -> None:
        row = BoqRow(material="Cement", quantity=Decimal("-5"), unit="kg")
        errors = row.validate()
        assert any("quantity is invalid" in e for e in errors)

    def test_rate_only_zero_qty_no_error(self) -> None:
        row = BoqRow(material="Item", quantity=Decimal("0"), unit="Sqm.", rate_only=True)
        errors = row.validate()
        assert errors == []

    def test_zero_qty_non_rate_only_no_error(self) -> None:
        """Zero qty without rate_only is allowed (BoqRow.validate allows qty >= 0)."""
        row = BoqRow(material="Item", quantity=Decimal("0"), unit="Sqm.")
        errors = row.validate()
        assert errors == []


class TestBoqRowConfidence:
    def test_confidence_range(self) -> None:
        row = BoqRow(material="Test", quantity=Decimal("10"), unit="kg", confidence=0.85)
        assert 0.0 <= row.confidence <= 1.0

    def test_confidence_default(self) -> None:
        row = BoqRow(material="Test", quantity=Decimal("10"), unit="kg")
        assert row.confidence == 0.0


class TestBoqRowWarnings:
    def test_warnings_default_empty(self) -> None:
        row = BoqRow(material="Test", quantity=Decimal("10"), unit="kg")
        assert row.warnings == []

    def test_warnings_with_value(self) -> None:
        row = BoqRow(material="Test", quantity=Decimal("10"), unit="kg", warnings=["LOW_CONFIDENCE"])
        assert row.warnings == ["LOW_CONFIDENCE"]


class TestBoqRowItemNo:
    """item_no accepts hierarchical / alphanumeric construction BOQ codes."""

    def test_integer_item_no(self) -> None:
        row = BoqRow(item_no=3, material="Cement", quantity=Decimal("1"), unit="kg")
        assert row.item_no == 3
        assert isinstance(row.item_no, int)

    def test_numeric_string_coerced_to_int(self) -> None:
        row = BoqRow(item_no="12", material="Cement", quantity=Decimal("1"), unit="kg")
        assert row.item_no == 12
        assert isinstance(row.item_no, int)

    def test_alphanumeric_hierarchical_code(self) -> None:
        # Seen on 05_zydus_animal_pharmez gold (A.6, B.drain.1, …)
        row = BoqRow(item_no="A.6", material="Insulation", quantity=Decimal("10"), unit="m2")
        assert row.item_no == "A.6"
        assert isinstance(row.item_no, str)

    def test_dotted_numeric_hierarchy(self) -> None:
        row = BoqRow(item_no="1.2.3", material="Pipe", quantity=Decimal("5"), unit="m")
        assert row.item_no == "1.2.3"

    def test_section_prefix_codes(self) -> None:
        for code in ("A.6", "B.10", "B.drain.1", "11.1.1"):
            row = BoqRow(item_no=code, material="x", quantity=Decimal("1"), unit="nos")
            assert row.item_no == code

    def test_reject_zero_int(self) -> None:
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BoqRow(item_no=0, material="x", quantity=Decimal("1"), unit="kg")

    def test_reject_empty_string(self) -> None:
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            BoqRow(item_no="  ", material="x", quantity=Decimal("1"), unit="kg")

    def test_serialization_roundtrip_str(self) -> None:
        row = BoqRow(item_no="A.6", material="Insulation", quantity=Decimal("10"), unit="m2")
        d = row.model_dump(mode="json")
        assert d["item_no"] == "A.6"
        restored = BoqRow(**d)
        assert restored.item_no == "A.6"
