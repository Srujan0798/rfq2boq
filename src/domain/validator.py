"""Domain validation rules for BOQ items."""

from dataclasses import dataclass

from src.domain.models import BoqRow, WarningType

MATERIAL_STANDARDS = {
    "cement": ["IS 1489", "IS 455"],
    "steel": ["IS 2062", "IS 1786", "IS 8500"],
    "concrete": ["IS 456", "IS 4926"],
    "brick": ["IS 1077", "IS 2180"],
    "aggregate": ["IS 383"],
    "sand": ["IS 383"],
    "timber": ["IS 7193"],
    "aluminum": ["IS 5082"],
}


VALID_UNITS = {
    "cement": ["bags", "kg", "tonnes"],
    "steel": ["kg", "tonnes", "no."],
    "concrete": ["m³", "cum", "cu.m"],
    "brick": ["no.", "thousand"],
    "aggregate": ["m³", "kg"],
    "sand": ["m³", "kg"],
}


@dataclass
class ValidationWarning:
    type: WarningType
    item_no: int
    message: str


class DomainValidator:
    def __init__(self, ontology: object | None = None):
        self.ontology = ontology

    def validate_boq(self, items: list[BoqRow]) -> list[ValidationWarning]:
        """Validate a list of BOQ items."""
        warnings = []
        for item in items:
            warnings.extend(self._validate_item(item))
        return warnings

    def validate_item(self, item: BoqRow) -> list[ValidationWarning]:
        """Validate a single BOQ item."""
        return self._validate_item(item)

    def _validate_item(self, item: BoqRow) -> list[ValidationWarning]:
        """Internal method to validate a single BOQ item."""
        warnings = []

        if not item.material or not item.material.strip():
            warnings.append(ValidationWarning(
                type=WarningType.QUANTITY_MISSING,
                item_no=item.item_no,
                message="Material description is empty",
            ))

        if item.quantity is None or item.quantity <= 0:
            warnings.append(ValidationWarning(
                type=WarningType.QUANTITY_MISSING,
                item_no=item.item_no,
                message="Quantity is missing or zero",
            ))
        elif item.quantity > 1000000:
            warnings.append(ValidationWarning(
                type=WarningType.QUANTITY_MISSING,
                item_no=item.item_no,
                message=f"Unusually large quantity: {item.quantity}",
            ))

        if not item.unit or item.unit.strip() == "":
            warnings.append(ValidationWarning(
                type=WarningType.UNIT_AMBIGUOUS,
                item_no=item.item_no,
                message="Unit is missing",
            ))

        if item.unit and item.material:
            mat_lower = item.material.lower()
            unit_lower = item.unit.lower() if item.unit else ""
            valid_for_mat = VALID_UNITS.get(mat_lower, [])
            if valid_for_mat and unit_lower not in valid_for_mat:
                warnings.append(ValidationWarning(
                    type=WarningType.LOW_CONFIDENCE,
                    item_no=item.item_no,
                    message=f"Unusual unit '{item.unit}' for material '{item.material}'",
                ))

        if item.material and self.ontology and hasattr(self.ontology, "lookup_material"):
            try:
                if not self.ontology.lookup_material(item.material):
                    warnings.append(ValidationWarning(
                        type=WarningType.LOW_CONFIDENCE,
                        item_no=item.item_no,
                        message=f"Unknown material '{item.material}'",
                    ))
            except Exception:
                pass

        if item.standard:
            for std in item.standard:
                if std:
                    ontology_valid = None
                    if self.ontology and hasattr(self.ontology, "validate_material_standard"):
                        try:
                            ontology_valid = self.ontology.validate_material_standard(item.material, str(std))
                        except Exception:
                            ontology_valid = None

                    mat_lower = item.material.lower() if item.material else ""
                    std_str = str(std).upper()
                    valid_stds = MATERIAL_STANDARDS.get(mat_lower, [])
                    static_valid = not valid_stds or any(v in std_str for v in valid_stds)
                    if ontology_valid is False or (ontology_valid is None and not static_valid):
                        warnings.append(ValidationWarning(
                            type=WarningType.LOW_CONFIDENCE,
                            item_no=item.item_no,
                            message=f"Standard '{std}' may not match material '{item.material}'",
                        ))

        if item.confidence < 0.7:
            warnings.append(ValidationWarning(
                type=WarningType.LOW_CONFIDENCE,
                item_no=item.item_no,
                message=f"Low confidence score: {item.confidence:.2f}",
            ))

        return warnings

    def validate_boq_item(self, item: BoqRow) -> list[ValidationWarning]:
        """Alias for _validate_item."""
        return self._validate_item(item)
