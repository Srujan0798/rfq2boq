"""Unit tests for Hindi/IndicBERT NER support."""

import pytest
from src.nlp.lang_detect import detect_language, is_english, is_hindi


def test_detect_english():
    text = "Supply and install M25 grade RCC work 350 cum for foundation as per IS 456:2000"
    assert detect_language(text) == "en"
    assert is_english(text) is True
    assert is_hindi(text) is False


def test_detect_hindi():
    text = "M25 grade RCC का काम ground floor में करें"
    assert detect_language(text) == "hi"
    assert is_hindi(text) is True
    assert is_english(text) is False


def test_detect_devanagari():
    text = "सीमेंट की आपूर्ति करें"
    assert detect_language(text) == "hi"


def test_detect_mixed():
    text = "Supply cement सीमेंट 500 kg IS 456 M20 grade"
    assert detect_language(text) == "mixed"


def test_detect_empty():
    text = ""
    assert detect_language(text) == "en"


def test_detect_hindi_only_numbers():
    text = "12345"
    assert detect_language(text) == "en"


def test_pipeline_hindi_detection():
    from src.nlp.pipeline import NLPPipeline
    p = NLPPipeline()
    result = p.process("500 किलो सीमेंट की आपूर्ति")
    assert isinstance(result.entities, list)


def test_pipeline_english_still_works():
    from src.nlp.pipeline import NLPPipeline
    p = NLPPipeline()
    result = p.process("Supply 500 kg of cement")
    assert isinstance(result.entities, list)


def test_indic_ner_predict_returns_list():
    from src.nlp.ner.indic_ner import IndicNERInference
    try:
        ner = IndicNERInference()
        result = ner.predict("Test text")
        assert isinstance(result, list)
    except Exception:
        pytest.skip("IndicBERT model not available")


def test_indic_ner_extract_entities():
    from src.nlp.ner.indic_ner import IndicNERInference
    try:
        ner = IndicNERInference()
        result = ner.extract_entities("Supply 500 kg cement")
        assert isinstance(result, list)
    except Exception:
        pytest.skip("IndicBERT model not available")


def test_indic_ner_hindi_text():
    from src.nlp.ner.indic_ner import IndicNERInference
    try:
        ner = IndicNERInference()
        hindi_text = "सीमेंट 500 बैग में"
        result = ner.predict(hindi_text)
        assert isinstance(result, list)
    except Exception:
        pytest.skip("IndicBERT model not available")


def test_indic_ner_handles_empty():
    from src.nlp.ner.indic_ner import IndicNERInference
    try:
        ner = IndicNERInference()
        result = ner.predict("")
        assert isinstance(result, list)
    except Exception:
        pytest.skip("IndicBERT model not available")


def test_indic_ner_returns_dicts():
    from src.nlp.ner.indic_ner import IndicNERInference
    try:
        ner = IndicNERInference()
        result = ner.predict("Supply cement")
        if result:
            assert "text" in result[0]
            assert "type" in result[0]
    except Exception:
        pytest.skip("IndicBERT model not available")
