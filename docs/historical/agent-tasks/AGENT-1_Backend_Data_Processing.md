> **SUPERSEDED** — This file's code signatures are useful implementation guidance, but architectural decisions (entity names, tagging scheme, directory paths) have been overridden by `plan/` frozen specs. See `docs/merge_decisions.md` for the 15 conflict resolutions. Key remaps: `src/` → `code/`, BIO → BIOES, THICKNESS → DIMENSION, WORK_TYPE → ACTION, SPECIFICATION → GRADE.

# AGENT-1: Backend / Data / Processing Specialist

## Role
You are responsible for the **data foundation** of the RFQ-to-BOQ system. You build the document ingestion pipeline, the construction knowledge base, and the synthetic data generator. Everything downstream depends on your output quality.

## Timeline: Weeks 1–2

---

## Your Files & Ownership

```
config/
├── __init__.py
├── settings.py              # Pydantic settings (paths, model dirs, thresholds)
└── constants.py             # Entity labels, relation types, confidence thresholds

data/
├── ontology/
│   ├── materials.json       # 200+ construction materials with properties
│   ├── standards.json       # 50+ standards (IS, ASTM, BS EN, DIN)
│   ├── units.json           # All construction units (sqm, cum, rmt, kg, nos...)
│   └── locations.json       # 50+ building zones/areas
├── synthetic/               # Generated synthetic RFQ documents
├── annotated/               # BIO-tagged NER training data
└── samples/                 # Demo/test PDFs

src/ingestion/
├── __init__.py
├── pdf_extractor.py         # pdfplumber: text + tables + page metadata
├── ocr_processor.py         # Tesseract OCR for scanned documents
├── layout_analyzer.py       # Detect tables, headers, sections, lists
└── preprocessor.py          # Text cleaning, normalization, sentence splitting

scripts/
├── generate_synthetic.py    # Synthetic RFQ document generator
└── annotate_data.py         # Auto-annotation pipeline (BIO format)
```

---

## Week 1 Tasks: Project Setup + Knowledge Base

### Task 1.1: Project Configuration
**Create `config/settings.py`**
```python
# Use pydantic-settings for type-safe config
# Keys to include:
#   - PDF_UPLOAD_DIR, SYNTHETIC_DATA_DIR, ANNOTATED_DATA_DIR
#   - MODEL_DIR (where trained BERT model is saved)
#   - TESSERACT_CMD path
#   - CONFIDENCE_THRESHOLD (default 0.7)
#   - MAX_FILE_SIZE_MB (default 50)
#   - SUPPORTED_FORMATS: [".pdf"]
```

### Task 1.2: Constants Definition
**Create `config/constants.py`**
```python
# Entity labels for NER
ENTITY_LABELS = [
    "MATERIAL",       # galvanized steel, HDPE pipe, M25 concrete
    "THICKNESS",      # 2mm, 50mm thick, gauge 16
    "QUANTITY",        # 500, 100, 25
    "UNIT",           # sqm, m, kg, nos, cum, rmt
    "LOCATION",       # ground floor, roof level, basement
    "STANDARD",       # IS 2062, ASTM A36, BS EN 10025
    "SPECIFICATION",  # Grade 43, M25, Fe 500
    "WORK_TYPE",      # supply and install, fabrication, erection
]

# BIO tags: B-MATERIAL, I-MATERIAL, B-THICKNESS, I-THICKNESS, ..., O
BIO_LABELS = ["O"] + [f"{prefix}-{label}" for label in ENTITY_LABELS for prefix in ["B", "I"]]

# Relation types
RELATION_TYPES = [
    "material_has_thickness",
    "material_at_location",
    "material_meets_standard",
    "material_has_quantity",
    "material_has_spec",
    "work_uses_material",
]

# Section types for classification
SECTION_TYPES = ["scope", "specifications", "commercial", "general", "bill_of_materials"]
```

### Task 1.3: Construction Knowledge Base
**Create 4 JSON files in `data/ontology/`**

**materials.json** — 200+ entries:
```json
{
  "materials": [
    {
      "name": "galvanized steel",
      "aliases": ["GI steel", "galv steel", "galvanised steel"],
      "category": "metals",
      "common_units": ["sqm", "kg", "rmt"],
      "common_standards": ["IS 2062", "IS 277"]
    },
    ...
  ]
}
```
Categories: metals, concrete, polymers/plastics, wood/timber, insulation, roofing, waterproofing, glass, masonry, finishes, piping, electrical, HVAC.

**standards.json** — 50+ entries:
```json
{
  "standards": [
    {
      "code": "IS 2062",
      "full_name": "Hot Rolled Medium and High Tensile Structural Steel",
      "aliases": ["IS2062", "IS-2062"],
      "applies_to": ["structural steel", "mild steel", "steel plate"]
    },
    ...
  ]
}
```
Include IS (Indian), ASTM (American), BS EN (British/European), DIN (German) standards.

**units.json**:
```json
{
  "units": [
    {"symbol": "sqm", "aliases": ["sq.m", "sq m", "m2", "m²"], "full_name": "square meter", "dimension": "area"},
    {"symbol": "cum", "aliases": ["cu.m", "cu m", "m3", "m³"], "full_name": "cubic meter", "dimension": "volume"},
    {"symbol": "rmt", "aliases": ["rm", "r.m.", "running meter"], "full_name": "running meter", "dimension": "length"},
    {"symbol": "kg", "aliases": ["kgs", "kilogram"], "full_name": "kilogram", "dimension": "weight"},
    {"symbol": "nos", "aliases": ["no.", "no", "numbers", "each"], "full_name": "numbers", "dimension": "count"},
    ...
  ]
}
```

**locations.json**:
```json
{
  "locations": [
    {"name": "basement", "aliases": ["basement level", "below ground", "cellar"]},
    {"name": "ground floor", "aliases": ["GF", "ground level", "grade level"]},
    {"name": "first floor", "aliases": ["1st floor", "FF"]},
    {"name": "roof level", "aliases": ["rooftop", "terrace", "roof"]},
    {"name": "exterior walls", "aliases": ["external walls", "outer walls", "facade"]},
    ...
  ]
}
```

---

## Week 2 Tasks: Document Ingestion Pipeline + Synthetic Data

### Task 1.4: PDF Text Extraction
**Create `src/ingestion/pdf_extractor.py`**

Responsibilities:
- Use `pdfplumber` to extract text page-by-page
- Extract tables separately (preserve structure as list-of-lists)
- Return page metadata (page number, dimensions)
- Handle multi-column layouts
- Fallback: if text extraction yields < 50 chars per page, flag as "likely scanned"

```python
class PDFExtractor:
    def extract(self, pdf_path: str) -> DocumentContent:
        """Returns DocumentContent with pages, tables, metadata."""

    def extract_text(self, pdf_path: str) -> list[PageText]:
        """Extract text per page."""

    def extract_tables(self, pdf_path: str) -> list[TableData]:
        """Extract tables with page numbers."""

    def is_scanned(self, pdf_path: str) -> bool:
        """Check if PDF needs OCR."""
```

### Task 1.5: OCR Processor
**Create `src/ingestion/ocr_processor.py`**

Responsibilities:
- Convert PDF pages to images using `pdf2image`
- Run Tesseract OCR on each image
- Return text with confidence scores per page
- Support language configuration (default: English)

```python
class OCRProcessor:
    def process(self, pdf_path: str) -> list[OCRPage]:
        """OCR all pages, return text + confidence."""

    def process_page(self, image) -> OCRPage:
        """OCR a single page image."""
```

### Task 1.6: Layout Analyzer
**Create `src/ingestion/layout_analyzer.py`**

Responsibilities:
- Detect document sections by headers/formatting
- Identify section types: scope, specifications, bill of materials, commercial, general
- Detect table regions vs paragraph regions
- Return structured section list with type + content + page range

```python
class LayoutAnalyzer:
    def analyze(self, pages: list[PageText]) -> list[DocumentSection]:
        """Segment document into typed sections."""
```

### Task 1.7: Text Preprocessor
**Create `src/ingestion/preprocessor.py`**

Responsibilities:
- Clean text: remove headers/footers, page numbers, artifacts
- Normalize: standardize whitespace, fix encoding, expand abbreviations
- Segment into sentences using spaCy sentence splitter
- Preserve original character offsets (needed for NER span mapping)

```python
class TextPreprocessor:
    def preprocess(self, raw_text: str) -> PreprocessedText:
        """Clean, normalize, and segment text."""

    def clean(self, text: str) -> str:
        """Remove noise, normalize whitespace."""

    def segment_sentences(self, text: str) -> list[Sentence]:
        """Split into sentences with offsets."""
```

### Task 1.8: Synthetic RFQ Generator
**Create `scripts/generate_synthetic.py`**

This is CRITICAL — it produces all training data for AGENT-2's NER model.

Responsibilities:
- Load construction knowledge base (ontology JSONs)
- Generate 300–500 realistic RFQ documents
- Each document contains:
  - **Scope of Work** (3–8 paragraphs, free-text describing requirements)
  - **Technical Specifications** (structured specs with standards references)
  - **Bill of Materials** (table format with material, qty, unit, spec)
  - **General Terms** (boilerplate)
- Add realistic variation:
  - Synonyms ("supply and install" vs "supply & erect" vs "provide and fix")
  - Abbreviations ("GI" for galvanized iron, "MS" for mild steel)
  - Typos (5% of documents)
  - Mixed formats (paragraphs + bullets + tables)
- Save each as:
  - `data/synthetic/{id}.txt` (plain text with section markers)
  - `data/synthetic/{id}.pdf` (generated PDF for ingestion testing)
  - `data/synthetic/{id}_metadata.json` (ground truth entities + relations)

### Task 1.9: Auto-Annotation Pipeline
**Create `scripts/annotate_data.py`**

Responsibilities:
- Read synthetic documents + their metadata (ground truth)
- Convert entity spans to BIO/IOB tag format at token level
- Generate relation triples from metadata
- Output:
  - `data/annotated/train.json` (70% of corpus)
  - `data/annotated/val.json` (15%)
  - `data/annotated/test.json` (15%)
- Each entry format:
```json
{
  "tokens": ["Supply", "and", "install", "2mm", "galvanized", "steel", "cladding"],
  "ner_tags": ["B-WORK_TYPE", "I-WORK_TYPE", "I-WORK_TYPE", "B-THICKNESS", "B-MATERIAL", "I-MATERIAL", "I-MATERIAL"],
  "relations": [
    {"head": [4,6], "tail": [3,3], "type": "material_has_thickness"}
  ]
}
```

---

## Unit Tests You Must Write

```
tests/unit/
├── test_pdf_extractor.py     # Test text extraction, table extraction, scanned detection
├── test_ocr_processor.py     # Test OCR on sample images
├── test_preprocessor.py      # Test cleaning, normalization, sentence splitting
└── test_layout_analyzer.py   # Test section detection, type classification
```

Test with at least:
- A well-formatted text PDF
- A scanned PDF (image-based)
- A PDF with tables
- An empty/corrupted PDF (error handling)
- Edge cases: very long pages, mixed languages, special characters

---

## Dependencies You Need

```
pdfplumber>=0.10
pytesseract>=0.3
Pillow>=10.0
pdf2image>=1.16
spacy>=3.7
pydantic>=2.5
pydantic-settings>=2.1
fpdf2>=2.7           # For generating synthetic PDFs
```

---

## Definition of Done

- [ ] `config/settings.py` and `config/constants.py` created and importable
- [ ] All 4 ontology JSON files populated with 200+ materials, 50+ standards, units, locations
- [ ] `pdf_extractor.py` extracts text + tables from sample PDFs correctly
- [ ] `ocr_processor.py` handles scanned PDFs with reasonable accuracy
- [ ] `layout_analyzer.py` detects and classifies document sections
- [ ] `preprocessor.py` cleans and segments text with offset preservation
- [ ] `generate_synthetic.py` produces 300+ diverse synthetic RFQ documents
- [ ] `annotate_data.py` produces BIO-tagged train/val/test splits
- [ ] All unit tests pass
- [ ] Code has type hints and docstrings on public methods

---

## Handoff to AGENT-2

When you're done, AGENT-2 needs:
1. `data/annotated/train.json`, `val.json`, `test.json` — BIO-tagged NER training data
2. `data/ontology/` — knowledge base JSONs (for pattern matching)
3. `src/ingestion/` — working pipeline that produces clean text from PDFs
4. `config/constants.py` — entity labels and BIO tag list

**Quality matters**: If your synthetic data is poor or annotations are wrong, AGENT-2's NER model will fail. Verify annotation quality by spot-checking 20+ samples manually.
