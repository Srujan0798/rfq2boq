# TASK: P2T3 — Slim Test Suite — Agent-4

**Phase:** 2 | **Effort:** 0.5 day | **Priority:** P1

## 1. GOAL
Reduce the test suite from full enterprise scale (mutation testing, chaos engineering, load testing, full Playwright E2E) to what a non-technical company actually needs: unit + integration + golden + a smoke E2E. Tests run in ≤30 seconds.

## 2. CONTEXT
Read first:
- `tests/` directory layout
- `pyproject.toml` `[tool.pytest.ini_options]`
- [docs/HYBRID_PLAN.md](../../../docs/HYBRID_PLAN.md) § cut over-engineering
- [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md) § Testing

Current `tests/` has: unit/, integration/, e2e/, golden/, fuzz/, property/, chaos/, load/. The last three are over-engineering for our scale.

## 3. DELIVERABLES
- [ ] `attic/tests/property/` — moved
- [ ] `attic/tests/chaos/` — moved
- [ ] `attic/tests/load/` — moved
- [ ] `tests/e2e/` — kept but trimmed to one smoke flow only
- [ ] `pyproject.toml` — updated markers/addopts (drop `playwright`, `load`, `chaos` markers since their tests are archived)
- [ ] `Makefile` — `test` target unchanged; remove any references to mutation/chaos/load
- [ ] `docs/testing.md` — updated to reflect slim suite

## 4. STEPS
1. Read context.
2. Move:
   ```bash
   git mv tests/property attic/tests/property
   git mv tests/chaos attic/tests/chaos
   git mv tests/load attic/tests/load
   ```
3. Trim `tests/e2e/` to keep only 1 smoke test (one end-to-end flow: PDF → BOQ → Excel). Move others to attic:
   ```bash
   git mv tests/e2e/test_playwright_flows.py attic/tests/e2e/ 2>/dev/null || true
   # keep tests/e2e/test_full_pipeline.py (the simple one)
   ```
4. Update `pyproject.toml` `[tool.pytest.ini_options]`:
   ```toml
   markers = [
     "slow: slow tests (run with --slow)",
   ]
   addopts = ""
   ```
   Remove `playwright` and `load` markers since those tests are gone.
5. Update `docs/testing.md`:
   ```markdown
   # Testing

   Run all tests: `make test`
   With coverage: `make test-cov`

   Layout:
   - tests/unit/        Unit tests for modules
   - tests/integration/ Integration tests for API + pipeline
   - tests/golden/      Tests against frozen ground truth examples
   - tests/fuzz/        Property-based / random input tests
   - tests/e2e/         One smoke test (full PDF → BOQ flow)

   Not in the default suite (moved to attic/tests/):
   - property/  - chaos/  - load/
   ```
6. Make sure `Makefile`'s `clean` doesn't reference deleted markers.
7. Run verification.

## 5. VERIFICATION
```bash
# Slim test layout
$ ls tests/
EXPECT: unit/ integration/ e2e/ golden/ fuzz/ conftest.py (no property/chaos/load)

# Tests run fast
$ time python3 -m pytest tests/unit tests/integration tests/golden tests/fuzz --tb=no
EXPECT: all pass; time <= ~60s (acceptable; <30s ideal)

# No marker errors
$ python3 -m pytest tests/ --collect-only 2>&1 | grep -i "PytestUnknownMarkWarning\|errors during collection"
EXPECT: no output

# E2E smoke runs
$ python3 -m pytest tests/e2e --tb=short
EXPECT: passes

# Lint
$ python3 -m ruff check tests
EXPECT: clean
```

## 6. ACCEPTANCE CRITERIA
- [ ] property/, chaos/, load/ moved to `attic/tests/`
- [ ] `tests/e2e/` has ≤1 active test file (smoke)
- [ ] pyproject markers/addopts cleaned up
- [ ] `docs/testing.md` reflects slim suite
- [ ] `make test` runs and passes
- [ ] No pytest collection warnings or errors

## 7. CONSTRAINTS
- Use `git mv` to preserve history
- DO NOT delete tests outright — archive
- KEEP unit/, integration/, golden/, fuzz/ in active tests
- Coverage target: still ≥80% on active code (may drop slightly since some code is archived too)

## 8. DEPENDENCIES
- **Blocked by:** P2T1, P2T2 (test pruning happens after code pruning)
- **Blocks:** P2T4 (docs update)
- **Parallel-safe with:** None (sequential)

## 9. GOTCHAS
- Property tests need `@st.composite` to take `draw` (gotcha already encoded) — moot now that they're archived
- Locust tests had gevent recursion issue — moot now
- Playwright tests needed browser install — moot now
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md) § Testing
