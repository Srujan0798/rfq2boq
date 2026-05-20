# Phase 1 — Plug in Free Official Stuff

| ID | Task | Owner | Effort |
|----|------|-------|--------|
| [P1T1](P1T1_OMNICLASS_MAPPING.md) | OmniClass mapping | Agent-1 | 2 h |
| [P1T2](P1T2_INDICBERT_INTEGRATION.md) | IndicBERT integration | Agent-2 | 1 day |
| [P1T3](P1T3_ARCBERT_INTEGRATION.md) | ARCBERT integration | Agent-2 | 2–3 days |
| [P1T4](P1T4_CPWD_DSR_RATES.md) | CPWD DSR rates | Agent-1 | 2 days |
| [P1T5](P1T5_REAL_RFQ_COLLECTION.md) | Real RFQ collection (50 PDFs) | Owner+Agent-1 | 2 days |

**All five tasks parallel-safe.** Dispatch in one batch across different agents.

## Exit gate (before Phase 2)

- [ ] `data/ontology/omniclass_map.json` exists with 8 entity types
- [ ] `ai4bharat/indic-bert` loadable; Hindi test passes
- [ ] ARCBERT obtained (or SciBERT fallback documented)
- [ ] `data/rates/cpwd_dsr_2023.json` has ≥500 items
- [ ] `data/real_rfqs/raw/` has ≥50 PDFs
- [ ] `make test` passes (existing tests still green)
