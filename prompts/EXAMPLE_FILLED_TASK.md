# TASK: Fix Broken Tests After Wave 1 — Agent-4

## 1. GOAL
Restore the test suite to a clean state (0 collection errors, 292+ passing) so subsequent Wave 2 work can use tests as a regression gate. Currently 2 collection errors in `tests/property/` and `tests/load/`, plus 12 Playwright errors in `tests/e2e/` block CI and produce noisy output.

## 2. CONTEXT
Files to read FIRST:
- `tests/property/test_properties.py` — currently fails: `@st.composite` decorator on a function with zero positional args
- `tests/load/test_locust.py` — currently fails: `RecursionError` on collection from gevent monkey-patch order
- `tests/e2e/test_playwright.py` — currently 12 errors: needs Playwright browsers installed
- `pyproject.toml` — `[tool.pytest.ini_options]` section needs `markers` block

Current state:
- 292 tests pass
- 2 collection errors (property + load)
- 12 e2e errors (playwright browsers not installed)
- Test gate is broken; CI cannot reliably catch regressions

## 3. DELIVERABLES
Create or modify EXACTLY these files:
- [ ] `tests/property/test_properties.py` — fix `@st.composite` signatures to accept `draw` as first arg
- [ ] `tests/load/test_locust.py` — add module-level skip marker, or move file to `bench/load/test_locust.py`
- [ ] `tests/e2e/test_playwright.py` — add `pytestmark = pytest.mark.playwright` at module top
- [ ] `pyproject.toml` — add `markers` block + `addopts = "-m 'not playwright and not load'"`
- [ ] `README.md` — add "Running Playwright tests" subsection under Testing

## 4. STEPS
1. Read all files in Section 2
2. Run `python3 -m pytest tests/ --collect-only 2>&1 | tail -20` and confirm the 2 collection errors
3. Fix `tests/property/test_properties.py`:
   - For every `@st.composite` decorated function, ensure first positional arg is `draw`
   - Example: `@st.composite\ndef bioes_label(draw):\n    return draw(st.sampled_from(BIOES_LABELS))`
4. Fix `tests/load/test_locust.py`:
   - Add at top: `import pytest; pytestmark = pytest.mark.skip(reason="locust load tests run via locust CLI, not pytest")`
5. Fix `tests/e2e/test_playwright.py`:
   - Add at top after imports: `pytestmark = pytest.mark.playwright`
6. Update `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   markers = [
     "playwright: requires playwright browsers (run `playwright install` first)",
     "load: load/stress tests (run via locust CLI, not pytest)",
     "slow: slow tests"
   ]
   addopts = "-m 'not playwright and not load'"
   ```
7. Update README.md with run instructions for playwright
8. Run verification (Section 5)

## 5. VERIFICATION
```bash
# No collection errors
$ python3 -m pytest tests/ --collect-only 2>&1 | tail -3
EXPECT: "X tests collected" with no "errors during collection"

# All non-playwright, non-load tests pass
$ python3 -m pytest tests/ --tb=no
EXPECT: "292+ passed" (no errors)

# Playwright marker works (when explicitly requested)
$ python3 -m pytest tests/e2e -m playwright --collect-only 2>&1 | tail -3
EXPECT: tests collected without errors (even if browsers missing — that's a runtime issue)

# Property tests run (no decoration errors)
$ python3 -m pytest tests/property -v --tb=short 2>&1 | head -20
EXPECT: tests collected and either pass or fail at runtime, not at collection

# Lint clean
$ python3 -m ruff check tests/
EXPECT: All checks passed!
```

## 6. ACCEPTANCE CRITERIA
- [ ] `pytest tests/ --collect-only` reports 0 errors
- [ ] `pytest tests/` (default, no markers) reports 292+ passed, 0 failed
- [ ] Playwright tests still exist and run when invoked with `-m playwright`
- [ ] Load tests still exist and run when invoked separately via locust
- [ ] README documents how to enable each marker
- [ ] No regression: every test that previously passed still passes

## 7. CONSTRAINTS
- DO NOT delete any test files — they have value, just need correct gating
- DO NOT skip tests by `pytest.skip()` inside the body — use module-level `pytestmark` or markers
- DO NOT modify `src/` code — this is a tests-only task
- DO NOT change `config/`
- All marker names must be lowercase, snake_case

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** All Wave 2 tasks (clean test suite is a prerequisite gate)
- **Parallel-safe with:** S4-RealRFQ-Scraping (different files entirely)

## 9. GOTCHAS
- `@st.composite` requires `draw` as the first positional argument — this is a Hypothesis library contract, not optional
- `tests/load/test_locust.py` may import `locust` which monkey-patches gevent on import; skipping at module level avoids triggering this
- Playwright tests need browsers installed via `playwright install chromium` — that's a separate setup step, not part of this task
- Python 3.14 may have additional compatibility issues with hypothesis — if so, document them in the README and add a comment in test_properties.py

## End-of-task report

When done, reply with:
```
## REPORT: Fix Broken Tests

Deliverables:
- tests/property/test_properties.py — modified (fixed @st.composite signatures)
- tests/load/test_locust.py — modified (added skip marker)
- tests/e2e/test_playwright.py — modified (added playwright marker)
- pyproject.toml — modified (markers + addopts)
- README.md — modified (added playwright run instructions)

Verification:
- pytest --collect-only: 0 errors (was 2)
- pytest tests/ default: XXX passed, 0 failed
- pytest tests/e2e -m playwright --collect-only: works
- ruff: clean

Blockers encountered: [none]
Deviations from spec: [none]
Files modified outside spec: [none]
```
