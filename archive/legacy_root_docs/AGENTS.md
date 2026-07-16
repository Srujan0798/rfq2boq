# AGENTS.md — RFQ2BOQ

> This file is the authoritative onboarding guide for AI coding agents working on RFQ2BOQ. Read this first before touching any code. The project uses English for all comments, documentation, and code.

---

## 1. Project Overview

RFQ2BOQ transforms unstructured construction RFQ (Request for Quotation) tender documents into structured Bill of Quantities (BOQ) data using NLP. It is a Python-based system with a hybrid ML + rules architecture.

**Current honest metrics (as of the latest evaluation):**
- Entity-level F1 (macro): 44.1%
- Row-level F1 (macro): 37.7%
- XLSX extraction (entity): 89.0% macro F1
- PDF extraction (entity): 14.2% macro F1

**Production NER:** Pattern-based (regex + gazetteer) — more reliable than the ML model on real docs.
**ML NER v5:** Val F1=0.755, but only 0.188 on held-out real docs (overfit to synthetic).

**Bottom line:** XLSX extraction is production-ready. PDF extraction needs real human-annotated training data, not code fixes.

For full context, see [`README.md`](README.md) and [`PROJECT_MAP.md`](PROJECT_MAP.md).

---

## 2. Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11–3.13 (strictly `<3.14`; typer breaks on 3.14) |
| NER (production) | Pattern-based (regex + gazetteer) |
| NER (experimental) | BERT-base-cased LoRA via HuggingFace Transformers |
| PDF extraction | pdfplumber + pytesseract + PyMuPDF |
| XLSX extraction | openpyxl |
| OCR | Tesseract (pytesseract) |
| Ontology | JSON knowledge base + rdflib |
| API | FastAPI + uvicorn |
| UI | Streamlit |
| CLI | Typer + Rich |
| ML framework | PyTorch + Transformers + spaCy |
| Vector store | ChromaDB |
| Embeddings | sentence-transformers |
| Data / domain | Pydantic v2 + Pydantic Settings |
| Testing | pytest + pytest-cov + pytest-asyncio + httpx |
| Linting / formatting | Ruff |
| Type checking | mypy |
| Pre-commit | pre-commit hooks (ruff + mypy + trailing-whitespace + etc.) |
| Deployment | Docker Compose (API + UI + frontend + nginx + redis) |

**Notable exclusions:** No camelot-py (complex PDF tables use pdfplumber only). No multi-language support yet (English only).

---

## 3. Build, Install, and Run Commands

### Prerequisites
- Python 3.11+
- Tesseract OCR installed system-wide (`tesseract`)
- poppler-utils (for pdf2image)

### Installation

```bash
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
```

### Running the System

```bash
# FastAPI server
make run-api
# or: uvicorn src.api.main:app --reload --port 8000

# Streamlit UI
make run-ui
# or: streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0

# CLI single-file extraction
rfq2boq extract --input-file data/real_rfqs/swa_enquiries/... --output boq.json

# CLI batch
rfq2boq batch --input-dir data/real_rfqs/swa_enquiries/ --output-dir output/

# Demo script
make demo
# or: python3 scripts/demo.py
```

### Docker

```bash
docker-compose up --build      # full stack
docker-compose up api          # API only
docker-compose up ui           # UI only
```

The Docker image is `python:3.11-slim` with system packages `tesseract-ocr poppler-utils libgl1 libglib2.0-0`. The API exposes port `7860` inside the container.

---

## 4. Test Commands and Strategy

### Run Tests

```bash
# Full test suite (skips OCR and BERT NER unit tests by default)
make test
# or: pytest tests/ -v --ignore=tests/unit/test_ocr_processor.py --ignore=tests/unit/test_bert_ner.py

# With coverage
make test-cov
# or: pytest tests/ --cov=src --cov-report=term-missing

# CI gate (critical tests + lint + anti-cheat + clean tree)
make verify
```

### Test Structure

| Directory | Purpose |
|-----------|---------|
| `tests/unit/` | Fast unit tests for every module |
| `tests/integration/` | Integration tests (API, pipeline, real RFQ corpus, self-attack) |
| `tests/e2e/` | End-to-end tests across full pipeline |
| `tests/golden/` | Golden-path regression tests |
| `tests/fuzz/` | Fuzz / robustness tests |
| `tests/performance/` | Performance regression tests |
| `tests/security/` | Security-focused tests |

### Critical Unit Tests (run by `make verify`)

- `tests/unit/test_boq_assembler.py`
- `tests/unit/test_pipeline_xlsx.py`
- `tests/unit/test_anti_cheat.py`
- `tests/unit/test_validator.py`
- `tests/unit/test_final_model.py`
- `tests/unit/test_ui_app.py`
- `tests/integration/test_real_rfq_corpus.py`
- `tests/integration/test_self_attack.py`
- `tests/integration/test_xlsx_row_preservation_e2e.py`

### Test Markers (configured in `pyproject.toml`)

- `slow` — slow tests (run with `--slow`)
- `playwright` — requires browsers (skipped by default)
- `load` — load tests via locust (skipped by default)

### Coverage Configuration

- Source paths: `src`, `config`
- Omitted: `src/cli/*`, `src/nlp/ner/inference.py`, `src/nlp/ner/trainer.py`, `src/api/routes/upload.py`, `src/api/routes/review.py`, `*/__init__.py`, `*/migrations/*`

---

## 5. Code Style and Linting

### Tools
- **Ruff** for linting and formatting
- **mypy** for type checking

### Ruff Configuration (`pyproject.toml`)

```toml
[tool.ruff]
target-version = "py311"
line-length = 120
src = ["src", "config", "scripts", "tests"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM"]
ignore = ["E501", "B023", "N802", "N803", "N806", "E741"]
```

### mypy Configuration

```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
```

### Pre-commit Hooks (`.pre-commit-config.yaml`)

1. `ruff` (with `--fix`) + `ruff-format`
2. `mypy` (ignores missing imports; scans `code/` and `config/`)
3. `end-of-file-fixer`, `trailing-whitespace`, `check-yaml`, `check-json`, `check-added-large-files` (max 5 MB)

Install with:
```bash
pip install pre-commit
pre-commit install
```

---

## 6. Code Organization

```
src/                    # All production Python code
├── api/                # FastAPI REST API (main.py, routes/, schemas.py, dependencies.py)
├── cli/                # Typer CLI entry point (main.py)
├── domain/             # Business logic: models.py, boq_assembler.py, validator.py,
│                       #   risk_engine.py, confidence.py, variance.py, xlsx_column_mapper.py
├── eval/               # Evaluation matchers and scoring logic
├── export/             # Output generators: excel_generator.py, json_formatter.py,
│                       #   csv_exporter.py, report.py, risk_report.py, adapters/
├── ingest/             # Document ingestion: pdf_extractor.py, ocr_processor.py,
│                       #   layout_analyzer.py, preprocessor.py, table_extractor.py,
│                       #   text_boq_extractor.py, xlsx_parser.py, pdf_extractor_bbox.py
├── nlp/                # NLP pipeline
│   ├── ner/            # NER model implementations (BERT, BiLSTM, CRF, LoRA trainers)
│   ├── patterns/       # spaCy EntityRuler + regex pattern definitions
│   ├── re/             # Relation extraction models
│   ├── pipeline.py     # NER orchestration
│   ├── train_ner.py    # Training script helpers
│   └── ...
├── preproc/            # Preprocessing: section classification, text cleaning
├── ontology/           # Domain ontology loaders and graph ontology (graph_ontology.py,
│                       #   loader.py, materials.json, standards.json, units.json, etc.)
├── rules/              # Rule engine for domain validation
├── confidence/         # Confidence scoring and calibration
├── risk/               # Risk analysis engine
├── llm/                # LLM-based ambiguity resolution
├── labeling/           # Annotation and labeling utilities
├── normalize/          # Unit and text normalization
├── models/             # Pydantic / data models (duplicates some domain/ models; check imports)
├── auth/               # Authentication helpers
├── pipeline.py         # Main PDF/text extraction pipeline
├── pipeline_xlsx.py    # Main XLSX extraction pipeline
├── boq_generator.py    # Legacy/high-level BOQ generation
├── logging_config.py   # Structured logging setup
└── unit_normalization.py  # Standalone unit normalizer

config/                 # Project-wide configuration
├── constants.py        # EntityType, RelationType, BIOES labels, canonical units, etc.
├── settings.py         # Pydantic Settings with RFQ2BOQ_ env prefix
└── __init__.py

tests/                  # All tests (see Test Strategy above)
scripts/                # Runnable utility scripts (eval, train, annotate, demo, etc.)
ui/                     # Streamlit UI (app.py, components.py, pdf_viewer.py, annotate*.py)
data/                   # All data
├── real_rfqs/          # Real tender documents (swa_enquiries/ = the 10 sacred files)
├── annotations/        # Training annotations
├── ontology/           # Domain ontology JSON files
├── gold/               # Ground truth data
├── jobs/               # Background job storage
└── ...
models/                 # Trained model artifacts (gitignored; LoRA checkpoints live here)
prompts/                # Agent task prompts
├── wave4/              # ACTIVE prompts — dispatch from here
├── archive/            # Historical prompts — read-only, do not dispatch
├── TASK_TEMPLATE.md    # Template for writing new prompts
└── INDEX.md            # Dispatch table for active prompts
docs/                   # Documentation
├── wave_status.md      # Single source of truth for done vs pending
├── SCOPE_GUARD.md      # What is out of scope (read before adding features)
├── conventions.md      # Locked coding conventions
├── architecture.md     # System architecture overview
├── PHASE8_UNIFIED...   # Full timeline, decisions, and principles
├── api.md              # API endpoint documentation
└── ...
deployment/             # Docker, docker-compose, nginx config
results/                # Evaluation outputs and honest reports
deliverables/           # Final reports and summaries
attic/                  # Archived old code and docs (read-only)
```

---

## 7. Key Conventions and Rules

These are **locked conventions**. Violating them counts as a task failure.

### 7.1 Import Root
Use `src.` for all production imports. Do NOT use `code.` (the `code/` shim was removed).

```python
# ✅ correct
from src.nlp.pipeline import NLPPipeline
from config.constants import EntityType

# ❌ wrong
from code.nlp.pipeline import NLPPipeline
```

### 7.2 Entity and Relation Types
Entity types (8) — use `config.constants.EntityType`:
```
MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE
```

Relation types (6) — use `config.constants.RelationType`:
```
HAS_QUANTITY, HAS_UNIT, AT_LOCATION, OF_GRADE, COMPLIES_WITH, HAS_DIMENSION
```

### 7.3 Tagging Scheme
Use **BIOES**, not BIO. Reference `config.constants.BIOES_LABELS`, `LABEL2ID`, `ID2LABEL`, `NUM_LABELS`.

### 7.4 Settings
All configuration flows through `config.settings.settings` (Pydantic). Env prefix: `RFQ2BOQ_`. Never hard-code paths; never read env vars directly.

```python
from config.settings import settings
model_dir = settings.MODEL_DIR
```

### 7.5 Type Hints
Required on all new code. Public APIs must have type hints. Use `from __future__ import annotations` for forward refs in Python 3.11.

### 7.6 File Naming
- Python modules: `snake_case.py`
- Test modules: `test_<unit>.py`
- Documentation: `kebab-case.md` or `UPPERCASE.md` for top-level
- JSON data: `snake_case.json`

### 7.7 Logging
Use Python `logging` with structured fields. Never log PII or full document text at `INFO`+.
- `DEBUG` — internal trace
- `INFO` — request received, stage complete, entities found
- `WARNING` — scope gaps, low confidence, unknown standards
- `ERROR` — extraction failures, OCR failures, API errors

### 7.8 API Route Versioning
- New endpoints: `/v1/...`
- Health: `GET /v1/health` (liveness), `GET /v1/ready` (readiness)
- Extract: `POST /v1/extract`
- Rate limit: 10 req/min per IP on `/v1/extract`
- Legacy alias `/api/health` exists for older clients

### 7.9 Annotation JSON Format
Both `ner_tags` and `labels` keys must be supported in loaders:
```json
{
  "tokens": ["Supply", "500", "kg", "cement"],
  "ner_tags": ["B-ACTION", "S-QUANTITY", "S-UNIT", "S-MATERIAL"],
  "labels": ["B-ACTION", "S-QUANTITY", "S-UNIT", "S-MATERIAL"]
}
```

### 7.10 Forbidden Patterns
Do not introduce:
- Backwards-compatibility shims for code that hasn't shipped yet
- Dead code or commented-out blocks
- Speculative features ("might need this later")
- Mock data in production code paths
- Silent exception swallowing (`except: pass`)
- `assert` for production validation (use proper raises)
- Untyped public API signatures

---

## 8. Environment and Configuration

Copy `.env.example` to `.env` and override as needed. All settings use the `RFQ2BOQ_` prefix.

**Important paths and defaults:**
| Variable | Default | Description |
|----------|---------|-------------|
| `RFQ2BOQ_MODEL_DIR` | `./models/ner-bert-bilstm-crf-v1` | NER model path |
| `RFQ2BOQ_ONTOLOGY_DIR` | `./src/ontology` | Ontology JSON files |
| `RFQ2BOQ_DATA_DIR` | `./data` | Root data directory |
| `RFQ2BOQ_TESSERACT_CMD` | `tesseract` | Tesseract executable |
| `RFQ2BOQ_OCR_CONFIDENCE_THRESHOLD` | `0.80` | Min OCR confidence |
| `RFQ2BOQ_ENTITY_CONFIDENCE_THRESHOLD` | `0.70` | Min entity confidence |
| `RFQ2BOQ_MAX_FILE_SIZE_MB` | `50` | Max upload size |
| `RFQ2BOQ_MAX_PAGES` | `200` | Max pages per doc |
| `RFQ2BOQ_API_HOST` | `0.0.0.0` | API bind host |
| `RFQ2BOQ_API_PORT` | `8000` | API bind port |
| `RFQ2BOQ_LOG_LEVEL` | `INFO` | Logging level |
| `RFQ2BOQ_RATE_LIMIT` | `10/minute` | Rate limit for `/v1/extract` |

See `.env.example` for the complete list.

---

## 9. Security Considerations

- **Authentication:** Optional API key via `RFQ2BOQ_API_KEY`. Empty string = no auth.
- **CORS:** Configured via `RFQ2BOQ_CORS_ORIGINS`. Default allows all (`["*"]`) if unset — not recommended for production.
- **File uploads:** Max size enforced (`RFQ2BOQ_MAX_FILE_SIZE_MB`). Uploaded files are processed and not persisted permanently unless explicitly saved.
- **Rate limiting:** 10 req/min per IP on `/v1/extract`.
- **PII:** Never log full document text or personally identifiable information at `INFO`+.
- **OCR:** Scanned PDFs are processed in-memory; images are not stored unless debugging is enabled.
- **Dependencies:** Dependabot is configured for pip and GitHub Actions. Major version updates for `torch` and `transformers` are ignored to prevent breakage.

---

## 10. CI / CD and Automation

GitHub Actions workflows (`.github/workflows/`):

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push to `main` / `phase8-clean-slate`, PRs to `main` | Full CI gate (`make verify`) + Docker build test |
| `test.yml` | Push / PR | Extended test matrix |
| `security.yml` | Push / PR | Security scanning (bandit, safety, etc.) |
| `perf_regression.yml` | Schedule / manual | Performance regression checks |
| `train_on_data.yml` | Manual | Training pipeline trigger |

Dependabot runs weekly for pip and GitHub Actions.

---

## 11. How Work Gets Done

The project uses an agent-task model. Active prompts live in `prompts/wave4/`. Historical prompts are in `prompts/archive/`.

**Before starting any new work:**
1. Read `docs/wave_status.md` — single source of truth for done vs pending.
2. Read `docs/SCOPE_GUARD.md` — strict boundaries on what NOT to build.
3. Read `docs/conventions.md` — locked coding rules.
4. Read `prompts/wave4/INDEX.md` — active dispatch table.

**Lanes (parallel work without collisions):**
- Lane A (Extraction): `src/ingest/`, `src/preproc/`
- Lane B (Data/Model): `data/ontology/`, `src/nlp/`, `models/`
- Lane C (Domain/Rules): `src/domain/`, `src/rules/`
- Lane D (QA): `tests/e2e/`, `scripts/`

**The 10 Sacred SWA Files** (`data/real_rfqs/swa_enquiries/`) are the only real documents that matter for validation. Do not add synthetic files to this set.

---

## 12. Quick Reference

```bash
# Install
pip install -e ".[dev]"
python -m spacy download en_core_web_sm

# Run
make run-api            # API server
make run-ui             # Streamlit UI
make demo               # End-to-end demo

# Quality
make test               # Run tests
make lint               # Ruff lint
make typecheck          # mypy type check
make verify             # CI gate (tests + lint + anti-cheat + clean tree)
pre-commit run -a       # Run all pre-commit hooks

# Eval
python3 scripts/eval_honest.py      # Entity-level honest eval
python3 scripts/eval_honest_rows.py # Row-level honest eval

# Train
python3 scripts/train_lora_ner_v5.py
```
