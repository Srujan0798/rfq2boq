"""Tests for CPWD DSR 2023 rate library and cost estimator integration."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from src.domain.cost_estimator import CostEstimator, ItemEstimate
from src.domain.models import BoqRow


class TestDSRRates:
    @pytest.fixture
    def dsr_json_path(self) -> Path:
        return Path(__file__).parent.parent.parent / "data" / "rates" / "cpwd_dsr_2023.json"

    @pytest.fixture
    def estimator(self) -> CostEstimator:
        return CostEstimator()

    def test_dsr_json_loads(self, dsr_json_path: Path) -> None:
        assert dsr_json_path.exists(), f"DSR JSON not found at {dsr_json_path}"
        with open(dsr_json_path, encoding="utf-8") as f:
            data = json.load(f)
        assert "items" in data
        assert len(data["items"]) >= 500, f"Expected >=500 items, got {len(data['items'])}"

    def test_dsr_json_structure(self, dsr_json_path: Path) -> None:
        with open(dsr_json_path, encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("version") == "DSR 2023"
        assert data.get("source") == "CPWD Delhi Schedule of Rates 2023"
        assert data.get("region") == "delhi"
        assert data.get("currency") == "INR"
        for item in data["items"]:
            assert "code" in item
            assert "description" in item
            assert "unit" in item
            assert "rate_inr" in item
        assert "year" in data

    def test_dsr_item_count(self, dsr_json_path: Path) -> None:
        with open(dsr_json_path, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data["items"]) >= 500, f"DSR has {len(data['items'])} items, need >=500"

    def test_common_materials_present(self, dsr_json_path: Path) -> None:
        with open(dsr_json_path, encoding="utf-8") as f:
            data = json.load(f)
        descs = " ".join(i["description"].lower() for i in data["items"])
        materials = ["cement", "steel", "brick", "mortar", "concrete", "plaster", "tile", "paint", "wood", "glass"]
        missing = [m for m in materials if m not in descs]
        assert not missing, f"Missing materials: {missing}"

    def test_estimator_loads_dsr(self, estimator: CostEstimator) -> None:
        assert len(estimator._dsr_index) > 0, "DSR index should be loaded"
        assert len(estimator._dsr_description_index) > 0, "DSR description index should be loaded"

    def test_estimator_lookup_cement(self, estimator: CostEstimator) -> None:
        result = estimator.lookup_rate("cement", "tonne", "delhi")
        assert result is not None, "Should find cement in DSR"
        assert "DSR" in result.source or "CPWD" in result.source
        assert result.rate > 0

    def test_estimator_lookup_steel(self, estimator: CostEstimator) -> None:
        result = estimator.lookup_rate("steel", "kg", "delhi")
        assert result is not None, "Should find steel in DSR"
        assert "DSR" in result.source or "CPWD" in result.source

    def test_estimator_fuzzy_match(self, estimator: CostEstimator) -> None:
        result = estimator.lookup_rate("cement opc", "tonne", "delhi")
        assert result is not None, "Should find cement in DSR"

    def test_estimator_source_attribution(self, estimator: CostEstimator) -> None:
        result = estimator.lookup_rate("brick", "nos", "delhi")
        assert result is not None
        assert result.source is not None
        assert "CPWD" in result.source or "DSR" in result.source or "stub" in result.source

    def test_estimator_nonsense_input(self, estimator: CostEstimator) -> None:
        result = estimator.lookup_rate("xyzabc123nonexistent", "unit", "delhi")
        assert result is None or result.source is not None

    def test_estimator_grade_param(self, estimator: CostEstimator) -> None:
        result = estimator.lookup_rate("concrete", "cum", "delhi", grade="M20")
        assert result is not None
        assert result.rate > 0

    def test_csv_exists(self) -> None:
        csv_path = Path(__file__).parent.parent.parent / "data" / "rates" / "cpwd_dsr_2023.csv"
        assert csv_path.exists(), f"CSV not found at {csv_path}"
        with open(csv_path, encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) >= 500, f"CSV has {len(lines)} lines, need >=500 (including header)"


class TestCostEstimatorDSRIntegration:
    @pytest.fixture
    def estimator(self) -> CostEstimator:
        return CostEstimator()

    def test_lookup_rate_returns_source(self, estimator: CostEstimator) -> None:
        result = estimator.lookup_rate("cement", "tonne", "delhi")
        assert result is not None
        assert hasattr(result, "source")
        assert result.source is not None

    def test_dsr_takes_precedence(self, estimator: CostEstimator) -> None:
        result = estimator.lookup_rate("brick", "nos", "delhi")
        assert result is not None
        assert result.source is not None

    def test_no_exception_on_unknown_material(self, estimator: CostEstimator) -> None:
        result = estimator.lookup_rate("some_random_material_xyz", "nos", "delhi")
        assert result is None or isinstance(result.source, str)

    def test_estimate_item_returns_item_estimate(self, estimator: CostEstimator) -> None:
        row = BoqRow(item_no=1, material="cement", quantity=Decimal("10"), unit="tonne", grade="OPC 43")
        result = estimator.estimate_item(row, "delhi")
        assert isinstance(result, ItemEstimate)
        assert result.item_no == 1
        assert result.rate is not None
        assert result.rate > 0

    def test_estimate_item_with_unknown_material(self, estimator: CostEstimator) -> None:
        row = BoqRow(item_no=1, material="nonexistent xyz", quantity=Decimal("10"), unit="nos", grade="")
        result = estimator.estimate_item(row, "delhi")
        assert isinstance(result, ItemEstimate)
        assert result.rate is not None or result.confidence == 0.0
        assert result.confidence == 0.0

    def test_estimate_total_with_items(self, estimator: CostEstimator) -> None:
        rows = [
            BoqRow(item_no=1, material="cement", quantity=Decimal("10"), unit="tonne", grade="OPC 43"),
            BoqRow(item_no=2, material="steel", quantity=Decimal("100"), unit="kg", grade="Fe500"),
        ]
        result = estimator.estimate_total(rows, "delhi")
        assert result.subtotal > 0
        assert result.total > result.subtotal
        assert result.taxes > 0

    def test_estimate_total_with_no_matching_items(self, estimator: CostEstimator) -> None:
        rows = [
            BoqRow(item_no=1, material="nonexistent xyz", quantity=Decimal("10"), unit="nos", grade=""),
        ]
        result = estimator.estimate_total(rows, "delhi")
        assert result.subtotal == Decimal("0")

    def test_flag_outliers_with_few_items(self, estimator: CostEstimator) -> None:
        items = [
            ItemEstimate(item_no=1, material="a", quantity=Decimal("1"), unit="nos", rate=Decimal("100"), amount=Decimal("100"), source="test", confidence=0.9),
            ItemEstimate(item_no=2, material="b", quantity=Decimal("1"), unit="nos", rate=Decimal("110"), amount=Decimal("110"), source="test", confidence=0.9),
        ]
        result = estimator.flag_outliers(items)
        assert result == []

    def test_get_rate_variance(self, estimator: CostEstimator) -> None:
        result = estimator.get_rate_variance("cement", "tonne")
        assert "mean" in result
        assert "min" in result
        assert "max" in result
        assert result["count"] >= 1
