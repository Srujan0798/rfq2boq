# TASK: P2T2 — Archive Unused Features — Agent-4

**Phase:** 2 | **Effort:** 1 day | **Priority:** P1

## 1. GOAL
Move features that aren't valuable for the company's non-technical estimators (voice input, drawing analysis, sub-domain models, multi-tenant SaaS billing, public benchmark) into `attic/`. Code becomes ~40% smaller and easier to maintain.

## 2. CONTEXT
Read first:
- `src/voice/`, `src/vision/`, `src/drawing/` — voice + drawing analysis
- `src/auth/`, `src/billing/`, `src/db/` (tenancy parts) — SaaS multi-tenant code
- `benchmark/` — public benchmark code
- `src/nlp/project_classifier.py`, `src/nlp/router.py` — sub-domain routing
- [docs/HYBRID_PLAN.md](../../../docs/HYBRID_PLAN.md) § "What we should CUT entirely"

Why archive: a non-technical company doesn't need voice + drawing + multi-tenancy + public benchmark + 5 sub-domain models. One good model + a clear UI is better.

## 3. DELIVERABLES
- [ ] `attic/voice/` — moved: `src/voice/`, `src/api/routes/voice.py`, related tests
- [ ] `attic/drawing/` — moved: `src/vision/`, `src/drawing/`, models
- [ ] `attic/subdomain/` — moved: `src/nlp/project_classifier.py`, `src/nlp/router.py`, per-domain model dirs
- [ ] `attic/saas/` — moved: `src/auth/tenant.py`, `src/billing/`, tenant DB tables migration
- [ ] `attic/benchmark/` — moved: `benchmark/`
- [ ] `src/nlp/pipeline.py` — remove project-classifier routing; always use the single best model
- [ ] `src/api/main.py` — remove voice / billing / tenant routes
- [ ] Active tests still pass

## 4. STEPS
1. Read context.
2. Move each feature to `attic/`:
   ```bash
   git mv src/voice attic/
   git mv src/vision attic/drawing/vision 2>/dev/null || git mv src/vision attic/
   git mv src/drawing attic/ 2>/dev/null || true
   git mv src/api/routes/voice.py attic/voice/ 2>/dev/null || true
   git mv src/nlp/project_classifier.py attic/subdomain/
   git mv src/nlp/router.py attic/subdomain/
   git mv src/billing attic/saas/billing 2>/dev/null || git mv src/billing attic/
   git mv src/auth/tenant.py attic/saas/ 2>/dev/null || true
   git mv src/api/routes/tenants.py attic/saas/ 2>/dev/null || true
   git mv src/api/routes/billing.py attic/saas/ 2>/dev/null || true
   git mv benchmark attic/
   ```
   (Use `2>/dev/null || true` because some files may not exist; OK to skip.)
3. Keep `src/auth/security.py` (JWT, MFA) — single-tenant auth is fine.
4. Update `src/nlp/pipeline.py` — remove project-classifier routing.
5. Update `src/api/main.py` — remove imports of moved route files.
6. Move tests for these features to `attic/tests/`.
7. Update `attic/README.md` to document the new additions.
8. Run verification.

## 5. VERIFICATION
```bash
# No active imports of archived features
$ grep -rn "from src.voice\|from src.drawing\|from src.billing\|project_classifier\|src.nlp.router\|from benchmark" src/ tests/ scripts/ config/ 2>/dev/null
EXPECT: no output

# Routes don't include voice/billing/tenants
$ grep -E "voice|billing|tenants" src/api/main.py
EXPECT: no output

# Tests still pass
$ python3 -m pytest tests/unit tests/integration tests/golden --tb=no
EXPECT: all pass

# Pipeline smoke
$ python3 -c "from src.nlp.pipeline import NLPPipeline; p = NLPPipeline(); r = p.process('Supply 500 kg cement at ground floor'); assert len(r.entities) > 0"
EXPECT: no AssertionError

# API smoke
$ timeout 5 python3 -m uvicorn src.api.main:app --port 8765 2>&1 | grep -E "Application startup|Uvicorn running"
EXPECT: "Application startup complete." appears

# Line count went down meaningfully
$ find src -name "*.py" | xargs wc -l | tail -1
EXPECT: significantly fewer lines than before (compare to git log)

# Lint
$ python3 -m ruff check src
EXPECT: clean
```

## 6. ACCEPTANCE CRITERIA
- [ ] All five features moved to `attic/`
- [ ] `attic/README.md` updated
- [ ] No active code references the archived features
- [ ] Tests still pass
- [ ] API still starts cleanly
- [ ] `find src -name "*.py" | wc -l` shows meaningful reduction (target ~30–40%)

## 7. CONSTRAINTS
- Use `git mv` (preserves history)
- DO NOT delete attic contents
- KEEP `src/auth/security.py` (JWT) — single-tenant auth is still useful
- KEEP `src/llm/` (LLM ambiguity resolver from B2 is genuinely useful)
- KEEP `src/risk/` (risk engine is a differentiator)

## 8. DEPENDENCIES
- **Blocked by:** P2T1 (continues cleanup)
- **Blocks:** P2T3 (test slimming uses the slimmed codebase)
- **Parallel-safe with:** None (sequential)

## 9. GOTCHAS
- Some imports may be transitive — grep for partial matches too
- The CLI may reference moved commands — check `src/cli/main.py`
- docker-compose may reference moved services (already done in P2T1)
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)
