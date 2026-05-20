# RFQ2BOQ — Scope Extraction using NLP

Transforms unstructured construction RFQ (Request for Quotation) tender documents into structured Bill of Quantities (BOQ) data using NLP.

## Results

| Metric | Value |
|--------|-------|
| **Synthetic Test F1** | 99.56% |
| **Real-world F1** | 67.05% (10 annotated RFQs) |
| **Tests** | 237 passed, 6 skipped (unit tests) |
| **Pipeline latency** | <30s for 10-page RFQ |

**Trained Model:** `models/ner-bert-bilstm-crf-v1/` (3 epochs, bert-base-cased + BiLSTM + CRF)

## Known Limitations

- **Synthetic training gap**: Model trained on 300 synthetic RFQs. Real-world F1 is 67.05% vs 99.56% on synthetic test set. Main gaps: MATERIAL span mismatch, STANDARD code format ("IS" vs "IS 456:2000").
- **English only**: No multi-language support for Hindi, regional language tenders.
- **Indian construction focus**: Optimized for IS codes (IS 456, IS 1786, etc.). International standards (ASTM, BS, EN) have limited coverage.
- **Table extraction**: Complex multi-column layouts may fail. Simple row-based tables work well.
- **OCR quality**: Scan resolution below 300 DPI significantly reduces extraction accuracy.
- **Single document**: Processes one RFQ at a time. No batch PDF processing in API.

## Performance

| Scenario | Latency (p50) | Latency (p95) |
|----------|---------------|---------------|
| 1-page PDF (text) | 2.3s | 4.1s |
| 5-page PDF (text) | 8.7s | 15.2s |
| 10-page PDF (mixed) | 18.4s | 32.1s |
| Real RFQ (complex) | 45s+ | varies |

| Resource | Usage |
|----------|-------|
| Memory (loaded model) | ~2.1 GB |
| Cold start (API) | 8-12s |
| Disk (model + ontology) | ~450 MB |

## Roadmap

| Priority | Item | Status |
|----------|------|--------|
| P0 | Real RFQ annotation + retraining | **In progress** |
| P1 | Multi-page PDF batch processing | Planned |
| P2 | Hindi/regional language support | Backlog |
| P3 | International standards (ASTM, BS) | Backlog |
| P4 | Cloud deployment (AWS/GCP) | Planned |

## Overview

RFQ2BOQ is an AI-powered system that extracts bill of quantities from Request for Quotation documents commonly used in construction tenders. It uses a hybrid approach combining BERT-based NLP with rule-based validation against a construction ontology.

## Architecture

```
PDF ─► Ingest ─► Preprocess ─► NER (BERT-BiLSTM-CRF) ─► Relation Extraction ─► Rules + Ontology ─► Canonical JSON ─► Excel/JSON
       (OCR)    (tokenize)     (8 entities, BIOES)       (6 relation types)     (validation)        (BOQ schema)      (export)
```

**Entities:** MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE

**Relations:** HAS_QUANTITY, HAS_UNIT, AT_LOCATION, OF_GRADE, COMPLIES_WITH, HAS_DIMENSION

## Features

- **PDF Extraction** — Handles both born-digital and scanned PDFs with OCR fallback
- **Named Entity Recognition** — 8 entity types for construction domain using BERT-BiLSTM-CRF
- **Relation Extraction** — 6 relation types linking entities together
- **Domain Validation** — Rules-based validation against construction ontology
- **Confidence Scoring** — Per-entity and per-BOQ-item confidence scores
- **Multiple Output Formats** — Excel, JSON, and Markdown reports

## Tech Stack

| Component | Technology |
|-----------|-----------|
| NER | BERT-base-cased + BiLSTM + CRF (HuggingFace Transformers) |
| Pattern matching | spaCy 3 EntityRuler + regex |
| PDF extraction | pdfplumber + pytesseract |
| Ontology | JSON knowledge base + rdflib |
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
make serve-api
# or directly: uvicorn src.api.main:app --reload --port 8000
```

Then visit http://localhost:8000/docs for the interactive API documentation.

### Run Streamlit UI

```bash
make serve-ui
# or directly: streamlit run ui/app.py --server.port 8501
```

### Run CLI

```bash
# Process a single PDF
rfq2boq process data/samples/sample.pdf -o boq_output.xlsx

# Batch process all PDFs in a directory
rfq2boq batch data/rfqs/ -o output/

# Start API server
rfq2boq serve --host 0.0.0.0 --port 8000
```

### Run Tests

```bash
make test
# or with coverage
make test-cov
# or directly: pytest tests/ --cov=src --cov-report=term-missing
```

## Project Structure

```text
rfq2boq/
├── src/                    # Production Python code
│   ├── api/                # FastAPI REST API
│   ├── cli/                # Typer CLI
│   ├── domain/             # BOQ assembly, validation, confidence
│   ├── export/             # Excel/JSON/CSV/IFC/SAP/Primavera exporters
│   ├── ingest/             # PDF extraction, OCR, layout, table detection
│   ├── nlp/                # NER (BERT-BiLSTM-CRF / LayoutLM / IndicBERT / ARCBERT), patterns, RE
│   ├── ontology/           # Construction knowledge base + OmniClass mapper
│   ├── risk/               # Risk & variance engine
│   ├── llm/                # Claude ambiguity resolver
│   ├── auth/               # JWT authentication
│   └── rules/              # Validation, conflict resolution, units
├── config/                 # Settings + entity/relation/BIOES constants
├── tests/                  # unit/integration/e2e/golden/fuzz
├── scripts/                # Training, eval, scraping, demo
├── data/                   # synthetic, real_rfqs, ontology, rates, annotations
├── models/                 # Trained checkpoints (gitignored)
├── schema/                 # JSON schemas (BOQ v1)
├── ui/                     # Streamlit UI
├── web/                    # Next.js frontend
├── integrations/            # External plugins (Revit)
├── deployment/            # Docker, Nginx configs
├── prompts/               # AI task contracts (hybrid phases 1-3)
├── docs/                  # All documentation
├── deliverables/          # paper/, patent/, slides/
├── results/              # Evaluation metrics + figures
└── attic/                # Archived (Neo4j, SpERT, MLflow, voice, drawing)
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

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/upload` | Upload PDF for processing |
| POST | `/api/extract` | Extract BOQ from text |
| GET | `/api/boq/{extraction_id}` | Get BOQ result |

See [docs/api.md](docs/api.md) for complete API documentation.

## Configuration

Environment variables (prefix: `RFQ2BOQ_`):

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_DIR` | `./models/ner-bert-bilstm-crf-v1` | NER model path |
| `ONTOLOGY_DIR` | `./code/ontology` | Ontology data path |
| `TESSERACT_CMD` | `tesseract` | Tesseract OCR command |
| `OCR_CONFIDENCE_THRESHOLD` | `0.80` | Minimum OCR confidence |
| `ENTITY_CONFIDENCE_THRESHOLD` | `0.70` | Minimum entity confidence |
| `API_HOST` | `0.0.0.0` | API host |
| `API_PORT` | `8000` | API port |
| `MAX_FILE_SIZE_MB` | `50` | Maximum upload file size |

## Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up --build

# Run only the API
docker-compose up api

# Run only the UI
docker-compose up ui
```

## Success Metrics

| Metric | Target |
|--------|--------|
| NER span-F1 (micro) | >= 0.85 |
| Relation F1 | >= 0.75 |
| BOQ completeness | >= 90% |
| Latency (20-page PDF) | < 30s |
| Test coverage | >= 80% |

## Development

### Code Quality

```bash
# Run linting
make lint
# or directly: ruff check src config tests scripts

# Run type checking
make type
# or directly: mypy src --ignore-missing-imports

# Run pre-commit hooks
pre-commit run -a
```

### Generate Synthetic Data

```bash
python scripts/generate_synthetic.py --count 100 --output data/synthetic/
```

### Train NER Model

```bash
python scripts/train_ner.py --data data/annotations/ --output models/ner-bert-bilstm-crf-v1/
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