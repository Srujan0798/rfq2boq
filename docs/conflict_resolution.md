# Conflict Resolution — Hybrid ML + Rules

## Overview

When extracting entities from construction RFQs, three sources may produce overlapping or conflicting candidates:
1. **NER Model** — BERT-BiLSTM-CRF fine-tuned on synthetic + real data
2. **Pattern Matching** — Regex rules and entity dictionaries
3. **Dictionary Lookup** — Construction ontology terms

The conflict resolver decides which candidate wins when sources disagree.

## Strategy Types

Four resolution strategies, one per entity type or use case:

| Strategy | Used For | Logic |
|----------|----------|-------|
| `RulesFirstStrategy` | QUANTITY, UNIT, STANDARD | Rule confidence > 0.7 → pick rule; else fall back to model |
| `ModelFirstStrategy` | MATERIAL, LOCATION, ACTION | Model confidence > 0.6 → pick model; else fall back to rule |
| `HighestConfidenceStrategy` | DIMENSION, GRADE | Pick whichever has highest calibrated confidence |
| `EnsembleStrategy` | Unknown types | Weighted vote: model × 0.6 + rule × 0.4 |

Additional strategies:
- `ThresholdConfidenceStrategy` — requires 0.15 confidence margin between candidates
- `TypeSpecificStrategy` — per-entity-type thresholds (default)
- `HybridEnsembleStrategy` — type-weighted voting across all candidates

## Per-Entity Thresholds

| Entity Type | Pattern Threshold | Model Threshold | Default Source |
|-------------|-------------------|-----------------|----------------|
| QUANTITY | 0.60 | 0.50 | Rules |
| MATERIAL | 0.70 | 0.60 | Model |
| LOCATION | 0.75 | 0.60 | Model |
| GRADE | 0.80 | 0.50 | Rules |
| STANDARD | 0.65 | 0.55 | Rules |
| DIMENSION | 0.55 | 0.50 | Highest confidence |
| UNIT | 0.70 | 0.55 | Rules |
| ACTION | 0.70 | 0.60 | Model |

## Algorithm

1. Group candidates by overlapping span (any shared character counts as overlap)
2. For each group:
   - Check if entity type majority exists across sources
   - Apply the strategy for that entity type
   - Return the winning candidate
3. Handle non-overlapping candidates as independent additions

## Adding New Strategies

Implement `ConflictStrategy` protocol:

```python
class ConflictStrategy(Protocol):
    def resolve(self, candidates: list[EntityCandidate]) -> EntityCandidate: ...
```

Then register in `STRATEGY_MAP` in `src/rules/conflict.py`:

```python
STRATEGY_MAP: dict[str, type[ConflictStrategy]] = {
    "QUANTITY": RulesFirstStrategy,
    "MATERIAL": ModelFirstStrategy,
    ...
}
```

## Ground Truth

32 curated conflict scenarios in `data/conflict_ground_truth.json` covering all 8 entity types with expected resolutions. Run evaluation:

```bash
python3 -c "
import json
m = json.load(open('results/conflict_resolution_eval.json'))
print(f'Accuracy: {m[\"after_changes\"][\"passing\"]}/{m[\"after_changes\"][\"total_tests\"]}')
"
```

## Limitations

- Rule-based candidates are assigned a fixed 0.9 confidence (no probability available)
- Threshold values are domain-knowledge based and may need adjustment after real RFQ testing
- GRADE and STANDARD benefit most from rules-first due to strong pattern signatures