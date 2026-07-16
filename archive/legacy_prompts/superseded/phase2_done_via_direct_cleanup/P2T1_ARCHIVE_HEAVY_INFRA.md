# TASK: P2T1 — Archive Neo4j + SpERT + MLflow — Agent-4

**Phase:** 2 | **Effort:** 0.5 day | **Priority:** P1

## 1. GOAL
Move three heavy infrastructure components into `attic/` (preserved but no longer active) so the production codebase is leaner and the company doesn't need to maintain databases/services they don't use.

## 2. CONTEXT
Read first:
- `docker-compose.yml` — currently runs neo4j + mlflow services
- `src/ontology/graph_ontology.py` — Neo4j ontology client
- `src/nlp/spert/` — SpERT joint NER+RE model
- `src/mlflow/` — MLflow integration code
- [docs/HYBRID_PLAN.md](../../../docs/HYBRID_PLAN.md) — why we're cutting
- [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)

Why archive (not delete): preserves traceability + lets us restore selectively if requirements change.

## 3. DELIVERABLES
- [ ] `attic/neo4j/` — moved: `src/ontology/graph_ontology.py`, related routes, KG migration scripts
- [ ] `attic/spert/` — moved: `src/nlp/spert/` directory + related scripts + tests
- [ ] `attic/mlflow/` — moved: `src/mlflow/` + `scripts/train_ner_mlflow.py` + `scripts/detect_drift.py`
- [ ] `docker-compose.yml` — neo4j + mlflow services removed
- [ ] `src/nlp/pipeline.py` — SpERT path removed (default path is BERT-BiLSTM-CRF)
- [ ] `src/api/routes/kg.py` — moved to attic (or stubbed to return 410 Gone)
- [ ] `attic/README.md` — explains what's here and how to restore
- [ ] `tests/` — any tests for archived code moved alongside

## 4. STEPS
1. Read context.
2. Create `attic/` directory if absent. Add `attic/README.md`:
   ```
   # Attic — Archived components

   Preserved code that's no longer active in production. Restore by
   moving back into src/ + re-enabling in docker-compose.

   - neo4j/      Knowledge graph (replaced by JSON ontology + OmniClass map)
   - spert/      Joint NER+RE model (replaced by BERT-BiLSTM-CRF + rule RE)
   - mlflow/     ML lifecycle (replaced by metrics.json + git for now)
   ```
3. Move directories with `git mv` to preserve history:
   ```bash
   git mv src/ontology/graph_ontology.py attic/neo4j/
   git mv src/api/routes/kg.py attic/neo4j/ 2>/dev/null || true
   git mv src/nlp/spert attic/
   git mv src/mlflow attic/ 2>/dev/null || true
   git mv scripts/train_ner_mlflow.py attic/mlflow/ 2>/dev/null || true
   git mv scripts/detect_drift.py attic/mlflow/ 2>/dev/null || true
   ```
4. Update `docker-compose.yml` — remove `neo4j:` and `mlflow:` service blocks and their volumes.
5. Update `src/nlp/pipeline.py` — remove the `use_joint_model` SpERT branch; default path is BERT-BiLSTM-CRF.
6. Update `src/api/main.py` — remove `kg.py` route inclusion if present.
7. Move any tests that referenced these modules to `attic/tests/` (so they don't pollute the active test run).
8. Run verification.

## 5. VERIFICATION
```bash
# Attic exists with structure
$ ls attic/neo4j attic/spert attic/mlflow attic/README.md
EXPECT: all listed

# No active imports of archived modules
$ grep -rn "from src.nlp.spert\|from src.mlflow\|graph_ontology" src/ tests/ scripts/ config/ 2>/dev/null
EXPECT: no output (empty grep result)

# docker-compose has no neo4j/mlflow
$ grep -E "^\s*(neo4j|mlflow):" docker-compose.yml
EXPECT: no output

# Tests still pass
$ python3 -m pytest tests/unit tests/integration tests/golden --tb=no
EXPECT: all pass (count may be lower due to moved tests)

# Pipeline smoke
$ python3 -c "from src.nlp.pipeline import NLPPipeline; p = NLPPipeline(); r = p.process('Supply 500 kg cement'); assert len(r.entities) >= 0"
EXPECT: no AssertionError

# Lint
$ python3 -m ruff check src
EXPECT: clean (no broken imports)
```

## 6. ACCEPTANCE CRITERIA
- [ ] All three components moved to `attic/`, not deleted
- [ ] `attic/README.md` documents restoration path
- [ ] `docker-compose.yml` slimmed (no neo4j, no mlflow)
- [ ] No active code references the archived modules
- [ ] Tests still pass (any moved tests run from `attic/tests/` if desired)
- [ ] No ruff or import errors

## 7. CONSTRAINTS
- Use `git mv` so history is preserved
- DO NOT delete `attic/` contents
- DO NOT remove tests outright — move them with their code
- After move, the project must still build, run, and pass tests

## 8. DEPENDENCIES
- **Blocked by:** None (Phase 2 starts after Phase 1 done)
- **Blocks:** P2T2 (continues the cleanup)
- **Parallel-safe with:** None (Phase 2 is sequential)

## 9. GOTCHAS
- Removing services from docker-compose may leave orphan volumes — document `docker volume prune` for cleanup
- Some tests may import from archived paths — search before assuming none do
- The `code/` shim doesn't exist anymore (removed in 2026-05 recompose) so no shim to update
- Be careful with `git mv` of directories with __pycache__ — clean first: `find src -name __pycache__ -exec rm -rf {} +`
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md) § Path references
