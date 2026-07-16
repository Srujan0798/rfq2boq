"""Conflict resolution rules for entity merging."""

from src.rules.conflict_strategies import (
    STRATEGY_MAP,
    EntityCandidate,
    get_strategy,
)


def resolve_conflicts(
    bert_entities: list[dict],
    pattern_entities: list[dict],
    dictionary_entities: list[dict] | None = None,
) -> list[dict]:
    """Resolve conflicts between BERT, pattern, and dictionary entities.

    For each overlapping group of candidates, applies per-entity-type strategy.
    Non-overlapping entities are passed through unchanged.
    """
    all_entities = []
    for e in bert_entities:
        e_copy = e.copy()
        e_copy["source"] = "bert"
        all_entities.append(e_copy)

    for e in pattern_entities:
        e_copy = e.copy()
        e_copy["source"] = "pattern"
        all_entities.append(e_copy)

    if dictionary_entities:
        for e in dictionary_entities:
            e_copy = e.copy()
            e_copy["source"] = "dictionary"
            all_entities.append(e_copy)

    resolved = _resolve_by_strategy(all_entities)

    return [c.entity for c in resolved]


def _resolve_by_strategy(entities: list[dict]) -> list[EntityCandidate]:
    """Group overlapping candidates and resolve each group by strategy."""
    if not entities:
        return []

    candidates = [EntityCandidate(e) for e in entities]
    groups = _group_overlapping(candidates)

    resolved = []
    for group in groups:
        if len(group) == 1:
            resolved.append(group[0])
        else:
            winner = _resolve_group(group)
            resolved.append(winner)

    return resolved


def _group_overlapping(candidates: list[EntityCandidate]) -> list[list[EntityCandidate]]:
    """Group candidates by overlapping spans."""
    groups = []
    used = set()

    for i, candidate in enumerate(candidates):
        if i in used:
            continue

        group = [candidate]
        used.add(i)

        for j, other in enumerate(candidates):
            if j in used:
                continue
            if _overlaps_spans(candidate, other):
                group.append(other)
                used.add(j)

        groups.append(group)

    return groups


def _resolve_group(group: list[EntityCandidate]) -> EntityCandidate:
    """Resolve a group of overlapping candidates using the appropriate strategy."""
    entity_types = {c.type for c in group}

    if len(entity_types) == 1:
        strategy = get_strategy(entity_types.pop())
    else:
        strategy = STRATEGY_MAP.get(max(entity_types, key=lambda t: _type_priority(t)), get_strategy("UNKNOWN"))

    return strategy.resolve(group)


def _type_priority(t: str) -> int:
    """Priority of entity type for disambiguation."""
    priority = {
        "QUANTITY": 7,
        "UNIT": 7,
        "STANDARD": 7,
        "MATERIAL": 5,
        "LOCATION": 5,
        "ACTION": 5,
        "DIMENSION": 3,
        "GRADE": 3,
    }
    return priority.get(t, 0)


def resolve_conflicts_legacy(
    bert_entities: list[dict],
    pattern_entities: list[dict],
) -> list[dict]:
    """Legacy resolver — kept for fallback."""
    pattern_wins = {"QUANTITY", "UNIT", "STANDARD"}
    confidence_wins = {"DIMENSION", "GRADE"}

    merged = []
    used_pattern_indices = set()

    for bert_ent in bert_entities:
        ent_type = bert_ent.get("type", "")

        if ent_type in pattern_wins:
            matching = [
                (i, p)
                for i, p in enumerate(pattern_entities)
                if p.get("type") == ent_type
                and _overlaps_spans(EntityCandidate(bert_ent), EntityCandidate(p))
                and i not in used_pattern_indices
            ]
            if matching:
                idx, pattern_ent = matching[0]
                used_pattern_indices.add(idx)
                merged.append(pattern_ent)
            else:
                merged.append(bert_ent)
        else:
            merged.append(bert_ent)

    for i, pattern_ent in enumerate(pattern_entities):
        if i in used_pattern_indices:
            continue

        ent_type = pattern_ent.get("type", "")
        if ent_type in confidence_wins:
            overlap_berts = [
                b
                for b in bert_entities
                if b.get("type") == ent_type and _overlaps_spans(EntityCandidate(pattern_ent), EntityCandidate(b))
            ]
            if overlap_berts:
                best = max(overlap_berts, key=lambda x: x.get("confidence", 0))
                if best.get("confidence", 0) > pattern_ent.get("confidence", 0):
                    continue
            merged.append(pattern_ent)
        elif ent_type not in {e.get("type") for e in bert_entities}:
            merged.append(pattern_ent)

    merged = _merge_overlapping(merged)
    return merged


def _overlaps_spans(c1: EntityCandidate, c2: EntityCandidate) -> bool:
    """Check if two candidates overlap."""
    return not (c1.end <= c2.start or c2.end <= c1.start)


def _overlaps(e1: dict, e2: dict) -> bool:
    """Check if two raw entities overlap."""
    s1, e1_ = e1.get("start", 0), e1.get("end", 0)
    s2, e2_ = e2.get("start", 0), e2.get("end", 0)
    return not (e1_ <= s2 or e2_ <= s1)


def _merge_overlapping(entities: list[dict]) -> list[dict]:
    """Merge overlapping entities of same type."""
    if not entities:
        return []

    sorted_entities = sorted(entities, key=lambda x: (x.get("start", 0), x.get("end", 0)))
    merged = []
    current = None

    for entity in sorted_entities:
        if current is None:
            current = entity.copy()
            continue

        if (
            _overlaps(current, entity)
            and current.get("type") == entity.get("type")
            and entity.get("source") == current.get("source")
        ):
            current["text"] = current.get("text", "") + entity.get("text", "")
            current["end"] = max(current.get("end", 0), entity.get("end", 0))
            current["confidence"] = max(current.get("confidence", 0), entity.get("confidence", 0))
        else:
            merged.append(current)
            current = entity.copy()

    if current is not None:
        merged.append(current)

    return merged


def resolve_unit_conflicts(entities: list[dict]) -> list[dict]:
    """Resolve conflicting unit assignments."""
    resolved = []
    for entity in entities:
        if entity.get("type") == "UNIT":
            continue
        resolved.append(entity)

    return resolved
