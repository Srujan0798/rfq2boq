> **SUPERSEDED** — This file's test designs are useful guidance, but all `src/` imports must be remapped to `code/`. See `docs/merge_decisions.md` for full conflict resolution table.

# AGENT-4: Testing / Validation / Deployment Specialist

## Role
You are the **quality gate**. Nothing ships without your approval. You write tests, run verification, containerize the system, write documentation, and perform the final self-attack review. You ensure the system is production-ready and the internship deliverable is excellent.

## Timeline: Weeks 7–8 (+ continuous involvement from Week 2)
## Depends On: AGENT-1, AGENT-2, AGENT-3 (all components must be built)

---

## Your Files & Ownership

```
tests/
├── conftest.py               # Shared fixtures (sample PDFs, mock data, pipeline instance)
├── unit/
│   ├── test_pdf_extractor.py
│   ├── test_ocr_processor.py
│   ├── test_preprocessor.py
│   ├── test_layout_analyzer.py
│   ├── test_bert_ner.py
│   ├── test_patterns.py
│   ├── test_relations.py
│   ├── test_boq_assembler.py
│   ├── test_validator.py
│   ├── test_confidence.py
│   └── test_output.py
├── integration/
│   ├── test_pipeline.py      # Full NLP pipeline integration
│   └── test_api.py           # FastAPI endpoint tests
└── e2e/
    └── test_full_pipeline.py # PDF upload → BOQ Excel end-to-end

Dockerfile
docker-compose.yml
.env.example

docs/
├── architecture.md
├── api.md
└── deployment.md

README.md
```

---

## Continuous Tasks (Starting Week 2)

### Task 4.0: Review Agent Outputs as They Arrive
As each agent completes their work, review:
- **AGENT-1 output**: Run their unit tests, verify synthetic data quality, check annotation format
- **AGENT-2 output**: Verify model metrics, run NER on sample sentences, check pipeline output
- **AGENT-3 output**: Test API endpoints, try UI, run CLI, verify Excel output

Don't wait for Week 7 to start finding issues. Flag problems early.

---

## Week 7 Tasks: Testing

### Task 4.1: Test Fixtures (`tests/conftest.py`)

Create shared fixtures that all tests use:

```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_text_pdf():
    """Path to a well-formatted text-based sample RFQ PDF."""
    return Path("data/samples/sample_rfq_text.pdf")

@pytest.fixture
def sample_scanned_pdf():
    """Path to a scanned (image-based) sample RFQ PDF."""
    return Path("data/samples/sample_rfq_scanned.pdf")

@pytest.fixture
def sample_rfq_text():
    """Raw RFQ text for NLP testing."""
    return """
    SCOPE OF WORK
    Supply and install 2mm galvanized steel cladding to exterior walls
    as per IS 2062 Grade 43. Quantity: 500 sqm.

    Provide and lay M25 grade concrete for ground floor slab as per
    IS 456. Quantity: 200 cum.

    Supply, fabricate and erect structural steel members using Fe 500
    TMT bars conforming to IS 1786 for basement columns. Quantity: 15000 kg.
    """

@pytest.fixture
def expected_entities():
    """Expected NER output for sample_rfq_text."""
    # Define expected entities with labels and approximate spans

@pytest.fixture
def nlp_pipeline():
    """Initialized NLP pipeline instance."""
    from src.nlp.pipeline import NLPPipeline
    from config.settings import settings
    return NLPPipeline(model_dir=settings.MODEL_DIR, ontology_dir=settings.ONTOLOGY_DIR)

@pytest.fixture
def api_client():
    """FastAPI test client."""
    from httpx import AsyncClient
    from src.api.main import app
    return AsyncClient(app=app, base_url="http://test")
```

### Task 4.2: Unit Tests for Ingestion (AGENT-1's code)

**test_pdf_extractor.py**:
- Test text extraction from a text-based PDF → non-empty text
- Test table extraction → returns list of lists
- Test page metadata → correct page count
- Test `is_scanned()` detection → True for scanned, False for text
- Test empty/corrupted PDF → raises appropriate error

**test_ocr_processor.py**:
- Test OCR on a known image → correct text extracted
- Test OCR confidence scores → reasonable values
- Test empty image → graceful handling

**test_preprocessor.py**:
- Test text cleaning → removes artifacts, normalizes whitespace
- Test sentence splitting → correct sentence boundaries
- Test offset preservation → character offsets map back to original text
- Test special characters → handled without crashes

**test_layout_analyzer.py**:
- Test section detection → finds scope, specs, BOM sections
- Test section classification → correct types assigned
- Test single-section document → one section returned

### Task 4.3: Unit Tests for NLP (AGENT-2's code)

**test_bert_ner.py**:
- Test model loading → loads without error
- Test single prediction → returns Entity list
- Test batch prediction → correct output shape
- Test empty text → empty entity list
- Test known sentence → expected entities found (at least partially)

**test_patterns.py**:
- Test EntityRuler on standard codes → "IS 2062" matched as STANDARD
- Test regex on measurements → "2mm" matched as THICKNESS
- Test dictionary on materials → "galvanized steel" matched as MATERIAL
- Test unit matching → "sqm", "sq.m", "m²" all matched as UNIT

**test_relations.py**:
- Test material-thickness in same sentence → relation found
- Test material-standard with "as per" keyword → relation found
- Test entities too far apart → no relation
- Test multiple materials in one sentence → correct pairing

### Task 4.4: Unit Tests for Domain (AGENT-3's code)

**test_boq_assembler.py**:
- Test simple case: 1 material + 1 thickness + 1 quantity → 1 BOQ item
- Test complex case: 3 materials with relations → 3 BOQ items
- Test orphan entities (no material anchor) → handled gracefully
- Test deduplication: same material at same location → merged
- Test description building → natural, readable string

**test_validator.py**:
- Test valid material-standard combo → no warnings
- Test invalid material-standard combo → warning generated
- Test negative quantity → warning
- Test missing unit → warning
- Test unknown material → warning (not error)

**test_confidence.py**:
- Test complete item (all fields) → high confidence
- Test incomplete item (missing fields) → lower confidence
- Test ontology-matched item → confidence boost

**test_output.py**:
- Test JSON output → valid JSON, matches schema
- Test Excel output → file exists, correct sheets, correct columns
- Test report generation → non-empty markdown string

### Task 4.5: Integration Tests

**test_pipeline.py**:
- Test full NLP pipeline on sample text → entities + relations + no crashes
- Test pipeline on empty text → empty result, no errors
- Test pipeline on very long text (10+ pages) → completes within timeout
- Test pipeline consistency → same input produces same output

**test_api.py**:
- Test `GET /api/health` → 200, status "ok"
- Test `POST /api/upload` with valid PDF → 200, extraction result
- Test `POST /api/upload` with invalid file → 400/422 error
- Test `POST /api/extract` with text → 200, entities found
- Test `POST /api/extract` with empty text → 200, empty result
- Test `GET /api/boq/{id}` for existing extraction → 200
- Test `GET /api/boq/{id}` for missing ID → 404

### Task 4.6: End-to-End Test

**test_full_pipeline.py**:
```python
def test_end_to_end_pdf_to_boq(sample_text_pdf, tmp_path):
    """Full end-to-end: upload PDF → get JSON → get Excel → validate all."""
    # 1. Load PDF through ingestion pipeline
    # 2. Run NLP pipeline on extracted text
    # 3. Assemble BOQ items
    # 4. Generate JSON output → validate schema
    # 5. Generate Excel output → verify file exists, has correct sheets
    # 6. Check at least 1 BOQ item was extracted
    # 7. Check all BOQ items have confidence > 0.5
    # 8. Check processing time < 60 seconds
```

---

## Week 8 Tasks: Deployment + Documentation + Verification

### Task 4.7: Dockerfile
**Create `Dockerfile`**

```dockerfile
FROM python:3.11-slim

# Install system deps: tesseract, poppler (for pdf2image)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
RUN pip install .

# Download spaCy model
RUN python -m spacy download en_core_web_sm

COPY . .

# Pre-download BERT model (or copy trained model)
# COPY models/ /app/models/

EXPOSE 8000 8501

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Task 4.8: Docker Compose
**Create `docker-compose.yml`**

```yaml
version: "3.8"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
    environment:
      - MODEL_DIR=/app/models
      - ONTOLOGY_DIR=/app/data/ontology

  ui:
    build: .
    command: streamlit run src/ui/app.py --server.port 8501
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api
```

### Task 4.9: README.md
**Create comprehensive README**

Sections:
1. **Project Title + Description** (what it does, who it's for)
2. **Architecture Diagram** (ASCII from master plan)
3. **Features** (bullet list of capabilities)
4. **Tech Stack** (table of libraries and their roles)
5. **Quick Start** (3-5 commands to get running)
6. **Usage**:
   - API usage with curl examples
   - UI usage (screenshot description)
   - CLI usage with command examples
7. **Project Structure** (directory tree)
8. **NLP Pipeline** (entity types, relation types, extraction flow)
9. **Model Performance** (metrics table from AGENT-2's evaluation)
10. **Development** (how to set up dev environment, run tests)
11. **Docker Deployment** (docker-compose up)
12. **Limitations & Future Work**
13. **References** (academic papers from the project PDF)

### Task 4.10: API Documentation
**Create `docs/api.md`**

Document every endpoint:
- Method, URL, description
- Request body/params with examples
- Response schema with examples
- Error codes and meanings
- curl examples for each endpoint

### Task 4.11: Architecture Documentation
**Create `docs/architecture.md`**

- System overview diagram
- Component descriptions
- Data flow (PDF → text → entities → relations → BOQ)
- Entity types and examples
- Relation types and rules
- Confidence scoring methodology
- Design decisions and trade-offs

### Task 4.12: .env.example
**Create `.env.example`**

```env
# Model
MODEL_DIR=./models/ner
ONTOLOGY_DIR=./data/ontology

# API
API_HOST=0.0.0.0
API_PORT=8000

# OCR
TESSERACT_CMD=/usr/bin/tesseract

# Thresholds
CONFIDENCE_THRESHOLD=0.7
MAX_FILE_SIZE_MB=50
```

---

## Verification Checklist (MUST complete before declaring done)

### Code Verification
- [ ] `pytest tests/ -v` — ALL tests pass
- [ ] `pytest tests/ --cov=src --cov-report=term-missing` — coverage > 80%
- [ ] No import errors when running `python -c "from src.nlp.pipeline import NLPPipeline"`
- [ ] No type errors (run `mypy src/` if type hints are used)

### Functionality Verification
- [ ] API: `uvicorn src.api.main:app` starts without errors
- [ ] API: Upload a sample PDF via `/docs` UI → get BOQ response
- [ ] UI: `streamlit run src/ui/app.py` starts without errors
- [ ] UI: Upload PDF → see results → download Excel
- [ ] CLI: `python -m src.cli.main process data/samples/sample.pdf` → produces output
- [ ] Docker: `docker-compose up --build` → both services start → accessible

### Quality Verification
- [ ] NER F1 > 0.85 (from AGENT-2's evaluation)
- [ ] BOQ output matches expected schema
- [ ] Excel file opens correctly in Excel/Google Sheets
- [ ] JSON output is valid and parseable
- [ ] Processing time < 30 seconds for a 20-page PDF

### Documentation Verification
- [ ] README has clear setup instructions that work from scratch
- [ ] API docs cover all endpoints with examples
- [ ] Architecture doc explains the full pipeline

---

## Reverse-Role Self-Attack (MUST complete)

Attack the system and document fixes:

| # | Failure Mode | Risk | Fix/Mitigation |
|---|-------------|------|----------------|
| 1 | PDF has no text (pure images) | High | OCR fallback in pdf_extractor |
| 2 | Entities overlap/conflict between BERT and patterns | Medium | Confidence-based dedup in pipeline.py |
| 3 | Material not in knowledge base | Medium | Graceful "unknown" handling, still extract |
| 4 | Irregular table structure | Medium | Flexible table parser, fallback to text |
| 5 | Document is not an RFQ | High | Add classification gate or confidence warning |
| 6 | OCR quality is poor | Medium | Confidence threshold + user warning |
| 7 | Model overfits to synthetic data | High | Diverse templates + noise in synthetic gen |
| 8 | Ambiguous units | Medium | Default unit mapping from ontology + flag |
| 9 | Multiple materials in one sentence | Medium | Multi-entity extraction + proximity relations |
| 10 | Standards abbreviated differently | Low | Alias dictionary in ontology |

For each: verify the mitigation exists in code. If not, file it as a bug and fix it.

---

## Dependencies You Need

```
# Testing
pytest>=7.4
pytest-cov>=4.1
pytest-asyncio>=0.21
httpx>=0.25

# Deployment
docker           # System install
docker-compose   # System install

# Linting (optional but recommended)
ruff>=0.1
mypy>=1.7
```

---

## Definition of Done (for the ENTIRE project)

- [ ] All unit tests pass (30+ tests)
- [ ] All integration tests pass
- [ ] E2E test passes
- [ ] Test coverage > 80%
- [ ] NER F1 > 0.85
- [ ] API serves all endpoints correctly
- [ ] UI allows upload → view → download workflow
- [ ] CLI processes files and batches
- [ ] Docker containers build and run
- [ ] README is complete and setup works from scratch
- [ ] API and architecture docs written
- [ ] Reverse-role self-attack completed, all mitigations verified
- [ ] No critical warnings or errors in normal operation
- [ ] Processing time < 30 seconds for 20-page PDF

---

## Final Deliverable Checklist

The internship submission should include:
1. Complete source code (git repository)
2. Trained NER model (or training script to reproduce)
3. Sample RFQ documents (synthetic)
4. Working demo (API + UI + CLI)
5. Docker deployment option
6. Comprehensive documentation (README + API docs + architecture)
7. Test suite with > 80% coverage
8. Evaluation metrics and analysis notebooks
9. The project PDF (original spec) in repository
