"""Tests for document layout analysis and section detection."""

from config.constants import SectionType
from src.ingest.layout_analyzer import (
    LayoutAnalysis,
    LayoutAnalyzer,
    LayoutSection,
)


class TestLayoutAnalyzer:
    def test_initialization(self):
        analyzer = LayoutAnalyzer()
        assert analyzer.section_patterns is not None

    def test_detect_section_type_scope(self):
        analyzer = LayoutAnalyzer()
        result = analyzer._detect_section_type("SCOPE OF WORK")
        assert result == SectionType.SCOPE

    def test_detect_section_type_specifications(self):
        analyzer = LayoutAnalyzer()
        result = analyzer._detect_section_type("TECHNICAL SPECIFICATIONS")
        assert result == SectionType.SPECIFICATIONS

    def test_detect_section_type_schedule_of_items(self):
        analyzer = LayoutAnalyzer()
        result = analyzer._detect_section_type("BILL OF QUANTITIES")
        assert result == SectionType.SCHEDULE_OF_ITEMS

    def test_detect_section_type_general(self):
        analyzer = LayoutAnalyzer()
        result = analyzer._detect_section_type("GENERAL TERMS AND CONDITIONS")
        assert result == SectionType.GENERAL

    def test_detect_section_type_commercial(self):
        analyzer = LayoutAnalyzer()
        result = analyzer._detect_section_type("COMMERCIAL TERMS")
        assert result == SectionType.COMMERCIAL

    def test_detect_section_type_preamble(self):
        analyzer = LayoutAnalyzer()
        result = analyzer._detect_section_type("SCOPE OF WORK")
        assert result == SectionType.SCOPE

    def test_detect_section_type_drawings_list(self):
        analyzer = LayoutAnalyzer()
        result = analyzer._detect_section_type("LIST OF DRAWINGS")
        assert result == SectionType.DRAWINGS_LIST

    def test_detect_section_type_returns_none_for_unknown(self):
        analyzer = LayoutAnalyzer()
        result = analyzer._detect_section_type("Some random text")
        assert result is None

    def test_detect_section_type_case_insensitive(self):
        analyzer = LayoutAnalyzer()
        result = analyzer._detect_section_type("scope of work")
        assert result == SectionType.SCOPE

    def test_is_table_line_with_pipe(self):
        analyzer = LayoutAnalyzer()
        assert analyzer._is_table_line("| Item | Qty | Unit |") is True

    def test_is_table_line_with_item_no(self):
        analyzer = LayoutAnalyzer()
        assert analyzer._is_table_line("  item no  1  ") is True

    def test_is_table_line_with_qty_header(self):
        analyzer = LayoutAnalyzer()
        assert analyzer._is_table_line("  qty  unit  rate  ") is True

    def test_is_table_line_not_table(self):
        analyzer = LayoutAnalyzer()
        assert analyzer._is_table_line("Just a regular line") is False

    def test_detect_scanned_layout_true_for_empty(self):
        analyzer = LayoutAnalyzer()
        result = analyzer._detect_scanned_layout([])
        assert result is True

    def test_detect_scanned_layout_true_for_short_text(self):
        analyzer = LayoutAnalyzer()
        pages = [(1, "Short")]
        result = analyzer._detect_scanned_layout(pages)
        assert result is True

    def test_detect_scanned_layout_false_for_long_text(self):
        analyzer = LayoutAnalyzer()
        pages = [(1, "A" * 200)]
        result = analyzer._detect_scanned_layout(pages)
        assert result is False

    def test_analyze_returns_layout_analysis(self):
        analyzer = LayoutAnalyzer()
        pages_text = [
            (1, "SCOPE OF WORK\nSome content here"),
            (2, "More content"),
        ]
        result = analyzer.analyze(pages_text)

        assert isinstance(result, LayoutAnalysis)
        assert len(result.sections) > 0
        assert result.page_count == 2

    def test_analyze_detects_multiple_sections(self):
        analyzer = LayoutAnalyzer()
        pages_text = [
            (1, "SCOPE OF WORK\nWork description\n\nSPECIFICATIONS\nMaterial specs"),
        ]
        result = analyzer.analyze(pages_text)

        section_types = [s.section_type for s in result.sections]
        assert SectionType.SCOPE in section_types
        assert SectionType.SPECIFICATIONS in section_types

    def test_analyze_empty_pages(self):
        analyzer = LayoutAnalyzer()
        result = analyzer.analyze([])
        assert result.page_count == 0

    def test_get_section_type_label(self):
        analyzer = LayoutAnalyzer()
        section = LayoutSection(section_type=SectionType.SCOPE, title="Scope")
        result = analyzer.get_section_type_label(section)
        assert result == "scope"


class TestLayoutSection:
    def test_layout_section_creation(self):
        section = LayoutSection(
            section_type=SectionType.SCOPE,
            title="Scope of Work",
            content="Detailed content",
            page_start=1,
            page_end=2,
            start_offset=0,
            end_offset=100,
            is_table=False,
        )
        assert section.section_type == SectionType.SCOPE
        assert section.title == "Scope of Work"
        assert section.page_start == 1
        assert section.page_end == 2
        assert section.is_table is False


class TestLayoutAnalysis:
    def test_layout_analysis_creation(self):
        sections = [
            LayoutSection(section_type=SectionType.SCOPE, title="Scope"),
        ]
        analysis = LayoutAnalysis(
            sections=sections,
            is_likely_scanned=False,
            page_count=1,
        )
        assert len(analysis.sections) == 1
        assert analysis.is_likely_scanned is False
        assert analysis.page_count == 1

    def test_layout_analysis_default_values(self):
        analysis = LayoutAnalysis()
        assert analysis.sections == []
        assert analysis.is_likely_scanned is False
        assert analysis.page_count == 0
