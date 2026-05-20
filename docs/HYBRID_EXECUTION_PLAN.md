# Hybrid Execution Plan — Internship-Scoped

Master execution doc for the RFQ2BOQ internship project. All work below is **directly required** for the RFQ→BOQ extraction tool. Anything outside this scope was removed on 2026-05-17 — see `CLAUDE.md` §1.

---

## Schedule

| Week | Phase | Theme | Tasks |
|------|-------|-------|-------|
| 1 | Phase 1 | Plug in free official tools | P1T1–P1T5 (5 tasks, parallel-safe) |
| 2 | Phase 2 | Slim codebase (move archived code into attic/) | P2T1–P2T4 (sequential) |
| 3–4 | Phase 3 | Polish unique 30% (final model, UI, Excel, demo) | P3T1–P3T5 |

**Total: 14 tasks, ~4 weeks.**

---

## Phase 1 — Plug in free official tools (Week 1)

| Task | Owner | Effort | Status |
|------|-------|--------|--------|
| [P1T1 — OmniClass mapping](../prompts/hybrid/phase1/P1T1_OMNICLASS_MAPPING.md) | Agent-1 | 2 h | PENDING |
| [P1T2 — IndicBERT (Hindi)](../prompts/hybrid/phase1/P1T2_INDICBERT_INTEGRATION.md) | Agent-2 | 1 day | PENDING |
| [P1T3 — ARCBERT base model](../prompts/hybrid/phase1/P1T3_ARCBERT_INTEGRATION.md) | Agent-2 | 2–3 days | PENDING |
| [P1T4 — CPWD DSR rate library](../prompts/hybrid/phase1/P1T4_CPWD_DSR_RATES.md) | Agent-1 | 2 days | PENDING |
| [P1T5 — 50 real RFQ PDFs](../prompts/hybrid/phase1/P1T5_REAL_RFQ_COLLECTION.md) | Owner + Agent-1 | 2 days | PARTIAL |

All five parallel-safe.

**Exit gate:**

- `data/ontology/omniclass_map.json` exists with all 8 entities mapped
- IndicBERT loads + Hindi smoke test passes
- ARCBERT downloaded (or SciBERT fallback documented)
- `data/rates/cpwd_dsr_2023.json` has ≥500 line items
- `data/real_rfqs/raw/` has ≥50 verified-real PDFs + `manifest.csv` + 20 gold annotations
- `make test` green

---

## Phase 2 — Slim codebase (Week 2)

| Task | Owner | Effort | Status |
|------|-------|--------|--------|
| [P2T1 — Archive Neo4j + SpERT + MLflow](../prompts/archive/superseded/phase2_done_via_direct_cleanup/P2T1_ARCHIVE_HEAVY_INFRA.md) | Agent-4 | 0.5 day | **DONE** (direct cleanup) |
| [P2T2 — Archive voice / drawing / sub-domain / multi-tenant / benchmark](../prompts/archive/superseded/phase2_done_via_direct_cleanup/P2T2_ARCHIVE_UNUSED_FEATURES.md) | Agent-4 | 1 day | **DONE** (direct cleanup) |
| [P2T3 — Slim test suite](../prompts/archive/superseded/phase2_done_via_direct_cleanup/P2T3_SLIM_TESTS.md) | Agent-4 | 0.5 day | **DONE** (direct cleanup) |
| [P2T4 — Update docs to slim scope](../prompts/archive/superseded/phase2_done_via_direct_cleanup/P2T4_UPDATE_DOCS.md) | Agent-4 | 1 day | **DONE** (direct cleanup) |

Sequential.

**Exit gate:**

- `attic/` populated; old modules no longer importable from active code
- `find src -name "*.py"` reduced ≥25%
- `make test` passes in ≤60 s
- README + CLAUDE.md trees match `ls -d src/*/`

---

## Phase 3 — Polish unique 30% (Weeks 3–4)

| Task | Owner | Effort | Status |
|------|-------|--------|--------|
| [P3T1 — Fine-tune final NER (ARCBERT + real data)](../prompts/hybrid/phase3/P3T1_FINETUNE_FINAL_MODEL.md) | Agent-2 | 3 days | PENDING |
| [P3T2 — Polish Streamlit UI](../prompts/hybrid/phase3/P3T2_POLISH_UI.md) | Agent-3 | 2 days | PENDING |
| [P3T3 — Polish Excel export (CPWD format)](../prompts/hybrid/phase3/P3T3_POLISH_EXCEL_EXPORT.md) | Agent-3 | 2 days | PENDING |
| [P3T4 — Strengthen conflict resolution](../prompts/hybrid/phase3/P3T4_STRENGTHEN_CONFLICT.md) | Agent-2 | 2 days | PENDING |
| [P3T5 — Demo video](../prompts/hybrid/phase3/P3T5_DEMO_VIDEO.md) | Owner | 1 day | PENDING |

P3T1 first; then T2/T3/T4 parallel; then T5 last.

**Exit gate:**

- Real-world F1 ≥ 75% on gold set
- Streamlit UI usable by non-technical estimator
- Excel output matches CPWD format
- 2–5 min demo video recorded
- README + final report finalized
- Git tagged `v1.0-handover`

---

## What does NOT happen any more

After the 2026-05-17 scope reset, the following are explicitly out of scope and NOT planned:

- Patent filing / IP paperwork (Srujan handles with SWA)
- Academic paper drafts, journal submissions
- Public dataset releases (HuggingFace Hub etc.)
- Public benchmark + leaderboard hosting
- Multi-tenant SaaS, Stripe billing, team roles
- Voice input
- Drawing / CAD / blueprint analysis
- Per-domain specialized models
- MLflow tracking servers, A/B testing infrastructure
- Comprehensive security audit (OWASP scan, pen tests, etc. beyond basic JWT)
- Observability stack (Prometheus + Grafana + Loki + Tempo + Sentry)
- Mutation / chaos / load testing
- Email / Slack / Notion automation to SWA

If anyone (agent or human) brings these up — point at this file and the CLAUDE.md §1.
