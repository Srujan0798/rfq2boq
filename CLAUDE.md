# CLAUDE.md — RFQ2BOQ Internship Project

Auto-loaded each session. Anyone working on this project reads this first.

---

## 1. What this project is (and is not)

**This is:** Srujan's internship project at SWA Consultancy. One focused NLP tool.

**Input:** construction RFQ tender PDFs (Indian government / private tenders).
**Output:** structured Bill of Quantities (BOQ) — Excel + JSON.
**Pipeline:** PDF → text/table extraction → NER + relation extraction → BOQ assembly → export.

**This is NOT:**

- A SaaS product (no multi-tenancy, no billing, no Stripe)
- An academic publication (no paper drafting, no dataset releases, no benchmarks)
- A patent filing exercise (Srujan handles IP discussions with SWA himself)
- A general AEC platform (no voice input, no CAD/drawing analysis, no sub-domain models)
- An MLOps showcase (no MLflow servers, no A/B routing, no observability stack)
- Anything requiring outbound communication automation (Slack, email, Notion)

**If Claude is tempted to plan or generate prompts for anything in the "is NOT" list above — stop. Ask Srujan first.**

---

## 2. Role boundary

Srujan assigns implementation work to external agents (MiniMax, Codex). Claude:

- Plans, decomposes work
- Generates 9-section task prompts ([prompts/TASK_TEMPLATE.md](prompts/TASK_TEMPLATE.md))
- Audits and verifies deliverables
- Maintains docs

Claude does NOT implement. Doing so wastes Srujan's tokens.

---

## 3. Project structure (slim, scoped)

```text
rfq2boq/
├── src/
│   ├── api/             FastAPI endpoints
│   ├── cli/             Typer CLI
│   ├── domain/          BOQ assembler + validator + confidence
│   ├── export/          Excel + JSON + CSV
│   ├── ingest/          PDF extractor + OCR + table detection
│   ├── nlp/             NER (BERT-BiLSTM-CRF), patterns, relation extraction
│   ├── ontology/        Construction knowledge base loader
│   ├── rules/           Rule engine (units, standards, scope gap, conflict resolution)
│   ├── llm/             Optional Claude/GPT fallback for low-confidence items
│   ├── risk/            Scope-gap + outlier risk scoring
│   └── pipeline.py      Top-level orchestrator
├── config/              Settings + constants (entities, relations, BIOES)
├── tests/               unit / integration / golden / fuzz / e2e
├── scripts/             train, evaluate, demo, scrape
├── data/
│   ├── ontology/        Materials, standards, units, locations JSON
│   ├── rates/           CPWD DSR + state SOR data
│   ├── synthetic/       Generated training PDFs
│   ├── real_rfqs/       Real tender PDFs + gold annotations
│   └── annotations/     BIOES-tagged training data
├── models/              Trained NER checkpoints (gitignored)
├── schema/              JSON schema for BOQ output
├── ui/                  Streamlit UI (the one Srujan demos)
├── deployment/          Dockerfile + docker-compose
├── docs/                Architecture, conventions, user guide, this charter
├── deliverables/        Report + slides (the internship handover artifacts)
└── attic/               Archived out-of-scope code (Neo4j, MLflow, SaaS, voice, etc.)
```

Root files: `README.md`, `CLAUDE.md`, `Makefile`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `.gitignore`.

---

## 4. Entity + relation schema (locked)

- **Entities (8):** MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE
- **Relations (6):** HAS_QUANTITY, HAS_UNIT, AT_LOCATION, OF_GRADE, COMPLIES_WITH, HAS_DIMENSION
- **Tagging:** BIOES (`config.constants.BIOES_LABELS`)
- **Languages:** English (primary). Hindi optional.

Source of truth: `config/constants.py`. Do not invent alternatives.

---

## 5. Task assignment protocol

Every task to an external agent uses the 9-section template ([prompts/TASK_TEMPLATE.md](prompts/TASK_TEMPLATE.md)):

1. GOAL — one sentence
2. CONTEXT — files to read first
3. DELIVERABLES — exact paths
4. STEPS — numbered with exact commands
5. VERIFICATION — commands + expected output
6. ACCEPTANCE CRITERIA — objective pass/fail
7. CONSTRAINTS — hard rules
8. DEPENDENCIES — blocks / blocked-by / parallel-safe
9. GOTCHAS — known pitfalls

Active prompts live in `prompts/wave2/`, `prompts/wave3/`, `prompts/hybrid/`. Out-of-scope prompts are in `prompts/archive/out_of_scope/` (kept for reference, do NOT dispatch).

---

## 6. Current status

Tracker: [docs/wave_status.md](docs/wave_status.md).

**Active blocker:** P1T5 — collect 50 real RFQ PDFs into `data/real_rfqs/raw/` + gold-annotate 20.

**Recent decision:** Removed all SaaS/patent/paper/benchmark/multi-tenant/voice/drawing scope. Project is back to its actual internship goal.

---

## 7. Constraints (every task)

- Imports: `src.` prefix only
- Entities/relations: from `config.constants`
- Tagging: BIOES
- Settings: `config.settings.settings` (env prefix `RFQ2BOQ_`)
- Python: 3.11–3.13 (not 3.14)
- Type hints required on new code
- Every new module gets tests in matching `tests/` subdir

---

## 8. Verification gates

```bash
make lint          # ruff
make type          # mypy
make test          # pytest
python3 -c "from src.nlp.pipeline import NLPPipeline; p=NLPPipeline(); r=p.process('Supply 500 kg cement as per IS 456 M20 grade at ground floor'); assert len(r.entities) > 0"
```

---

## 9. Known gotchas

- BIO vs BIOES — always BIOES
- `data/annotations/*.json` uses `ner_tags`; loaders must handle both `ner_tags` and `labels`
- Synthetic F1 ~99% but real F1 ~67% — report both honestly
- MPS only on this hardware, no CUDA
- Model files gitignored; distribute via Git LFS or external storage
- Python 3.14 has typer/click bug — avoid
- **`resources/` is SACRED.** Contains the SWA-provided project brief PDF, academic papers, knowledge base, video transcripts. **NEVER move, rename, or archive** this folder. It has been mistakenly moved twice and restored both times.

---

## 10. Source-of-truth precedence

1. `config/constants.py` — authoritative schema
2. `docs/conventions.md` — locked rules
3. `docs/` — operational docs
4. `prompts/` (active waves only — `archive/` is read-only history)
5. Agent self-reports — least trusted; always verify

---

## 11. End-of-task REPORT format (agents return this)

```text
## REPORT: [Task]

Deliverables:
- path — created/modified

Verification:
- pytest: N passed, 0 failed
- ruff: clean
- coverage: XX%
- [domain metric]: X.XX

Blockers: [none / list]
Deviations: [none / list]
Outside-spec edits: [none / list]
```

---

**Last updated:** 2026-05-17 — scope refocused to internship core after detecting drift into SaaS/patent/paper territory.
