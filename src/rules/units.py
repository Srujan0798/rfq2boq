"""Unit normalization rules."""

from config.constants import CANONICAL_UNITS


def normalize_unit(text: str) -> str:
    """Normalize unit text to canonical form."""
    if not text:
        return "no."
    text_lower = text.lower().strip()
    for key, value in CANONICAL_UNITS.items():
        if key.lower() == text_lower:
            return value
    return text_lower


def parse_quantity_unit(text: str) -> tuple:
    """Extract number and unit from strings like '500 sqm', '1,200 kg'."""
    import re

    match = re.match(r"([\d,]+(?:\.\d+)?)\s*([a-zA-Z³².]+)", text.strip())
    if match:
        number_str = match.group(1).replace(",", "")
        try:
            number = float(number_str)
        except ValueError:
            number = None
        unit = normalize_unit(match.group(2))
        return number, unit

    parts = text.strip().split()
    if parts:
        try:
            number = float(parts[0].replace(",", ""))
        except ValueError:
            number = None
        unit = normalize_unit(parts[-1]) if len(parts) > 1 else None
        return number, unit

    return None, None


def get_canonical_unit(unit_text: str) -> str:
    """Get canonical unit string."""
    return normalize_unit(unit_text)


def is_valid_unit(unit: str) -> bool:
    """Check if unit is valid canonical form."""
    return normalize_unit(unit) in CANONICAL_UNITS.values()


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
