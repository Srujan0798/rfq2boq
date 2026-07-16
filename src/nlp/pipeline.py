"""Unified NLP pipeline for RFQ-to-BOQ extraction.

Orchestrates the full extraction pipeline:
1. NER inference (BERT model if available)
2. Pattern matching (regex + dictionary)
3. Conflict resolution
4. Relation extraction
5. Scope gap detection
"""

from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExtractionResult:
    entities: list[dict] = field(default_factory=list)
    relations: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence: float = 0.0


class NLPPipeline:
    def __init__(
        self,
        model_dir: str | None = None,
        ontology_dir: str | None = None,
        id2label: dict[int, str] | None = None,
        label2id: dict[str, int] | None = None,
        layout_aware: bool = False,
        layoutlm_model_dir: str | None = None,
        use_joint_model: bool = False,
        ner_enabled: bool = True,
    ):
        self.model_dir = model_dir
        self.layout_aware = layout_aware
        self.layoutlm_model_dir = layoutlm_model_dir
        self.use_joint_model = use_joint_model
        self.ner_enabled = ner_enabled

        from config.settings import settings as _settings

        self.ontology_dir = Path(ontology_dir) if ontology_dir else _settings.ONTOLOGY_DIR

        from config.constants import ID2LABEL as _ID2LABEL
        from config.constants import LABEL2ID as _LABEL2ID

        self.id2label = id2label or _ID2LABEL
        self.label2id = label2id or _LABEL2ID

        self.ner: Any = None
        self.indic_ner: Any = None
        self.layout_ner: Any = None
        self.calibrator: Any = None
        self.pretrained_ner: Any = None

        self._init_patterns()
        if ner_enabled:
            self._init_ner(model_dir)
            self._init_pretrained_ner()

    def _init_ner(self, model_dir: str | None) -> None:
        """Initialize NER — pattern-based only. No LoRA, no pre-trained models.

        Phase 0 clean-slate: all ML NER wiring removed. Pipeline runs on
        regex + gazetteer + table extraction only until a genuine model
        is trained from scratch (Phase 2).
        """
        self.ner = None

    def _init_indic_ner(self) -> None:
        """Initialize IndicBERT NER model for Hindi/multilingual text."""
        if self.indic_ner is not None:
            return
        try:
            from src.nlp.ner.indic_ner import IndicNERInference

            self.indic_ner = IndicNERInference()
        except Exception:
            self.indic_ner = None

    def _init_pretrained_ner(self) -> None:
        """Initialize generic pretrained NER signal (non-domain, optional)."""
        if self.pretrained_ner is not None:
            return
        try:
            from config.settings import settings as _settings
            from src.nlp.ner.pretrained_signal import PretrainedNERSignal

            self.pretrained_ner = PretrainedNERSignal(enabled=_settings.PRETRAINED_NER_ENABLED)
        except Exception:
            self.pretrained_ner = None

    def _init_patterns(self) -> None:
        """Initialize pattern-based extractors with lazy imports."""
        self.regex_entities_fn: Any = None
        self.dictionary_lookup_fn: Any = None
        self.relation_extractor: Any = None
        self._dictionary: Any = None
        self._gem_gazetteer: Any = None

        try:
            from src.nlp.patterns.regex_patterns import extract_regex_entities

            self.regex_entities_fn = extract_regex_entities
        except Exception:
            self.regex_entities_fn = None

        try:
            from src.nlp.patterns.dictionary import DictionaryLookup

            self._dictionary = DictionaryLookup(ontology_dir=str(self.ontology_dir) if self.ontology_dir else None)
        except Exception:
            self._dictionary = None

        try:
            from src.nlp.patterns.gem_catalog import GeMCatalogGazetteer

            self._gem_gazetteer = GeMCatalogGazetteer()
        except Exception:
            self._gem_gazetteer = None

        try:
            from src.nlp.re.extractor import RelationExtractor

            self.relation_extractor = RelationExtractor()
        except Exception:
            self.relation_extractor = None

    def process(
        self,
        text: str,
        token_boxes: list[tuple[int, int, int, int]] | None = None,
        use_joint_model: bool = False,
        language: str | None = None,
    ) -> ExtractionResult:
        """Run full extraction pipeline."""
        if language is None:
            with suppress(Exception):
                from src.nlp.lang_detect import detect_language

                language = detect_language(text)

        all_entities: list[dict] = []
        all_relations: list[dict] = []
        warnings: list[str] = []

        is_hindi = language in ("hi", "mixed")

        if is_hindi:
            if self.indic_ner is None:
                self._init_indic_ner()
            if self.indic_ner:
                try:
                    bert_entities = self.indic_ner.predict(text)
                    all_entities.extend(bert_entities)
                except Exception:
                    pass
        elif self.ner:
            try:
                bert_entities = self.ner.predict(text)
                all_entities.extend(bert_entities)
            except Exception:
                pass

        if self.regex_entities_fn:
            try:
                regex_entities = self.regex_entities_fn(text)
                all_entities.extend(regex_entities)
            except Exception:
                pass

        if self._dictionary:
            try:
                dict_entities = self._dictionary.lookup(text)
                all_entities.extend(dict_entities)
            except Exception:
                pass

        if self._gem_gazetteer:
            try:
                gem_entities = self._gem_gazetteer.extract_materials(text)
                all_entities.extend(gem_entities)
            except Exception:
                pass

        if self.pretrained_ner:
            try:
                pretrained_entities = self.pretrained_ner.predict(text)
                all_entities.extend(pretrained_entities)
            except Exception:
                pass

        all_entities = [self._normalise_entity(e) for e in all_entities]
        merged_entities = self._merge_entities(all_entities)

        if len(merged_entities) > 1:
            try:
                from src.rules.conflict import resolve_conflicts

                bert_ents = [e for e in merged_entities if e.get("source") == "ner"]
                pattern_ents = [e for e in merged_entities if e.get("source") != "ner"]
                if bert_ents and pattern_ents:
                    merged_entities = resolve_conflicts(bert_ents, pattern_ents)
            except Exception:
                pass

        if merged_entities and self.relation_extractor:
            try:
                re_relations = self.relation_extractor.extract(merged_entities, text)
                all_relations.extend([self._relation_to_dict(r) for r in re_relations])
            except Exception:
                pass

        try:
            from src.rules.scope_gap import detect_scope_gaps

            warnings.extend(detect_scope_gaps(merged_entities, all_relations))
        except Exception:
            pass

        avg_confidence = (
            sum(e.get("confidence", 0) for e in merged_entities) / len(merged_entities) if merged_entities else 0.0
        )

        return ExtractionResult(
            entities=merged_entities,
            relations=all_relations,
            warnings=warnings,
            confidence=avg_confidence,
        )

    def _merge_entities(self, entities: list[dict]) -> list[dict]:
        """Merge overlapping entities, keeping highest confidence."""
        if not entities:
            return []

        sorted_entities = sorted(entities, key=lambda e: (e.get("start", 0), e.get("end", 0)))
        merged = []
        used_indices = set()

        for i, entity in enumerate(sorted_entities):
            if i in used_indices:
                continue

            current = entity.copy()
            used_indices.add(i)
            j = i + 1

            while j < len(sorted_entities):
                other = sorted_entities[j]
                if j in used_indices:
                    j += 1
                    continue

                if self._overlaps(current, other):
                    if other.get("type") == current.get("type"):
                        current_len = current.get("end", 0) - current.get("start", 0)
                        other_len = other.get("end", 0) - other.get("start", 0)
                        if (other_len, other.get("confidence", 0)) > (current_len, current.get("confidence", 0)):
                            current = other.copy()
                        else:
                            current["confidence"] = max(
                                current.get("confidence", 0),
                                other.get("confidence", 0),
                            )
                        used_indices.add(j)
                    elif other.get("confidence", 0) > current.get("confidence", 0):
                        current = other.copy()
                        current["confidence"] = other.get("confidence", 0)
                        used_indices.add(j)
                j += 1

            merged.append(current)

        return merged

    def _overlaps(self, e1: dict, e2: dict) -> bool:
        """Check if two entities overlap."""
        start1, end1 = e1.get("start", 0), e1.get("end", 0)
        start2, end2 = e2.get("start", 0), e2.get("end", 0)
        return not (end1 <= start2 or end2 <= start1)

    def _normalise_entity(self, entity: dict) -> dict:
        normalised = entity.copy()
        if "type" not in normalised and "label" in normalised:
            normalised["type"] = normalised["label"]
        normalised.setdefault("confidence", normalised.get("conf", 0.5))
        return normalised

    @staticmethod
    def _entity_to_dict(entity) -> dict:
        return {
            "text": entity.text,
            "type": entity.type.value if hasattr(entity.type, "value") else str(entity.type),
            "start": entity.start,
            "end": entity.end,
            "confidence": entity.confidence,
        }

    @staticmethod
    def _relation_to_dict(relation) -> dict:
        return {
            "type": relation.type,
            "head": relation.head_entity,
            "tail": relation.tail_entity,
            "confidence": relation.confidence,
        }
