"""Tests for relation extraction."""


from src.nlp.re.extractor import RelationExtractor
from src.nlp.re.rules import RELATION_RULES


class TestRelationRules:
    def test_has_quantity_rule(self):
        rule = next(r for r in RELATION_RULES if r["type"] == "HAS_QUANTITY")
        assert rule["head"] == "MATERIAL"
        assert rule["tail"] == "QUANTITY"
        assert rule["max_distance"] > 0

    def test_at_location_rule(self):
        rule = next(r for r in RELATION_RULES if r["type"] == "AT_LOCATION")
        assert rule["head"] == "MATERIAL"
        assert rule["tail"] == "LOCATION"

    def test_complies_with_rule(self):
        rule = next(r for r in RELATION_RULES if r["type"] == "COMPLIES_WITH")
        assert "keywords" in rule
        assert len(rule["keywords"]) > 0

    def test_all_rules_have_max_distance(self):
        for rule in RELATION_RULES:
            assert "max_distance" in rule
            assert rule["max_distance"] > 0


class TestRelationExtractor:
    def test_initialization(self):
        extractor = RelationExtractor()
        assert len(extractor.rules) == len(RELATION_RULES)

    def test_extract_no_entities(self):
        extractor = RelationExtractor()
        relations = extractor.extract([], "some text")
        assert relations == []

    def test_extract_material_quantity(self):
        extractor = RelationExtractor()
        entities = [
            {"text": "cement", "type": "MATERIAL", "start": 0, "end": 6, "confidence": 0.9},
            {"text": "50", "type": "QUANTITY", "start": 7, "end": 9, "confidence": 0.95},
        ]
        text = "cement 50 kg"
        relations = extractor.extract(entities, text)

        has_quantity_rels = [r for r in relations if r.type == "HAS_QUANTITY"]
        assert len(has_quantity_rels) > 0

    def test_extract_distance_filter(self):
        extractor = RelationExtractor()
        entities = [
            {"text": "cement", "type": "MATERIAL", "start": 0, "end": 6, "confidence": 0.9},
            {"text": "100", "type": "QUANTITY", "start": 1000, "end": 1003, "confidence": 0.95},
        ]
        text = "cement " + " " * 990 + "100"
        relations = extractor.extract(entities, text)

        has_quantity_rels = [r for r in relations if r.type == "HAS_QUANTITY"]
        assert len(has_quantity_rels) == 0

    def test_deduplication(self):
        extractor = RelationExtractor()
        entities = [
            {"text": "cement", "type": "MATERIAL", "start": 0, "end": 6, "confidence": 0.9},
            {"text": "50", "type": "QUANTITY", "start": 7, "end": 9, "confidence": 0.95},
        ]
        text = "cement 50"
        relations = extractor.extract(entities, text)
        relations = extractor._deduplicate_relations(relations)

        types = [r.type for r in relations]
        assert len(types) == len(set(types))
