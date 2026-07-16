# MASTER PROJECT PLAN
## RFQ → BOQ Scope Extraction using NLP
**Owner:** Srujan (Karna) | **Mode:** Internship | **Plan date:** 2026-05-15
**Inputs honored:** `prompts/archive/UNIVERSAL_ORCHESTRATOR_PROMPT.md` + `RFQ to BOQ Scope Extraction using NLP system.pdf` (all 10 references read)

---

## 0. ONE-PAGE SUMMARY (the only page non-technical readers need)

**Goal.** Build an end-to-end system that converts unstructured construction RFQ documents (PDF, scanned, mixed-layout) into a structured Bill of Quantities (BOQ) — line items with material, quantity, unit, location, standard, and confidence — reducing manual estimation time ≥70% and surfacing scope omissions before they become contractual disputes.

**Approach (3 layers, frozen).**
1. **Ingestion** — pdfplumber for digital PDFs; Tesseract / PaddleOCR for scans; LayoutParser (Detectron2) for table + section detection.
2. **Extraction** — domain-fine-tuned `bert-base-cased` + BiLSTM + CRF span NER (BIO tagging) for entities; span-pair relation extraction (PURE / SpERT style) for linking material↔quantity↔location↔standard; spaCy rule layer as deterministic fallback and validator.
3. **Output** — IFC/ifcOWL-aligned ontology mapping → JSON canonical → Excel BOQ template export; rule-based validators flag missing units, ambiguous quantities, and scope omissions with confidence scores.

**Success bar.** Span-level F1 ≥ 0.85 on held-out RFQs across 8 entity types; relation F1 ≥ 0.75; BOQ line completeness ≥ 90%; end-to-end < 60 s per 20-page RFQ on commodity CPU; reproducible Docker build.

**Scope guardrails.** This is an *extractor*, not a *pricer*. We do not predict unit rates or totals — those come from the user's cost database joined on the canonical BOQ. We do not auto-generate quantities from drawings (out of scope; needs CV + BIM).

**Deliverables (final).** Code repo + Docker image + trained model artifact + annotated 200-RFQ corpus + evaluation report + REST API + minimal web UI + technical report + presentation deck.

---

## 1. ORCHESTRATOR MAP — agents × phases × outputs

```
ORCHESTRATOR (you) — owns architecture, sequencing, integration, verification
├── AGENT-1  Data/Pipeline      → ingestion, OCR, layout, preprocessing, corpus
├── AGENT-2  ML/NLP             → NER, RE, model training, inference engine
├── AGENT-3  Output/Integration → ontology mapping, BOQ schema, exporters, API, UI
└── AGENT-4  Test/Verify/Deploy → pytest, CI, evals, Docker, performance, docs
```

Detailed agent × 9-step assignment matrix in `02_EXECUTION_PLAN.md`.

---

## 2. WHAT THE LITERATURE TELLS US (synthesis of all 10 refs in PDF)

| Ref | Core lesson absorbed into our design |
|---|---|
| **Zhang & El-Gohary (2015)** — Semantic NLP, P=0.969 R=0.944 on building code | Rule-based + ontology gives near-ceiling precision on technical text → use as **deterministic validator + cold-start labels** |
| **Sousa et al. (2024)** — SLR of NLP in construction budgeting | Quantity surveyors map RFQ tasks → internal cost DB *manually*; this is our exact wedge → ship a mapping API |
| **Nabavi et al. (2023)** — NLP + ifcOWL for BIM info inquiry | Anchor entity types in the **IFC ontology** so output downstream-integrates with BIM tools |
| **Helium42 (2026)** — Concrete pipeline benchmarks | OCR 98-99% typed / 78-85% scans; layout 91-96% / 62-78%; NRM3 87-91% on cost-code → these are our **acceptance thresholds** |
| **DesignDrafter (2026)** — Quantity extraction automation | Confirms unit-disambiguation (m³ vs m² vs lm) is the failure mode to guard against |
| **GeeksforGeeks — NER** | Foundational: BIO/BIOES tagging, evaluation conventions |
| **Microsoft NLP Recipes — BERT NER** | Reference fine-tuning recipe (`transformers.Trainer`, AdamW, linear warmup) |
| **Yan et al. (2022)** — Text-mining in construction survey | Common AEC methods: LDA, rule-based, SVM/NB/kNN — kept as baselines |
| **AEC Contracts — Scope risks** | BOQ is legally binding; **scope omission = lawsuit**. Validator MUST emit "missing item" warnings, never silently drop |
| **Zheng et al. (2023)** — Doc-level IE survey | Cross-sentence relations need doc-level RE; plan for long-context (FlanT5-XL or Longformer) for relation extraction |

**Five design takeaways frozen:**
1. **Hybrid is non-negotiable** — pure LLM hallucinates contracts; pure rules don't generalize. Architecture is BERT-CRF + ontology rules + validator.
2. **Ontology as backbone** — IFC/ifcOWL + custom construction terminology ontology; entities and relations are ontology-typed.
3. **Confidence + missing-item alerts** — every BOQ row carries a confidence; every detected scope gap is a structured warning, not a deletion.
4. **Doc-level RE, not sentence-level** — quantity often refers to a material 3 sentences away. Plan Longformer or graph-based RE.
5. **OCR quality gate** — a Helium42-style sanity check on OCR confidence routes scans below threshold to manual review queue.

---

## 3. SYSTEM ARCHITECTURE (preview — full version in `01_ARCHITECTURE.md`)

```
                  ┌──────────────────────────────────────────────┐
                  │              ORCHESTRATION (FastAPI)         │
                  └──┬─────────┬─────────┬─────────┬─────────┬───┘
                     │         │         │         │         │
  ┌──────────────────▼──┐ ┌────▼─────┐ ┌─▼────────┐ ┌▼──────┐ ┌▼────────┐
  │ 1. INGESTION         │ │2. PRE-   │ │3. NER    │ │4. RE  │ │5. RULES │
  │  - pdfplumber        │ │  PROCESS │ │ (BERT-   │ │ (PURE/│ │ + ONTOL │
  │  - tesseract/paddle  │ │  - clean │ │  BiLSTM- │ │ SpERT)│ │ (ifcOWL │
  │  - layoutparser      │ │  - segm. │ │  CRF)    │ │       │ │  + cust)│
  │  - quality gate      │ │  - sent  │ │          │ │       │ │         │
  └──────────────────────┘ └──────────┘ └──────────┘ └───────┘ └─────────┘
                     │         │         │         │         │
                     └─────────┴────┬────┴─────────┴─────────┘
                                    │
                  ┌─────────────────▼───────────────────┐
                  │ 6. CANONICAL JSON (BOQ schema)      │
                  │  - confidence scores                │
                  │  - missing-item warnings            │
                  └─────────────────┬───────────────────┘
                                    │
                  ┌─────────────────▼───────────────────┐
                  │ 7. EXPORTERS  │ 8. WEB UI │ 9. API  │
                  │  Excel/CSV    │  review   │ REST    │
                  └─────────────────────────────────────┘
```

Tech stack frozen: Python 3.11 · PyTorch 2.x · HuggingFace Transformers · spaCy 3 · FastAPI · React+Vite UI · Postgres for corpus/labels · Docker Compose.

---

## 4. 9-STEP EXECUTION FRAMEWORK (preview — full version in `02_EXECUTION_PLAN.md`)

| # | Step | Owner | Output | DoD | Week |
|---|---|---|---|---|---|
| 1 | Project setup | All | repo + env + CI | green build | W1 |
| 2 | Data understanding | A-1 | 50 RFQ corpus + EDA report | schema v1 frozen | W1-2 |
| 3 | Ingestion pipeline | A-1 | `ingest/` module + tests | 95% text recall on golden set | W2-3 |
| 4 | NER + RE models | A-2 | trained checkpoints + eval | span-F1 ≥ 0.85 | W3-6 |
| 5 | Ontology + rules | A-2/A-3 | `rules/` + ifcOWL bindings | 100% rule-test pass | W4-6 |
| 6 | Output generation | A-3 | JSON schema + Excel exporter | round-trip test pass | W6-7 |
| 7 | Testing | A-4 | pytest >80% coverage | all green, perf budget met | W7-8 |
| 8 | Verification (ORC self-attack) | Orch | risk-register closeouts | 0 P0 open | W8 |
| 9 | Deployment + docs | A-4 | Docker, README, API doc, report | reproducible from scratch | W8-10 |

---

## 5. DELIVERABLES (frozen list)

1. `code/` — production code (ingest, models, rules, exporters, API, UI)
2. `data/` — 200-RFQ annotated corpus (BIO + relations + BOQ ground truth)
3. `models/` — fine-tuned BERT-CRF checkpoint + tokenizer + ontology files
4. `notebooks/` — EDA, ablation studies, error analysis
5. `tests/` — unit + integration + golden-set + perf benchmarks
6. `docs/` — README, API ref, architecture, runbook, threat model
7. `report.pdf` — 15-25 page technical report (problem, related work, method, results, ablations, limitations, future work)
8. `slides.pptx` — 12-15 slide presentation deck
9. `docker-compose.yml` + image — reproducible deploy

---

## 6. RISK REGISTER (preview — full version in `03_RISK_REGISTER.md`)

Top 5 (full list = 14 items, each with mitigation + detection signal):
- **R1 OCR noise** on scans → quality gate + manual queue (mitigation: confidence threshold; signal: ocr_conf < 0.8)
- **R2 Cross-sentence relations** missed → Longformer for doc-level RE; signal: RE recall drop on multi-page docs
- **R3 Hallucinated entities** from any LLM fallback → rule-validator must approve every entity; signal: validator rejection rate
- **R4 Unit ambiguity** (m vs m² vs m³) → unit-grammar rule + context window; signal: unit mismatch rate in eval
- **R5 Annotator drift** in corpus → IAA (Cohen's κ) ≥ 0.75 enforced; signal: κ trend per batch

---

## 7. SUCCESS METRICS (target / acceptable / minimum)

| Metric | Target | Acceptable | Minimum |
|---|---|---|---|
| Span-F1 (NER, micro) | 0.90 | 0.85 | 0.80 |
| Relation-F1 | 0.80 | 0.75 | 0.70 |
| BOQ line completeness | 0.95 | 0.90 | 0.85 |
| End-to-end latency / 20pp RFQ | <30s | <60s | <120s |
| Test coverage | 90% | 80% | 70% |
| OCR text recall (scans) | 0.85 | 0.78 | 0.70 |
| Reproducibility (cold Docker → demo) | <10 min | <20 min | <30 min |

---

## 8. WHAT'S IN EACH PLAN FILE

```
plan/
├── 00_PROJECT_PLAN.md       ← THIS FILE — master narrative + index
├── 01_ARCHITECTURE.md       ← layered design, dataflow, module specs, sequence diagrams
├── 02_EXECUTION_PLAN.md     ← 9-step framework, agent×task matrix, weekly milestones
├── 03_RISK_REGISTER.md      ← 14 risks, mitigations, detection signals, reverse-role attack
├── 04_ENTITY_ONTOLOGY.md    ← 8 entity types, 6 relation types, IFC alignment, BIO scheme
├── 05_DATA_AND_ANNOTATION.md← corpus plan, sources, annotation guide, IAA, tools
├── 06_EVALUATION_PROTOCOL.md← train/dev/test splits, baselines, metrics, ablations, error taxonomy
├── 07_REPO_LAYOUT.md        ← file-level repo structure with module responsibilities
├── 08_VERIFICATION_GATES.md ← orchestrator quality gates, ORC reverse-role attack, sign-off checklist
└── 09_PRESENTATION_OUTLINE.md← internship report sections + slide deck outline
```

---

## 9. NEXT ACTIONS (immediately executable)

1. Approve this plan or flag changes.
2. Orchestrator initializes repo + CI + dev container (Step 1, W1).
3. Agent-1 begins corpus acquisition (Step 2, W1).
4. Agent-2 spikes BERT-CRF baseline on a public construction-text corpus while corpus is being built.
5. Weekly checkpoint cadence locked: Friday 30-min retro + Monday plan-update.

---

**Status:** ✅ PLAN COMPLETE — awaiting your go-ahead to begin Step 1.
