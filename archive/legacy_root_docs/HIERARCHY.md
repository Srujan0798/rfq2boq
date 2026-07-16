# HIERARCHY — End-to-End Project Map

> **DEPRECATED:** This file is from 2026-05-17. The current project map is [`PROJECT_MAP.md`](../PROJECT_MAP.md) — use that instead. This file is kept for historical context only.

The complete, crystal-clear picture of how this project is organized and how work flows through it.

---

## 1. Entry points (for any new session or person)

```text
HANDOFF.md   ◄── START HERE  (top-level handoff)
   │
   ├──► CLAUDE.md          (project charter, auto-loaded by Claude Code)
   │
   ├──► docs/SCOPE_GUARD.md (refuse-list — drift prevention)
   │
   ├──► docs/wave_status.md (current real status — single source of truth)
   │
   └──► HIERARCHY.md        (this file — the layout)
```

Reading any of these four leads to the others. They cross-reference cleanly.

---

## 2. Project folder tree (annotated)

```text
rfq2boq/
│
├── ROOT FILES — every one justifies its presence
│   ├── CLAUDE.md            ◄ Project charter (auto-loaded)
│   ├── HANDOFF.md           ◄ Entry point for next session
│   ├── HIERARCHY.md         ◄ This file
│   ├── README.md            ◄ Public-facing project description
│   ├── CHANGELOG.md         ◄ Release notes
│   ├── CONTRIBUTING.md      ◄ How to contribute
│   ├── Makefile             ◄ Common dev commands (make test, make push-first)
│   ├── pyproject.toml       ◄ Python package config (single source for deps)
│   ├── requirements.txt     ◄ Generated from pyproject (used only by Dockerfile)
│   ├── Dockerfile           ◄ API container
│   ├── docker-compose.yml   ◄ API + UI services
│   ├── .env.example         ◄ Env var template
│   ├── .gitignore           ◄ Includes lessons learned (2.8 GB duplicate incident)
│   ├── .dockerignore        ◄ Container build context filter
│   └── .pre-commit-config.yaml
│
├── src/                     ◄ Production Python code (16 in-scope modules)
│   ├── api/                 │   FastAPI endpoints (extract, upload, boq, cost, llm, risk, export, review)
│   ├── auth/                │   JWT only (no SaaS multi-tenant)
│   ├── cli/                 │   Typer CLI
│   ├── confidence/          │   Calibration helpers (light, not full A4)
│   ├── domain/              │   BOQ assembler, validator, cost estimator
│   ├── export/              │   Excel + JSON + CSV (CPWD-format ready)
│   ├── ingest/              │   PDF + OCR + Camelot tables
│   ├── labeling/            │   Active learning + review router
│   ├── llm/                 │   Claude/GPT ambiguity resolver (cache-optional)
│   ├── models/              │   Baselines (gazetteer, bert_linear) + inference pipeline
│   ├── nlp/                 │   NER (BERT-BiLSTM-CRF) + patterns + rule RE  ◄ the heart
│   ├── normalize/           │   Unit/dimension canonicalization, dedup
│   ├── ontology/            │   Construction KB loader + OmniClass map (DONE)
│   ├── preproc/             │   Text normalization, sentence split, sections
│   ├── risk/                │   Risk + scope-gap engine (DONE)
│   └── rules/               │   Units, standards, scope-gap, conflict resolution
│   └── pipeline.py          │   Top-level orchestrator
│
├── config/                  ◄ Settings + locked constants (entities, BIOES, relations)
│
├── tests/                   ◄ 353 passing tests
│   ├── unit/                │   per-module tests
│   ├── integration/         │   API + pipeline tests
│   ├── golden/              │   frozen ground-truth tests
│   ├── fuzz/                │   property-based tests
│   ├── e2e/                 │   one smoke test
│   └── conftest.py          │   shared fixtures
│
├── data/                    ◄ All data artifacts
│   ├── annotations/         │   BIOES-tagged training data
│   ├── annotations_combined/│   synthetic + real combined
│   ├── construction_kb.json │   construction knowledge base
│   ├── gold/                │   gold test set
│   ├── ontology/            │   8 entity-type JSON files + omniclass_map.json (DONE)
│   ├── rates/               │   CPWD DSR rate library (currently STUBS — P1T4 will fix)
│   ├── real_rfqs/           │   4 real + 113 synthetic PDFs (P1T5 will reorganize)
│   ├── samples/             │   sample PDFs for demos
│   └── synthetic/           │   300 generated training PDFs
│
├── models/                  ◄ Only the working model (413 MB) — gitignored
│   └── ner-bert-bilstm-crf-v1/
│
├── scripts/                 ◄ 27 in-scope scripts (training, eval, demo, scrape, annotate)
│
├── schema/                  ◄ JSON schemas (BOQ v1)
│
├── ui/                      ◄ Streamlit UI (the one demoed)
│
├── deployment/              ◄ Dockerfile + docker-compose only (observability stack archived)
│
├── docs/                    ◄ All active documentation
│   ├── HYBRID_PLAN.md             │ strategic rationale
│   ├── HYBRID_EXECUTION_PLAN.md   │ 4-week schedule
│   ├── STRATEGIC_REVIEW.md        │ build vs. leverage analysis
│   ├── SCOPE_GUARD.md             │ drift patterns to refuse  ◄ critical
│   ├── WAVE_GOTCHAS.md            │ encoded past failures
│   ├── wave_status.md             │ live progress  ◄ source of truth
│   ├── conventions.md             │ locked code rules
│   ├── orchestration.md           │ orchestrator patterns
│   ├── architecture.md            │ system overview
│   ├── api.md                     │ API reference
│   ├── deployment.md              │ deployment guide
│   ├── operations.md              │ production runbook
│   ├── ONBOARDING.md              │ for new developers
│   ├── USER_GUIDE.md              │ for estimators
│   ├── data_collection.md         │ how to collect real RFQs (legal posture)
│   ├── omniclass_mapping.md       │ P1T1 documentation
│   ├── indicbert.md               │ P1T2 documentation (when done)
│   └── historical/                │ superseded specs (read-only)
│
├── deliverables/            ◄ Internship handover artifacts
│   ├── report/              │   Technical report
│   ├── slides/              │   Presentation
│   ├── paper/               │   (kept but not for academic submission)
│   └── patent/              │   (kept but Srujan handles IP himself)
│
├── prompts/                 ◄ AI task contracts
│   ├── INDEX.md             │ master index ◄ start here
│   ├── TASK_TEMPLATE.md     │ 9-section template
│   ├── EXAMPLE_FILLED_TASK.md
│   ├── hybrid/              │ ACTIVE PATH
│   │   ├── INDEX.md         │
│   │   ├── WORKFLOW.md      │
│   │   ├── phase1/          │ P1T1 (DONE), P1T2, P1T3, P1T4, P1T5
│   │   └── phase3/          │ P3T1–P3T5 (blocked until Phase 1)
│   ├── wave2/               │ HISTORICAL (now under prompts/archive/wave2/)
│   ├── wave3/               │ HISTORICAL (now under prompts/archive/wave3/)
│   └── archive/
│       ├── superseded/      │ Old A3/A4/A6/A8 + Phase 2 prompts (replaced by hybrid plan)
│       └── out_of_scope/    │ ❌ Patent, paper, dataset, benchmark, SaaS, voice, drawing, etc.
│
├── results/                 ◄ Evaluation metrics + figures (only in-scope ones)
│
├── logs/                    ◄ Runtime logs (gitignored content)
│
├── resources/               ◄ SWA-provided project brief + papers + KB + transcripts — DO NOT MOVE
│
└── attic/                   ◄ ALL ARCHIVED CODE (preserved, not deleted)
    ├── src/                 │   Voice, drawing, billing, mlflow, observability, etc.
    ├── tests/               │   Tests for archived modules
    ├── scripts/             │   25 archived scripts
    ├── results/             │   Out-of-scope eval artifacts
    ├── models/              │   8 partial/old model dirs
    ├── deployment/          │   Grafana, Loki, Prometheus, Tempo, Triton, alerts, nginx
    ├── benchmark/, web/, integrations/, paper_root_dup/, patent_root_dup/
    ├── mutmut.config.toml, alembic.ini, PORTFOLIO_SUMMARY.md
    └── README.md            │   What's here and how to restore
```

---

## 3. Dispatch flow (how work actually happens)

```text
┌────────────────────────────────────────────────────┐
│                      OWNER (Srujan)                │
│  - Approves plans                                  │
│  - Copies prompts from prompts/archive/hybrid/phaseN/ (or wave4 for active) │
│  - Pastes to external agent (MiniMax, Codex, …)    │
│  - Verifies Section 5 commands locally             │
│  - Handles all SWA Consultancy communications      │
└──────────────────┬─────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────┐
│         CLAUDE (this assistant, orchestrator)      │
│  - Auto-loads CLAUDE.md + memory                   │
│  - Reads HANDOFF.md, wave_status.md, SCOPE_GUARD   │
│  - Plans, decomposes, writes 9-section prompts     │
│  - Audits agent deliverables                       │
│  - Updates wave_status.md after every delivery     │
│  - REFUSES out-of-scope work (SCOPE_GUARD §2)      │
│  - Never implements production code itself         │
└──────────────────┬─────────────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────┐
│         EXTERNAL AGENTS (MiniMax / Codex / …)      │
│  - Receive copy-pasted 9-section task prompt       │
│  - Implement code in src/, tests/, scripts/, docs/ │
│  - Run Section 5 verification themselves           │
│  - Return REPORT (Section 11 format)               │
└────────────────────────────────────────────────────┘
```

The owner sits at the center. Claude plans + audits. Agents implement.

---

## 4. State-change flow (what triggers what)

```text
Phase 1                  Phase 2                  Phase 3
(plug in free stuff)     (slim codebase)          (polish unique 30%)
        │                       │                         │
   P1T1 OmniClass         DONE 2026-05-17           P3T1 fine-tune NER
   P1T2 IndicBERT      ◄ direct orchestrator       P3T2 polish UI
   P1T3 ARCBERT          cleanup; original         P3T3 polish CPWD Excel
   P1T4 CPWD DSR  ◄──┐   P2T1–P2T4 prompts          P3T4 strengthen conflict
   P1T5 Real RFQs ◄──┤   archived as historical    P3T5 demo video
                    │                                     │
                    │       (no further work needed)     ▼
                    │                                v1.0 handover
                    └──── blockers ──── unlocks Phase 3
```

**Current state:** P1T1 DONE. P1T4 + P1T5 are real blockers. P1T2 + P1T3 are optional.

**You cannot start Phase 3 until P1T4 + P1T5 deliver real data + real rates.**

---

## 5. Information flow (where stuff lives, what reads what)

```text
config/constants.py     ← schema (authoritative)
    │
    └─► src/* (all modules import EntityType, RelationType, BIOES_LABELS from here)
              │
              └─► tests/* (validate against same constants)


data/ontology/*.json   ← knowledge base (materials, standards, units, locations, omniclass)
    │
    └─► src/ontology/loader.py
              │
              └─► src/nlp/pipeline.py (uses ontology for rule RE + validation)


data/rates/cpwd_dsr_2023.json  ← CPWD rates (P1T4 will populate from 70 → 500+)
    │
    └─► src/domain/cost_estimator.py
              │
              └─► src/export/excel_generator.py (CPWD-format BOQ)


data/annotations/*.json + data/real_rfqs/gold/*.json
    │
    └─► scripts/train_ner.py
              │
              └─► models/ner-bert-bilstm-crf-v1/  (production model)
                        │
                        └─► src/nlp/ner/inference.py
                                  │
                                  └─► src/nlp/pipeline.py (NER stage)
```

Every data file has one owner and a clear consumer chain.

---

## 6. Documentation flow (where to look for what)

| Question | Read |
|----------|------|
| What is this project? | `CLAUDE.md` §1 |
| What's the current scope? | `docs/SCOPE_GUARD.md` §3 |
| What's done vs pending? | `docs/wave_status.md` |
| How do I start work? | `HANDOFF.md` §6 |
| How does the orchestrator work? | `docs/orchestration.md` |
| What's the layout? | `HIERARCHY.md` (this file) |
| How do I write a task? | `prompts/TASK_TEMPLATE.md` + `prompts/EXAMPLE_FILLED_TASK.md` |
| What task is next? | `prompts/INDEX.md` (or archive/hybrid/ for historical) |
| What's archived? | `attic/README.md` + `prompts/archive/*/README.md` |
| What are the known pitfalls? | `docs/WAVE_GOTCHAS.md` |
| Should I do task X? | `docs/SCOPE_GUARD.md` §2 (refuse list) |

---

## 7. The single mental model

The project is a **funnel**:

1. **Input:** an RFQ PDF
2. **Pipeline:** PDF → ingest (text+tables+OCR) → preproc → NER → relations → BOQ assembly → cost lookup → validation → export
3. **Output:** an Excel BOQ that an estimator can hand to a contractor

Everything in `src/` exists to serve that funnel. If something doesn't, it's in `attic/`.

**The one rule:** if a proposed task doesn't make the funnel better, it's out of scope. Refuse it. See `docs/SCOPE_GUARD.md`.

---

**Last updated:** 2026-05-17 — final cleanup after 3 scope-drift incidents. Hierarchy stable.
