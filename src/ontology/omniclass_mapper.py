"""OmniClass mapper for RFQ2BOQ entities."""

import json
from pathlib import Path
from typing import Any


class OmniClassMapper:
    """Maps RFQ2BOQ entity types to OmniClass codes."""

    def __init__(self, mapping_path: str | None = None):
        if mapping_path is None:
            mapping_path = Path(__file__).parent / "omniclass_mapping.json"
        with open(mapping_path) as f:
            self._mapping = json.load(f)

    def map_entity(self, entity_type: str) -> list[dict[str, Any]]:
        """Map an entity type to OmniClass codes."""
        if entity_type not in self._mapping:
            return []
        return self._mapping[entity_type].get("codes", [])

    def get_all_mappings(self) -> dict[str, list[dict[str, Any]]]:
        """Get all entity to OmniClass mappings."""
        return {k: v.get("codes", []) for k, v in self._mapping.items()}

    def reverse_lookup(self, omniclass_code: str) -> list[str]:
        """Look up which entity types map to a given OmniClass code."""
        results = []
        for entity_type, data in self._mapping.items():
            for code_info in data.get("codes", []):
                if code_info.get("code") == omniclass_code:
                    results.append(entity_type)
                    break
        return results

    def get_description(self, entity_type: str) -> str:
        """Get the primary description for an entity type."""
        if entity_type not in self._mapping:
            return ""
        codes = self._mapping[entity_type].get("codes", [])
        return codes[0].get("description", "") if codes else ""

    def get_indian_specific(self, entity_type: str) -> list[dict[str, Any]]:
        """Get Indian-specific OmniClass codes for an entity type."""
        if entity_type not in self._mapping:
            return []
        return self._mapping[entity_type].get("indian_specific", {}).get("codes", [])

    def to_unified_format(self, entity_type: str, value: str) -> dict[str, Any]:
        """Convert extracted entity to unified OmniClass format."""
        codes = self.map_entity(entity_type)
        primary_code = codes[0].get("code", "") if codes else ""
        return {
            "original_value": value,
            "entity_type": entity_type,
            "omniclass_code": primary_code,
            "description": self.get_description(entity_type),
        }


def create_omniclass_mapper() -> OmniClassMapper:
    """Factory function to create OmniClassMapper."""
    return OmniClassMapper()


if __name__ == "__main__":
    mapper = OmniClassMapper()
    for entity_type in ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]:
        codes = mapper.map_entity(entity_type)
        print(f"{entity_type}: {codes[0] if codes else 'No mapping'}")
