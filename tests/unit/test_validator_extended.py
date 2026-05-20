"""Extended tests for domain validator."""

from decimal import Decimal

from src.domain.models import BoqRow, WarningType
from src.domain.validator import DomainValidator


class TestValidatorExtended:
    def test_validate_empty_material(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="",
            quantity=Decimal("100"),
            unit="kg",
            confidence=0.9,
        )
        warnings = validator.validate_boq_item(item)
        assert len(warnings) > 0
        assert any(w.type == WarningType.QUANTITY_MISSING for w in warnings)

    def test_validate_zero_quantity(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="cement",
            quantity=Decimal("0"),
            unit="bags",
            confidence=0.5,
        )
        warnings = validator.validate_boq_item(item)
        assert len(warnings) > 0
        assert any(w.type == WarningType.QUANTITY_MISSING for w in warnings)

    def test_validate_low_confidence(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="steel",
            quantity=Decimal("500"),
            unit="kg",
            confidence=0.5,
        )
        warnings = validator.validate_boq_item(item)
        assert len(warnings) > 0
        assert any(w.type == WarningType.LOW_CONFIDENCE for w in warnings)

    def test_validate_high_confidence(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="steel",
            quantity=Decimal("500"),
            unit="kg",
            confidence=0.85,
        )
        warnings = validator.validate_boq_item(item)
        assert len(warnings) == 0

    def test_validate_large_quantity(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="concrete",
            quantity=Decimal("9999999"),
            unit="m³",
            confidence=0.9,
        )
        warnings = validator.validate_boq_item(item)
        assert len(warnings) > 0

    def test_validate_all_warnings_at_once(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="",
            quantity=Decimal("0"),
            unit="",
            confidence=0.3,
        )
        warnings = validator.validate_boq_item(item)
        assert len(warnings) >= 3

    def test_validate_multiple_items(self):
        validator = DomainValidator()
        items = [
            BoqRow(item_no=1, material="cement", quantity=Decimal("100"), unit="bags", confidence=0.9),
            BoqRow(item_no=2, material="", quantity=Decimal("0"), unit="kg", confidence=0.4),
            BoqRow(item_no=3, material="steel", quantity=Decimal("200"), unit="kg", confidence=0.8),
        ]
        warnings = validator.validate_boq(items)
        assert len(warnings) >= 1

    def test_validate_none_values(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="cement",
            quantity=Decimal("100"),
            unit="bags",
            confidence=0.9,
        )
        assert validator.validate_boq_item(item) is not None

    def test_validate_whitespace_material(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="   ",
            quantity=Decimal("100"),
            unit="bags",
            confidence=0.9,
        )
        warnings = validator.validate_boq_item(item)
        assert len(warnings) > 0

    def test_validate_very_small_quantity(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="cement",
            quantity=Decimal("0.001"),
            unit="bags",
            confidence=0.9,
        )
        warnings = validator.validate_boq_item(item)
        assert len(warnings) == 0

    def test_validate_item_with_grade(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="concrete",
            quantity=Decimal("50"),
            unit="m³",
            grade="M30",
            confidence=0.85,
        )
        warnings = validator.validate_boq_item(item)
        assert len(warnings) == 0

    def test_validate_item_with_standard(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="steel",
            quantity=Decimal("1000"),
            unit="kg",
            standard=["IS 2062"],
            confidence=0.9,
        )
        warnings = validator.validate_boq_item(item)
        assert len(warnings) == 0
