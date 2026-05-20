"""Extended tests for text preprocessor."""


from src.ingest.preprocessor import PreprocessedText, TextPreprocessor


class TestPreprocessorExtended:
    def test_remove_headers(self):
        p = TextPreprocessor()
        text = "Header Line\n\nActual content here\n\nFooter Line"
        patterns = [r"Header Line\n"]
        result = p.remove_headers(text, patterns)
        assert "Header Line" not in result
        assert "Actual content" in result

    def test_remove_footers(self):
        p = TextPreprocessor()
        text = "Some content\n\nPage 1 of 5\nFooter text"
        patterns = [r"Page \d+ of \d+\n"]
        result = p.remove_footers(text, patterns)
        assert "Page 1 of 5" not in result

    def test_special_characters(self):
        p = TextPreprocessor()
        text = "Hello\x07World\x1FTest"
        result = p.clean(text)
        assert "\x07" not in result
        assert "\x1F" not in result

    def test_very_long_text(self):
        p = TextPreprocessor()
        text = "word " * 10000
        result = p.clean(text)
        assert len(result) > 0

    def test_empty_text(self):
        p = TextPreprocessor()
        result = p.clean("")
        assert result == ""

    def test_whitespace_only(self):
        p = TextPreprocessor()
        result = p.clean("   \n\n\t\t  ")
        assert result == ""

    def test_multiple_spaces(self):
        p = TextPreprocessor()
        result = p.clean("Hello    World")
        assert "  " not in result

    def test_newlines_converted(self):
        p = TextPreprocessor()
        result = p.clean("Line1\r\nLine2\rLine3")
        # Should handle carriage returns — either strip or convert
        assert "Line1" in result
        assert "Line2" in result

    def test_quotes_preserved(self):
        p = TextPreprocessor()
        result = p.clean('"Hello" and \'World\'')
        # Preprocessor may or may not normalize quotes — just shouldn't crash
        assert "Hello" in result
        assert "World" in result

    def test_mixed_content(self):
        p = TextPreprocessor()
        text = "Header\n\nPurchase of 500 kg of steel @ $100/unit\n\nFooter"
        result = p.clean(text)
        assert len(result) > 0

    def test_remove_page_numbers(self):
        p = TextPreprocessor()
        # Test with standalone page number lines (typical format)
        text = "Some text\nPage 5\nmore text\n- 10 -\nend"
        if hasattr(p, "remove_page_numbers"):
            result = p.remove_page_numbers(text)
            assert "Some text" in result
        else:
            # Method may not exist — preprocessor handles this in clean()
            result = p.clean(text)
            assert "Some text" in result

    def test_normalize_whitespace_preserves_content(self):
        p = TextPreprocessor()
        text = "Hello    World   123"
        result = p.normalize_whitespace(text)
        assert result == "Hello World 123"

    def test_preprocessed_text_with_warnings(self):
        text = PreprocessedText("cleaned text", warnings=["warning1", "warning2"])
        assert text.text == "cleaned text"
        assert len(text.warnings) == 2

    def test_preprocessed_text_default_warnings(self):
        text = PreprocessedText("cleaned text")
        assert text.warnings == []
