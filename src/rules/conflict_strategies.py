"""Strategy classes for entity conflict resolution."""

from typing import Protocol


class EntityCandidate:
    """Wrapper for an entity candidate from any source."""

    def __init__(self, entity: dict):
        self.entity = entity
        self.text = entity.get("text", "")
        self.type = entity.get("type", "")
        self.confidence = entity.get("confidence", 0.5)
        self.source = entity.get("source", "unknown")
        self.start = entity.get("start", 0)
        self.end = entity.get("end", 0)

    def __repr__(self):
        return f"Candidate({self.type}, conf={self.confidence:.2f}, src={self.source}, text={self.text[:30]!r})"


class ConflictStrategy(Protocol):
    """Protocol for conflict resolution strategies."""

    def resolve(self, candidates: list[EntityCandidate]) -> EntityCandidate:
        """Pick the winning candidate from a list of overlapping candidates."""
        ...


class RulesFirstStrategy:
    """Rules-first strategy for QUANTITY, UNIT, STANDARD.

    If any rule-based candidate exists and source_confidence > 0.7 -> pick it.
    Else fall back to model candidate.
    """

    RULE_SOURCES = {"pattern", "regex", "dictionary"}

    def resolve(self, candidates: list[EntityCandidate]) -> EntityCandidate:
        rule_candidates = [c for c in candidates if c.source in self.RULE_SOURCES]
        model_candidates = [c for c in candidates if c.source not in self.RULE_SOURCES]

        if rule_candidates:
            best_rule = max(rule_candidates, key=lambda c: c.confidence)
            if best_rule.confidence >= 0.7:
                return best_rule

        if model_candidates:
            return max(model_candidates, key=lambda c: c.confidence)

        if rule_candidates:
            return max(rule_candidates, key=lambda c: c.confidence)

        return candidates[0]


class ModelFirstStrategy:
    """Model-first strategy for MATERIAL, LOCATION, ACTION.

    If model candidate confidence > 0.6 -> pick it.
    Else if rule candidate exists -> pick it.
    Else lowest-confidence model.
    """

    RULE_SOURCES = {"pattern", "regex", "dictionary"}

    def resolve(self, candidates: list[EntityCandidate]) -> EntityCandidate:
        model_candidates = [c for c in candidates if c.source not in self.RULE_SOURCES]
        rule_candidates = [c for c in candidates if c.source in self.RULE_SOURCES]

        if model_candidates:
            best_model = max(model_candidates, key=lambda c: c.confidence)
            if best_model.confidence >= 0.6:
                return best_model

        if rule_candidates:
            return max(rule_candidates, key=lambda c: c.confidence)

        return candidates[0]


class HighestConfidenceStrategy:
    """Highest-confidence strategy for DIMENSION, GRADE.

    Pick whichever has highest calibrated confidence.
    """

    RULE_DEFAULT_CONFIDENCE = 0.9
    RULE_SOURCES = {"pattern", "regex"}

    def resolve(self, candidates: list[EntityCandidate]) -> EntityCandidate:
        if len(candidates) < 1:
            raise ValueError("HighestConfidenceStrategy requires at least one candidate")

        adjusted = []
        for c in candidates:
            conf = c.confidence
            if c.source in self.RULE_SOURCES:
                conf = max(conf, self.RULE_DEFAULT_CONFIDENCE)
            adjusted.append((conf, c))

        return max(adjusted, key=lambda x: x[0])[1]


class EnsembleStrategy:
    """Ensemble strategy — weighted vote for unknown types.

    Weighted vote: model_conf * 0.6 + rule_conf * 0.4
    """

    RULE_SOURCES = {"pattern", "regex", "dictionary"}

    def resolve(self, candidates: list[EntityCandidate]) -> EntityCandidate:
        if len(candidates) < 1:
            raise ValueError("EnsembleStrategy requires at least one candidate")

        scored = []
        for c in candidates:
            is_rule = c.source in self.RULE_SOURCES
            weight = 0.4 if is_rule else 0.6
            score = c.confidence * weight
            scored.append((score, c))

        return max(scored, key=lambda x: x[0])[1]


class ThresholdConfidenceStrategy:
    """Threshold-based strategy requiring confidence margin.

    Entity wins only if:
    - confidence > threshold AND
    - confidence > other_confidence + margin
    """

    MARGIN = 0.15

    def resolve(self, candidates: list[EntityCandidate]) -> EntityCandidate:
        if len(candidates) < 1:
            raise ValueError("ThresholdConfidenceStrategy requires at least one candidate")

        scored = [(c.confidence, c) for c in candidates]
        scored.sort(key=lambda x: x[0], reverse=True)
        top_conf, top_cand = scored[0]
        if len(scored) == 1:
            return top_cand

        second_conf = scored[1][0]
        if top_conf > second_conf + self.MARGIN:
            return top_cand

        rule_candidates = [c for c in candidates if c.source in {"pattern", "regex", "dictionary"}]
        if rule_candidates:
            return max(rule_candidates, key=lambda c: c.confidence)
        return top_cand


class TypeSpecificStrategy:
    """Type-specific thresholds with conservative defaults.

    Entity-type-aware thresholds (from task spec):
    - QUANTITY:    pattern wins if pattern_conf >= 0.6, else model
    - MATERIAL:    model wins if model_conf >= 0.7, else rules
    - LOCATION:    model wins if model_conf >= 0.75 (harder entity)
    - GRADE:       rules wins if rule_conf >= 0.8 (strong pattern signatures)
    - STANDARD:    model wins if model_conf >= 0.65
    - DIMENSION:   pattern wins if pattern_conf >= 0.55
    - UNIT:        pattern wins if pattern_conf >= 0.7
    - ACTION:      model wins if model_conf >= 0.7
    """

    RULE_SOURCES = {"pattern", "regex", "dictionary"}
    MODEL_SOURCES = {"bert", "ner"}

    THRESHOLDS: dict[str, tuple[float, float]] = {
        "QUANTITY": (0.6, 0.5),
        "MATERIAL": (0.7, 0.6),
        "LOCATION": (0.75, 0.6),
        "GRADE": (0.8, 0.5),
        "STANDARD": (0.65, 0.55),
        "DIMENSION": (0.55, 0.5),
        "UNIT": (0.7, 0.55),
        "ACTION": (0.7, 0.6),
    }

    def resolve(self, candidates: list[EntityCandidate]) -> EntityCandidate:
        if len(candidates) < 1:
            raise ValueError("TypeSpecificStrategy requires at least one candidate")

        if len(candidates) == 1:
            return candidates[0]

        entity_type = candidates[0].type
        rule_thresh, model_thresh = self.THRESHOLDS.get(entity_type, (0.6, 0.6))

        rule_candidates = [c for c in candidates if c.source in self.RULE_SOURCES]
        model_candidates = [c for c in candidates if c.source in self.MODEL_SOURCES]

        best_rule = max(rule_candidates, key=lambda c: c.confidence) if rule_candidates else None
        best_model = max(model_candidates, key=lambda c: c.confidence) if model_candidates else None

        if entity_type in {"QUANTITY", "DIMENSION", "UNIT"}:
            if best_rule and best_rule.confidence >= rule_thresh:
                return best_rule
            if best_model:
                return best_model
            return best_rule or best_model or candidates[0]
        if entity_type in {"GRADE", "STANDARD"}:
            if best_rule and best_rule.confidence >= rule_thresh:
                return best_rule
            if best_model:
                return best_model
            return best_rule or best_model or candidates[0]
        if best_model and best_model.confidence >= model_thresh:
            return best_model
        if best_rule:
            return best_rule
        return best_model or best_rule or candidates[0]


class HybridEnsembleStrategy:
    """Weighted ensemble by entity type + confidence gap.

    Uses type-specific weights and confidence gap to decide winner.
    """

    RULE_SOURCES = {"pattern", "regex", "dictionary"}
    MODEL_SOURCES = {"bert", "ner"}

    TYPE_WEIGHTS: dict[str, float] = {
        "QUANTITY": 0.3,
        "MATERIAL": 0.6,
        "LOCATION": 0.65,
        "GRADE": 0.2,
        "STANDARD": 0.5,
        "DIMENSION": 0.35,
        "UNIT": 0.3,
        "ACTION": 0.6,
    }

    def resolve(self, candidates: list[EntityCandidate]) -> EntityCandidate:
        if len(candidates) < 1:
            raise ValueError("HybridEnsembleStrategy requires at least one candidate")

        if len(candidates) == 1:
            return candidates[0]

        entity_type = candidates[0].type
        model_weight = self.TYPE_WEIGHTS.get(entity_type, 0.5)
        rule_weight = 1.0 - model_weight

        scored = []
        for c in candidates:
            is_rule = c.source in self.RULE_SOURCES
            weight = rule_weight if is_rule else model_weight
            score = c.confidence * weight
            scored.append((score, c))

        return max(scored, key=lambda x: x[0])[1]


STRATEGY_MAP: dict[str, ConflictStrategy] = {
    "QUANTITY": RulesFirstStrategy(),
    "UNIT": RulesFirstStrategy(),
    "STANDARD": RulesFirstStrategy(),
    "MATERIAL": ModelFirstStrategy(),
    "LOCATION": ModelFirstStrategy(),
    "ACTION": ModelFirstStrategy(),
    "DIMENSION": HighestConfidenceStrategy(),
    "GRADE": HighestConfidenceStrategy(),
}


def get_strategy(entity_type: str) -> ConflictStrategy:
    """Get the appropriate strategy for an entity type."""
    return STRATEGY_MAP.get(entity_type, EnsembleStrategy())
