# Figure 1: RFQ2BOQ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RFQ2BOQ SYSTEM ARCHITURE                              │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌──────────────────┐
                              │   INPUT LAYER    │
                              │  PDF Tender Docs │
                              │  (CPWD/PWD/Govt) │
                              └────────┬─────────┘
                                       │
                                       ▼
                         ┌────────────────────────────┐
                         │     INGESTION MODULE       │
                         │  • PDF Parser (PyPDF2)     │
                         │  • OCR (Tesseract)         │
                         │  • Table Extraction       │
                         └────────────┬───────────────┘
                                      │
                                      ▼
                         ┌────────────────────────────┐
                         │      NLP PIPELINE          │
                         │                            │
                         │  ┌──────────────────────┐  │
                         │  │  NER (BiLSTM-CRF)    │  │
                         │  │  LayoutLMv3 + SpERT  │  │
                         │  └──────────┬───────────┘  │
                         │             │              │
                         │  ┌──────────▼───────────┐  │
                         │  │  Relation Extraction │  │
                         │  │  (BERT-based)        │  │
                         │  └──────────┬───────────┘  │
                         │             │              │
                         │  ┌──────────▼───────────┐  │
                         │  │  LLM Ambiguity       │  │
                         │  │  Resolution (Claude) │  │
                         │  └──────────────────────┘  │
                         └────────────┬───────────────┘
                                      │
                                      ▼
                         ┌────────────────────────────┐
                         │    DOMAIN ONTOLOGY          │
                         │  • 249+ Materials           │
                         │  • Construction Rules       │
                         │  • Unit Normalization       │
                         │  • Grade Standards (IS)     │
                         └────────────┬───────────────┘
                                      │
                                      ▼
                         ┌────────────────────────────┐
                         │      BOQ ASSEMBLER          │
                         │  • Entity Linking           │
                         │  • Quantity Reconciliation  │
                         │  • Rate Estimation          │
                         │  • Validation               │
                         └────────────┬───────────────┘
                                      │
                         ┌────────────┴───────────────┐
                         │                            │
                         ▼                            ▼
              ┌──────────────────┐       ┌──────────────────┐
              │   OUTPUT LAYER   │       │  OUTPUT LAYER    │
              │   Excel/CSV BOQ  │       │  JSON/IFC/SAP   │
              └──────────────────┘       └──────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           SUPPORTING SYSTEMS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │   Neo4j  │  │  MLflow  │  │  Redis   │  │PostgreSQL│  │ Active Learn │   │
│  │   KG    │  │ Registry │  │  Cache   │  │  Multi-  │  │  Loop        │   │
│  │         │  │          │  │          │  │ tenancy  │  │              │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### Input Layer
- **PDF Tender Documents**: Government RFQs (CPWD, PWD, irrigation, electrical)
- **Formats**: Scanned images, native PDF text, table-heavy documents

### Ingestion Module
- **PDF Parser**: Extracts text and metadata from PDF files
- **OCR Engine**: Processes scanned documents (Tesseract)
- **Table Extractor**: Uses Camelot for tabular data extraction

### NLP Pipeline
1. **NER (Named Entity Recognition)**
   - Primary: BERT-BiLSTM-CRF with BIOES tagging
   - Alternative: LayoutLMv3 for visual document understanding
   - Joint: SpERT for simultaneous NER + Relation Extraction

2. **Relation Extraction**: Identifies relationships between entities (HAS_QUANTITY, HAS_UNIT, etc.)

3. **LLM Ambiguity Resolution**: Claude API for low-confidence predictions (< 0.5)

### Domain Ontology
- **249 Construction Materials**: Hierarchical organization
- **Business Rules**: Material-specific constraints
- **Standards**: Indian Bureau of Standards (IS codes)

### BOQ Assembler
- **Entity Linking**: Connects extracted entities to canonical materials
- **Quantity Reconciliation**: Validates quantities against context
- **Rate Estimation**: Cost per unit calculation
- **Validation**: Rule-based quality checks

### Output Formats
- **Excel/CSV**: Standard BOQ format
- **JSON**: Structured API output
- **IFC**: BIM integration
- **SAP**: ERP system integration