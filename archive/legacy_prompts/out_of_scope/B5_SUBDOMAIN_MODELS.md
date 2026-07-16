# TASK: Sub-Domain Specialized Models — Agent-2

**Wave:** 3 | **Tier:** B | **Priority:** P2

## 1. GOAL
Train per-domain NER models (buildings, roads, electrical, plumbing) and route documents to the best model based on detected project type.

## 2. CONTEXT
Read first:
- `src/nlp/pipeline.py` — current single-model pipeline
- `data/annotations/train.json` — current mixed-domain training data
- [docs/conventions.md](../../../docs/conventions.md)

Current state: One model handles all construction types. Domain-specific terms (e.g., "bitumen" for roads, "RCC" for buildings) get diluted.

## 3. DELIVERABLES
- [ ] `src/nlp/project_classifier.py` — classifies RFQ into project type
- [ ] `src/nlp/router.py` — routes to appropriate model
- [ ] `models/ner-buildings/` — building-specific NER
- [ ] `models/ner-roads/` — road/highway NER
- [ ] `models/ner-electrical/` — electrical work NER
- [ ] `models/ner-plumbing/` — plumbing NER
- [ ] `scripts/train_subdomain_models.py` — training entry
- [ ] `scripts/partition_data_by_domain.py` — split annotations by domain
- [ ] `tests/unit/test_subdomain_routing.py` — ≥6 tests

## 4. STEPS
1. Project classifier: BERT classification head, 5 classes (buildings, roads, electrical, plumbing, other)
2. Partition existing annotations using keyword matching (initial) + classifier (refined)
3. Train per-domain models from same base BERT-BiLSTM-CRF architecture
4. Router: detect project type → load appropriate model → fall back to general model on unknown
5. Tests verify routing decisions

## 5. VERIFICATION
```bash
$ python3 -c "from src.nlp.project_classifier import ProjectClassifier; c = ProjectClassifier(); t = c.classify('Construction of 4-lane highway'); assert t == 'roads'"
EXPECT: no AssertionError

$ python3 -c "from src.nlp.router import ModelRouter; r = ModelRouter(); m = r.route('highway construction'); print(m)"
EXPECT: model identifier including "roads"

$ python3 -m pytest tests/unit/test_subdomain_routing.py -v
EXPECT: ≥6 passed
```

## 6. ACCEPTANCE CRITERIA
- [ ] Classifier accuracy ≥85% on held-out test
- [ ] Each per-domain model F1 ≥ general model F1 on its domain
- [ ] Router falls back gracefully if domain model missing
- [ ] Coverage ≥80% on new code
- [ ] No regression on existing tests

## 7. CONSTRAINTS
- All imports `src.` prefix
- DO NOT remove or replace existing general model
- Model files stay under 500MB each
- Router decision must be deterministic (no random)

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** None
- **Parallel-safe with:** B1, B2, B3, B4

## 9. GOTCHAS
- Limited per-domain data — start with 100+ docs per domain minimum
- Some RFQs span multiple domains (e.g., metro construction = building + electrical) — handle multi-label
- Roads have very specific terms (bitumen grades VG-30, IRC standards) not in general model
- Plumbing has many UNIT variants (LM, RMT, NOS) requiring careful unit normalization
- Use stratified split: ensure all 5 classes in train + val + test
