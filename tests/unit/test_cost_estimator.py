from decimal import Decimal

from src.domain.cost_estimator import CostEstimator, ItemEstimate
from src.domain.models import BoqRow


def test_lookup_rate_concrete():
    est = CostEstimator()
    entry = est.lookup_rate("M25 concrete", "cu.m", "cpwd_delhi")
    assert entry is not None
    assert entry.rate > 0

def test_lookup_rate_steel():
    est = CostEstimator()
    entry = est.lookup_rate("TMT steel bars Fe500", "quintal", "cpwd_delhi")
    assert entry is not None
    assert entry.rate > 0

def test_lookup_rate_not_found():
    est = CostEstimator()
    entry = est.lookup_rate("some unknown material", "unit", "cpwd_delhi")
    assert entry is None

def test_estimate_item():
    est = CostEstimator()
    row = BoqRow(item_no=1, material="M25 concrete", quantity=Decimal("10"), unit="cu.m")
    result = est.estimate_item(row, "cpwd_delhi")
    assert isinstance(result, ItemEstimate)
    assert result.amount > 0

def test_estimate_total():
    est = CostEstimator()
    rows = [
        BoqRow(item_no=1, material="M25 concrete", quantity=Decimal("10"), unit="cu.m"),
        BoqRow(item_no=2, material="TMT steel bars Fe500", quantity=Decimal("5"), unit="quintal"),
    ]
    total = est.estimate_total(rows, "cpwd_delhi")
    assert total.subtotal > 0
    assert total.taxes > 0
    assert total.total > 0

def test_flag_outliers():
    est = CostEstimator()
    rows = [
        BoqRow(item_no=1, material="M25 concrete", quantity=Decimal("10"), unit="cu.m"),
        BoqRow(item_no=2, material="M30 concrete", quantity=Decimal("10000"), unit="cu.m"),
    ]
    item_estimates = [est.estimate_item(row, "cpwd_delhi") for row in rows]
    outliers = est.flag_outliers(item_estimates)
    assert isinstance(outliers, list)

def test_rate_variance():
    est = CostEstimator()
    variance = est.get_rate_variance("portland cement", "tonne")
    assert isinstance(variance, dict)
    assert "mean" in variance
    assert "min" in variance
    assert "max" in variance
