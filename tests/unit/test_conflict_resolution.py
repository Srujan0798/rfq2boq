"""Tests for entity conflict resolution."""

from src.rules.conflict import resolve_conflicts, resolve_unit_conflicts
from src.rules.conflict_strategies import (
    EnsembleStrategy,
    EntityCandidate,
    HighestConfidenceStrategy,
    HybridEnsembleStrategy,
    ModelFirstStrategy,
    RulesFirstStrategy,
    ThresholdConfidenceStrategy,
    TypeSpecificStrategy,
    get_strategy,
)


class TestRulesFirstStrategy:
    def test_rule_wins_high_confidence(self):
        rule = EntityCandidate({"type": "QUANTITY", "text": "500", "confidence": 0.95, "source": "pattern"})
        model = EntityCandidate({"type": "QUANTITY", "text": "500", "confidence": 0.55, "source": "bert"})
        strategy = RulesFirstStrategy()
        result = strategy.resolve([model, rule])
        assert result.source == "pattern"

    def test_model_wins_low_rule_confidence(self):
        rule = EntityCandidate({"type": "QUANTITY", "text": "500", "confidence": 0.60, "source": "pattern"})
        model = EntityCandidate({"type": "QUANTITY", "text": "500", "confidence": 0.80, "source": "bert"})
        strategy = RulesFirstStrategy()
        result = strategy.resolve([model, rule])
        assert result.source == "bert"

    def test_model_only(self):
        model = EntityCandidate({"type": "QUANTITY", "text": "500", "confidence": 0.75, "source": "bert"})
        strategy = RulesFirstStrategy()
        result = strategy.resolve([model])
        assert result.source == "bert"

    def test_rule_only(self):
        rule = EntityCandidate({"type": "QUANTITY", "text": "500", "confidence": 0.95, "source": "pattern"})
        strategy = RulesFirstStrategy()
        result = strategy.resolve([rule])
        assert result.source == "pattern"


class TestModelFirstStrategy:
    def test_model_wins_high_confidence(self):
        model = EntityCandidate({"type": "MATERIAL", "text": "cement", "confidence": 0.80, "source": "bert"})
        rule = EntityCandidate({"type": "MATERIAL", "text": "cement", "confidence": 0.90, "source": "pattern"})
        strategy = ModelFirstStrategy()
        result = strategy.resolve([model, rule])
        assert result.source == "bert"

    def test_rule_fallback_low_model_confidence(self):
        model = EntityCandidate({"type": "MATERIAL", "text": "cement", "confidence": 0.50, "source": "bert"})
        rule = EntityCandidate({"type": "MATERIAL", "text": "cement", "confidence": 0.95, "source": "pattern"})
        strategy = ModelFirstStrategy()
        result = strategy.resolve([model, rule])
        assert result.source == "pattern"

    def test_no_model_candidates(self):
        rule = EntityCandidate({"type": "MATERIAL", "text": "cement", "confidence": 0.90, "source": "pattern"})
        strategy = ModelFirstStrategy()
        result = strategy.resolve([rule])
        assert result.source == "pattern"


class TestHighestConfidenceStrategy:
    def test_highest_confidence_wins(self):
        low = EntityCandidate({"type": "GRADE", "text": "M20", "confidence": 0.72, "source": "bert"})
        high = EntityCandidate({"type": "GRADE", "text": "M20", "confidence": 0.90, "source": "pattern"})
        strategy = HighestConfidenceStrategy()
        result = strategy.resolve([low, high])
        assert result.confidence == 0.90

    def test_rule_candidates_get_adjusted_confidence(self):
        rule = EntityCandidate({"type": "GRADE", "text": "M20", "confidence": 0.50, "source": "pattern"})
        model = EntityCandidate({"type": "GRADE", "text": "M20", "confidence": 0.60, "source": "bert"})
        strategy = HighestConfidenceStrategy()
        result = strategy.resolve([rule, model])
        assert result.source == "pattern"


class TestEnsembleStrategy:
    def test_weighted_vote_model_wins(self):
        model = EntityCandidate({"type": "UNKNOWN", "text": "item", "confidence": 0.90, "source": "bert"})
        rule = EntityCandidate({"type": "UNKNOWN", "text": "item", "confidence": 0.90, "source": "pattern"})
        strategy = EnsembleStrategy()
        result = strategy.resolve([model, rule])
        assert result.source == "bert"

    def test_single_candidate(self):
        model = EntityCandidate({"type": "UNKNOWN", "text": "item", "confidence": 0.75, "source": "bert"})
        strategy = EnsembleStrategy()
        result = strategy.resolve([model])
        assert result.text == "item"


class TestGetStrategy:
    def test_quantity_rules_first(self):
        s = get_strategy("QUANTITY")
        assert isinstance(s, RulesFirstStrategy)

    def test_material_model_first(self):
        s = get_strategy("MATERIAL")
        assert isinstance(s, ModelFirstStrategy)

    def test_dimension_highest_confidence(self):
        s = get_strategy("DIMENSION")
        assert isinstance(s, HighestConfidenceStrategy)

    def test_grade_highest_confidence(self):
        s = get_strategy("GRADE")
        assert isinstance(s, HighestConfidenceStrategy)

    def test_unknown_ensemble(self):
        s = get_strategy("UNKNOWN")
        assert isinstance(s, EnsembleStrategy)


class TestResolveConflicts:
    def test_pattern_wins_for_quantity(self):
        bert = [{"type": "QUANTITY", "text": "500", "confidence": 0.55, "source": "bert", "start": 6, "end": 9}]
        pattern = [{"type": "QUANTITY", "text": "500", "confidence": 0.95, "source": "pattern", "start": 6, "end": 9}]
        result = resolve_conflicts(bert, pattern)
        assert result[0]["source"] == "pattern"

    def test_bert_wins_for_material(self):
        bert = [{"type": "MATERIAL", "text": "cement", "confidence": 0.80, "source": "bert", "start": 5, "end": 11}]
        pattern = [
            {"type": "MATERIAL", "text": "cement", "confidence": 0.90, "source": "pattern", "start": 5, "end": 11}
        ]
        result = resolve_conflicts(bert, pattern)
        assert result[0]["source"] == "bert"

    def test_highest_confidence_for_dimension(self):
        bert = [{"type": "DIMENSION", "text": "12", "confidence": 0.55, "source": "bert", "start": 0, "end": 2}]
        pattern = [{"type": "DIMENSION", "text": "12mm", "confidence": 0.90, "source": "pattern", "start": 0, "end": 4}]
        result = resolve_conflicts(bert, pattern)
        assert result[0]["confidence"] == 0.90

    def test_dictionary_entities_included(self):
        bert = [{"type": "MATERIAL", "text": "cement", "confidence": 0.55, "source": "bert", "start": 5, "end": 11}]
        dictionary = [
            {"type": "MATERIAL", "text": "cement", "confidence": 0.85, "source": "dictionary", "start": 5, "end": 11}
        ]
        result = resolve_conflicts(bert, [], dictionary)
        assert len(result) == 1
        assert result[0]["source"] == "dictionary"

    def test_non_overlapping_entities_both_kept(self):
        bert = [{"type": "MATERIAL", "text": "cement", "confidence": 0.80, "source": "bert", "start": 0, "end": 5}]
        pattern = [{"type": "UNIT", "text": "kg", "confidence": 0.95, "source": "pattern", "start": 10, "end": 12}]
        result = resolve_conflicts(bert, pattern)
        assert len(result) == 2

    def test_empty_inputs(self):
        result = resolve_conflicts([], [])
        assert result == []

    def test_single_entity_passthrough(self):
        entity = [{"type": "MATERIAL", "text": "cement", "confidence": 0.80, "source": "bert", "start": 0, "end": 5}]
        result = resolve_conflicts(entity, [])
        assert len(result) == 1


class TestResolveUnitConflicts:
    def test_removes_unit_entities(self):
        entities = [
            {"type": "MATERIAL", "text": "cement"},
            {"type": "UNIT", "text": "kg"},
            {"type": "QUANTITY", "text": "500"},
        ]
        result = resolve_unit_conflicts(entities)
        assert all(e["type"] != "UNIT" for e in result)


class TestEdgeCases:
    def test_conflicting_entity_types(self):
        bert = [{"type": "GRADE", "text": "M20", "confidence": 0.72, "source": "bert", "start": 10, "end": 14}]
        pattern = [{"type": "GRADE", "text": "M20", "confidence": 0.90, "source": "pattern", "start": 10, "end": 14}]
        result = resolve_conflicts(bert, pattern)
        assert result[0]["type"] == "GRADE"
        assert result[0]["source"] == "pattern"

    def test_only_one_candidate(self):
        bert = [{"type": "MATERIAL", "text": "cement", "confidence": 0.80, "source": "bert", "start": 0, "end": 5}]
        result = resolve_conflicts(bert, [])
        assert len(result) == 1

    def test_all_candidates_disagree(self):
        bert = EntityCandidate(
            {"type": "DIMENSION", "text": "cement", "confidence": 0.82, "source": "bert", "start": 0, "end": 5}
        )
        pattern = EntityCandidate(
            {"type": "DIMENSION", "text": "cement", "confidence": 0.89, "source": "pattern", "start": 0, "end": 5}
        )
        dictionary = EntityCandidate(
            {"type": "DIMENSION", "text": "cement", "confidence": 0.92, "source": "dictionary", "start": 0, "end": 5}
        )
        result = resolve_conflicts([bert.entity], [pattern.entity], [dictionary.entity])
        assert result[0]["source"] == "dictionary"


class TestThresholdConfidenceStrategy:
    def test_threshold_logic_wins(self):
        bert = EntityCandidate(
            {"type": "MATERIAL", "text": "cement bag", "confidence": 0.85, "source": "bert", "start": 0, "end": 10}
        )
        pattern = EntityCandidate(
            {"type": "MATERIAL", "text": "cement bag", "confidence": 0.45, "source": "pattern", "start": 0, "end": 10}
        )
        strategy = ThresholdConfidenceStrategy()
        result = strategy.resolve([bert, pattern])
        assert result.source == "bert"

    def test_no_margin_no_win(self):
        bert = EntityCandidate(
            {"type": "MATERIAL", "text": "cement", "confidence": 0.75, "source": "bert", "start": 0, "end": 5}
        )
        pattern = EntityCandidate(
            {"type": "MATERIAL", "text": "cement", "confidence": 0.65, "source": "pattern", "start": 0, "end": 5}
        )
        strategy = ThresholdConfidenceStrategy()
        result = strategy.resolve([bert, pattern])
        assert result.source == "pattern"

    def test_boundary_threshold(self):
        bert = EntityCandidate(
            {"type": "MATERIAL", "text": "steel", "confidence": 0.60, "source": "bert", "start": 0, "end": 5}
        )
        pattern = EntityCandidate(
            {"type": "MATERIAL", "text": "steel", "confidence": 0.45, "source": "pattern", "start": 0, "end": 5}
        )
        strategy = ThresholdConfidenceStrategy()
        result = strategy.resolve([bert, pattern])
        assert result.source == "pattern"

    def test_single_candidate(self):
        cand = EntityCandidate(
            {"type": "MATERIAL", "text": "cement", "confidence": 0.80, "source": "bert", "start": 0, "end": 5}
        )
        strategy = ThresholdConfidenceStrategy()
        result = strategy.resolve([cand])
        assert result.text == "cement"


class TestTypeSpecificStrategy:
    def test_quantity_pattern_wins_high_conf(self):
        pattern = EntityCandidate(
            {"type": "QUANTITY", "text": "500", "confidence": 0.65, "source": "pattern", "start": 0, "end": 3}
        )
        model = EntityCandidate(
            {"type": "QUANTITY", "text": "500", "confidence": 0.80, "source": "bert", "start": 0, "end": 3}
        )
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "pattern"

    def test_quantity_model_wins_low_pattern_conf(self):
        pattern = EntityCandidate(
            {"type": "QUANTITY", "text": "500", "confidence": 0.55, "source": "pattern", "start": 0, "end": 3}
        )
        model = EntityCandidate(
            {"type": "QUANTITY", "text": "500", "confidence": 0.80, "source": "bert", "start": 0, "end": 3}
        )
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "bert"

    def test_material_model_wins_high_conf(self):
        model = EntityCandidate(
            {"type": "MATERIAL", "text": "cement", "confidence": 0.75, "source": "bert", "start": 0, "end": 5}
        )
        pattern = EntityCandidate(
            {"type": "MATERIAL", "text": "cement", "confidence": 0.85, "source": "pattern", "start": 0, "end": 5}
        )
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "bert"

    def test_grade_rules_wins_very_high_conf(self):
        pattern = EntityCandidate(
            {"type": "GRADE", "text": "M20", "confidence": 0.85, "source": "pattern", "start": 0, "end": 3}
        )
        model = EntityCandidate(
            {"type": "GRADE", "text": "M20", "confidence": 0.90, "source": "bert", "start": 0, "end": 3}
        )
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "pattern"

    def test_location_model_wins_high_conf(self):
        model = EntityCandidate(
            {"type": "LOCATION", "text": "ground floor", "confidence": 0.80, "source": "bert", "start": 0, "end": 11}
        )
        pattern = EntityCandidate(
            {"type": "LOCATION", "text": "ground floor", "confidence": 0.90, "source": "pattern", "start": 0, "end": 11}
        )
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "bert"

    def test_both_low_confidence_rules_default(self):
        pattern = EntityCandidate(
            {"type": "MATERIAL", "text": "cement", "confidence": 0.50, "source": "pattern", "start": 0, "end": 5}
        )
        model = EntityCandidate(
            {"type": "MATERIAL", "text": "cement", "confidence": 0.45, "source": "bert", "start": 0, "end": 5}
        )
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "pattern"


class TestHybridEnsembleStrategy:
    def test_model_weighted_wins(self):
        model = EntityCandidate(
            {"type": "MATERIAL", "text": "steel", "confidence": 0.90, "source": "bert", "start": 0, "end": 5}
        )
        pattern = EntityCandidate(
            {"type": "MATERIAL", "text": "steel", "confidence": 0.90, "source": "pattern", "start": 0, "end": 5}
        )
        strategy = HybridEnsembleStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "bert"

    def test_quantity_pattern_weighted(self):
        model = EntityCandidate(
            {"type": "QUANTITY", "text": "500", "confidence": 0.80, "source": "bert", "start": 0, "end": 3}
        )
        pattern = EntityCandidate(
            {"type": "QUANTITY", "text": "500", "confidence": 0.80, "source": "pattern", "start": 0, "end": 3}
        )
        strategy = HybridEnsembleStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "pattern"

    def test_grade_rules_heavily_weighted(self):
        model = EntityCandidate(
            {"type": "GRADE", "text": "Fe500", "confidence": 0.80, "source": "bert", "start": 0, "end": 4}
        )
        pattern = EntityCandidate(
            {"type": "GRADE", "text": "Fe500", "confidence": 0.80, "source": "pattern", "start": 0, "end": 4}
        )
        strategy = HybridEnsembleStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "pattern"


class TestGetStrategyOriginalMapping:
    def test_quantity_rules_first(self):
        s = get_strategy("QUANTITY")
        assert isinstance(s, RulesFirstStrategy)

    def test_material_model_first(self):
        s = get_strategy("MATERIAL")
        assert isinstance(s, ModelFirstStrategy)

    def test_dimension_highest_confidence(self):
        s = get_strategy("DIMENSION")
        assert isinstance(s, HighestConfidenceStrategy)

    def test_grade_highest_confidence(self):
        s = get_strategy("GRADE")
        assert isinstance(s, HighestConfidenceStrategy)

    def test_unit_rules_first(self):
        s = get_strategy("UNIT")
        assert isinstance(s, RulesFirstStrategy)

    def test_standard_rules_first(self):
        s = get_strategy("STANDARD")
        assert isinstance(s, RulesFirstStrategy)

    def test_action_model_first(self):
        s = get_strategy("ACTION")
        assert isinstance(s, ModelFirstStrategy)

    def test_location_model_first(self):
        s = get_strategy("LOCATION")
        assert isinstance(s, ModelFirstStrategy)


class TestEdgeCasesEnhanced:
    def test_threshold_boundary_exactly_at_threshold(self):
        model = EntityCandidate({"type": "MATERIAL", "text": "cement", "confidence": 0.70, "source": "bert"})
        pattern = EntityCandidate({"type": "MATERIAL", "text": "cement", "confidence": 0.70, "source": "pattern"})
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result is not None

    def test_both_low_confidence_uses_rules_default(self):
        model = EntityCandidate({"type": "LOCATION", "text": "ground floor", "confidence": 0.40, "source": "bert"})
        pattern = EntityCandidate({"type": "LOCATION", "text": "ground floor", "confidence": 0.50, "source": "pattern"})
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "pattern"

    def test_both_high_confidence_uses_model_aggressive(self):
        model = EntityCandidate({"type": "MATERIAL", "text": "steel", "confidence": 0.90, "source": "bert"})
        pattern = EntityCandidate({"type": "MATERIAL", "text": "steel", "confidence": 0.65, "source": "pattern"})
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "bert"

    def test_overlapping_entities_different_type(self):
        text1 = EntityCandidate({"type": "LOCATION", "text": "ground floor", "confidence": 0.80, "source": "bert"})
        text2 = EntityCandidate({"type": "DIMENSION", "text": "ground", "confidence": 0.55, "source": "pattern"})
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([text1, text2])
        assert result is not None

    def test_grade_strong_pattern_wins_heavily(self):
        model = EntityCandidate({"type": "GRADE", "text": "M20", "confidence": 0.85, "source": "bert"})
        pattern = EntityCandidate({"type": "GRADE", "text": "M20", "confidence": 0.80, "source": "pattern"})
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "pattern"

    def test_standard_model_wins_with_high_conf(self):
        model = EntityCandidate({"type": "STANDARD", "text": "IS 456", "confidence": 0.75, "source": "bert"})
        pattern = EntityCandidate({"type": "STANDARD", "text": "IS 456", "confidence": 0.80, "source": "pattern"})
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "pattern"

    def test_quantity_pattern_wins_with_threshold(self):
        model = EntityCandidate({"type": "QUANTITY", "text": "500", "confidence": 0.65, "source": "bert"})
        pattern = EntityCandidate({"type": "QUANTITY", "text": "500", "confidence": 0.60, "source": "pattern"})
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "pattern"

    def test_dimension_pattern_wins_low_threshold(self):
        model = EntityCandidate({"type": "DIMENSION", "text": "250mm", "confidence": 0.60, "source": "bert"})
        pattern = EntityCandidate({"type": "DIMENSION", "text": "250mm", "confidence": 0.55, "source": "pattern"})
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "pattern"

    def test_unit_pattern_wins_high_threshold(self):
        model = EntityCandidate({"type": "UNIT", "text": "cum", "confidence": 0.80, "source": "bert"})
        pattern = EntityCandidate({"type": "UNIT", "text": "cum", "confidence": 0.70, "source": "pattern"})
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "pattern"

    def test_action_model_wins_with_high_conf(self):
        model = EntityCandidate({"type": "ACTION", "text": "supply", "confidence": 0.75, "source": "bert"})
        pattern = EntityCandidate({"type": "ACTION", "text": "supply", "confidence": 0.65, "source": "pattern"})
        strategy = TypeSpecificStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "bert"

    def test_confidence_margin_with_threshold_strategy(self):
        model = EntityCandidate({"type": "MATERIAL", "text": "cement", "confidence": 0.85, "source": "bert"})
        pattern = EntityCandidate({"type": "MATERIAL", "text": "cement", "confidence": 0.45, "source": "pattern"})
        strategy = ThresholdConfidenceStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "bert"

    def test_no_margin_no_win_threshold_strategy(self):
        model = EntityCandidate({"type": "MATERIAL", "text": "cement", "confidence": 0.60, "source": "bert"})
        pattern = EntityCandidate({"type": "MATERIAL", "text": "cement", "confidence": 0.55, "source": "pattern"})
        strategy = ThresholdConfidenceStrategy()
        result = strategy.resolve([model, pattern])
        assert result.source == "pattern"

    def test_empty_candidates_raises(self):
        strategy = ThresholdConfidenceStrategy()
        import pytest

        with pytest.raises(ValueError):
            strategy.resolve([])

    def test_single_candidate_threshold_passthrough(self):
        candidate = EntityCandidate({"type": "MATERIAL", "text": "cement", "confidence": 0.75, "source": "bert"})
        strategy = ThresholdConfidenceStrategy()
        result = strategy.resolve([candidate])
        assert result.text == "cement"
