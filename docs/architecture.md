# Architecture Documentation

## System Overview

RFQ2BOQ transforms unstructured construction RFQ documents into structured Bill of Quantities using a hybrid NLP approach combining BERT-based machine learning with rule-based validation.

## Architecture Diagram

```
                         ┌──────────────────┐
                         │  Estimator / QS  │
                         │   (end user)     │
                         └────────┬─────────┘
                                  │ uploads RFQ PDF
                                  ▼
┌──────────────────────────────────────────────────────────────┐
│                     RFQ→BOQ SYSTEM                          │
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌─────────────┐  │
│  │  Ingest │→ │Preproc  │→ │ NLP/NER   │→ │Relations    │  │
│  │ (PDF)   │  │(clean)  │  │ (BERT)    │  │ (BiLSTM)    │  │
│  └─────────┘  └─────────┘  └──────────┘  └─────────────┘  │
│       │                                          │          │
│       │                                          ▼          │
│       │                                   ┌─────────────┐  │
│       │                                   │   Domain    │  │
│       │                                   │  (Assembler)│  │
│       │                                   └─────────────┘  │
│       │                                          │          │
│       ▼                                          ▼          │
│  ┌─────────┐                              ┌─────────────┐  │
│  │ Export  │←                             │  Validation│  │
│  │(Excel)  │                              │(Ontology)  │  │
│  └─────────┘                              └─────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Components

### 1. Ingestion (`src/ingest/`)

Handles PDF extraction with OCR fallback:

- **pdf_extractor.py** — Extracts text from born-digital PDFs using pdfplumber
- **ocr_processor.py** — OCR for scanned/image-based PDFs using pytesseract
- **layout_analyzer.py** — Detects sections (scope, specs, schedule)
- **preprocessor.py** — Text cleaning and normalization

### 2. NLP Pipeline (`src/nlp/`)

Named Entity Recognition and Relation Extraction:

- **ner/bert_ner.py** — BERT-BiLSTM-CRF model for 8 entity types
- **ner/trainer.py** — Training pipeline using HuggingFace Trainer
- **patterns/** — spaCy EntityRuler + regex patterns
- **pipeline.py** — Orchestrates NER + patterns + relations
- **re/** — Relation extraction using BiLSTM classifier

### 3. Domain Layer (`src/domain/`)

Business logic for BOQ assembly and validation:

- **models.py** — Pydantic models: Entity, Relation, BOQItem, ExtractionResult
- **boq_assembler.py** — Groups entities by material, builds BOQ items
- **ontology.py** — Construction material/standard knowledge base
- **validator.py** — Domain validation rules
- **confidence.py** — Confidence scoring

### 4. Export Layer (`src/export/`)

Output generation:

- **json_formatter.py** — Structured JSON output
- **excel_generator.py** — Styled Excel BOQ with color-coded confidence
- **report.py** — Markdown extraction report

### 5. API (`src/api/`)

FastAPI REST service:

- **main.py** — FastAPI app with CORS middleware
- **routes/** — upload, extract, boq, health endpoints
- **schemas.py** — Request/response models
- **dependencies.py** — Pipeline singleton container

### 6. UI (`src/ui/`)

Streamlit web interface:

- **app.py** — File upload, results table, download buttons

### 7. CLI (`src/cli/`)

Typer command-line interface:

- **main.py** — process, batch, evaluate, serve commands

## Data Flow

### PDF to BOQ

1. **Ingestion** — PDF → text + tables + layout metadata
2. **Preprocessing** — Clean text, sentence segmentation
3. **NER** — Text → entity spans (MATERIAL, QUANTITY, UNIT, etc.)
4. **Relation Extraction** — Entity pairs → relations (HAS_QUANTITY, etc.)
5. **Domain Assembly** — Entities + relations → BOQ items
6. **Validation** — Check material/standard/unit consistency
7. **Export** — BOQ items → Excel/JSON

## Entity Types

| Entity | Description | Example |
|--------|-------------|---------|
| MATERIAL | Construction material | cement, concrete, steel |
| QUANTITY | Numeric value | 100, 500, 1.5 |
| UNIT | Measurement unit | m³, kg, bags |
| LOCATION | Location in building | ground floor, basement |
| DIMENSION | Physical size | 230mm thick, Ø12mm |
| STANDARD | Industry standard | IS 456, ASTM A615 |
| ACTION | Work verb | supply, install, lay |
| GRADE | Quality grade | M20, Fe500 |

## Relation Types

| Relation | Head → Tail | Example |
|----------|-------------|---------|
| HAS_QUANTITY | MATERIAL → QUANTITY | concrete → 150 |
| HAS_UNIT | QUANTITY → UNIT | 150 → m³ |
| AT_LOCATION | MATERIAL → LOCATION | brickwork → ground floor |
| OF_GRADE | MATERIAL → GRADE | concrete → M20 |
| COMPLIES_WITH | MATERIAL → STANDARD | steel → IS 1786 |
| HAS_DIMENSION | MATERIAL → DIMENSION | wall → 230mm thick |

## Confidence Scoring

Per-entity confidence from NER model (0-1).

Per-BOQ-item confidence = weighted average of:
- Entity confidences (40%)
- Completeness (30%) — how many fields filled
- Ontology match bonus (10%)
- Rule validation (20%)

## Design Decisions

1. **Hybrid ML + Rules** — BERT-BiLSTM-CRF for NER, rules for validation (not pure LLM)
2. **Ontology-first** — Every entity typed against CTO knowledge base
3. **Stateless services** — Each stage persists to disk, resumable
4. **Confidence everywhere** — No silent drops, all outputs have confidence scores
5. **Two pipelines, one codepath** — Batch (CLI) and online (REST) share same code
