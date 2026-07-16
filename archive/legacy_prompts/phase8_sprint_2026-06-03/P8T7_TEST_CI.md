# TASK: P8T7 — Test + CI Hardening (fast, green, real) — Agent-QA

**Phase:** 8 | **Priority:** P1 | **Effort:** half–1 day

## 1. GOAL
Make the test suite fast, green, and trustworthy on Python 3.11–3.13, add real end-to-end coverage on all 10 enquiries, and wire a CI gate (lint + type + test) so regressions can't sneak in.

## 2. CONTEXT
838 tests pass but `pytest tests/` can hang ~10 min loading models; heavy tests time out. There's no enforced CI gate, which is partly how cheat commits landed. We want a quick green signal + a slow full lane.

Read first: `Makefile` (lint/type/test targets), `tests/` layout, `pyproject.toml`, `CLAUDE.md` §8 (verification gates).

## 3. DELIVERABLES
- [ ] Test markers: `unit`, `integration`, `slow`/`model` so `make test` runs fast (no model load) and a separate `make test-slow` runs the heavy lane.
- [ ] `tests/e2e/test_all_enquiries.py` — runs `Pipeline().run()` on each of the 10 enquiry source files; asserts no crash and `boq_items > 0` (XLSX) / `>= 0` with no exception (PDF). Marked `slow`.
- [ ] Anti-cheat regression test: assert `scripts/validate_product.py` (and any eval) does NOT build gold from `XLSXRowPipeline`/`Pipeline` (grep-based unit test).
- [ ] Coverage report; raise floor on `src/` core modules.
- [ ] CI config (GitHub Actions `.github/workflows/ci.yml` OR a `make ci` target) running `lint → type → test` on 3.11/3.12/3.13.

## 4. STEPS
1. Add markers; make `make test` exclude `slow` and finish < 5 min.
2. Write the e2e + anti-cheat regression tests (TDD).
3. Add coverage; set a sensible floor.
4. Wire CI (Actions or `make ci`); document how to run it.

## 5. VERIFICATION
```bash
time make test
EXPECT: green, < 5 min, no model-load hang

python3 -m pytest tests/e2e/test_all_enquiries.py -m slow -v
EXPECT: 10 enquiries, all run without exception

python3 -m pytest tests/ -k "anticheat or self_comparison" -v
EXPECT: passes — proves no eval builds gold from the prediction pipeline

make lint && make type
EXPECT: clean
```

## 6. ACCEPTANCE CRITERIA
- [ ] `make test` green and < 5 min on 3.11–3.13; heavy lane separated.
- [ ] e2e test covers all 10 enquiries; anti-cheat regression test present and passing.
- [ ] CI gate runs lint+type+test; documented.

## 7. CONSTRAINTS
- Tests must be honest: no asserting against pipeline-derived "gold"; no `xfail` to hide real failures (mark + explain if truly external).
- Don't delete existing passing tests to make the suite "green"; fix or mark with justification.

## 8. DEPENDENCIES
- **Blocked by:** P8T0. **Parallel-safe with:** P8T2/T3/T6. **Supports:** every other task (gate).

## 9. GOTCHAS
- Cold model load ~140s — keep it out of the fast lane via markers/fixtures.
- 09 GeM is slow (~3.6 min) — mark its e2e case `slow` and give it a generous timeout, or use a page cap for the smoke assertion.
- Python 3.14 is excluded by policy — CI matrix is 3.11/3.12/3.13 only.
