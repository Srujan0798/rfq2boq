"""OmniClass mapper for RFQ2BOQ entities."""

import json
from pathlib import Path
from typing import Any


class OmniClassMapper:
    """Bidirectional mapper between RFQ2BOQ entities and OmniClass codes."""

    def __init__(self, path: str | Path | None = None):
        if path is None:
            path = Path(__file__).parent.parent.parent / "data" / "ontology" / "omniclass_map.json"
        with open(path) as f:
            self._data = json.load(f)

    def map_entity(self, entity_type: str, text: str | None = None) -> dict[str, Any]:
        """Map an entity type to OmniClass table info."""
        entity_map = self._data.get("entity_to_omniclass", {})
        if entity_type not in entity_map:
            return {"table": None, "code": None, "name": None, "note": "Unknown entity type"}

        result = dict(entity_map[entity_type])

        if text and entity_type == "MATERIAL":
            mat_specifics = self._data.get("material_specifics", {})
            text_lower = text.lower().replace(" ", "_")
            if text_lower in mat_specifics:
                result["code"] = mat_specifics[text_lower]
                result["specific"] = True
            else:
                for mat_key, code in mat_specifics.items():
                    if mat_key.replace("_", " ") in text.lower():
                        result["code"] = code
                        result["specific"] = True
                        break

        return result

    def reverse_lookup(self, omniclass_code: str) -> str | None:
        """Look up which entity type maps to a given OmniClass code."""
        entity_map = self._data.get("entity_to_omniclass", {})

        # First check exact matches in material_specifics
        mat_specifics = self._data.get("material_specifics", {})
        for _mat, code in mat_specifics.items():
            if code == omniclass_code:
                return "MATERIAL"

        # Check action_specifics
        action_specifics = self._data.get("action_specifics", {})
        for _act, code in action_specifics.items():
            if str(code) == omniclass_code:
                return "ACTION"

        # Check entity_to_omniclass with prefix matching
        for entity_type, info in entity_map.items():
            # Skip entities with no table (QUANTITY, UNIT)
            if info.get("table") is None:
                continue
            code = str(info.get("default_code", ""))
            if code and omniclass_code.startswith(code):
                return str(entity_type)

        return None

    def get_material_code(self, material_text: str) -> str | None:
        """Get OmniClass code for a specific material."""
        mat_specifics = self._data.get("material_specifics", {})
        text_lower = material_text.lower().replace(" ", "_")
        if text_lower in mat_specifics:
            return str(mat_specifics[text_lower])
        for mat_key, code in mat_specifics.items():
            if mat_key.replace("_", " ") in text_lower:
                return str(code)
        return None

    def get_action_code(self, action_text: str) -> str | None:
        """Get OmniClass code for a specific action."""
        action_specifics = self._data.get("action_specifics", {})
        text_lower = action_text.lower()
        if text_lower in action_specifics:
            return str(action_specifics[text_lower])
        for act_key, code in action_specifics.items():
            if act_key in text_lower:
                return str(code)
        return None


def create_mapper() -> OmniClassMapper:
    """Factory function to create OmniClassMapper."""
    return OmniClassMapper()


if __name__ == "__main__":
    mapper = OmniClassMapper()
    for entity_type in ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]:
        result = mapper.map_entity(entity_type)
        print(f"{entity_type}: table={result.get('table')}, code={result.get('default_code') or result.get('code')}")
