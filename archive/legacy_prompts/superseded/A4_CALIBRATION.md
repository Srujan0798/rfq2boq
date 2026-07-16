# TASK: Calibrated Confidence + Conformal Prediction — Agent-2

**Wave:** 2 | **Tier:** A | **Priority:** P1

## 1. GOAL
Replace heuristic confidence with proper uncertainty quantification: temperature scaling (calibration), MC Dropout (epistemic uncertainty), and conformal prediction (coverage guarantee). Enables principled routing of low-confidence entities to human review.

## 2. CONTEXT
Read first:
- `src/domain/confidence.py` — current heuristic confidence
- `src/nlp/ner/bert_ner.py` — model returning logits
- `src/nlp/pipeline.py` — where confidence is assembled
- [docs/conventions.md](../../../docs/conventions.md)
- References: "On Calibration of Modern Neural Networks" (Guo et al. 2017), "A Tutorial on Conformal Prediction" (Angelopoulos & Bates 2022)

Current state: confidence is computed via component scoring (entity_conf × field_completeness × ontology_match). No probabilistic guarantee.

## 3. DELIVERABLES
- [ ] `src/nlp/calibration.py` — `TemperatureScaler` class
- [ ] `src/nlp/uncertainty.py` — `MCDropoutEstimator` class
- [ ] `src/nlp/conformal.py` — `ConformalPredictor` class
- [ ] `scripts/calibrate_model.py` — fits temperature on val set, saves to `models/.../temperature.json`
- [ ] `scripts/calibration_plot.py` — generates reliability diagram
- [ ] `deliverables/report/figures/calibration_before.png` — pre-calibration reliability
- [ ] `deliverables/report/figures/calibration_after.png` — post-calibration reliability
- [ ] `src/labeling/review_router.py` — routes low-conf entities to review queue
- [ ] `src/nlp/pipeline.py` — extended to attach `(point_pred, calibrated_conf, epistemic_unc, prediction_set)` per entity
- [ ] `src/api/routes/extract.py` — supports `?return_uncertainty=true` query param
- [ ] `tests/unit/test_calibration.py` — minimum 8 tests

## 4. STEPS
1. Read context files
2. Implement `TemperatureScaler` (fit T to minimize NLL on val set via LBFGS)
3. Implement `MCDropoutEstimator` (10 stochastic forward passes with dropout enabled at inference, return mean + std)
4. Implement `ConformalPredictor` (split conformal: compute nonconformity scores on calib set, return prediction sets at α=0.1)
5. Fit temperature: `python3 scripts/calibrate_model.py --model models/ner-bert-bilstm-crf-v1 --val data/annotations/val.json`
6. Generate reliability diagrams: `python3 scripts/calibration_plot.py` (writes to `deliverables/report/figures/`)
7. Extend pipeline to attach uncertainty to each entity
8. Add review router: confidence < 0.5 OR prediction_set size > 1 → flag for review
9. Update API: `?return_uncertainty=true` returns full uncertainty data
10. Run verification

## 5. VERIFICATION
```bash
# Temperature fitted
$ ls models/ner-bert-bilstm-crf-v1/temperature.json
EXPECT: exists

$ python3 -c "import json; t=json.load(open('models/ner-bert-bilstm-crf-v1/temperature.json'))['temperature']; assert 0.1 < t < 10, f'T={t} out of sane range'"
EXPECT: no AssertionError

# Reliability plots exist
$ ls deliverables/report/figures/calibration_before.png deliverables/report/figures/calibration_after.png
EXPECT: both exist

# Pipeline returns uncertainty
$ python3 -c "from src.nlp.pipeline import NLPPipeline; p = NLPPipeline(); r = p.process('Supply 500 kg cement', return_uncertainty=True); assert hasattr(r.entities[0], 'epistemic_uncertainty') or 'epistemic_uncertainty' in r.entities[0]"
EXPECT: no AssertionError

# Review router works
$ python3 -c "from src.labeling.review_router import ReviewRouter; r = ReviewRouter(); flagged = r.flag([{'text':'X','confidence':0.3}, {'text':'Y','confidence':0.9}]); assert len(flagged) == 1"
EXPECT: no AssertionError

# Tests
$ python3 -m pytest tests/unit/test_calibration.py -v
EXPECT: ≥8 passed

# No regression
$ python3 -m pytest tests/ --tb=no
EXPECT: same or higher pass count
```

## 6. ACCEPTANCE CRITERIA
- [ ] All Section 5 commands succeed
- [ ] Expected Calibration Error (ECE) decreases after temperature scaling
- [ ] Conformal prediction sets achieve ≥90% empirical coverage at α=0.1 on test set
- [ ] Review router flags between 5%–30% of entities (sanity range)
- [ ] Coverage of new code ≥ 80%
- [ ] No regression in tests

## 7. CONSTRAINTS
- All imports use `src.` prefix
- DO NOT modify model weights — calibration is post-hoc
- DO NOT change `config/constants.py`
- Backward compatibility: `return_uncertainty=False` (default) preserves current API shape

## 8. DEPENDENCIES
- **Blocked by:** A0 (test fix), A3 (calibrate on best model — but can run on current model if A3 not done)
- **Blocks:** B1 (risk engine uses calibrated confidence)
- **Parallel-safe with:** A1, A2, A5, A6, A7
- **Shared files:** `src/nlp/pipeline.py` (also A1, A3) — sequence after A3, before A1 wiring

## 9. GOTCHAS
- Temperature scaling needs held-out validation set — use `data/annotations/val.json`, NOT test set (would leak)
- MC Dropout requires `model.train()` mode (dropout active) but `with torch.no_grad()` — careful state management
- Conformal needs separate calibration set — split val 80/20 into fit/calib if no dedicated set exists
- Reliability diagram needs binning (15 bins standard)
- Per-entity coverage may differ — track per-class
- Pipeline must accept `return_uncertainty` kw without breaking existing call sites
