# Phase 2 — Cut Over-Engineering

| ID | Task | Owner | Effort |
|----|------|-------|--------|
| [P2T1](P2T1_ARCHIVE_HEAVY_INFRA.md) | Archive Neo4j + SpERT + MLflow | Agent-4 | 0.5 day |
| [P2T2](P2T2_ARCHIVE_UNUSED_FEATURES.md) | Archive voice / drawing / sub-domain / multi-tenant / benchmark | Agent-4 | 1 day |
| [P2T3](P2T3_SLIM_TESTS.md) | Slim test suite | Agent-4 | 0.5 day |
| [P2T4](P2T4_UPDATE_DOCS.md) | Update docs to slim scope | Agent-4 | 1 day |

**Sequential** — do in order. All Agent-4.

## Exit gate (before Phase 3)

- [ ] `attic/` contains all archived modules
- [ ] `docker-compose.yml` slimmed (no neo4j, no mlflow)
- [ ] `find src -name "*.py" | wc -l` reduced by ≥25%
- [ ] `make test` passes in ≤60s
- [ ] No active doc references archived features
- [ ] CLAUDE.md + README project-structure trees match reality
