# EXECUTION PLAN
## 9-Step Framework × 4 Agents × 10-Week Internship Calendar

Calendar assumes a 10-week internship. Compress to 8 by dropping Step 9's stretch items, expand to 12 by adding LLM-RAG side-experiment in W11-12.

---

## STEP 1 — PROJECT SETUP  (Week 1)

**Goal.** Repo + dev environment + CI green on a "hello pipeline" stub.

| Owner | Task | Output | DoD |
|---|---|---|---|
| Orch | Initialize repo, set MIT license, write `README.md` skeleton | `code/` tree | branch protection on main |
| A-1 | Author `pyproject.toml`, lock with `uv`/`poetry`, pin Python 3.11 | env file | `uv sync` clean |
| A-1 | Dev Container `.devcontainer/devcontainer.json` with VS Code + extensions | container | container builds in CI |
| A-4 | GitHub Actions: `lint → type → test → build` | `.github/workflows/ci.yml` | first PR passes CI |
| A-4 | Pre-commit (ruff, black, mypy, end-of-file-fixer) | `.pre-commit-config.yaml` | `pre-commit run -a` green |
| A-3 | Skeleton FastAPI `/healthz`, Dockerfile, compose | running container | `curl :8080/healthz` = 200 |
| Orch | `CONTRIBUTING.md`, `CHANGELOG.md`, conventional-commits enforced | docs | first commit follows |

**Milestone M1 (Fri W1):** repo cloneable → `make demo` returns canned BOQ.

---

## STEP 2 — DATA UNDERSTANDING  (Week 1-2, parallel with Step 1)

**Goal.** 200-document corpus identified + EDA + schema v1 frozen.

| Owner | Task | Output | DoD |
|---|---|---|---|
| A-1 | Source RFQs: CPWD India, NHAI, World Bank tenders, GeM, EU TED open data | `data/raw/*.pdf` | 200 PDFs, ≥30% scanned |
| A-1 | EDA notebook: page counts, OCR-needed %, table density, language, language mix | `notebooks/01_eda.ipynb` | committed with cell outputs |
| A-2 | Existing BOQ samples for ground-truth (paired RFQ↔BOQ) | `data/gold/pairs.csv` | ≥30 paired |
| A-3 | Excel templates we must output to | `templates/boq_template.xlsx` | reviewed by SME |
| Orch | Freeze entity + relation taxonomy v1 | `04_ENTITY_ONTOLOGY.md` | sign-off |

**Milestone M2 (Fri W2):** corpus exists; schema v1 frozen.

---

## STEP 3 — CORE COMPONENT A: INGESTION PIPELINE  (Week 2-3)

**Goal.** Robust `ingest/` module that handles digital + scanned + mixed PDFs.

| Owner | Task | Output | DoD |
|---|---|---|---|
| A-1 | `ingest/pdf_parser.py` (pdfplumber + fallback) | module | unit tests on 5 PDFs |
| A-1 | `ingest/ocr.py` (Tesseract + PaddleOCR), language auto-detect | module | OCR conf reported |
| A-1 | `ingest/layout.py` (LayoutParser) | module | table cells extracted from sample |
| A-1 | `ingest/quality_gate.py` — confidence + coverage thresholds | module | unit-tested branching |
| A-4 | Integration test: 10 mixed PDFs → `doc.json` each | test suite | all green |
| A-4 | Performance: < 15 s / 20pp PDF (digital), < 60 s (scanned) | benchmark log | logged in `perf.md` |

**Milestone M3 (Fri W3):** any RFQ → structured `doc.json` with quality scores.

---

## STEP 4 — CORE COMPONENT B: ML / NLP  (Week 3-6, the longest)

**Goal.** Trained NER + RE models meeting acceptance thresholds.

### 4a — Annotation (W3-5)
| Owner | Task | Output | DoD |
|---|---|---|---|
| A-2 | Annotation guidelines doc (with BIOES examples for all 8 entities) | `docs/annotation_guide.md` | reviewed by 2 SMEs |
| A-2 | Stand up Label Studio (or doccano) instance | running service | accessible to annotators |
| A-2 | 200-doc annotation campaign (sentences pre-segmented, ~10k sentences) | `data/annotations/` | IAA Cohen's κ ≥ 0.75 |
| A-2 | Relation annotation pass (entity pairs within ±3 sentences) | `data/annotations/relations.jsonl` | 5k+ pairs |

### 4b — Modeling (W4-6)
| Owner | Task | Output | DoD |
|---|---|---|---|
| A-2 | Baselines: spaCy CNN, regex+gazetteer | `models/baselines/` | report card per model |
| A-2 | BERT-base-cased + BiLSTM-CRF training script | `models/ner/train.py` | reproducible from CLI |
| A-2 | Hyperparameter sweep: lr, dropout, BiLSTM dim, batch | sweep log | best config chosen on dev |
| A-2 | PURE-style RE model with entity markers | `models/re/train.py` | F1 reported |
| A-2 | Inference engine `models/infer.py` (ONNX-compatible) | module | CPU latency budget met |
| A-2 | Error-analysis notebook | `notebooks/04_errors.ipynb` | top-10 error types named |
| A-4 | Model-card written | `models/MODEL_CARD.md` | published with checkpoint |

**Milestone M4 (Fri W6):** span-F1 ≥ 0.85 dev, relation-F1 ≥ 0.75 dev.

---

## STEP 5 — CORE COMPONENT C: RULES + ONTOLOGY  (Week 4-6, parallel with 4b)

**Goal.** Deterministic validator that catches what ML misses.

| Owner | Task | Output | DoD |
|---|---|---|---|
| A-2 | Unit-grammar parser (`pyparsing` or `lark`) | `rules/units.py` | passes 100 unit test cases |
| A-2 | Standards regex registry (IS/BS/EN/ASTM/ACI) | `rules/standards.py` | recognized across corpus |
| A-3 | Construction Terms Ontology (CTO) draft in Turtle | `ontology/cto.ttl` | 500+ concepts |
| A-3 | ifcOWL integration (subset) | `ontology/ifcOWL.ttl` (vendored) | resolver works |
| A-2 | Conflict-resolution policy (ML vs rules) | `rules/conflict.py` | unit-tested |
| A-2 | Co-occurrence rules → SCOPE_GAP_WARNING emission | `rules/scope_gap.py` | golden gaps detected |
| A-4 | Rule-engine test suite (≥200 cases) | `tests/rules/` | 100% pass |

**Milestone M5 (Fri W6):** rule layer catches 90%+ of seeded errors in test set.

---

## STEP 6 — OUTPUT GENERATION  (Week 6-7)

**Goal.** Canonical JSON → Excel / CSV / JSON exporters with confidence.

| Owner | Task | Output | DoD |
|---|---|---|---|
| A-3 | `schema/boq.v1.json` (JSON Schema) + Pydantic models | schema + models | `pydantic` validates |
| A-3 | `export/excel.py` against template, with confidence column + warnings column | exporter | round-trip test |
| A-3 | `export/csv.py`, `export/json.py` | exporters | identical row count |
| A-3 | Minimal review UI (React) — table view, edit-in-place, approve/reject | `ui/` | usable in browser |
| A-4 | E2E test: PDF in → xlsx out, schema-validated | test | passes in CI |

**Milestone M6 (Fri W7):** demoable PDF → Excel with confidences + warnings.

---

## STEP 7 — TESTING  (Week 7-8)

**Goal.** 80%+ coverage + performance budget proven.

| Owner | Task | Output | DoD |
|---|---|---|---|
| A-4 | Unit tests for every module | `tests/unit/` | ≥80% line coverage |
| A-4 | Integration tests on golden set (20 RFQs with manual ground truth) | `tests/golden/` | all green |
| A-4 | Performance benchmarks (`pytest-benchmark`) | `bench/` | latency budget met |
| A-4 | Fuzz tests — malformed PDFs, empty pages, password-protected | `tests/fuzz/` | graceful errors only |
| A-4 | Load test — 100 concurrent extractions | `tests/load/` | no crashes, p95 < 90s |
| A-2 | Model regression test — checkpoint hash + dev-F1 enforced in CI | gate in CI | blocks regressions |

**Milestone M7 (Fri W8):** all tests green; latency proven; coverage hit.

---

## STEP 8 — VERIFICATION (ORC SELF-ATTACK)  (Week 8)

**Goal.** Brutal review by orchestrator wearing red-team hat; all P0 closed.

Checklist (full version in `08_VERIFICATION_GATES.md`):
- [ ] Code: syntax, logic, error handling, edge cases, perf — all green
- [ ] Quality: ≥80% coverage, zero `# TODO` in core paths, docs complete
- [ ] Domain: meets PDF spec, BOQ standards respected, terminology accurate
- [ ] Reverse-role attack — see `03_RISK_REGISTER.md`, 14 modes; close all P0/P1
- [ ] Adversarial inputs — scanned-then-photographed RFQs, multi-language, malformed
- [ ] Privacy — no PII leaks, license-compliant deps (SBOM committed)

**Milestone M8 (Wed W8):** zero P0/P1 risks open.

---

## STEP 9 — DEPLOYMENT + DOCS  (Week 8-10)

**Goal.** Reproducible deployment + technical report + presentation.

| Owner | Task | Output | DoD |
|---|---|---|---|
| A-4 | Production Docker images (multi-stage) | `Dockerfile`, `compose.prod.yml` | image < 4 GB |
| A-4 | `make demo` cold-start under 10 min | scripted | timed in CI |
| A-3 | `README.md` (quickstart, demo, screenshots) | doc | reviewer can run blind |
| A-3 | API reference (auto from OpenAPI) + runbook | docs | published to `/docs` site |
| Orch | 20-page technical report (LaTeX or Markdown→PDF) | `report.pdf` | mentor-approved |
| Orch | 12-15 slide deck | `slides.pptx` | dry-run done |
| Orch | Demo video (3-5 min screencast) | `demo.mp4` | posted to repo |

**Milestone M9 (Fri W10):** internship deliverables shippable.

---

## AGENT × STEP RACI MATRIX

| Step | A-1 Data | A-2 ML | A-3 Output | A-4 Test | Orch |
|---|---|---|---|---|---|
| 1 Setup        | C | I | C | R | A |
| 2 Data         | R | C | I | I | A |
| 3 Ingestion    | R | C | I | C | A |
| 4 ML/NLP       | C | R | I | C | A |
| 5 Rules/Onto   | I | R | C | C | A |
| 6 Output       | I | I | R | C | A |
| 7 Testing      | C | C | C | R | A |
| 8 Verification | C | C | C | C | R |
| 9 Deploy/Docs  | I | I | C | R | A |

R=Responsible, A=Accountable, C=Consulted, I=Informed.

---

## WEEKLY CADENCE

- **Mon 09:00** — Plan-update meeting (15m): blockers + week's PR plan
- **Wed 16:00** — Mid-week deep-dive (45m): one technical topic
- **Fri 16:00** — Demo + retro (30m): demo a PR + 1 thing learned / blocker
- **Daily** — Standup in TASKS.md (yesterday/today/blocker), <5 min

---

## CRITICAL PATH (CPM)

```
[1 Setup]──►[2 Data]──►[3 Ingest]──►[6 Output]──►[7 Test]──►[8 Verify]──►[9 Deploy]
                  \──►[4 ML]──►[5 Rules]──►──────────────────────►
```
Longest path: Setup → Data → ML → Rules → Output → Test → Verify → Deploy = 10 weeks.
ML and Rules can compress to 4 weeks combined if annotation parallelizes.

---

## CHECKPOINTS THE ORCHESTRATOR WILL ENFORCE

1. **W2** — schema frozen; can rerun ingestion against frozen schema.
2. **W3** — ingestion stable; ML team has clean inputs.
3. **W5** — model first baseline beats regex baseline by ≥10 F1 points.
4. **W6** — full pipeline runs end-to-end on one RFQ.
5. **W7** — Excel output passes round-trip test.
6. **W8** — all P0 risks closed.
7. **W10** — demo to mentor + report submitted.

---

**Status:** ✅ Execution plan locked. Each step has a single owner, written DoD, and a calendar slot.
