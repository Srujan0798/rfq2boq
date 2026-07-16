"""Tests for text preprocessing and cleaning."""

from src.ingest.preprocessor import (
    PreprocessedText,
    TextPreprocessor,
)


class TestTextPreprocessor:
    def test_initialization(self):
        preprocessor = TextPreprocessor()
        assert preprocessor.smart_quotes is not None
        assert preprocessor.unit_replacements is not None

    def test_clean_removes_control_characters(self):
        preprocessor = TextPreprocessor()
        text = "Hello\x07World\x0bTest"
        result = preprocessor.clean(text)
        assert "\x07" not in result
        assert "\x0b" not in result

    def test_clean_normalizes_smart_quotes(self):
        preprocessor = TextPreprocessor()
        text = '"Hello" and \u2018single\u2019 quotes'
        result = preprocessor.clean(text)
        assert '"' in result
        assert "'" in result
        assert "\u201c" not in result
        assert "\u2019" not in result

    def test_clean_normalizes_unicode(self):
        preprocessor = TextPreprocessor()
        text = "caf\u00e9"  # café with é
        result = preprocessor.clean(text)
        assert "caf" in result

    def test_clean_removes_header_footer_patterns(self):
        preprocessor = TextPreprocessor()
        text = "Page 5\nSome content\n\n\n- 10 -\nMore content"
        result = preprocessor.clean(text)
        assert "Page 5" not in result
        assert "- 10 -" not in result

    def test_clean_normalizes_dashes(self):
        preprocessor = TextPreprocessor()
        text = "word\u2013dash\u2014long"
        result = preprocessor.clean(text)
        assert "\u2013" not in result
        assert "\u2014" not in result

    def test_clean_collapses_whitespace(self):
        preprocessor = TextPreprocessor()
        text = "Multiple   spaces\n\n\n\nNewlines"
        result = preprocessor.clean(text)
        assert "  " not in result

    def test_clean_replaces_unit_abbreviations(self):
        preprocessor = TextPreprocessor()
        text = "500 sq.m of concrete"
        result = preprocessor.clean(text)
        assert "sq.m" not in result
        assert "sqm" in result

    def test_normalize_whitespace(self):
        preprocessor = TextPreprocessor()
        text = "Multiple   spaces\n\n\nNewlines"
        result = preprocessor.normalize_whitespace(text)
        assert "  " not in result

    def test_remove_page_numbers(self):
        preprocessor = TextPreprocessor()
        text = "Page 10\nSome content\n100\n- 5 -"
        result = preprocessor.remove_page_numbers(text)
        assert "Page 10" not in result
        assert "100" not in result
        assert "- 5 -" not in result

    def test_expand_abbreviations_tmt(self):
        preprocessor = TextPreprocessor()
        text = "TMT bars for reinforcement"
        result = preprocessor.expand_abbreviations(text)
        assert "thermo mechanically treated" in result

    def test_expand_abbreviations_rcc(self):
        preprocessor = TextPreprocessor()
        text = "RCC slab"
        result = preprocessor.expand_abbreviations(text)
        assert "reinforced cement concrete" in result

    def test_expand_abbreviations_multiple(self):
        preprocessor = TextPreprocessor()
        text = "GI MS SS RCC"
        result = preprocessor.expand_abbreviations(text)
        assert "galvanized iron" in result
        assert "mild steel" in result
        assert "stainless steel" in result
        assert "reinforced cement concrete" in result


class TestSegmentSentences:
    def test_segment_sentences_basic(self):
        preprocessor = TextPreprocessor()
        text = "First sentence. Second sentence!"
        result = preprocessor.segment_sentences(text)
        assert len(result) == 2
        assert result[0].text == "First sentence."
        assert result[1].text == "Second sentence!"

    def test_segment_sentences_with_offsets(self):
        preprocessor = TextPreprocessor()
        text = "Hello world."
        result = preprocessor.segment_sentences(text)
        assert len(result) == 1
        assert result[0].start == 0
        assert result[0].end == len("Hello world.")

    def test_segment_sentences_empty_text(self):
        preprocessor = TextPreprocessor()
        result = preprocessor.segment_sentences("")
        assert result == []

    def test_segment_sentences_preserves_page(self):
        preprocessor = TextPreprocessor()
        text = "Sentence one. Sentence two."
        result = preprocessor.segment_sentences(text, page=5)
        assert all(s.page == 5 for s in result)

    def test_segment_sentences_single_line(self):
        preprocessor = TextPreprocessor()
        text = "Single line without punctuation"
        result = preprocessor.segment_sentences(text)
        assert len(result) == 1


class TestPreprocessedText:
    def test_preprocessed_text_default_warnings(self):
        result = PreprocessedText(cleaned_text="test", sentences=[])
        assert result.warnings == []

    def test_preprocessed_text_with_warnings(self):
        result = PreprocessedText(cleaned_text="test", sentences=[], warnings=["warning1"])
        assert result.warnings == ["warning1"]

    def test_preprocess_returns_preprocessed_text(self):
        preprocessor = TextPreprocessor()
        text = "Test input."
        result = preprocessor.preprocess(text)
        assert isinstance(result, PreprocessedText)
        assert result.cleaned_text == "Test input."
        assert len(result.sentences) > 0
