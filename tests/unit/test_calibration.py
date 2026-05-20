"""Tests for Calibration/Conformal Prediction."""


from src.confidence.calibration import (
    CalibratedConfidence,
    ConfidenceCalibrator,
    ConformalPredictor,
    compute_mc_dropout_entropy,
)


class TestConfidenceCalibrator:
    def test_init(self):
        cal = ConfidenceCalibrator()
        assert cal.temperature == 1.0
        assert cal.target_coverage == 0.95

    def test_init_custom(self):
        cal = ConfidenceCalibrator(temperature=0.8, target_coverage=0.9)
        assert cal.temperature == 0.8
        assert cal.target_coverage == 0.9

    def test_add_calibration_sample(self):
        cal = ConfidenceCalibrator()
        cal.add_calibration_sample(0.8, 0.9)
        cal.add_calibration_sample(0.6, 0.7)
        assert len(cal._calibration_scores) == 2

    def test_fit_with_insufficient_samples(self):
        cal = ConfidenceCalibrator()
        cal.add_calibration_sample(0.5, 0.6)
        q = cal.fit()
        assert q == 1.0

    def test_calibrate(self):
        cal = ConfidenceCalibrator()
        result = cal.calibrate(0.7, {"has_quantity": True, "has_unit": True})
        assert isinstance(result, CalibratedConfidence)
        assert 0.0 <= result.confidence <= 1.0

    def test_build_prediction_set_high_conf(self):
        cal = ConfidenceCalibrator()
        result = cal._build_prediction_set(0.8, {})
        assert "HIGH" in result

    def test_build_prediction_set_low_conf(self):
        cal = ConfidenceCalibrator()
        result = cal._build_prediction_set(0.3, {})
        assert len(result) > 1


class TestConformalPredictor:
    def test_init(self):
        pred = ConformalPredictor()
        assert pred.target_coverage == 0.95

    def test_predict_set(self):
        pred = ConformalPredictor()
        result = pred.predict_set("cement", "MATERIAL", 0.7, {"has_quantity": True})
        assert result.entity_text == "cement"
        assert result.entity_type == "MATERIAL"
        assert result.is_low_confidence is False

    def test_predict_set_low_confidence(self):
        pred = ConformalPredictor()
        result = pred.predict_set("some text", "MATERIAL", 0.3, {"has_quantity": False})
        assert result.is_low_confidence is True

    def test_filter_low_confidence(self):
        pred = ConformalPredictor()
        entities = [
            {"text": "high", "type": "MATERIAL", "confidence": 0.9},
            {"text": "low", "type": "MATERIAL", "confidence": 0.3},
        ]
        high, low = pred.filter_low_confidence(entities)
        assert len(high) == 1
        assert len(low) == 1

    def test_filter_low_confidence_custom_threshold(self):
        pred = ConformalPredictor()
        entities = [
            {"text": "medium", "type": "MATERIAL", "confidence": 0.6},
        ]
        high, low = pred.filter_low_confidence(entities, threshold=0.8)
        assert len(high) == 0
        assert len(low) == 1


class TestMCDropoutEntropy:
    def test_compute_mc_dropout_entropy(self):
        logits = [0.5, 0.5, 0.5]
        entropy = compute_mc_dropout_entropy(logits)
        assert entropy >= 0.0

    def test_compute_mc_dropout_entropy_extreme(self):
        logits = [10.0, 10.0, 10.0]
        entropy = compute_mc_dropout_entropy(logits)
        assert entropy >= 0.0
