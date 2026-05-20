"""Tests for coverage analyzer."""

from src.risk.coverage import CategoryCoverage, CoverageAnalyzer, CoverageReport


class TestCoverageAnalyzer:
    def test_init(self):
        analyzer = CoverageAnalyzer()
        assert analyzer is not None
        assert analyzer.categories is not None

    def test_analyze_empty_items(self):
        analyzer = CoverageAnalyzer()
        report = analyzer.analyze([])
        assert isinstance(report, CoverageReport)
        assert report.overall_coverage == 0.0
        assert len(report.missing_categories) > 0

    def test_analyze_structure_items(self):
        from decimal import Decimal

        from src.domain.models import BoqRow

        analyzer = CoverageAnalyzer()
        items = [
            BoqRow(item_no=1, material="M20 concrete", quantity=Decimal("100"), unit="m3"),
            BoqRow(item_no=2, material="steel reinforcement", quantity=Decimal("50"), unit="kg"),
        ]
        report = analyzer.analyze(items)
        assert isinstance(report, CoverageReport)
        assert "structure" in [c.category for c in report.categories]
        assert report.overall_coverage >= 0.0

    def test_analyze_electrical_items(self):
        from decimal import Decimal

        from src.domain.models import BoqRow

        analyzer = CoverageAnalyzer()
        items = [
            BoqRow(item_no=1, material="electrical cable", quantity=Decimal("500"), unit="m"),
            BoqRow(item_no=2, material="switch socket", quantity=Decimal("20"), unit="nos"),
        ]
        report = analyzer.analyze(items)
        assert isinstance(report, CoverageReport)
        electrical_cat = next((c for c in report.categories if c.category == "electrical"), None)
        if electrical_cat:
            assert electrical_cat.present is True

    def test_analyze_mixed_items(self):
        from decimal import Decimal

        from src.domain.models import BoqRow

        analyzer = CoverageAnalyzer()
        items = [
            BoqRow(item_no=1, material="concrete", quantity=Decimal("100"), unit="m3"),
            BoqRow(item_no=2, material="paint", quantity=Decimal("50"), unit="ltr"),
            BoqRow(item_no=3, material="pipe pvc", quantity=Decimal("200"), unit="m"),
            BoqRow(item_no=4, material="cable", quantity=Decimal("1000"), unit="m"),
        ]
        report = analyzer.analyze(items)
        assert report.overall_coverage > 0.0
        assert len(report.missing_categories) < len(analyzer.categories)

    def test_recommendations_generated(self):
        from decimal import Decimal

        from src.domain.models import BoqRow

        analyzer = CoverageAnalyzer()
        items = [BoqRow(item_no=1, material="unknown material", quantity=Decimal("1"), unit="nos")]
        report = analyzer.analyze(items)
        assert isinstance(report.recommendations, list)


class TestCategoryCoverage:
    def test_category_coverage_dataclass(self):
        cat = CategoryCoverage(
            category="structure",
            present=True,
            items_found=["concrete", "cement"],
            coverage_fraction=0.7,
        )
        assert cat.category == "structure"
        assert cat.present is True
        assert len(cat.items_found) == 2
        assert cat.coverage_fraction == 0.7
