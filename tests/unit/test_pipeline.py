"""Tests for unified NLP pipeline."""

from src.nlp.pipeline import ExtractionResult, NLPPipeline


class TestNLPPipeline:
    def test_initialization(self):
        pipeline = NLPPipeline(
            model_dir=None,
            ontology_dir=None,
            id2label={0: "O"},
            label2id={"O": 0},
        )
        assert pipeline.id2label is not None
        assert pipeline.label2id is not None

    def test_process_empty_text(self):
        pipeline = NLPPipeline(
            model_dir=None,
            ontology_dir=None,
        )
        result = pipeline.process("")

        assert isinstance(result, ExtractionResult)
        assert len(result.entities) == 0

    def test_process_no_model(self):
        pipeline = NLPPipeline(
            model_dir=None,
            ontology_dir=None,
        )
        result = pipeline.process("Supply 50 kg cement")

        assert isinstance(result, ExtractionResult)

    def test_merge_entities_same_span(self):
        pipeline = NLPPipeline()

        entities = [
            {"text": "cement", "type": "MATERIAL", "start": 0, "end": 6, "confidence": 0.9, "source": "bert"},
            {"text": "cement", "type": "MATERIAL", "start": 0, "end": 6, "confidence": 0.8, "source": "regex"},
        ]
        merged = pipeline._merge_entities(entities)

        assert len(merged) == 1
        assert merged[0]["confidence"] == 0.9

    def test_merge_entities_different_span(self):
        pipeline = NLPPipeline()

        entities = [
            {"text": "cement mortar", "type": "MATERIAL", "start": 0, "end": 12, "confidence": 0.9},
            {"text": "cement", "type": "MATERIAL", "start": 0, "end": 6, "confidence": 0.95},
        ]
        merged = pipeline._merge_entities(entities)

        assert len(merged) >= 1

    def test_entity_to_dict(self):
        from src.nlp.ner.inference import Entity

        entity = Entity(
            text="cement",
            type="MATERIAL",
            start=0,
            end=6,
            confidence=0.9,
        )
        result = NLPPipeline._entity_to_dict(entity)

        assert result["text"] == "cement"
        assert result["type"] == "MATERIAL"
        assert result["start"] == 0
        assert result["end"] == 6
        assert result["confidence"] == 0.9

    def test_relation_to_dict(self):
        from src.nlp.re.extractor import Relation

        relation = Relation(
            type="HAS_QUANTITY",
            head_entity={"text": "cement", "type": "MATERIAL"},
            tail_entity={"text": "50", "type": "QUANTITY"},
            confidence=0.85,
        )
        result = NLPPipeline._relation_to_dict(relation)

        assert result["type"] == "HAS_QUANTITY"
        assert result["confidence"] == 0.85


class TestExtractionResult:
    def test_default_values(self):
        result = ExtractionResult()

        assert result.entities == []
        assert result.relations == []
        assert result.warnings == []
        assert result.confidence == 0.0

    def test_with_data(self):
        result = ExtractionResult(
            entities=[{"text": "cement", "type": "MATERIAL"}],
            relations=[{"type": "HAS_QUANTITY"}],
            warnings=["Test warning"],
            confidence=0.9,
        )

        assert len(result.entities) == 1
        assert len(result.relations) == 1
        assert len(result.warnings) == 1
        assert result.confidence == 0.9
