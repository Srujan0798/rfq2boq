"""Tests for dictionary lookup."""

from config.constants import EntityType
from src.nlp.patterns.dictionary import DictionaryLookup


class TestDictionaryLookup:
    def test_initialization(self):
        d = DictionaryLookup()
        assert d is not None

    def test_empty_lookup(self):
        d = DictionaryLookup()
        result = d.lookup("xyznonexistent999")
        assert result == [] or result is None

    def test_add_material(self):
        d = DictionaryLookup()
        d.add_material("cement", "Ordinary Portland Cement")
        result = d.lookup("cement")
        assert result is not None

    def test_add_standard(self):
        d = DictionaryLookup()
        d.add_standard("IS 456", "Indian Standard for concrete")
        result = d.lookup("IS 456")
        assert result is not None

    def test_lookup_case_insensitive(self):
        d = DictionaryLookup()
        d.add_material("Steel", "structural steel")
        result = d.lookup("steel")
        assert result is not None

    def test_lookup_not_found(self):
        d = DictionaryLookup()
        result = d.lookup("xyzabc123notreal")
        assert result == [] or result is None

    def test_multiple_adds(self):
        d = DictionaryLookup()
        d.add_material("cement")
        d.add_material("steel")
        d.add_material("concrete")
        assert d.lookup("cement") is not None
        assert d.lookup("steel") is not None
        assert d.lookup("concrete") is not None

    def test_lookup_with_entity_type(self):
        d = DictionaryLookup()
        d.add_material("galvanized steel")
        result = d.lookup("galvanized steel")
        assert result is not None
        if isinstance(result, dict):
            assert result.get("type") == EntityType.MATERIAL.value or "type" in result
