"""Tests for OmniClass mapping."""

from src.ontology.omniclass import OmniClassMapper


class TestOmniClassMapper:
    def setup_method(self):
        self.mapper = OmniClassMapper()

    def test_all_8_entity_types_mappable(self):
        entity_types = ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]
        for et in entity_types:
            result = self.mapper.map_entity(et)
            assert isinstance(result, dict)
            assert "table" in result

    def test_material_specific_mapping(self):
        result = self.mapper.map_entity("MATERIAL", "cement")
        assert result["specific"] is True
        assert result["code"].startswith("23-")

    def test_reverse_lookup_material(self):
        result = self.mapper.reverse_lookup("23-13-21-13")
        assert result == "MATERIAL"

    def test_reverse_lookup_action(self):
        result = self.mapper.reverse_lookup("22-03")
        assert result == "ACTION"

    def test_reverse_lookup_unknown_code(self):
        result = self.mapper.reverse_lookup("99-99-99-99")
        assert result is None

    def test_map_unknown_entity_type(self):
        result = self.mapper.map_entity("UNKNOWN_TYPE")
        assert result["table"] is None
        assert result["code"] is None
        assert "Unknown entity type" in result["note"]

    def test_minimum_material_specifics(self):
        data = self.mapper._data
        assert len(data.get("material_specifics", {})) >= 8

    def test_minimum_action_specifics(self):
        data = self.mapper._data
        assert len(data.get("action_specifics", {})) >= 5

    def test_map_entity_returns_required_keys(self):
        result = self.mapper.map_entity("GRADE", "M30")
        assert all(k in result for k in ["table", "default_code", "name"])

    def test_map_entity_no_text_fallback(self):
        result = self.mapper.map_entity("MATERIAL")
        assert "table" in result
        assert result["table"] == "23"
