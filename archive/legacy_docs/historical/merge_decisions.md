# Merge Decisions — Three-Layer Unification

Date: 2026-05-15

This document records the 15 conflict resolutions made when unifying the project's three documentation layers into a single execution plan.

## Sources

| Source | Location | Role |
|--------|----------|------|
| A | `plan/` (10 docs) | AUTHORITATIVE frozen architecture specs |
| B | `docs/agent-tasks/` (4 docs) | Detailed code signatures (SUPERSEDED for conflicts) |
| C | `prompts/` (9 docs) | Agent orchestration scaffolding |

## Conflict Resolution Table

| # | Conflict | Source A | Source B | Decision | Rationale |
|---|----------|---------|---------|----------|-----------|
| 1 | Code root | `code/` | `src/` | `code/` | Source A authoritative |
| 2 | NER model | BERT-BiLSTM-CRF | Plain BERT | BERT-BiLSTM-CRF (phased) | Grounded in literature; plain BERT as Week 3 baseline |
| 3 | Tagging | BIOES | BIO | BIOES | CRF supports natively; better for short construction spans |
| 4 | Entity names | DIMENSION, ACTION, GRADE | THICKNESS, WORK_TYPE, SPEC | Source A | IFC-aligned ontology |
| 5 | Relation names | UPPER_SNAKE | snake_case | UPPER_SNAKE | Ontology-typed |
| 6 | RE model | PURE-style ML | Rule-based proximity | Rules first, PURE stretch | No RE training data yet |
| 7 | Frontend | React+Vite | Streamlit | Streamlit | Cut-priority item #9 in risk register |
| 8 | Database | Postgres | File-based | File-based MVP | Less DevOps for internship |
| 9 | Worker | Celery/RQ | Synchronous | Sync MVP | Single-user demo adequate |
| 10 | Ontology | TTL/RDF | JSON | JSON source, TTL generated | Human-editable JSON, derived TTL |
| 11 | Package mgmt | pyproject.toml + uv | requirements.txt | pyproject.toml + uv | Modern standard |
| 12 | Data strategy | 200 real corpus | Synthetic only | Synthetic-first | No real data available |
| 13 | Agent RACI | plan/'s matrix | Different boundaries | plan/ RACI + B's code sigs | Clean ownership + detail |
| 14 | Timeline | 10 weeks | 8 weeks | 8 weeks | User constraint; plan/ allows compression |
| 15 | Module structure | plan/ layout | Different layout | plan/ + `code/domain/` | Pipeline-stage mapping + BOQ assembly |

## ADRs Created

- `0003-streamlit-over-react.md` — Streamlit for MVP (conflict #7)
- `0004-file-based-over-postgres.md` — File-based storage (conflict #8)
- `0005-sync-over-celery.md` — Synchronous processing (conflict #9)
- `0006-synthetic-first-data.md` — Synthetic data strategy (conflict #12)
- `0007-json-ontology-source.md` — JSON as ontology source (conflict #10)
