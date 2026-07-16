# ARCHITECTURE
## RFQ → BOQ Scope Extraction — Systems Design

---

## A. ARCHITECTURAL PRINCIPLES (decisions made up front)

1. **Hybrid > pure-LLM.** Deterministic rules + ontology bracket the ML output. Lessons: Zhang & El-Gohary 2015 (P=0.97 with rules); AEC Contracts (LLM hallucination = lawsuit).
2. **Ontology-first.** Every entity and relation is typed against an ontology. We extend IFC/ifcOWL (Nabavi 2023) with a custom Construction-Terms-Ontology (CTO) for materials, units, standards.
3. **Stateless services, durable artifacts.** Each pipeline stage is a pure function over JSON; intermediate artifacts persist to disk so any stage can be re-run independently.
4. **Confidence everywhere.** OCR conf, entity conf, relation conf, BOQ-row conf — never silently drop.
5. **Human-in-the-loop is a first-class output mode.** A "review queue" surface where low-confidence rows go for SME approval, not the trash.
6. **Two pipelines, one codepath.** Batch (CLI/folder watch) and online (REST API) share the same `Pipeline` class.

---

## B. C4 — CONTEXT (L1)

```
                           ┌──────────────────┐
                           │  Estimator / QS  │
                           │   (end user)     │
                           └────────┬─────────┘
                                    │ uploads RFQ PDF
                                    ▼
           ┌──────────────────────────────────────────────┐
           │     RFQ→BOQ SYSTEM (this project)            │
           │                                              │
           │   ingest → extract → validate → export       │
           └──┬─────────┬────────────┬──────────────┬────┘
              │         │            │              │
              ▼         ▼            ▼              ▼
        ┌─────────┐ ┌────────┐ ┌──────────┐  ┌──────────┐
        │ Tess /  │ │HF Model│ │ifcOWL +  │  │ Estimator │
        │ Paddle  │ │ Hub    │ │CTO files │  │ Cost DB   │
        │ OCR     │ │(BERT)  │ │(rdflib)  │  │(out-scope)│
        └─────────┘ └────────┘ └──────────┘  └──────────┘
```

---

## C. C4 — CONTAINER (L2)

```
┌────────────────────────────────────────────────────────────────────────┐
│                          DOCKER-COMPOSE                                 │
│                                                                         │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ API service  │  │ Worker      │  │ Web UI       │  │ Postgres    │ │
│  │ (FastAPI)    │──│ (Celery /   │──│ (React+Vite) │  │ (corpus,    │ │
│  │ /v1/extract  │  │  RQ)        │  │ /review queue│  │  jobs, runs)│ │
│  └──────────────┘  └──────┬──────┘  └──────────────┘  └─────────────┘ │
│                           │                                             │
│                           ▼                                             │
│        ┌──────────────────────────────────────────┐                    │
│        │  Pipeline stages (pure-Python, no state) │                    │
│        │  1.ingest 2.preproc 3.ner 4.re           │                    │
│        │  5.rules 6.normalize 7.export            │                    │
│        └──────────────────────────────────────────┘                    │
│                                                                         │
│  ┌──────────────────────────┐    ┌────────────────────────────────┐    │
│  │ Volume: ./data           │    │ Volume: ./models               │    │
│  │  raw/ interim/ processed │    │  bert-construction-ner/        │    │
│  │  golden/ annotations/    │    │  ifcOWL.ttl + cto.ttl          │    │
│  └──────────────────────────┘    └────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## D. PIPELINE — 7 stages (dataflow)

```
                    Stage 0   Stage 1     Stage 2    Stage 3   Stage 4    Stage 5      Stage 6
PDF ─► doc.json ─► clean.txt ─► spans ─► relations ─► validated ─► canonical.json ─► boq.xlsx
        ▲ OCR              ▲ regex/      ▲ BERT-     ▲ PURE/   ▲ ifcOWL    ▲ schema-      ▲ openpyxl/
        ▲ layout           ▲ sent.split  ▲ BiLSTM-   ▲ SpERT   ▲ rules     ▲ enforced     ▲ template-
        ▲ tables                         ▲ CRF                  ▲ unit-     ▲ JSON         ▲ filled
                                                                ▲ grammar
                                                                ▲ ontology
```

### Stage 0 — Ingestion (`ingest/`)
- `pdfplumber` for born-digital → text + bbox + table cells.
- `pytesseract` (CPU) and `paddleocr` (GPU optional) for scans → text + per-token confidence.
- `layoutparser` (Detectron2 model `PrimaLayout` or `PubLayNet`) for region segmentation: title, paragraph, table, figure.
- Quality gate: if mean OCR conf < 0.80 OR layout coverage < 0.60 → route to manual review queue.
- Output: `doc.json` = `{pages:[{blocks:[{type, text, bbox, conf}]}], meta:{...}}`.

### Stage 1 — Preprocessing (`preproc/`)
- Whitespace + ligature normalization (Unicode NFKC).
- Sentence segmentation (spaCy `senter`).
- Construction-aware tokenizer rules: keep `M20`, `Fe500`, `IS 456`, `25mm`, `0.5m³` as single tokens.
- Section detection (regex + heading layout class): preamble, scope, schedule of items, specifications, drawings list.
- Output: `clean.json` with sentence array + section labels.

### Stage 2 — NER (`models/ner/`)
- Architecture: `BERT-base-cased` → BiLSTM(2x256) → CRF (span decoding).
- Tagging: **BIOES** (precision over BIO for short technical spans).
- Entities (8) — see `04_ENTITY_ONTOLOGY.md`: MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE.
- Training: `transformers.Trainer`, AdamW lr=2e-5 (BERT) / 1e-3 (head), 8 epochs, warmup 10%, mixed precision.
- Inference: ONNX export for CPU serving; batch size auto-tuned.
- Eval: span-F1 (exact), partial-match-F1 (helper), per-type confusion matrix.

### Stage 3 — Relation Extraction (`models/re/`)
- Model: PURE-style span-pair classifier with entity-type markers; for long-context (cross-paragraph) we keep a Longformer variant in reserve.
- Relations (6): HAS_QUANTITY, HAS_UNIT, AT_LOCATION, OF_GRADE, COMPLIES_WITH, HAS_DIMENSION.
- Training set: entity pairs within ±3 sentences + every (MATERIAL, anything) pair in same section.
- Negative sampling: 4× negatives per positive.

### Stage 4 — Rule + Ontology Validation (`rules/`)
- **Unit grammar** — regex parser for SI/imperial construction units (m, m², m³, kg, t, no., ls, lm) with normalization table.
- **Ontology check** — material must resolve to CTO concept; standard must match a known body (IS, BS, EN, ASTM, ACI) and a code regex.
- **Co-occurrence rules** — MATERIAL with no QUANTITY in same row → flag `SCOPE_GAP_WARNING`.
- **Conflict resolution** — when ML + rules disagree, rule wins for QUANTITY/UNIT/STANDARD; ML wins for ACTION/LOCATION. Documented in code.

### Stage 5 — Canonical normalization (`normalize/`)
- JSON Schema (versioned, `schema/boq.v1.json`).
- Cardinality: one BOQ row = one (action, material, quantity, unit, location) tuple.
- Unit canonicalization (e.g., `mm` → `m`, `MT` → `t`).
- Cross-row dedup (Levenshtein on description ≥ 0.92 + same unit + same location).
- Output: `canonical.json` with row-level confidence = product of NER × RE × rule scores.

### Stage 6 — Exporters (`export/`)
- Excel via `openpyxl` against a configurable template (sheet, header row, column map).
- CSV (UTF-8 BOM for Excel users).
- JSON (canonical, schema-validated).
- Optional: IFC-XML stub (post-MVP).

---

## E. INTERFACES (the seams)

### Internal — Python types
```python
# ingest output
class IngestedDoc(BaseModel):
    doc_id: str
    pages: list[Page]
    meta: DocMeta
    quality: IngestQuality  # ocr_conf, layout_coverage, route_to_manual: bool

# NER output
class EntitySpan(BaseModel):
    text: str; type: EntityType; start: int; end: int
    page: int; conf: float; rule_validated: bool

# RE output
class Relation(BaseModel):
    head_id: str; tail_id: str; type: RelationType; conf: float

# canonical BOQ row
class BoqRow(BaseModel):
    item_no: int
    action: str | None       # "supply", "install", "lay", "cast"...
    material: str
    grade: str | None
    dimensions: dict | None
    quantity: Decimal
    unit: str                # canonical
    location: str | None
    standard: list[str]      # e.g. ["IS 456", "IS 383"]
    source_pages: list[int]
    confidence: float        # [0,1]
    warnings: list[Warning]  # SCOPE_GAP, UNIT_AMBIGUOUS, etc.
```

### External — REST API (FastAPI)
```
POST /v1/extract                multipart PDF → job_id
GET  /v1/jobs/{job_id}          job status + canonical JSON when done
GET  /v1/jobs/{job_id}/boq.xlsx download Excel
GET  /v1/review-queue           low-confidence items needing SME approval
POST /v1/review-queue/{row_id}  approve/reject/edit → updates training set
POST /v1/feedback               full-doc correction → annotation server
GET  /v1/ontology               returns active CTO concepts
```

OpenAPI auto-served at `/docs`; auth via API key header for MVP, JWT later.

---

## F. NON-FUNCTIONAL REQUIREMENTS

| Property | Target | Mechanism |
|---|---|---|
| Latency p50 | < 30 s / 20 pp | ONNX, batch=8, lazy OCR |
| Latency p95 | < 90 s | timeout + paginated processing |
| Throughput | 100 RFQs/hour | 4 workers, queue |
| Recovery | Crash-safe pipeline | stage outputs persisted to disk; resume from last successful stage |
| Observability | Per-stage metrics + traces | OpenTelemetry → Grafana (optional) |
| Determinism | Same input → same output | seeded models, pinned versions, no time/random in rules |
| Reproducibility | Cold Docker → demo | `make demo` runs end-to-end on shipped sample |
| Security | Tenant isolation MVP | filesystem namespaces per job_id; no shared state |

---

## G. SEQUENCE DIAGRAM — happy path

```
User ──upload──► API
API ──enqueue──► Worker
Worker ──► Ingest ─► doc.json (saved)
        ──► Preproc ─► clean.json
        ──► NER ─► spans.json
        ──► RE ─► relations.json
        ──► Rules ─► validated.json
        ──► Normalize ─► canonical.json
        ──► Export ─► boq.xlsx
Worker ──update job status──► API
User ──poll/download──► API ──► boq.xlsx
```

Failure modes branch at every arrow; each stage has its own retry policy + dead-letter path to review queue.

---

## H. DEPLOYMENT TOPOLOGY

- **Dev**: VS Code Dev Container, hot-reload FastAPI, models from local volume.
- **CI** (GitHub Actions): lint (ruff) → type (mypy) → unit (pytest) → integration on shipped sample → build Docker → push to ghcr.
- **Demo**: single host, docker-compose up; reachable at `http://localhost:8080`.
- **(Stretch) Cloud**: same compose on AWS EC2 t3.large; GPU optional via spot g4dn.xlarge for re-training.

---

## I. ARCHITECTURAL FITNESS FUNCTIONS (automated gates)

Each merge to main must keep these green:
1. End-to-end runtime on shipped 20-page RFQ < 60 s.
2. Span-F1 on frozen dev set ≥ last-known minus 1 percentage point.
3. Test coverage ≥ 80%.
4. Docker image size ≤ 4 GB.
5. No `Critical/High` vulns from `pip-audit`.

---

**Status:** ✅ Architecture frozen. Implementation may begin once Step 1 of the execution plan is approved.
