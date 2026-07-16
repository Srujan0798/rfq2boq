# TASK: P3T1 — Fine-tune Final NER Model — Agent-2

**Phase:** 3 | **Effort:** 3 days | **Priority:** P0 (everything else uses this model)

## 1. GOAL
Produce the final production NER model: ARCBERT (or SciBERT fallback) as base, fine-tuned on a mix of our synthetic data + the 50 real RFQ PDFs collected in P1T5. Target real-world F1 ≥ 75%.

## 2. CONTEXT
Read first:
- `models/arcbert-base/` — from P1T3
- `models/arcbert-ner-v1/` — from P1T3 (fine-tuned on synthetic only)
- `data/annotations/` — synthetic BIOES annotations
- `data/real_rfqs/gold/` — 20 gold-annotated real PDFs from P1T5
- `data/real_rfqs/raw/` — 30 additional unlabeled real PDFs (for self-training)
- `results/arcbert_vs_baseline.json` — baseline numbers
- [docs/HYBRID_PLAN.md](../../../docs/HYBRID_PLAN.md)
- [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md) § ML/training

## 3. DELIVERABLES
- [ ] `scripts/finetune_final_model.py` — combined-data training script
- [ ] `data/annotations_combined/` — merged synthetic + real annotations (train/val/test)
- [ ] `models/rfq2boq-ner-final/` — fine-tuned model + tokenizer + metrics.json
- [ ] `results/final_model_eval.json` — F1 per entity on real test set
- [ ] `src/nlp/pipeline.py` — points to `models/rfq2boq-ner-final/` as default
- [ ] `tests/unit/test_final_model.py` — ≥5 tests
- [ ] `docs/model_card.md` — comprehensive model card (datasets, performance, limitations)

## 4. STEPS
1. Read context.
2. **Combine training data**:
   - Synthetic: `data/annotations/{train,val,test}.json`
   - Real: convert `data/real_rfqs/gold/*.json` to BIOES format
   - Split real into: 14 train, 3 val, 3 test (≈70/15/15)
   - Combined output to `data/annotations_combined/`
   - Re-weight real examples (3× sampling weight) so they don't drown in synthetic noise
3. **Fine-tune from ARCBERT-NER-v1** (already fine-tuned on synthetic):
   - Continue training on combined data for 8 more epochs
   - Lower lr (1e-5) to avoid destroying synthetic knowledge
   - Batch 16, dropout 0.1, BIOES labels from `config.constants`
   - Use MPS device
   - Save to `models/rfq2boq-ner-final/`
4. **Evaluate on real test set only**:
   - Span-level F1 (seqeval) on the 3 held-out real PDFs
   - Per-entity breakdown
   - Compare with: ARCBERT-NER-v1 (synthetic-only), baseline bert-base-cased
   - Save to `results/final_model_eval.json`
5. **Update pipeline**:
   - `src/nlp/pipeline.py` defaults to `models/rfq2boq-ner-final/`
   - Falls back to `models/ner-bert-bilstm-crf-v1/` if final not available
6. **Write model card** `docs/model_card.md`:
   - Architecture: ARCBERT + BiLSTM + CRF
   - Training data: X synthetic + Y real
   - Test data: 3 real RFQs (held-out)
   - F1 numbers (real, synthetic, per entity)
   - Limitations (small real corpus, English+Hindi only, etc.)
   - Intended use vs. out-of-scope
   - License attribution (ARCBERT/SciBERT, IndicBERT, our additions)
7. Tests verify: model loads, predicts, F1 ≥ thresholds.

## 5. VERIFICATION
```bash
# Combined data exists
$ ls data/annotations_combined/train.json data/annotations_combined/val.json data/annotations_combined/test.json
EXPECT: all three exist

# Model trained
$ ls models/rfq2boq-ner-final/metrics.json
EXPECT: exists

# Real F1 ≥ 75%
$ python3 -c "import json; m = json.load(open('results/final_model_eval.json')); assert m['real_test_f1'] >= 0.75, f'real F1 = {m[\"real_test_f1\"]} < 0.75'"
EXPECT: no AssertionError

# Pipeline uses final model
$ python3 -c "
from src.nlp.pipeline import NLPPipeline
p = NLPPipeline()
r = p.process('Supply 500 kg of OPC 43 grade cement as per IS 8112 at ground floor')
assert len(r.entities) >= 4, f'only {len(r.entities)} entities'
print(f'entities: {len(r.entities)}, relations: {len(r.relations)}')
"
EXPECT: ≥4 entities

# Model card exists with required sections
$ for section in "Architecture" "Training Data" "Performance" "Limitations" "Intended Use"; do
    grep -q "$section" docs/model_card.md || echo "MISSING: $section"
  done
EXPECT: no MISSING lines

# Tests
$ python3 -m pytest tests/unit/test_final_model.py -v
EXPECT: ≥5 passed

# No regression
$ python3 -m pytest tests/unit tests/integration tests/golden --tb=no
EXPECT: all pass
```

## 6. ACCEPTANCE CRITERIA
- [ ] Combined dataset built (synthetic + real)
- [ ] Final model trained
- [ ] **Real-world F1 ≥ 0.75** on held-out real test set
- [ ] Pipeline defaults to final model
- [ ] Model card complete and honest about limitations
- [ ] Coverage of new code ≥ 80%

## 7. CONSTRAINTS
- All imports `src.` prefix
- DO NOT remove prior model versions — keep them in `models/` for comparison
- BIOES tagging (do NOT switch to BIO)
- Honest reporting: if real F1 is 0.72, report 0.72 — do not inflate
- Source attribution: cite ARCBERT/SciBERT origin in model card

## 8. DEPENDENCIES
- **Blocked by:** P1T3 (ARCBERT integration), P1T5 (real RFQ collection)
- **Blocks:** P3T2, P3T3, P3T4 (they use the final model)
- **Parallel-safe with:** None (sequential Phase 3 start)

## 9. GOTCHAS
- Real corpus is small (20 gold) — overfitting risk is real; rely on val set for early stopping
- Class imbalance: some entity types (e.g., ACTION) have many examples, others (e.g., GRADE) few — use weighted loss or oversample rare classes
- MPS memory: ARCBERT + BiLSTM + CRF takes ~3GB; reduce batch if OOM
- Don't retrain from scratch — fine-tune the existing v1 to retain learned knowledge
- If real F1 < 0.75: try (a) more aggressive real-data reweighting, (b) self-training on unlabeled real PDFs, (c) better gold annotations
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md) § ML/training
