"""Tests for domain validator."""

from decimal import Decimal

from src.domain.models import BoqRow, WarningType
from src.domain.validator import DomainValidator, ValidationWarning


class TestDomainValidator:
    def test_initialization(self):
        validator = DomainValidator()
        assert validator.ontology is None

    def test_validate_empty(self):
        validator = DomainValidator()
        result = validator.validate_boq([])
        assert result == []

    def test_validate_item_with_missing_quantity(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="cement",
            quantity=Decimal("0"),
            unit="bags",
            confidence=0.8,
        )
        warnings = validator._validate_item(item)
        assert len(warnings) > 0
        assert any(w.type == WarningType.QUANTITY_MISSING for w in warnings)

    def test_validate_item_with_large_quantity(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="concrete",
            quantity=Decimal("1000001"),
            unit="m³",
            confidence=0.8,
        )
        warnings = validator._validate_item(item)
        assert len(warnings) > 0

    def test_validate_item_with_reasonable_values(self):
        validator = DomainValidator()
        item = BoqRow(
            item_no=1,
            material="concrete",
            quantity=Decimal("150.5"),
            unit="m³",
            confidence=0.8,
        )
        warnings = validator._validate_item(item)
        qty_warnings = [w for w in warnings if w.type == WarningType.QUANTITY_MISSING or "large" in w.message.lower()]
        assert len(qty_warnings) == 0


class TestValidationWarning:
    def test_repr(self):
        warning = ValidationWarning(
            type=WarningType.QUANTITY_MISSING,
            item_no=1,
            message="No quantity specified",
        )
        assert "QUANTITY_MISSING" in repr(warning)
        assert "item_no=1" in repr(warning)
