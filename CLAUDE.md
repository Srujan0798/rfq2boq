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
├── src/                 Production code (pipeline, NER, BOQ assembly, export)
├── config/              Settings + constants (entities, relations, BIOES) — locked
├── tests/               unit / integration / golden / fuzz / e2e
├── scripts/             Train, evaluate, audit, intake (see scripts/README.md)
├── data/
│   ├── real_rfqs/       ⭐ 127 real RFQ docs — frozen TEST anchor + TRAIN/DEV pool
│   ├── ontology/        Materials, standards, units, locations JSON
│   └── annotations/     BIOES-tagged training data
├── models/              Trained NER checkpoints (gitignored)
├── schema/              JSON schema for BOQ output
├── ui/                  Streamlit UI
├── docs/                Architecture, conventions, SWA requirements
├── tasks/phase9/        Active plan — the ONLY dispatch source
├── archive/             Legacy files (git-mved, history preserved) — see archive/README.md
├── deliverables/        Report + SWA handoff + closeout (no slides)
├── resources/           SACRED — SWA-provided materials, never move
└── attic/               Archived out-of-scope code
```

Root files: `README.md`, `CLAUDE.md`, `HANDOFF.md`, `Makefile`, `pyproject.toml`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `.gitignore`.

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

Active dispatch lives in `tasks/phase9/`. Historical prompts are in `archive/legacy_prompts/`. Template: `prompts/TASK_TEMPLATE.md`.

---

## 6. Current status

> **⭐ READ FIRST — [docs/CORE_UNDERSTANDING.md](docs/CORE_UNDERSTANDING.md).** The grounded core: architecture is correct (matches the SWA source 1:1); honest re-checked numbers (2026-07-16) are **sacred-10 fidelity auditor 10/10 PASS / broader BOQ 33/33 PASS / partial product row-match ~82% / ~0.43 NER F1** — R1 row-capture is closed on the current corpus, but neural NER accuracy and unseen-document generalization remain open; and **THE CORE PROBLEM** is that the original NER training data was **regex-auto-generated from `resources/` papers/videos, not human-annotated real tenders** — that is why real F1 is ~0.43. Fix = real human-annotated tender gold. Never grade the pipeline against its own output (fake-100% cheat); gold must be independent + human-verified.

> **⭐ CLIENT REQUIREMENTS — [docs/SWA_REQUIREMENTS_2026-06-11.md](docs/SWA_REQUIREMENTS_2026-06-11.md).** Locked outcomes of the 2026-06-11 SWA review meeting: R1 100% data-conversion fidelity (flag, never drop), R2 GeM catalog = authoritative NER reference, R3 ~100 real PDFs incoming (annotation loop must be ready), R4 structure-first extraction for large PDFs, R6 ERP project is a separate repo (never here). Every task must serve these. **Active dispatch: [tasks/phase9/00_README.md](tasks/phase9/00_README.md)** (Phase-9 master plan — supersedes tasks/NEXT_WAVE.md, tasks/sonnet/, and any "wave5"). THIS repo (`~/rfq2boq-phase9`, branch `phase9-final`) is the project; the Desktop repo is contaminated and abandoned as a workspace — see tasks/phase9/01_STATE_OF_THE_WORLD.md §4.

Operational source of truth: [tasks/phase9/00_README.md](tasks/phase9/00_README.md). Brief handoff: [HANDOFF.md](HANDOFF.md). Archived history: [archive/README.md](archive/README.md).

**Active blocker:** real human-annotated tender gold (the data foundation) — per the source's Phase 1: 50+ real RFQ PDFs + 1000+ human BIOES sentences. **The data has arrived: 127 real RFQ documents are already in the repo** (see [data/real_rfqs/ALL_RFQS_README.md](data/real_rfqs/ALL_RFQS_README.md)) — the 10 SWA gold enquiries were the first real instance and remain the frozen TEST anchor, but annotation/training work must cover all 127, not just those 10. See [docs/CORPUS_DEFINITION.md](docs/CORPUS_DEFINITION.md) and `data/real_rfqs/corpus_manifest.json`.

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
- Scope (S1+S2 2026-06): unpriced BOQ only (no Rate/Amount/cost/DSR); no demo/samples/synthetic in data/ (only real_rfqs + attic/); UI upload real tenders only. See docs/CORE_UNDERSTANDING.md and STEP tasks.

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
