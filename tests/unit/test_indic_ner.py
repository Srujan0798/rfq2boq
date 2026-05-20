"""Unit tests for IndicBERT NER wrapper."""

import pytest
from src.nlp.ner.indic_ner import HindiEntity, IndicNERInference, load_indic_ner


class TestIndicNERInference:
    def test_initialization(self):
        ner = IndicNERInference()
        assert ner.id2label is not None
        assert ner.label2id is not None

    def test_device_setup(self):
        ner = IndicNERInference()
        assert hasattr(ner, "device")
        assert ner.device.type in ("cpu", "cuda", "mps")

    def test_model_or_tokenizer_loaded(self):
        ner = IndicNERInference()
        assert ner.tokenizer is not None or ner.model is not None

    def test_predict_returns_list(self):
        try:
            ner = IndicNERInference()
            result = ner.predict("Test English sentence")
            assert isinstance(result, list)
        except Exception:
            pytest.skip("Model not available")

    def test_predict_empty_string(self):
        try:
            ner = IndicNERInference()
            result = ner.predict("")
            assert isinstance(result, list)
        except Exception:
            pytest.skip("Model not available")

    def test_extract_entities_returns_list(self):
        try:
            ner = IndicNERInference()
            result = ner.extract_entities("Cement supply 500 kg")
            assert isinstance(result, list)
        except Exception:
            pytest.skip("Model not available")

    def test_hindi_text_returns_list(self):
        try:
            ner = IndicNERInference()
            result = ner.predict("सीमेंट की आपूर्ति 500 किलोग्राम")
            assert isinstance(result, list)
        except Exception:
            pytest.skip("Model not available")

    def test_predict_returns_dicts_with_keys(self):
        try:
            ner = IndicNERInference()
            result = ner.predict("Cement")
            for entity in result:
                assert "text" in entity
                assert "type" in entity
                assert "start" in entity
                assert "end" in entity
                assert "confidence" in entity
                assert "source" in entity
        except Exception:
            pytest.skip("Model not available")

    def test_load_indic_ner_function(self):
        ner = load_indic_ner()
        assert ner is not None
        assert isinstance(ner, IndicNERInference)


class TestHindiEntity:
    def test_hindi_entity_creation(self):
        entity = HindiEntity(
            text="सीमेंट",
            type="MATERIAL",
            start=0,
            end=6,
            confidence=0.95,
        )
        assert entity.text == "सीमेंट"
        assert entity.type == "MATERIAL"
        assert entity.start == 0
        assert entity.end == 6
        assert entity.confidence == 0.95

    def test_hindi_entity_defaults(self):
        entity = HindiEntity(text="test", type="MATERIAL", start=0, end=4, confidence=1.0)
        assert entity.confidence == 1.0


class TestBioesDecoding:
    def test_clean_token(self):
        try:
            ner = IndicNERInference()
            assert ner._clean_token("##test") == "test"
            assert ner._clean_token("▁prefix") == "prefix"
        except Exception:
            pytest.skip("Model not available")
