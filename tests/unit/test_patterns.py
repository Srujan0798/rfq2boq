"""Tests for entity patterns."""

from src.nlp.patterns.dictionary import DictionaryLookup
from src.nlp.patterns.entity_ruler import ConstructionEntityRuler
from src.nlp.patterns.regex_patterns import extract_regex_entities
from src.nlp.pipeline import NLPPipeline


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


class TestInsulationNER:
    def test_nitrile_rubber_tagged(self):
        pipeline = NLPPipeline()
        text = "Nitrile rubber insulation 50mm thick as per IS 15577"
        result = pipeline.process(text)
        materials = [e for e in result.entities if e["type"] == "MATERIAL" and "nitrile" in e["text"].lower()]
        assert len(materials) > 0, "nitrile rubber should be tagged as MATERIAL"

    def test_rock_wool_tagged(self):
        pipeline = NLPPipeline()
        text = "Rock wool insulation for thermal protection"
        result = pipeline.process(text)
        materials = [e for e in result.entities if e["type"] == "MATERIAL" and "rock wool" in e["text"].lower()]
        assert len(materials) > 0, "rock wool should be tagged as MATERIAL"

    def test_mineral_wool_tagged(self):
        pipeline = NLPPipeline()
        text = "Mineral wool bats for acoustic insulation"
        result = pipeline.process(text)
        materials = [e for e in result.entities if e["type"] == "MATERIAL" and "mineral wool" in e["text"].lower()]
        assert len(materials) > 0, "mineral wool should be tagged as MATERIAL"

    def test_insulation_is_codes_tagged(self):
        pipeline = NLPPipeline()
        text = "IS 8183, IS 9842, IS 11433 insulation materials"
        result = pipeline.process(text)
        standards = [e for e in result.entities if e["type"] == "STANDARD"]
        assert len(standards) >= 3, "IS 8183, IS 9842, IS 11433 should be tagged as STANDARD"
        codes = [e["text"] for e in standards]
        assert "IS 8183" in codes, "IS 8183 should be tagged"
        assert "IS 9842" in codes, "IS 9842 should be tagged"
        assert "IS 11433" in codes, "IS 11433 should be tagged"

    def test_rmt_unit_tagged(self):
        pipeline = NLPPipeline()
        text = "Provide 500 Rmt of duct insulation"
        result = pipeline.process(text)
        units = [e for e in result.entities if e["type"] == "UNIT"]
        unit_texts = [e["text"].lower() for e in units]
        assert "rmt" in unit_texts, "Rmt should be tagged as UNIT"

    def test_sqm_unit_tagged(self):
        pipeline = NLPPipeline()
        text = "Supply at 100 sqm per day"
        result = pipeline.process(text)
        units = [e for e in result.entities if e["type"] == "UNIT"]
        unit_texts = [e["text"].lower() for e in units]
        assert "sqm" in unit_texts or "m²" in [e["text"] for e in units], "sqm should be tagged as UNIT"

    def test_full_insulation_line_extraction(self):
        pipeline = NLPPipeline()
        text = "Supply 100 Rmt rock wool insulation conforming to IS 8183 for pipe work"
        result = pipeline.process(text)
        entities_by_type = {}
        for e in result.entities:
            entities_by_type.setdefault(e["type"], []).append(e)

        assert "MATERIAL" in entities_by_type, "MATERIAL entity should be present"
        assert "STANDARD" in entities_by_type, "STANDARD entity should be present"
        assert "UNIT" in entities_by_type, "UNIT entity should be present"
        assert "QUANTITY" in entities_by_type, "QUANTITY entity should be present"
        assert "ACTION" in entities_by_type, "ACTION entity should be present"

        materials = [e["text"].lower() for e in entities_by_type.get("MATERIAL", [])]
        assert any("rock wool" in m for m in materials), "rock wool should be tagged as MATERIAL"

        standards = [e["text"] for e in entities_by_type.get("STANDARD", [])]
        assert "IS 8183" in standards, "IS 8183 should be tagged as STANDARD"

        units = [e["text"].lower() for e in entities_by_type.get("UNIT", [])]
        assert "rmt" in units, "Rmt should be tagged as UNIT"


class TestInsulationDictionaryLookup:
    def test_insulation_materials_loaded(self):
        lookup = DictionaryLookup(load_defaults=True)
        materials_lower = {k: v for k, v in lookup.materials.items()}

        assert "nitrile rubber" in materials_lower or "elastomeric foam" in materials_lower, \
            "nitrile rubber should be in materials"
        assert "rock wool" in materials_lower or "mineral wool" in materials_lower, \
            "rock wool should be in materials"
        assert "mineral wool" in materials_lower, "mineral wool should be in materials"

    def test_insulation_standards_loaded(self):
        lookup = DictionaryLookup(load_defaults=True)
        standards_lower = {k: v for k, v in lookup.standards.items()}

        assert "is 8183" in standards_lower, "IS 8183 should be in standards"
        assert "is 9842" in standards_lower, "IS 9842 should be in standards"
        assert "is 11433" in standards_lower, "IS 11433 should be in standards"
        assert "is 15577" in standards_lower, "IS 15577 should be in standards"

    def test_insulation_units_loaded(self):
        lookup = DictionaryLookup(load_defaults=True)

        assert "rmt" in lookup.units, "rmt should be in units"
        assert "sqm" in lookup.units or "m²" in lookup.units, "sqm should be in units"
