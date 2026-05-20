"""Relation extraction engine."""

from dataclasses import dataclass

from src.nlp.re.rules import DEFAULT_MAX_DISTANCE, DEFAULT_SENTENCE_GAP, RELATION_RULES


@dataclass
class Relation:
    type: str
    head_entity: dict
    tail_entity: dict
    confidence: float


class RelationExtractor:
    def __init__(
        self,
        rules: list[dict] | None = None,
        max_distance: int = DEFAULT_MAX_DISTANCE,
        max_sentence_gap: int = DEFAULT_SENTENCE_GAP,
    ):
        self.rules = rules or RELATION_RULES
        self.max_distance = max_distance
        self.max_sentence_gap = max_sentence_gap

    def extract(
        self,
        entities: list[dict],
        text: str,
        sentences: list[tuple[int, int]] | None = None,
    ) -> list[Relation]:
        relations = []

        for rule in self.rules:
            rule_relations = self._extract_by_rule(entities, text, rule, sentences)
            relations.extend(rule_relations)

        return self._deduplicate_relations(relations)

    def _extract_by_rule(
        self,
        entities: list[dict],
        text: str,
        rule: dict,
        sentences: list[tuple[int, int]] | None = None,
    ) -> list[Relation]:
        head_type = rule["head"]
        tail_type = rule["tail"]
        relations = []

        heads = [e for e in entities if e.get("type") == head_type]
        tails = [e for e in entities if e.get("type") == tail_type]

        for head in heads:
            for tail in tails:
                confidence = self._check_rule(head, tail, rule, text, sentences)
                if confidence is not None:
                    relations.append(
                        Relation(
                            type=rule["type"],
                            head_entity=head,
                            tail_entity=tail,
                            confidence=confidence,
                        )
                    )

        return relations

    def _check_rule(
        self,
        head: dict,
        tail: dict,
        rule: dict,
        text: str,
        sentences: list[tuple[int, int]] | None = None,
    ) -> float | None:
        head_start = head.get("start", 0)
        head_end = head.get("end", 0)
        tail_start = tail.get("start", 0)
        tail_end = tail.get("end", 0)

        if head_end > tail_start:
            return None

        distance = tail_start - head_end
        max_dist = rule.get("max_distance", self.max_distance)

        if distance > max_dist:
            return None

        if rule.get("same_sentence") and sentences:
            in_same_sentence = False
            for sent_start, sent_end in sentences:
                if (head_start >= sent_start and head_end <= sent_end) and (
                    tail_start >= sent_start and tail_end <= sent_end
                ):
                    in_same_sentence = True
                    break
            if not in_same_sentence:
                return None

        keywords = rule.get("keywords", [])
        if keywords:
            substring = text[head_end:tail_start]
            keyword_found = any(kw.lower() in substring.lower() for kw in keywords)
            if not keyword_found:
                return None

        confidence = 1.0 - (distance / max_dist) if max_dist > 0 else 0.5

        if keywords:
            confidence = min(confidence + 0.1, 1.0)

        return confidence

    def _deduplicate_relations(self, relations: list[Relation]) -> list[Relation]:
        seen = set()
        unique = []

        for rel in relations:
            key = (
                rel.type,
                rel.head_entity.get("text", ""),
                rel.tail_entity.get("text", ""),
            )
            if key not in seen:
                seen.add(key)
                unique.append(rel)

        return unique
