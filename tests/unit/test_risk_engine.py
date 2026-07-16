"""Tests for RiskEngine."""

from src.domain.risk_engine import RiskEngine, RiskScore


class TestRiskEngine:
    def test_init(self):
        engine = RiskEngine()
        assert engine is not None

    def test_score_item_zero_for_normal_item(self):
        engine = RiskEngine()
        item = {
            "item_no": 1,
            "material": "cement",
            "grade": "M25",
            "quantity": 100,
            "unit": "cum",
            "standard": ["IS 456"],
        }
        risk = engine.score_item(item)
        assert risk.score >= 0
        assert risk.score <= 100

    def test_score_item_unknown_material(self):
        engine = RiskEngine()
        item = {"item_no": 1, "material": "unknown", "quantity": 100, "unit": "cum"}
        risk = engine.score_item(item)
        assert "unknown_material" in risk.factors

    def test_score_item_missing_standard(self):
        engine = RiskEngine()
        item = {
            "item_no": 1,
            "material": "steel",
            "grade": "Fe500",
            "quantity": 500,
            "unit": "kg",
            "standard": [],
        }
        risk = engine.score_item(item)
        assert "missing_standard" in risk.factors

    def test_score_item_no_grade(self):
        engine = RiskEngine()
        item = {
            "item_no": 1,
            "material": "steel",
            "quantity": 500,
            "unit": "kg",
            "standard": ["IS 432"],
        }
        risk = engine.score_item(item)
        assert "no_grade" in risk.factors

    def test_score_item_quantity_outlier(self):
        engine = RiskEngine()
        item = {
            "item_no": 1,
            "material": "cement",
            "quantity": 50000,
            "unit": "cum",
        }
        risk = engine.score_item(item)
        assert "quantity_outlier" in risk.factors

    def test_score_item_long_description(self):
        engine = RiskEngine()
        item = {
            "item_no": 1,
            "material": "cement",
            "quantity": 100,
            "unit": "cum",
            "description": "A" * 600,
        }
        risk = engine.score_item(item)
        assert "suspiciously_long_description" in risk.factors

    def test_score_project_empty(self):
        engine = RiskEngine()
        result = engine.score_project([])
        assert result["overall_risk"] == 0
        assert "high_risk_items" in result

    def test_score_project_normal(self):
        engine = RiskEngine()
        boq = [
            {
                "item_no": 1,
                "material": "cement",
                "grade": "M25",
                "quantity": 100,
                "unit": "cum",
                "standard": ["IS 456"],
            },
            {
                "item_no": 2,
                "material": "steel",
                "grade": "Fe500",
                "quantity": 500,
                "unit": "kg",
                "standard": ["IS 432"],
            },
        ]
        result = engine.score_project(boq)
        assert result["total_items"] == 2
        assert "overall_risk" in result
        assert "risk_distribution" in result

    def test_score_project_high_risk(self):
        engine = RiskEngine()
        boq = [
            {"item_no": 1, "material": "unknown", "quantity": 0, "unit": ""},
        ]
        result = engine.score_project(boq)
        assert result["high_risk_count"] >= 1

    def test_coverage_analysis(self):
        engine = RiskEngine()
        boq = [
            {"item_no": 1, "material": "concrete", "quantity": 100, "unit": "cum"},
            {"item_no": 2, "material": "steel", "quantity": 500, "unit": "kg"},
        ]
        result = engine.coverage_analysis(boq)
        assert "coverage_pct" in result
        assert "missing_categories" in result
        assert result["categories_found"] >= 2

    def test_coverage_analysis_empty(self):
        engine = RiskEngine()
        result = engine.coverage_analysis([])
        assert result["coverage_pct"] == 0.0
        assert len(result["missing_categories"]) == result["total_categories"]

    def test_generate_recommendations_high_risk(self):
        engine = RiskEngine()
        boq = [
            {"item_no": 1, "material": "unknown", "quantity": 0, "unit": ""},
            {"item_no": 2, "material": "unknown", "quantity": 0, "unit": ""},
            {"item_no": 3, "material": "unknown", "quantity": 0, "unit": ""},
            {"item_no": 4, "material": "unknown", "quantity": 0, "unit": ""},
            {"item_no": 5, "material": "unknown", "quantity": 0, "unit": ""},
            {"item_no": 6, "material": "unknown", "quantity": 0, "unit": ""},
        ]
        recs = engine.generate_recommendations(boq)
        assert len(recs) > 0
        assert any("risky items" in r for r in recs)

    def test_generate_recommendations_low_coverage(self):
        engine = RiskEngine()
        boq = [
            {"item_no": 1, "material": "unknown", "quantity": 100, "unit": "nos"},
        ]
        recs = engine.generate_recommendations(boq)
        assert isinstance(recs, list)

    def test_generate_recommendations_unknown_material(self):
        engine = RiskEngine()
        boq = [{"item_no": 1, "material": "unknown", "quantity": 0, "unit": ""}]
        recs = engine.generate_recommendations(boq)
        assert any("unknown material" in r for r in recs)

    def test_generate_recommendations_missing_grade(self):
        engine = RiskEngine()
        boq = [{"item_no": i, "material": "cement", "quantity": 100, "unit": "cum"} for i in range(1, 11)]
        recs = engine.generate_recommendations(boq)
        assert any("grade" in r.lower() for r in recs)

    def test_risk_score_dataclass(self):
        risk = RiskScore(score=50.0, factors=["test_factor"], item={"item_no": 1})
        assert risk.score == 50.0
        assert risk.factors == ["test_factor"]
        assert risk.item == {"item_no": 1}

    def test_risk_score_max_100(self):
        engine = RiskEngine()
        item = {
            "item_no": 1,
            "material": "",
            "quantity": 0,
            "unit": "",
            "standard": [],
            "description": "X" * 600,
        }
        risk = engine.score_item(item)
        assert risk.score <= 100
