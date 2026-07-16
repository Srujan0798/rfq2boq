# RFQ2BOQ — Scope Extraction using NLP

Transforms unstructured construction RFQ (Request for Quotation) tender documents into structured Bill of Quantities (BOQ) data using NLP.

> **Navigation (closing handoff):**  
> - **Client closeout:** [`deliverables/PROJECT_CLOSEOUT_HANDOFF.md`](deliverables/PROJECT_CLOSEOUT_HANDOFF.md)  
> - **SWA runbook:** [`deliverables/SWA_HANDOFF_GUIDE.md`](deliverables/SWA_HANDOFF_GUIDE.md)  
> - **Maintainers:** [`HANDOFF.md`](HANDOFF.md) · plan [`tasks/phase9/00_README.md`](tasks/phase9/00_README.md) · [`docs/CORE_UNDERSTANDING.md`](docs/CORE_UNDERSTANDING.md)

## Honest Current Results

From on-disk audit artifacts after final cleanup (2026-07-16). Re-run audits after any code change.

| Metric | Value | Evidence |
|--------|-------|----------|
| **Corpus size** | 127 unique client docs (33 `boq_bearing`) | `data/real_rfqs/corpus_manifest.json` |
| **Fidelity audit (BOQ-bearing corpus)** | **33/33 PASS** (`results/fidelity/summary.json`) | `scripts/audit_fidelity_per_doc.py --all` |
| **Sacred-10 (same auditor)** | **10/10 PASS** | docs `01`–`10` (excl. bundle copies) |
| **Product row-match (XLSX sample)** | **~82.5%** (66/80) on 02/03/05/08 | `results/PRODUCT_EVAL.md` |
| **Completeness report** | Sacred-10 **0 silent drops** when low-confidence rows count as **flagged** | `results/FIDELITY_REPORT.md` — *completeness ≠ content F1* |
| **Real NER F1** | **~0.43** (pattern path; not domain-retrained) | holdout / historical honest figure |

> **Do not cite** missing files `results/eval_honest_rows.json` or `results/FINAL_HONEST_REPORT.md` — they are **not** in the repo.

**Production NER:** Pattern-based (regex + gazetteer). Experimental BERT/LoRA is **not** production.  
**Owner-verified BIOES for retrain:** still the open data gate (tooling exists; human review required).

**Bottom line:** Table/XLSX path is strong; free-text / odd layouts still need Flag Review. Accuracy jumps need **human-annotated gold**, not slogan metrics.

## Known Limitations

- **Two fidelity definitions** — do not mix: (1) completeness via `measure_fidelity.py` / `FIDELITY_REPORT.md`; (2) source-truth auditor via `audit_fidelity_per_doc.py` / `results/fidelity/`.
- **NER data foundation** was historically weak (regex-auto labels from papers) — do not trust synthetic F1.
- **No camelot-py:** complex PDF tables use pdfplumber only.
- **English primary:** no production Hindi/regional path.
- **OCR:** scans under ~300 DPI degrade badly.

## Performance (order-of-magnitude only)

No committed latency benchmark suite backs exact p50/p95 tables. Observed behaviour in development: simple XLSX often under a few seconds; multi-page PDFs commonly tens of seconds to minutes depending on OCR/tables. Treat any fixed latency table as **unverified**.

## Roadmap

| Priority | Item | Status |
|----------|------|--------|
| P0 | Real RFQ human annotation + retrain | **Blocked** on owner review |
| P1 | Keep fidelity/regression green; watch hard multi-column PDFs | Ongoing |
| P2 | Multi-page / multi-range PDF robustness | Partial (structure-first exists) |
| P3 | Hindi/regional language support | Backlog |
| P4 | International standards (ASTM, BS) | Backlog |
| P5 | Cloud deployment | Out of internship core scope |

## Overview

RFQ2BOQ extracts bill of quantities from construction tender RFQs. The **production** path is structure/table extraction plus **pattern-based** NER (regex + gazetteer) and rule/ontology validation. Experimental BERT/LoRA NER code exists but is **not** the production default and is not domain-retrained on owner-verified gold.

## Architecture

```
PDF/XLSX → Ingest → Table Extraction → BOQ Assembly → Export
               ↓                           ↑
          Pattern NER (fallback) ──────────┘
          + OCR (scanned PDFs)
```

**Entities:** MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE

**Relations:** HAS_QUANTITY, HAS_UNIT, AT_LOCATION, OF_GRADE, COMPLIES_WITH, HAS_DIMENSION

## Features

- **PDF Extraction** — Born-digital and scanned PDFs with OCR fallback (quality varies by layout)
- **XLSX Extraction** — Structure-driven row-preservation pipeline (strongest path today)
- **Named Entity Recognition** — 8 entity types; production path is pattern-based (regex + gazetteer)
- **Domain Validation** — Rules/ontology checks; GeM catalog validation for GeM tenders (19 products ingested)
- **Confidence / flags** — Uncertain rows can be flagged rather than silently dropped (R1 intent)
- **Multiple Output Formats** — Excel, JSON (and related exports)

> **Honest evaluation artifacts:** [`results/fidelity/summary.json`](results/fidelity/summary.json), [`results/FIDELITY_REPORT.md`](results/FIDELITY_REPORT.md), [`results/PRODUCT_EVAL.md`](results/PRODUCT_EVAL.md).

## Tech Stack

| Component | Technology |
|-----------|-----------|
| NER | Pattern-based (regex + gazetteer) — production; BERT-base-cased LoRA — experimental |
| PDF extraction | pdfplumber + pytesseract |
| XLSX extraction | openpyxl |
| Ontology | JSON knowledge base |
| API | FastAPI |
| UI | Streamlit |
| CLI | Typer |
| Export | openpyxl (Excel) |
| Testing | pytest |
| Deployment | Docker Compose |

## Quick Start

### Prerequisites

- Python 3.11+
- Tesseract OCR (for scanned PDFs)

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/rfq2boq.git
cd rfq2boq

# Install dependencies
pip install -e ".[dev]"

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Run API Server

```bash
make run-api
# or directly: uvicorn src.api.main:app --reload --port 8000
```

Then visit http://localhost:8000/docs for the interactive API documentation.

### Run Streamlit UI

```bash
make run-ui
# or directly: streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0
```

### Run CLI

```bash
# Process a single RFQ document (PDF, text, or XLSX)
rfq2boq extract --input-file data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx --output boq_output.json

# Batch process all RFQ files in a directory
rfq2boq batch --input-dir data/real_rfqs/swa_enquiries/ --output-dir output/

# Run the end-to-end demo
make demo
```

### Run Tests

```bash
make test
# or with coverage
make test-cov
# or directly: pytest tests/ --cov=src --cov-report=term-missing
```

## Project Structure

See [`HANDOFF.md`](HANDOFF.md) for where to start, [`deliverables/SWA_HANDOFF_GUIDE.md`](deliverables/SWA_HANDOFF_GUIDE.md) for the SWA runbook, and [`tasks/phase9/00_README.md`](tasks/phase9/00_README.md) for the active plan.

```text
rfq2boq/
├── src/                    # Production Python code
│   ├── api/                # FastAPI REST API
│   ├── cli/                # Typer CLI
│   ├── domain/             # BOQ assembly, validation, models
│   ├── eval/               # Evaluation matchers
│   ├── export/             # Excel/JSON/CSV exporters
│   ├── ingest/             # PDF extraction, OCR, tables
│   ├── nlp/                # NER pipeline, patterns, training
│   ├── preproc/            # Section classification
│   └── ...
├── tests/                  # All tests (unit/integration/e2e/golden)
├── data/                   # All data
│   ├── real_rfqs/          # Real tender documents
│   │   ├── swa_enquiries/  # The 10 sacred SWA files
│   │   ├── gold/           # Entity-level + row-level gold
│   ├── annotations/        # Training annotations
│   └── ontology/           # Domain ontology files
├── models/                 # Trained models (gitignored)
├── scripts/                # Runnable scripts (eval, train, demo)
├── ui/                     # Streamlit UI
├── tasks/                  # Active Phase-9 task plans (SSOT for agent dispatch)
│   └── phase9/             # Current wave — the only dispatch source
├── prompts/                # Agent task prompt templates
├── docs/                   # Documentation
│   ├── CORE_UNDERSTANDING.md   # Architecture + honest metrics
│   ├── SWA_REQUIREMENTS_*.md   # Client requirements
│   └── conventions.md          # Locked coding rules
├── config/                 # Constants and settings (locked)
├── schema/                 # JSON schema for BOQ output
├── deployment/             # Docker, docker-compose
├── results/                # Evaluation outputs
├── deliverables/           # Final reports and presentation
├── archive/                # Quarantine + preserved legacy history
├── resources/              # SACRED — SWA-provided materials, never move
└── attic/                  # Archived old code (read-only)
```

## NLP Pipeline

### Entity Types

| Entity | Description | Example |
|--------|-------------|---------|
| MATERIAL | Construction materials | cement, concrete, steel |
| QUANTITY | Numeric values | 100, 500, 1.5 |
| UNIT | Measurement units | m³, kg, bags |
| LOCATION | Location in building | ground floor, basement |
| DIMENSION | Physical dimensions | 230mm thick, Ø12mm |
| STANDARD | Industry standards | IS 456, ASTM A615 |
| ACTION | Work action | supply, install, lay |
| GRADE | Material grade | M20, Fe500, Grade 43 |

### Relation Types

| Relation | Description |
|----------|-------------|
| HAS_QUANTITY | Links material to its quantity |
| HAS_UNIT | Links quantity to its unit |
| AT_LOCATION | Links material to location |
| OF_GRADE | Links material to grade |
| COMPLIES_WITH | Links material to standard |
| HAS_DIMENSION | Links material to dimension |

## API Documentation

### Endpoints (as implemented under `src/api/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/health` | Health check |
| GET | `/api/health` | Legacy health alias |
| POST | `/v1/extract` | Extract BOQ from text (also `/api/extract`) |
| POST | `/v1/extract/upload` | Upload RFQ for processing (also `/api/upload`) |
| POST | `/v1/extract/download-excel` | Upload and download Excel output |
| GET | `/v1/jobs/{extraction_id}` | Get job/BOQ result (also `/api/boq/{extraction_id}`) |

There is **no** `/v1/ready` route in the current code. SAP/Primavera/IFC export routes exist only as explicit out-of-scope stubs. See [docs/api.md](docs/api.md) for broader docs (may lag code — trust `src/api/` if they disagree).

## Configuration

Environment variables (prefix: `RFQ2BOQ_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_DIR` | `./models/ner-bert-bilstm-crf-v1` | NER model path |
| `ONTOLOGY_DIR` | `./src/ontology` | Ontology data path |
| `DATA_DIR` | `./data` | Root data directory |
| `TESSERACT_CMD` | `tesseract` | Tesseract OCR command |
| `OCR_CONFIDENCE_THRESHOLD` | `0.80` | Minimum OCR confidence |
| `ENTITY_CONFIDENCE_THRESHOLD` | `0.70` | Minimum entity confidence |
| `API_HOST` | `0.0.0.0` | API host |
| `API_PORT` | `8000` | API port |
| `MAX_FILE_SIZE_MB` | `50` | Maximum upload file size |
| `MAX_PAGES` | `200` | Maximum pages per document |

## Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up --build

# Run only the API
docker-compose up api

# Run only the UI
docker-compose up ui
```

## Current Honest Metrics

| Metric | Actual (re-measured) | Target (literature / R1) |
|--------|----------------------|---------------------------|
| Fidelity auditor (33 boq_bearing) | 33/33 PASS | 100% capture, flag-never-drop |
| Sacred-10 auditor | 10/10 PASS | 10/10, 0 missing |
| Product row-match (4 XLSX enquiries) | 82.5% | ≥ 85% line-item match |
| Completeness (FIDELITY_REPORT) | 0 silent drops if flags count | 0 silent drops |
| Real NER F1 | ~0.43 | 0.88 with real gold |
| Lint (ruff src/) | clean | clean |

## Development

### Code Quality

```bash
# Run linting
make lint
# or directly: ruff check src config tests scripts

# Run type checking
make typecheck
# or directly: mypy src --ignore-missing-imports
# Note: host mypy may fail on third-party numpy stubs; that is an environment issue, not a free pass on src/ type errors.

# CI-style gate (lint + selected tests + anti-cheat greps)
make verify
```

### Train NER Model

```bash
# Pattern-based production NER (no training required)
# Experimental BERT LoRA fine-tuning on annotated data:
python3 scripts/train_lora_ner_v5.py --output-dir models/rfq2boq-ner-lora-v5
```

## Limitations & Future Work

- **Current:** MVP handles English RFQs with standard formats
- **Planned:** Multi-language support (Hindi, Arabic)
- **Planned:** IFC-XML export for BIM integration
- **Planned:** Active learning for continuous improvement
- **Planned:** Load balancing for high-volume processing

## References

Based on research in automated construction document extraction:
- Zhang & El-Gohary (2015) — NLP-based information extraction
- Sousa et al. (2024) — Deep learning for construction documents
- Nabavi et al. (2023) — IFC-based ontology alignment
- Industry sources: Helium42, DesignDrafter, AEC Contracts

## License

MIT
