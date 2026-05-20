# TASK: P3T4 — Strengthen Hybrid ML+Rules Conflict Resolution — Agent-2

**Phase:** 3 | **Effort:** 2 days | **Priority:** P1

## 1. GOAL
Improve the hybrid conflict resolution logic in `src/rules/conflict.py` — when BERT NER, regex patterns, and dictionary lookup disagree on an entity, the resolver currently uses a simple priority rule. Add a smarter rule set + confidence weighting + per-entity-type tuning, leveraging the calibrated confidences from A4.

## 2. CONTEXT
Read first:
- `src/rules/conflict.py` — current conflict resolution
- `src/nlp/pipeline.py` — where conflicts are detected
- `src/nlp/patterns/` — pattern matching producing one set of entities
- `src/nlp/ner/` — model producing another set
- `src/nlp/calibration.py` — calibrated confidences (from A4)
- [docs/HYBRID_PLAN.md](../../../docs/HYBRID_PLAN.md) § "Hybrid ML + rules conflict resolution"
- [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)

Current strategy: rules win for QUANTITY/UNIT/STANDARD; BERT wins for MATERIAL/LOCATION/ACTION; confidence wins for DIMENSION/GRADE. Works ok but doesn't use calibrated confidence.

## 3. DELIVERABLES
- [ ] `src/rules/conflict.py` — enhanced resolution logic with per-type strategies + confidence weighting
- [ ] `src/rules/conflict_strategies.py` — strategy classes for different entity types
- [ ] `data/conflict_ground_truth.json` — hand-curated test cases (≥30 conflict scenarios with expected resolution)
- [ ] `tests/unit/test_conflict_resolution.py` — ≥15 tests using the ground truth
- [ ] `results/conflict_resolution_eval.json` — accuracy on ground truth before/after
- [ ] `docs/conflict_resolution.md` — explains the algorithm

## 4. STEPS
1. Read context.
2. **Design enhanced strategy** in `conflict_strategies.py`:
   ```python
   class ConflictStrategy(Protocol):
       def resolve(self, candidates: list[EntityCandidate]) -> EntityCandidate: ...

   class RulesFirstStrategy: # for QUANTITY, UNIT, STANDARD
       # If any rule-based candidate exists AND its source confidence > 0.7 → pick it
       # Else fall back to model candidate
       ...

   class ModelFirstStrategy: # for MATERIAL, LOCATION, ACTION
       # If model candidate confidence > 0.6 → pick it
       # Else if rule candidate exists → pick it
       # Else lowest-confidence model
       ...

   class HighestConfidenceStrategy: # for DIMENSION, GRADE
       # Pick whichever has highest calibrated confidence
       ...

   class EnsembleStrategy: # fallback for unknown types
       # Weighted vote: model_conf × 0.6 + rule_conf × 0.4
       ...
   ```
3. **Update `conflict.py`**:
   ```python
   def resolve_conflicts(bert_entities, pattern_entities, dictionary_entities) -> list[EntitySpan]:
       # Group candidates by overlapping span
       # For each group:
       #   - Get entity type majority (or ensemble vote)
       #   - Apply strategy for that type
       #   - Return winner
       # Handle non-overlapping additions
   ```
4. **Build ground-truth** `data/conflict_ground_truth.json`:
   - 30+ scenarios: sentence + candidates from each source + expected winner
   - Cover all 8 entity types
   - Include hard cases (rules say QUANTITY but model says UNIT; both could be right)
5. **Evaluate**:
   - Run before/after on ground truth
   - Compute resolution accuracy per entity type
   - Save to `results/conflict_resolution_eval.json`
6. **Document** `docs/conflict_resolution.md`:
   - The 4 strategy types
   - Per-entity-type assignment table
   - How to add new strategies
7. Tests cover: each strategy in isolation, full resolve_conflicts, edge cases (only one candidate, all candidates disagree, etc.).

## 5. VERIFICATION
```bash
# Ground truth exists with ≥30 cases
$ python3 -c "import json; gt = json.load(open('data/conflict_ground_truth.json')); assert len(gt['cases']) >= 30; print(len(gt['cases']))"
EXPECT: prints ≥30

# Strategy module loads
$ python3 -c "from src.rules.conflict_strategies import RulesFirstStrategy, ModelFirstStrategy, HighestConfidenceStrategy, EnsembleStrategy; print('OK')"
EXPECT: prints "OK"

# Resolution improves on ground truth
$ python3 -c "
import json
m = json.load(open('results/conflict_resolution_eval.json'))
assert m['after_accuracy'] > m['before_accuracy'], f\"after={m['after_accuracy']} <= before={m['before_accuracy']}\"
print(f\"improvement: {m['before_accuracy']:.2%} -> {m['after_accuracy']:.2%}\")
"
EXPECT: prints improvement

# Tests
$ python3 -m pytest tests/unit/test_conflict_resolution.py -v
EXPECT: ≥15 passed

# Pipeline still works
$ python3 -c "
from src.nlp.pipeline import NLPPipeline
p = NLPPipeline()
r = p.process('Supply 500 sqm 2mm thick galvanized steel cladding as per IS 2062 Grade 43')
assert len(r.entities) >= 6
"
EXPECT: no AssertionError
```

## 6. ACCEPTANCE CRITERIA
- [ ] ≥30 conflict scenarios in ground truth
- [ ] All 4 strategy classes implemented + tested
- [ ] Resolution accuracy improves vs baseline
- [ ] All 8 entity types have an assigned strategy
- [ ] Coverage ≥ 85% on `src/rules/conflict.py` + `src/rules/conflict_strategies.py`

## 7. CONSTRAINTS
- All imports `src.` prefix
- DO NOT remove the existing simple strategy — keep as fallback
- Use calibrated confidences if available (from A4); else use raw scores
- DO NOT slow the pipeline down by >10% on the standard benchmark

## 8. DEPENDENCIES
- **Blocked by:** P3T1 (final model for testing)
- **Blocks:** None
- **Parallel-safe with:** P3T2, P3T3

## 9. GOTCHAS
- Overlapping spans: need a clear definition of "overlap" (any shared char? majority shared?)
- Some candidates have different entity types — that's a "type conflict" (rare; pick the most confident)
- Calibrated confidences from A4 may not be available for all sources (rules don't have probabilities) — assign rule-based candidates a fixed 0.9 confidence
- This is the genuinely-novel part of our project — make it well-tested and document the design choices
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)
