# TASK: SpERT Joint NER+RE Model — Agent-2

**Wave:** 2 | **Tier:** A | **Priority:** P1

## 1. GOAL
Replace separate NER + rule-based RE with a learned joint span model (SpERT), enabling better overlapping-entity handling and higher relation F1 from end-to-end training.

## 2. CONTEXT
Read first:
- `src/nlp/ner/bert_ner.py` — current BERT-BiLSTM-CRF NER model (signature reference)
- `src/nlp/re/extractor.py` — current rule-based RE (what we're replacing)
- `src/nlp/re/rules.py` — relation rule definitions (still used as fallback)
- `config/constants.py` — entity types (8), relation types (6), BIOES labels
- `data/annotations/train.json` — current annotation format
- [docs/conventions.md](../../../docs/conventions.md)
- Paper reference: "Span-based Joint Entity and Relation Extraction with Transformer Pre-training" (Eberts & Ulges, 2020)

Current state: NER and RE are pipelined separately. RE is rule-based, no learning from labeled relations.

## 3. DELIVERABLES
- [ ] `src/nlp/spert/__init__.py`
- [ ] `src/nlp/spert/model.py` — `SpERTModel` class
- [ ] `src/nlp/spert/dataset.py` — `SpERTDataset` (converts BIOES → spans)
- [ ] `src/nlp/spert/sampling.py` — negative sampling for non-entity spans / non-relations
- [ ] `src/nlp/spert/inference.py` — `SpERTInference` with `extract(text) -> (entities, relations)`
- [ ] `scripts/convert_bioes_to_spans.py` — preprocess data/annotations/ to data/annotations_spans/
- [ ] `scripts/train_spert.py` — training entry point
- [ ] `scripts/compare_spert_vs_pipeline.py` — F1 + latency comparison
- [ ] `models/spert/` — trained checkpoint + metrics.json
- [ ] `results/spert_comparison.json`
- [ ] `tests/unit/test_spert.py` — minimum 8 tests
- [ ] `src/nlp/pipeline.py` — add `use_joint_model` flag wired to SpERT

## 4. STEPS
1. Read all context files. Confirm `SpERTModel` will use:
   - BERT encoder (`bert-base-cased`)
   - Span representation: concat(BERT[start], BERT[end], max-pool span, span width embedding)
   - Span classifier: 9-way (8 entities + None)
   - Relation classifier: 7-way (6 relations + None) over entity pairs
2. Convert BIOES annotations to span format:
   - Run `python3 scripts/convert_bioes_to_spans.py`
   - Output JSON per split with: `{tokens, entities[(start, end, type)], relations[(head_idx, tail_idx, type)]}`
3. Implement model + dataset + sampling per Section 3 deliverables
4. Train: `python3 scripts/train_spert.py --epochs 20 --batch-size 8 --lr 5e-5 --max-span-size 10`
   - On MPS: pin `device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")`
   - Save to `models/spert/`
5. Evaluate vs current pipeline: `python3 scripts/compare_spert_vs_pipeline.py`
6. Wire into pipeline: `src/nlp/pipeline.py` accepts `use_joint_model: bool = False`
7. Add tests, run verification

## 5. VERIFICATION
```bash
# Training completes
$ ls models/spert/model.pt models/spert/metrics.json
EXPECT: both files exist

# Metrics meet minimum
$ python3 -c "import json; m=json.load(open('models/spert/metrics.json')); assert m['joint_f1'] > 0.5, f'joint_f1={m[\"joint_f1\"]} too low'"
EXPECT: no AssertionError

# Inference works
$ python3 -c "from src.nlp.spert.inference import SpERTInference; s=SpERTInference('models/spert'); ents, rels = s.extract('Supply 500 kg cement IS 456'); assert len(ents) > 0 and len(rels) >= 0"
EXPECT: no AssertionError

# Pipeline can opt into joint model
$ python3 -c "from src.nlp.pipeline import NLPPipeline; p=NLPPipeline(use_joint_model=True); r=p.process('Supply 500 kg cement'); print(len(r.entities))"
EXPECT: positive integer

# Comparison file exists
$ test -f results/spert_comparison.json
EXPECT: exit 0

# All tests pass
$ python3 -m pytest tests/unit/test_spert.py -v
EXPECT: ≥8 passed

# No regression
$ python3 -m pytest tests/ --tb=no
EXPECT: same or higher pass count than before
```

## 6. ACCEPTANCE CRITERIA
- [ ] All commands in Section 5 produce expected output
- [ ] SpERT entity F1 ≥ 0.85 on synthetic test set (lower bar for joint task)
- [ ] SpERT relation F1 ≥ 0.50 on synthetic test set
- [ ] Latency: SpERT inference < 3× current pipeline latency
- [ ] `results/spert_comparison.json` shows per-metric deltas
- [ ] Coverage of new code ≥ 80%
- [ ] No regression in existing tests

## 7. CONSTRAINTS
- All imports use `src.` prefix
- Reuse `config.constants` enums for entity/relation types
- Do NOT modify existing `src/nlp/ner/bert_ner.py` or `src/nlp/re/extractor.py` — keep both available
- Pipeline must default to current behavior (`use_joint_model=False`)
- Do NOT touch `config/constants.py`
- Type hints required

## 8. DEPENDENCIES
- **Blocked by:** A0 (fix broken tests) — for clean baseline
- **Blocks:** A5 (MLflow — needs SpERT as a tracked model)
- **Parallel-safe with:** A2, A3, A4, A6, A7
- **Shared files:** `src/nlp/pipeline.py` (also touched by A3, A4 — sequence with A3 first)

## 9. GOTCHAS
- MPS available, CUDA not — use device detection
- LayoutLM bbox handling NOT applicable here (SpERT is text-only)
- BIOES → span conversion: `S-X` = single-token span of type X; `B-X ... E-X` = multi-token span
- Negative sampling ratio: 1:1 entity:non-entity, 1:5 relation:non-relation (standard SpERT setting)
- Span width embedding helps for long material names — use 25-dim
- 8GB MPS memory limit — keep batch_size ≤ 8 and max_span_size ≤ 10
- Synthetic F1 will be inflated; report real-world F1 too (use `data/real_rfqs/test_gold/` if it exists)
