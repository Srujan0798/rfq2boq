# TASK: Remove Out-of-Scope API Modules — Agent-P6-B

## 1. GOAL
Remove `src/api/ab_test.py` and `src/api/metrics_observability.py` — both explicitly excluded by the project charter (CLAUDE.md: "not an MLOps showcase — no A/B routing, no observability stack") — without breaking anything that currently depends on `src/api/`.

## 2. CONTEXT
Files to read FIRST:
- `CLAUDE.md` §1 "What this project is (and is not)" — the scope boundary being enforced
- `src/api/main.py` — the FastAPI app; check what it imports from `ab_test.py`/`metrics_observability.py`
- `src/api/ab_test.py`, `src/api/metrics_observability.py` — the files being removed
- `src/cli/main.py:106` — imports `from src.api.main import app`
- `tests/conftest.py:136` and `tests/integration/test_api.py` — both import from `src.api.main`/`src.api.schemas`

Current state: these two modules exist but are out of scope. Nothing in the documented daily workflow (`HANDOFF.md`, `deliverables/SWA_HANDOFF_GUIDE.md`) uses the API layer at all — the UI (`ui/app.py`) calls `src.pipeline.Pipeline` directly. The API + CLI wrapper may still be legitimate as a thin interface, but the A/B testing and observability/metrics sub-modules are not.

## 3. DELIVERABLES
- [ ] Delete `src/api/ab_test.py` and `src/api/metrics_observability.py`
- [ ] `src/api/main.py` — remove any imports/routes/usages of the deleted modules
- [ ] `tests/integration/test_api.py` — remove or update any test that specifically exercises A/B testing or observability metrics; core API tests (health, upload, extract) must still pass
- [ ] Confirm `src/cli/main.py` still works end-to-end after the removal

## 4. STEPS
1. `grep -rn "ab_test\|metrics_observability" --include="*.py" .` — find every reference across the whole repo, not just the obvious ones
2. Remove the two files
3. Fix every import site found in step 1
4. Run the full test suite, fix any breakage caused specifically by this removal (do not fix unrelated pre-existing failures — note them instead)
5. Manually smoke-test the CLI: `PYTHONPATH=. python3.12 -m src.cli.main --help` (or whatever the actual entrypoint invocation is — check `src/cli/main.py`)

## 5. VERIFICATION
```bash
grep -rn "ab_test\|metrics_observability" --include="*.py" .
EXPECT: no output (zero references remain)

PYTHONPATH=. python3.12 -c "from src.api.main import app; print('OK')"
EXPECT: OK (app still imports cleanly without the removed modules)

PYTHONPATH=. python3.12 -m pytest tests/integration/test_api.py -v
EXPECT: all remaining tests pass

PYTHONPATH=. python3.12 -m pytest tests/ --tb=no -q
EXPECT: no new failures vs the pre-task baseline

ruff check src/api/ src/cli/
EXPECT: All checks passed!
```

## 6. ACCEPTANCE CRITERIA
- [ ] Zero remaining references to the deleted modules anywhere in the repo
- [ ] `src/api/main.py` imports and runs cleanly
- [ ] `src/cli/main.py` still works
- [ ] No new test failures introduced by this change
- [ ] `CLAUDE.md` §1 scope boundary is now actually true of the codebase, not just the docs

## 7. CONSTRAINTS
- Do not remove the API layer entirely (`src/api/main.py`, `schemas.py`, `routes/`) unless you find it is completely unused elsewhere — check `src/cli/main.py` dependency first, since that DOES use it
- Do not touch `src/pipeline.py` or `src/ingest/` (owned by P6_01)
- Do not add replacement abstractions or "simplified" versions of what you removed — if it's out of scope, it's just gone

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** P6_04
- **Parallel-safe with:** P6_01, P6_03
- **Shared files:** None overlapping with P6_01/P6_03

## 9. GOTCHAS
- `tests/conftest.py` has a fixture importing `src.api.main` — make sure removing the two modules doesn't break fixture collection for unrelated tests
- Check `pyproject.toml`/`requirements.txt` for dependencies that existed ONLY for A/B testing or metrics (e.g. `mlflow`, `prometheus_client`) — remove those too if nothing else uses them, but verify with a grep first
