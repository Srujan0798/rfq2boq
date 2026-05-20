> **SUPERSEDED** — This file's code signatures are useful implementation guidance, but paths and entity names have been updated. See `docs/merge_decisions.md`. Key remaps: `src/` → `code/`, thickness → dimension, specification → grade, work_type → action. Streamlit UI confirmed as the MVP choice.

# AGENT-3: Frontend / Integration / Output Specialist

## Role
You are responsible for **everything after NLP extraction**: turning raw entities and relations into structured BOQ output, building the API, web UI, and CLI. You make the system usable and deliverable.

## Timeline: Weeks 5–7
## Depends On: AGENT-1 (ingestion pipeline), AGENT-2 (NLP pipeline + trained model)

---

## Your Files & Ownership

```
src/domain/
├── __init__.py
├── models.py                 # Pydantic data models (Entity, Relation, BOQItem, etc.)
├── boq_assembler.py          # Entities + Relations → BOQ line items
├── validator.py              # Domain validation rules
├── ontology.py               # Load + query knowledge base
└── confidence.py             # Confidence scoring system

src/output/
├── __init__.py
├── json_formatter.py         # Structured JSON output
├── excel_generator.py        # Styled Excel BOQ spreadsheet
└── report.py                 # Extraction summary report

src/api/
├── __init__.py
├── main.py                   # FastAPI application
├── routes/
│   ├── __init__.py
│   ├── upload.py             # POST /api/upload — PDF upload + full extraction
│   ├── extract.py            # POST /api/extract — text-only extraction
│   ├── boq.py                # GET /api/boq/{id} — retrieve BOQ result
│   └── health.py             # GET /api/health
├── schemas.py                # API request/response models
└── dependencies.py           # Shared dependencies (pipeline singleton)

src/ui/
└── app.py                    # Streamlit web application

src/cli/
└── main.py                   # Typer CLI tool
```

---

## What You Receive from AGENT-1 & AGENT-2

From **AGENT-1**:
- `src/ingestion/` — `PDFExtractor`, `OCRProcessor`, `LayoutAnalyzer`, `TextPreprocessor`
- `data/ontology/` — knowledge base JSONs
- `config/settings.py`, `config/constants.py`

From **AGENT-2**:
- `src/nlp/pipeline.py` — `NLPPipeline.process(text) -> ExtractionResult`
  - `ExtractionResult.entities: list[Entity]`
  - `ExtractionResult.relations: list[Relation]`
- Trained model in `MODEL_DIR`

---

## Week 5 Tasks: Domain Logic

### Task 3.1: Pydantic Data Models
**Create `src/domain/models.py`**

These models are used across the entire system:

```python
from pydantic import BaseModel
from datetime import datetime

class Entity(BaseModel):
    text: str
    label: str          # MATERIAL, THICKNESS, QUANTITY, UNIT, LOCATION, STANDARD, SPECIFICATION, WORK_TYPE
    start: int          # Character offset start in source text
    end: int            # Character offset end
    confidence: float   # 0.0–1.0
    source: str         # "bert" | "pattern" | "regex" | "dictionary"

class Relation(BaseModel):
    head: Entity
    tail: Entity
    relation_type: str  # material_has_thickness, material_at_location, etc.
    confidence: float

class BOQItem(BaseModel):
    item_no: int
    description: str                  # Human-readable description assembled from entities
    material: str | None = None
    specification: str | None = None
    thickness: str | None = None
    location: str | None = None
    quantity: float | None = None
    unit: str | None = None
    work_type: str | None = None
    confidence: float                 # Average confidence of constituent entities
    source_text: str                  # Original text this was extracted from
    source_page: int                  # Page number in source PDF

class ExtractionMetadata(BaseModel):
    total_items: int
    avg_confidence: float
    processing_time_sec: float
    pages_processed: int
    entity_counts: dict[str, int]     # {"MATERIAL": 15, "STANDARD": 8, ...}
    warnings: list[str]

class ExtractionResult(BaseModel):
    project_name: str
    extraction_date: datetime
    source_file: str
    entities: list[Entity]
    relations: list[Relation]
    boq_items: list[BOQItem]
    metadata: ExtractionMetadata
```

### Task 3.2: Ontology Loader
**Create `src/domain/ontology.py`**

```python
class ConstructionOntology:
    def __init__(self, ontology_dir: str):
        """Load all ontology JSON files."""

    def lookup_material(self, name: str) -> dict | None:
        """Find material by name or alias. Return full entry."""

    def lookup_standard(self, code: str) -> dict | None:
        """Find standard by code or alias."""

    def validate_material_standard(self, material: str, standard: str) -> bool:
        """Check if a standard is valid for a given material."""

    def get_default_unit(self, material: str) -> str | None:
        """Return the most common unit for a material."""

    def normalize_unit(self, unit_text: str) -> str:
        """Normalize unit text to standard symbol (e.g., 'sq.m' → 'sqm')."""
```

### Task 3.3: BOQ Assembler
**Create `src/domain/boq_assembler.py`**

This is the **core business logic** — it takes entities + relations and builds BOQ line items:

```python
class BOQAssembler:
    def __init__(self, ontology: ConstructionOntology):
        """Initialize with ontology for validation."""

    def assemble(self, entities: list[Entity], relations: list[Relation],
                 source_text: str, pages: list[int] = None) -> list[BOQItem]:
        """Convert entities + relations into BOQ line items."""
        # Algorithm:
        # 1. Group entities by MATERIAL (anchor entity)
        # 2. For each MATERIAL, find connected entities via relations:
        #    - thickness, standard, specification, quantity, unit, location, work_type
        # 3. Build description string from assembled parts
        # 4. Handle orphan entities (entities not linked to any material)
        # 5. Deduplicate similar BOQ items
        # 6. Assign sequential item numbers

    def _group_by_material(self, entities, relations) -> list[dict]:
        """Group related entities around each MATERIAL entity."""

    def _build_description(self, material_group: dict) -> str:
        """Generate human-readable description from entity group."""
        # Example: "Supply and install 2mm galvanized steel cladding to exterior walls as per IS 2062 Grade 43"

    def _deduplicate(self, items: list[BOQItem]) -> list[BOQItem]:
        """Merge duplicate/near-duplicate BOQ items."""
```

**Assembly logic in detail**:
1. Find all MATERIAL entities
2. For each material, follow relations to find its thickness, standard, spec, quantity, unit, location, work_type
3. If a material has no quantity (common), still create the BOQ item but flag as "quantity_missing" in warnings
4. If a material has no location, it's still valid (some BOQ items don't specify location)
5. Build a natural language description: `"{work_type} {thickness} {material} {specification} to {location} as per {standard}"`
6. Deduplicate: if two BOQ items have same material + location + spec, merge them (sum quantities)

### Task 3.4: Domain Validator
**Create `src/domain/validator.py`**

```python
class DomainValidator:
    def __init__(self, ontology: ConstructionOntology):
        """Initialize with ontology."""

    def validate_boq(self, items: list[BOQItem]) -> list[ValidationWarning]:
        """Validate all BOQ items, return warnings."""

    def _validate_item(self, item: BOQItem) -> list[ValidationWarning]:
        """Validate a single BOQ item."""
        # Checks:
        # - Material exists in ontology (or flag as unknown)
        # - Standard is valid for this material type
        # - Unit is appropriate for material (e.g., concrete → cum, not sqm)
        # - Quantity is in reasonable range (not negative, not absurdly large)
        # - Thickness is reasonable for material type
```

### Task 3.5: Confidence Scoring
**Create `src/domain/confidence.py`**

```python
class ConfidenceScorer:
    def score_item(self, item: BOQItem, entities: list[Entity]) -> float:
        """Calculate overall confidence for a BOQ item."""
        # Factors:
        # - Average entity confidence (from NER/pattern)
        # - Completeness (how many fields are filled)
        # - Ontology match (material/standard found in knowledge base)
        # - Validation pass (no warnings = higher confidence)

    def score_extraction(self, result: ExtractionResult) -> float:
        """Calculate overall extraction confidence."""
```

---

## Week 6 Tasks: Output + API

### Task 3.6: JSON Formatter
**Create `src/output/json_formatter.py`**

```python
class JSONFormatter:
    def format(self, result: ExtractionResult) -> str:
        """Convert ExtractionResult to formatted JSON string."""

    def save(self, result: ExtractionResult, output_path: str):
        """Save JSON to file."""
```

Output the full schema as defined in the master plan (project_name, extraction_date, boq_items array, metadata).

### Task 3.7: Excel Generator
**Create `src/output/excel_generator.py`**

Generate a professional, styled Excel BOQ spreadsheet:

```python
class ExcelGenerator:
    def generate(self, result: ExtractionResult, output_path: str):
        """Generate styled Excel BOQ file."""
        # Sheet 1: "BOQ" — main Bill of Quantities
        #   Columns: Item No | Description | Material | Specification |
        #            Thickness | Location | Quantity | Unit | Confidence
        #   Header row: bold, blue background
        #   Confidence color coding: green (>0.8), yellow (0.6-0.8), red (<0.6)
        #   Column widths auto-fitted
        #   Freeze top row
        #
        # Sheet 2: "Extraction Details" — raw entities and relations
        #   All entities with label, text, confidence, source
        #
        # Sheet 3: "Summary" — metadata
        #   Total items, avg confidence, processing time, warnings
```

### Task 3.8: Extraction Report
**Create `src/output/report.py`**

```python
class ReportGenerator:
    def generate(self, result: ExtractionResult) -> str:
        """Generate human-readable extraction report (markdown)."""
        # Sections:
        # - Summary (items found, avg confidence, time)
        # - Entity distribution (count per type)
        # - Warnings and flags
        # - Low-confidence items (for manual review)
```

### Task 3.9: FastAPI Application
**Create `src/api/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RFQ to BOQ Extraction API",
    description="NLP-powered RFQ document to BOQ structured data extraction",
    version="1.0.0",
)

# Add CORS for Streamlit/frontend access
# Include routers: upload, extract, boq, health
# On startup: load NLP pipeline (singleton)
```

### Task 3.10: API Routes
**Create route files in `src/api/routes/`**

**upload.py** — `POST /api/upload`
- Accept PDF file upload (multipart/form-data)
- Run full pipeline: PDF → text → NLP → BOQ → output
- Return ExtractionResult JSON
- Support query params: `?format=json` or `?format=excel` (return file download)

**extract.py** — `POST /api/extract`
- Accept raw text (JSON body)
- Run NLP pipeline only (skip PDF ingestion)
- Return entities + relations + BOQ items

**boq.py** — `GET /api/boq/{extraction_id}`
- Retrieve a previous extraction result by ID
- Support `?format=json|excel|csv`
- (Store results in memory or simple file-based cache)

**health.py** — `GET /api/health`
- Return system status: model loaded, ontology loaded, version

### Task 3.11: API Schemas
**Create `src/api/schemas.py`**

```python
class UploadResponse(BaseModel):
    extraction_id: str
    result: ExtractionResult
    download_url: str | None = None

class ExtractRequest(BaseModel):
    text: str
    project_name: str = "Untitled"

class ExtractResponse(BaseModel):
    extraction_id: str
    result: ExtractionResult

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str
```

---

## Week 7 Tasks: UI + CLI

### Task 3.12: Streamlit Web UI
**Create `src/ui/app.py`**

Build a demo-quality web interface:

```
Page Layout:
┌──────────────────────────────────────────────┐
│  RFQ to BOQ Extraction System      [logo]    │
├──────────────────────────────────────────────┤
│                                              │
│  📄 Upload RFQ Document                      │
│  ┌──────────────────────────────┐            │
│  │  Drag & drop PDF here        │            │
│  │  or click to browse          │            │
│  └──────────────────────────────┘            │
│  [Extract BOQ]                               │
│                                              │
├──────────────────────────────────────────────┤
│  Results                                     │
│                                              │
│  Tab: [BOQ Table] [Entities] [Report]        │
│                                              │
│  BOQ Table:                                  │
│  ┌─────┬────────────┬─────┬─────┬──────┐    │
│  │ # │ Description │ Qty │ Unit│ Conf │    │
│  ├─────┼────────────┼─────┼─────┼──────┤    │
│  │ 1 │ 2mm GI...  │ 500 │ sqm │ 0.92 │    │
│  │ 2 │ M25 conc...│ 200 │ cum │ 0.88 │    │
│  └─────┴────────────┴─────┴─────┴──────┘    │
│                                              │
│  [Download JSON] [Download Excel] [Report]   │
│                                              │
├──────────────────────────────────────────────┤
│  Metadata                                    │
│  Items: 25 │ Avg Confidence: 0.87            │
│  Processing Time: 12.5s │ Pages: 15          │
│  Warnings: 2                                 │
└──────────────────────────────────────────────┘
```

Features:
- File upload with drag-and-drop
- Progress bar during extraction
- BOQ results table with color-coded confidence
- Entity viewer (highlight entities in source text)
- Download buttons: JSON, Excel, CSV
- Extraction metadata and warnings display

### Task 3.13: Typer CLI Tool
**Create `src/cli/main.py`**

```python
import typer
app = typer.Typer(help="RFQ to BOQ Extraction CLI")

@app.command()
def process(
    input_path: str,                    # PDF file path
    output: str = "boq_output.xlsx",    # Output file path
    format: str = "excel",              # json | excel | csv
    verbose: bool = False,
):
    """Process a single RFQ PDF and generate BOQ."""

@app.command()
def batch(
    input_dir: str,                     # Directory of PDFs
    output_dir: str = "output/",
    format: str = "excel",
):
    """Process all PDFs in a directory."""

@app.command()
def evaluate(
    test_data: str,                     # Path to test data
):
    """Run model evaluation and print metrics."""

if __name__ == "__main__":
    app()
```

CLI usage examples:
```bash
# Process single PDF
python -m src.cli.main process data/samples/sample_rfq.pdf --output boq.xlsx

# Batch process
python -m src.cli.main batch data/raw/ --output-dir output/ --format json

# Evaluate model
python -m src.cli.main evaluate data/annotated/test.json
```

---

## Unit & Integration Tests You Must Write

```
tests/unit/
├── test_boq_assembler.py     # Test entity grouping, description building, dedup
├── test_validator.py         # Test domain validation rules
├── test_output.py            # Test JSON, Excel, report generation
└── test_confidence.py        # Test confidence scoring

tests/integration/
├── test_pipeline.py          # Full pipeline: PDF → text → entities → BOQ
└── test_api.py               # API endpoint tests with httpx
```

---

## Dependencies You Need

```
# Domain
pydantic>=2.5

# Output
openpyxl>=3.1       # Excel generation

# API
fastapi>=0.104
uvicorn>=0.24
python-multipart>=0.0.6   # File uploads

# UI
streamlit>=1.28

# CLI
typer>=0.9
rich>=13.0          # Pretty terminal output

# Testing
httpx>=0.25         # Async API testing
pytest-asyncio>=0.21
```

---

## Definition of Done

- [ ] All Pydantic models defined and used consistently across modules
- [ ] BOQ assembler correctly groups entities and builds line items
- [ ] Domain validator catches invalid material-standard combos and unreasonable quantities
- [ ] Confidence scorer produces meaningful scores (higher for complete, ontology-matched items)
- [ ] JSON output matches the schema from the master plan
- [ ] Excel output is professionally styled with color-coded confidence
- [ ] FastAPI serves all 4 endpoints, auto-generates OpenAPI docs at `/docs`
- [ ] Streamlit UI allows upload → view → download workflow
- [ ] CLI processes single files and batch directories
- [ ] Integration tests pass for full PDF-to-BOQ pipeline
- [ ] API tests pass for all endpoints

---

## Handoff to AGENT-4

When you're done, AGENT-4 needs:
1. `src/api/main.py` — running FastAPI app for API testing
2. `src/ui/app.py` — running Streamlit app for UI testing
3. `src/cli/main.py` — working CLI for end-to-end testing
4. All output formats (JSON, Excel) for validation
5. The full pipeline wired together: PDF → ingestion → NLP → domain → output
