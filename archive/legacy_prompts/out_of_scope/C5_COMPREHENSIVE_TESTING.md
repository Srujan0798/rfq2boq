# TASK: Comprehensive Testing Suite — Agent-4

**Wave:** 4 | **Tier:** C | **Priority:** P2

## 1. GOAL
Push test maturity to enterprise grade: mutation testing, property-based, load, chaos, full E2E Playwright, performance regression gate in CI.

## 2. CONTEXT
Read first:
- `tests/` — current 302+ tests
- `pyproject.toml` — test config
- [docs/conventions.md](../../../docs/conventions.md) Section 8

Current state: Unit/integration/e2e/golden/fuzz tests exist. Mutation, property-based, load, chaos coverage is thin.

## 3. DELIVERABLES
- [ ] `pyproject.toml` — add mutmut, hypothesis, locust, pytest-playwright config
- [ ] `tests/property/test_pipeline_properties.py` — property-based tests (≥10)
- [ ] `tests/property/test_boq_properties.py` — BOQ invariants (≥8)
- [ ] `tests/chaos/test_chaos_pipeline.py` — chaos engineering tests (≥6)
- [ ] `tests/load/locustfile.py` — Locust scenarios (3 scenarios)
- [ ] `tests/e2e/test_playwright_flows.py` — full user flows (≥10)
- [ ] `tests/performance/test_perf_regression.py` — perf gates
- [ ] `.github/workflows/perf_regression.yml` — fails if p95 > target
- [ ] `mutmut.config.toml` — mutation test config
- [ ] `docs/testing.md` — test runbook

## 4. STEPS
1. Property-based: pipeline never crashes on any text, BOQ schema always valid, confidence in [0,1], dedup idempotent
2. Chaos: random delays in OCR, model inference failures, network partitions — assert graceful degradation
3. Load: 100 concurrent users, ramp 10/s, spike 0→500, soak 50 users for 1h. Pass: p95 < 5s at 100 RPS
4. Playwright: signup → upload → extract → edit → export, multi-browser
5. Performance regression: bench script in CI, fail if p95 regresses > 10%
6. Mutation: target ≥70% mutation score on core modules

## 5. VERIFICATION
```bash
$ python3 -m pytest tests/property -v
EXPECT: ≥18 passed

$ python3 -m pytest tests/chaos -v
EXPECT: ≥6 passed

$ python3 -m pytest tests/performance -v
EXPECT: passes; reports p95

$ locust -f tests/load/locustfile.py --headless -u 100 -r 10 --run-time 30s --host http://localhost:8000
EXPECT: median latency < 5s

$ python3 -m mutmut run --paths-to-mutate src/domain --tests-dir tests/unit
$ python3 -m mutmut results
EXPECT: ≥70% killed

$ python3 -m pytest tests/e2e -m playwright
EXPECT: ≥10 passed (after `playwright install chromium`)
```

## 6. ACCEPTANCE CRITERIA
- [ ] All Section 5 commands succeed
- [ ] Total test count > 400
- [ ] Mutation score ≥70% on `src/domain` and `src/nlp`
- [ ] Load test passes at 100 concurrent users
- [ ] Chaos tests demonstrate graceful degradation
- [ ] Performance regression workflow in CI

## 7. CONSTRAINTS
- All imports `src.` prefix
- Property tests: deterministic seeds in CI
- Load tests: separate target from production (use dedicated env)
- Mutation tests: focus on logic-heavy modules, skip plumbing code

## 8. DEPENDENCIES
- **Blocked by:** A0 (test fix), C1 (perf baseline)
- **Blocks:** None
- **Parallel-safe with:** C2, C3, C4

## 9. GOTCHAS
- Hypothesis `@st.composite` needs `draw` arg — gotcha from A0
- Locust + gevent monkey-patch order — keep load tests out of pytest default
- Playwright in CI: use the playwright Docker image
- Mutation testing is slow — start with one module, expand
- Chaos: use `pytest-asyncio` for async chaos scenarios
- Performance baseline: warmed-up first, then measure
