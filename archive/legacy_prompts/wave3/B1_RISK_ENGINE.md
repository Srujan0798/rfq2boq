# TASK: Risk & Variance Engine — Agent-4

**Wave:** 3 | **Tier:** B | **Priority:** P2

## 1. GOAL
Score every BOQ item and project for risk (price outliers, missing standards, scope gaps, ambiguous entities) so estimators can flag problematic tenders before bidding.

## 2. CONTEXT
Read first:
- `src/domain/cost_estimator.py` — S3 cost engine (provides expected rates)
- `src/domain/models.py` — BoqRow, ExtractionResult schemas
- `src/nlp/calibration.py` — calibrated confidence from A4
- `src/domain/validator.py` — current warning types
- [docs/conventions.md](../../../docs/conventions.md)

Current state: Validator emits warnings but no aggregated risk score. No comparison with historical norms.

## 3. DELIVERABLES
- [ ] `src/risk/__init__.py`
- [ ] `src/risk/engine.py` — `RiskEngine` with `score_item`, `score_project`
- [ ] `src/risk/factors.py` — individual risk factor implementations
- [ ] `src/risk/coverage.py` — completeness analysis (% of typical BOQ items present)
- [ ] `src/risk/recommendations.py` — recommendation generator
- [ ] `src/api/routes/risk_routes.py` — `POST /v1/risk/analyze`
- [ ] `src/export/risk_report.py` — Excel risk heatmap + PDF summary
- [ ] `tests/unit/test_risk_engine.py` — ≥10 tests

## 4. STEPS
1. Read context. Risk factors (each contributes 0-30 points):
   - Price outlier (>2σ from market): +30
   - Missing standard for material: +15
   - Ambiguous entity type (prediction_set size > 1): +10
   - Unknown material (not in ontology): +20
   - Scope gap (material without quantity): +25
   - Quantity outlier (>3σ from typical): +10
   - Low confidence (<0.5): +15
2. Implement engine with factor pipeline
3. Coverage analyzer: compare against template categories (concrete, steel, plumbing, electrical, etc.)
4. Recommendation generator: rule-based suggestions per risk factor
5. API endpoint accepts BOQ JSON, returns risk report
6. Excel exporter: heatmap (red/yellow/green per item), top-10 risks summary
7. Tests

## 5. VERIFICATION
```bash
$ python3 -c "from src.risk.engine import RiskEngine; e = RiskEngine(); s = e.score_item({'material':'unobtainium', 'quantity':1e9, 'unit':'kg', 'confidence':0.2}); assert s > 50, f'Expected high risk, got {s}'"
EXPECT: no AssertionError

$ python3 -m pytest tests/unit/test_risk_engine.py -v
EXPECT: ≥10 passed

$ curl -X POST http://localhost:8000/v1/risk/analyze -H "Content-Type: application/json" -d '{"items":[{"material":"cement","quantity":500,"unit":"kg"}]}' | python3 -c "import sys,json; r=json.load(sys.stdin); assert 'overall_risk' in r and 'top_risks' in r"
EXPECT: no AssertionError
```

## 6. ACCEPTANCE CRITERIA
- [ ] Risk scores in 0-100 range
- [ ] Top-10 risks always populated when items exist
- [ ] Coverage analyzer detects missing waterproofing, finishing, etc.
- [ ] Coverage ≥80% on new code
- [ ] No regression

## 7. CONSTRAINTS
- All imports `src.` prefix
- Risk weights configurable via `config.settings.RISK_WEIGHTS`
- Do NOT couple to specific cost engine — accept rates as input

## 8. DEPENDENCIES
- **Blocked by:** S3 (cost engine), A4 (calibration)
- **Blocks:** None
- **Parallel-safe with:** B2, B3, B4, B5

## 9. GOTCHAS
- Outlier detection needs ≥30 historical items to be meaningful — fall back gracefully
- Scope gap detection from S4 already exists in `src/rules/scope_gap.py` — reuse, don't duplicate
- Risk score is a heuristic, not probability — document this clearly
- Excel heatmap conditional formatting via openpyxl `ColorScaleRule`
