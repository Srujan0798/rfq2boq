# TASK: C5 Comprehensive Testing — Fix Failures, Complete Coverage

**Wave:** 4 | **Tier:** C | **Priority:** P2

## 1. GOAL

Fix the 2 failing property tests, fix the locust load test, and add the missing test files (locustfile.py, playwright flows, perf regression, mutmut config).

## 2. CONTEXT

Files to read first:
- `tests/property/test_properties.py` — failing tests (test_boq_item_quantity_positive, test_unit_normalization)
- `tests/load/test_locust.py` — broken locust test
- `tests/e2e/test_playwright.py` — existing playwright test
- `tests/e2e/test_full_pipeline.py` — existing e2e test
- `pyproject.toml` — pytest configuration

## 3. DELIVERABLES

Fix:
1. `tests/property/test_properties.py` — fix 2 failing tests
2. `tests/load/locustfile.py` — create proper locust load test
3. `tests/property/test_boq_properties.py` — add BOQ-specific property tests
4. `tests/property/test_pipeline_properties.py` — add pipeline property tests
5. `tests/e2e/test_playwright_flows.py` — add multi-step playwright flows
6. `tests/chaos/test_chaos_pipeline.py` — add chaos tests for pipeline
7. `tests/performance/test_perf_regression.py` — add performance regression tests
8. `mutmut.config.toml` — mutation testing config
9. `.github/workflows/perf_regression.yml` — performance regression CI workflow
10. `docs/testing.md` — testing documentation

## 4. STEPS

1. **Fix `tests/property/test_properties.py` failures:**
   - `test_boq_item_quantity_positive` — likely assertion on quantity <= 0 or type mismatch; debug and fix
   - `test_unit_normalization` — likely unit parsing edge case; debug and fix
   - Run with `-v --tb=long` to see exact failures, then fix

2. **Create `tests/load/locustfile.py`:**
   - `RFQLoadTest` class inheriting from `HttpUser`
   - Endpoints: POST /v1/extract, GET /v1/health, POST /v1/boq
   - Task sets: extraction, health check, full pipeline
   - Spawn: 10-50 users, 30s ramp-up, 2min duration
   - Track: p50/p95/p99 latency, error rate

3. **Create `tests/property/test_boq_properties.py`:**
   - `test_boq_total_positive` — total_amt must be >= 0
   - `test_boq_item_count_match` — item_count must match len(items)
   - `test_boq_no_duplicate_ids` — all item IDs must be unique
   - `test_boq_currency_consistent` — all items must use same currency
   - `test_boq_serializable` — BOQ must JSON-serialize without error

4. **Create `tests/property/test_pipeline_properties.py`:**
   - `test_pipeline_deterministic` — same input → same output (modulo timestamps)
   - `test_pipeline_no_data_leak` — output should not contain unrelated input text
   - `test_pipeline_idempotent` — running twice gives same result

5. **Create `tests/e2e/test_playwright_flows.py`:**
   - `test_full_extraction_flow` — upload RFQ → view entities → export BOQ
   - `test_multi_pdf_flow` — upload 3 PDFs → process → compare results
   - `test_health_check_flow` — hit health → verify all subsystems respond
   - Use `page.goto()`, `page.locator()`, `page.wait_for_selector()` patterns

6. **Create `tests/chaos/test_chaos_pipeline.py`:**
   - `test_pipeline_redis_down` — run pipeline with Redis unavailable
   - `test_pipeline_db_timeout` — run pipeline with DB timeout
   - `test_pipeline_model_missing` — run pipeline when model file is missing

7. **Create `tests/performance/test_perf_regression.py`:**
   - `test_inference_latency_regression` — p95 latency < 500ms for NER inference
   - `test_pdf_parsing_latency` — p95 latency < 2s for 10-page PDF
   - `test_boq_export_latency` — p95 latency < 1s for 100-item BOQ
   - Use `time.perf_counter()` and assert quantiles

8. **Create `mutmut.config.toml`:**
   - Target: `src/` directory
   - Exclude: `tests/`, `docs/`, `scripts/`
   - Suffix: `.py`
   - Run command: `pytest tests/unit/ -x`

9. **Create `.github/workflows/perf_regression.yml`:**
   - Trigger: on PR to main, or weekly schedule
   - Run: `pytest tests/performance/ -v`
   - Comment on PR with results table
   - Fail if p95 > threshold

10. **Create `docs/testing.md`:**
    - Test categories overview
    - Running each suite
    - Coverage requirements
    - Adding new tests

## 5. VERIFICATION

```bash
# Fix and run property tests
python3 -m pytest tests/property/test_properties.py -v --tb=short

# Run all property tests
python3 -m pytest tests/property/ -v --tb=short

# Verify locustfile
python3 -c "import sys; sys.path.insert(0, 'tests/load'); from locustfile import RFQLoadTest; print('OK')"

# Run playwright flows (if browser available)
python3 -m pytest tests/e2e/test_playwright_flows.py -v --tb=short 2>&1 | head -30

# Run perf regression
python3 -m pytest tests/performance/test_perf_regression.py -v --tb=short

# Verify mutmut config
python3 -c "import tomllib; tomllib.load(open('mutmut.config.toml')); print('OK')"

# ruff check
ruff check tests/property/ tests/load/locustfile.py tests/e2e/test_playwright_flows.py tests/chaos/test_chaos_pipeline.py tests/performance/test_perf_regression.py
```

## 6. ACCEPTANCE CRITERIA

- [ ] `tests/property/test_properties.py` — all 7 tests pass
- [ ] `tests/load/locustfile.py` — valid locust file, no import errors
- [ ] `tests/property/test_boq_properties.py` — ≥5 passing tests
- [ ] `tests/property/test_pipeline_properties.py` — ≥3 passing tests
- [ ] `tests/e2e/test_playwright_flows.py` — ≥3 passing tests
- [ ] `tests/chaos/test_chaos_pipeline.py` — ≥3 passing tests
- [ ] `tests/performance/test_perf_regression.py` — ≥3 passing tests
- [ ] `mutmut.config.toml` — valid TOML
- [ ] `.github/workflows/perf_regression.yml` — valid YAML
- [ ] `docs/testing.md` — exists and is non-empty (>100 lines)

## 7. CONSTRAINTS

- Python 3.11–3.13 only
- Type hints required on all new code
- Use `src.` import prefix
- Property tests use `hypothesis` for generative testing
- Playwright tests should handle browser not installed gracefully
- Performance tests should have timeout guards

## 8. DEPENDENCIES

- Blocks: None
- Blocked by: C1 Performance (needs onnx_inference for perf baseline)

## 9. GOTCHAS

- Locust import issue: ensure locust is in PYTHONPATH correctly
- Property test failures often come from assertions on generated data — use `assume()` to skip invalid data
- Playwright flows need `async` page operations in some cases
- Performance tests may need to warm up the model first (first inference is slower)
