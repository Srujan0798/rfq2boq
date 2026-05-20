"""Tests for entity patterns."""


from src.nlp.patterns.dictionary import DictionaryLookup
from src.nlp.patterns.entity_ruler import ConstructionEntityRuler
from src.nlp.patterns.regex_patterns import extract_regex_entities


class TestRegexPatterns:
    def test_standard_patterns(self):
        text = "Supply M20 concrete conforming to IS 456:2000"
        entities = extract_regex_entities(text)

        standard_entities = [e for e in entities if e["type"] == "STANDARD"]
        assert len(standard_entities) > 0

    def test_quantity_patterns(self):
        text = "150.5 cubic meters of concrete"
        entities = extract_regex_entities(text)

        quantity_entities = [e for e in entities if e["type"] == "QUANTITY"]
        assert len(quantity_entities) > 0

    def test_dimension_patterns(self):
        text = "230 mm thick wall"
        entities = extract_regex_entities(text)

        dimension_entities = [e for e in entities if e["type"] == "DIMENSION"]
        assert len(dimension_entities) > 0

    def test_empty_text(self):
        entities = extract_regex_entities("")
        assert entities == []


class TestConstructionEntityRuler:
    def test_initialization(self):
        ruler = ConstructionEntityRuler()
        assert ruler.nlp is not None
        assert ruler.ruler is None

    def test_build_patterns(self):
        ruler = ConstructionEntityRuler()
        patterns = ruler.build_patterns()
        assert len(patterns) > 0

    def test_create_ruler(self):
        ruler = ConstructionEntityRuler()
        ruler_result = ruler.create_ruler()
        assert ruler_result is not None


class TestDictionaryLookup:
    def test_initialization(self):
        lookup = DictionaryLookup()
        assert lookup.materials == {}
        assert lookup.standards == {}

    def test_add_material(self):
        lookup = DictionaryLookup()
        lookup.add_material("cement", alias="OPC")
        assert "cement" in lookup.materials

    def test_lookup_found(self):
        lookup = DictionaryLookup()
        lookup.add_material("cement")

        results = lookup.lookup("cement")
        assert len(results) > 0
        assert results[0]["type"] == "MATERIAL"

    def test_lookup_not_found(self):
        lookup = DictionaryLookup()
        results = lookup.lookup("xyz123")
        assert results == []
