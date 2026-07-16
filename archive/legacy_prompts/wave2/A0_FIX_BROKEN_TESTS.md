# TASK: Fix Broken Tests After Wave 1 — Agent-4

**Wave:** 2 prerequisite | **Priority:** P0 (blocks all Wave 2 audits)

## 1. GOAL
Restore the test suite to a clean state (0 collection errors) so subsequent Wave 2 tasks can use tests as a regression gate. Currently 2 collection errors + 12 Playwright errors poison every audit.

## 2. CONTEXT
Read first:
- `tests/property/test_properties.py` — fails: `@st.composite` decorator on function with no positional args
- `tests/load/test_locust.py` — fails: `RecursionError` from gevent monkey-patch order
- `tests/e2e/test_playwright.py` — 12 errors: needs Playwright browsers
- `pyproject.toml` — `[tool.pytest.ini_options]` needs `markers` block
- [CLAUDE.md](../../CLAUDE.md) Section 7 for verification gates
- [docs/conventions.md](../../../docs/conventions.md) Section 8 for test conventions

Current state: 292 passing, 2 collection errors, 12 e2e errors. CI cannot run clean.

## 3. DELIVERABLES
- [ ] `tests/property/test_properties.py` — fix every `@st.composite` to accept `draw` as first positional arg
- [ ] `tests/load/test_locust.py` — add `pytestmark = pytest.mark.skip(reason="run via locust CLI")` at module top
- [ ] `tests/e2e/test_playwright.py` — add `pytestmark = pytest.mark.playwright` at module top
- [ ] `pyproject.toml` — add markers block + addopts to exclude playwright/load by default
- [ ] `README.md` — add "Running specialized tests" subsection

## 4. STEPS
1. Run `python3 -m pytest tests/ --collect-only 2>&1 | tail -20` and capture both error tracebacks
2. Edit `tests/property/test_properties.py`: every `@st.composite\ndef strategy_name():` must become `@st.composite\ndef strategy_name(draw):` and use `draw(st.sampled_from(...))` inside
3. Edit `tests/load/test_locust.py`: add at module top:
   ```python
   import pytest
   pytestmark = pytest.mark.skip(reason="locust load tests run via locust CLI, not pytest")
   ```
4. Edit `tests/e2e/test_playwright.py`: add at module top after imports:
   ```python
   import pytest
   pytestmark = pytest.mark.playwright
   ```
5. Add to `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   markers = [
     "playwright: requires playwright browsers (run `playwright install chromium` first)",
     "load: load/stress tests (run via locust CLI)",
     "slow: slow tests"
   ]
   addopts = "-m 'not playwright and not load'"
   ```
6. Add README section explaining how to enable each marker
7. Run verification commands (Section 5)

## 5. VERIFICATION
```bash
# No collection errors
$ python3 -m pytest tests/ --collect-only 2>&1 | tail -5
EXPECT: "N tests collected" with NO "errors during collection"

# Default run passes
$ python3 -m pytest tests/ --tb=no
EXPECT: "292+ passed, 0 failed" (no errors)

# Playwright marker works when explicitly requested
$ python3 -m pytest tests/ -m playwright --collect-only 2>&1 | tail -3
EXPECT: tests collected without errors

# Load marker works
$ python3 -m pytest tests/ -m load --collect-only 2>&1 | tail -3
EXPECT: tests collected without errors

# Lint
$ python3 -m ruff check tests/
EXPECT: All checks passed!
```

## 6. ACCEPTANCE CRITERIA
- [ ] `pytest --collect-only` reports 0 errors
- [ ] `pytest tests/` (default) reports 292+ passed, 0 failed
- [ ] Playwright tests still collectable via `-m playwright`
- [ ] Load tests still collectable via `-m load`
- [ ] README documents marker usage
- [ ] No regression in any previously passing test

## 7. CONSTRAINTS
- DO NOT delete any test files
- DO NOT modify `src/` code
- DO NOT change `config/`
- Marker names: lowercase, snake_case
- Skip at module level via `pytestmark`, not body-level `pytest.skip()`

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** All Wave 2 audit completions
- **Parallel-safe with:** S4-RealRFQ-Scraping

## 9. GOTCHAS
- `@st.composite` requires `draw` as first positional arg — Hypothesis library contract
- `locust` monkey-patches gevent on import; module-level skip avoids triggering
- Playwright tests need browsers installed via `playwright install chromium` — runtime concern, not collection concern
- Python 3.14 may have hypothesis compat issues — document if encountered
