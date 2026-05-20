# RFQ2BOQ Presentation Slides

## Slide 1: Title

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║      AUTOMATED BILL OF QUANTITIES EXTRACTION                   ║
║            FROM CONSTRUCTION TENDER DOCUMENTS                  ║
║                                                                ║
║      Using Hybrid NLP + Domain Ontology                        ║
║                                                                ║
║      ─────────────────────────────────────────               ║
║                                                                ║
║      Srujan Sai                                                ║
║      B.Tech Final Year, Civil Engineering                      ║
║      IIT Hyderabad                                              ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

## Slide 2: Problem Statement

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE PROBLEM                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ❌ Manual BOQ extraction takes 40+ hours per tender             │
│                                                                 │
│  ❌ Government tenders (CPWD, PWD) use non-standard formats      │
│                                                                 │
│  ❌ Errors cause cost overruns and project delays               │
│                                                                 │
│  ❌ Different states have different tender document formats     │
│                                                                 │
│  ❌ Mixed English-Hindi terminology                             │
│                                                                 │
│  ──────────────────────────────────────────────────────────    │
│                                                                 │
│  SOLUTION: Automated extraction using NLP + Ontology           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Slide 3: System Architecture

```
                    INPUT
                       │
                       ▼
        ┌──────────────────────────────┐
        │     PDF INGESTION             │
        │  • PDFplumber + OCR           │
        │  • Camelot table extraction   │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │     NLP PIPELINE              │
        │                               │
        │  ┌────────────────────────┐  │
        │  │  NER (BERT-BiLSTM-CRF) │  │
        │  │  8 entity types        │  │
        │  └────────────┬───────────┘  │
        │              │              │
        │  ┌───────────▼───────────┐  │
        │  │  Relation Extraction │  │
        │  │  6 relation types     │  │
        │  └────────────┬───────────┘  │
        │              │              │
        │  ┌───────────▼───────────┐  │
        │  │  LLM Resolution      │  │
        │  │  (Claude API)        │  │
        │  └────────────────────────┘  │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │     DOMAIN ONTOLOGY           │
        │  • 249+ Materials             │
        │  • IS Standards               │
        │  • Unit Normalization         │
        └──────────────┬───────────────┘
                       │
                       ▼
                   OUTPUT
            ┌──────────┼──────────┐
            │          │          │
            ▼          ▼          ▼
         Excel       JSON       IFC/BIM
```

---

## Slide 4: Entity Types (BIOES Tagging)

```
┌─────────────────────────────────────────────────────────────────┐
│                    8 ENTITY TYPES                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MATERIAL     │ cement, steel, brick, concrete, sand            │
│  QUANTITY     │ 500, 1000, 2.5, 15000                           │
│  UNIT         │ kg, m³, sqm, bags, no.                          │
│  LOCATION     │ ground floor, level 2, roof                      │
│  DIMENSION    │ 10m x 20m, 500sqft, 3m depth                    │
│  STANDARD     │ IS 456, ASTM A615, IRC                           │
│  ACTION       │ supply, install, cast, erect                     │
│  GRADE        │ M25, Fe500, Class A, Grade 30                   │
│                                                                 │
│  ───────────────────────────────────────────────────────────   │
│                                                                 │
│  TAGGING SCHEME: BIOES                                          │
│                                                                 │
│  "Supply 500 bags of cement"                                    │
│  B-ACT S-QTY B-UNIT S-MAT                                       │
│                                                                 │
│  B = Begin, I = Inside, E = End, S = Single                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Slide 5: Ontology Validation

```
┌─────────────────────────────────────────────────────────────────┐
│                  ONTOLOGY VALIDATION LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CONSTRUCTION MATERIAL ONTOLOGY                                  │
│                                                                 │
│  CEMENT                                                         │
│  ├── typical_units: ["bags", "tonnes"]                           │
│  ├── grade_ranges: ["M15", "M20", "M25", ...]                  │
│  ├── standards: ["IS 269", "IS 8112", "IS 12269"]               │
│  └── co_occurrence: ["aggregate", "sand", "water"]             │
│                                                                 │
│  STEEL                                                          │
│  ├── typical_units: ["kg", "tonnes"]                            │
│  ├── grade_ranges: ["Fe250", "Fe415", "Fe500", "Fe550"]        │
│  └── standards: ["IS 2062", "IS 432 Part 1"]                    │
│                                                                 │
│  ───────────────────────────────────────────────────────────   │
│                                                                 │
│  VALIDATION RULES:                                              │
│  ✓ Grade must be in material.grade_ranges                       │
│  ✓ Unit must be in material.typical_units (or canonicalized)   │
│  ✓ Quantity must be within reasonable bounds                   │
│  ✓ Co-occurring materials should appear together              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Slide 6: Conflict Resolution Algorithm

```
┌─────────────────────────────────────────────────────────────────┐
│              HYBRID ML + RULE CONFLICT RESOLUTION                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│         EXTRACTED ENTITY                                         │
│              │                                                  │
│              ▼                                                   │
│     ┌─────────────────┐                                         │
│     │ CONFLICT CHECK  │                                         │
│     │ (Rule-based)    │                                         │
│     └────────┬────────┘                                         │
│              │                                                   │
│     ┌───────┴───────┐                                           │
│     │               │                                           │
│   NO              YES                                           │
│     │               │                                           │
│     ▼               ▼                                           │
│  ┌─────────┐  ┌─────────────────┐                              │
│  │ ACCEPT  │  │ CHECK BERT CONF │                              │
│  └─────────┘  └────────┬────────┘                              │
│                        │                                         │
│               ┌────────┴────────┐                              │
│               │                 │                               │
│            HIGH              LOW                                │
│               │                 │                               │
│               ▼                 ▼                               │
│          ┌─────────┐  ┌─────────────────┐                      │
│          │ ACCEPT  │  │ LLM VERIFICATION │                      │
│          │ BERT    │  │   (Claude API)   │                      │
│          └─────────┘  └─────────────────┘                      │
│                              │                                  │
│                              ▼                                  │
│                        ┌─────────┐                              │
│                        │ ACCEPT  │                              │
│                        │ RESOLVED│                              │
│                        └─────────┘                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Slide 7: Active Learning Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                   ACTIVE LEARNING LOOP                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   NEW RFQ DOCS  ──►  NER INFERENCE  ──►  ENTITY EXTRACTION      │
│                                              │                  │
│                           ┌─────────────────┘                  │
│                           ▼                                     │
│                   ┌─────────────────┐                          │
│                   │  CONFIDENCE      │                         │
│                   │  SCORING         │                          │
│                   └────────┬────────┘                          │
│                            │                                    │
│          ┌─────────────────┼─────────────────┐                  │
│          │                 │                 │                  │
│          ▼                 ▼                 ▼                  │
│     HIGH CONF          MED CONF          LOW CONF               │
│       (≥0.7)           (0.5-0.7)          (<0.5)                │
│          │                 │                 │                  │
│          ▼                 ▼                 ▼                  │
│      ADD TO BOQ       FLAG REVIEW    ──► HUMAN REVIEW           │
│                                              │                  │
│                                              ▼                  │
│                                      CORRECTED SAMPLES          │
│                                              │                  │
│                                              ▼                  │
│                                       MODEL RETRAINING          │
│                                              │                  │
│                                              ▼                  │
│                                        MODEL v1.4+             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Slide 8: Performance Results

```
┌─────────────────────────────────────────────────────────────────┐
│                     PERFORMANCE RESULTS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ENTITY-LEVEL F1 SCORES (SYNTHETIC TEST SET)                    │
│                                                                 │
│   ┌─────────────────┬──────┬──────┬──────┬──────┐              │
│   │ Model           │ MAT  │ QTY  │ UNIT │ LOC  │ ...          │
│   ├─────────────────┼──────┼──────┼──────┼──────┤              │
│   │ Gazetteer       │ 0.71 │ 0.83 │ 0.76 │ 0.54 │              │
│   │ BERT-linear     │ 0.94 │ 0.97 │ 0.95 │ 0.91 │              │
│   │ BiLSTM-CRF      │ 0.95 │ 0.97 │ 0.96 │ 0.93 │              │
│   │ BERT-BiLSTM-CRF │ 0.99 │ 0.99 │ 0.98 │ 0.97 │  ◄ BEST     │
│   │ SpERT           │ 0.97 │ 0.98 │ 0.97 │ 0.95 │              │
│   └─────────────────┴──────┴──────┴──────┴──────┘              │
│                                                                 │
│   ───────────────────────────────────────────────────────────  │
│                                                                 │
│   REAL-WORLD PERFORMANCE                                         │
│                                                                 │
│   ┌────────────────────┬─────────────────┐                      │
│   │ Metric             │ Value           │                      │
│   ├────────────────────┼─────────────────┤                      │
│   │ Synthetic F1       │ 99.6%           │                      │
│   │ Real-world F1      │ 67.05%          │                      │
│   │ Ontology boost     │ +8.3% precision │                      │
│   │ Processing speed   │ ~4 sec/page     │                      │
│   └────────────────────┴─────────────────┘                      │
│                                                                 │
│   ⚠ Domain shift: synthetic → real-world is the key challenge  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Slide 9: Dataset & Training

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATASET SUMMARY                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RFQ-BOQ-NER DATASET                                             │
│                                                                 │
│  ┌────────────┬────────────┬──────────┬───────────────┐       │
│  │ Split      │ Documents  │ Entities │ Avg Tokens    │       │
│  ├────────────┼────────────┼──────────┼───────────────┤       │
│  │ Train      │ 2,400      │ 48,320   │ 342           │       │
│  │ Val        │ 300        │ 6,210    │ 338           │       │
│  │ Test (syn) │ 300        │ 5,940    │ 341           │       │
│  │ Test (real)│ 50         │ 1,847    │ 1,203         │       │
│  └────────────┴────────────┴──────────┴───────────────┘       │
│                                                                 │
│  ────────────────────────────────────────────────────────────  │
│                                                                 │
│  TRAINING SETUP                                                  │
│  • Model: bert-base-cased                                        │
│  • Optimizer: AdamW (lr=5e-5)                                   │
│  • Epochs: 50 (early stopping @ patience=5)                      │
│  • Batch size: 16                                                │
│  • Hardware: Apple M2 Pro (16GB)                                │
│  • Training time: ~4.5 hours                                     │
│                                                                 │
│  SYNTHETIC DATA GENERATION:                                      │
│  • 200+ templates across 5 construction domains                 │
│  • Indian construction terminology (bags, cum, sqm)             │
│  • IS codes (IS 456, IS 8112, IS 2062)                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Slide 10: Applications & Export

```
┌─────────────────────────────────────────────────────────────────┐
│                   APPLICATIONS & EXPORT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GOVERNMENT TENDERS                                              │
│  • CPWD (Central Works Department)                               │
│  • Delhi PWD                                                     │
│  • State PWDs (Maharashtra, Karnataka, etc.)                     │
│  • Railway tenders                                               │
│  • Irrigation departments                                        │
│                                                                 │
│  ───────────────────────────────────────────────────────────   │
│                                                                 │
│  EXPORT FORMATS                                                  │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  EXCEL   │  │   JSON   │  │   IFC    │  │   SAP    │       │
│  │  BOQ     │  │  API     │  │  BIM     │  │  XML     │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                 │
│  ───────────────────────────────────────────────────────────   │
│                                                                 │
│  INTEGRATIONS                                                    │
│  • Autodesk Revit (IFC)                                          │
│  • SAP (ERP)                                                     │
│  • Oracle                                                        │
│  • CostX (cost estimation)                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Slide 11: Project Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                      PROJECT STRUCTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  rfq2boq/                                                        │
│  ├── src/                    # Production code                   │
│  │   ├── nlp/               # NLP pipeline (NER, RE, Layout)   │
│  │   ├── domain/            # Domain models (BOQ, entities)    │
│  │   ├── rules/             # Validation rules                  │
│  │   ├── llm/               # LLM client (Claude)               │
│  │   └── api/               # FastAPI routes                   │
│  ├── tests/                 # Test suite (237+ tests)           │
│  ├── data/                  # Datasets (3,000+ RFQs)            │
│  ├── models/                # Trained model checkpoints         │
│  ├── paper/                 # Academic paper draft               │
│  └── deliverables/          # Patent & presentation docs        │
│                                                                 │
│  STATS:                                                          │
│  • 200+ Python files                                           │
│  • 86%+ test coverage                                           │
│  • 237+ tests passing                                           │
│  • ~15,000 lines of code                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Slide 12: Future Work & Contact

```
┌─────────────────────────────────────────────────────────────────┐
│                      FUTURE WORK                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SHORT-TERM:                                                     │
│  • Annotate more real tender PDFs (target: 200+)                │
│  • Improve real-world F1 to 80%+                                │
│  • File provisional patent                                       │
│                                                                 │
│  MEDIUM-TERM:                                                    │
│  • Add Hindi language support                                    │
│  • Deploy as SaaS product                                        │
│  • Integrate with procurement platforms                          │
│                                                                 │
│  LONG-TERM:                                                     │
│  • Multi-language support (Tamil, Telugu, Bengali)             │
│  • Real-time tender monitoring                                   │
│  • Automated bid generation                                       │
│                                                                 │
│  ───────────────────────────────────────────────────────────   │
│                                                                 │
│  CONTACT                                                         │
│  • Developer: Srujan Sai                                         │
│  • Institution: IIT Hyderabad                                    │
│  • Project: https://github.com/rfq2boq/rfq2boq                   │
│  • Paper: ITcon Journal submission                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Slide 13: Thank You

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║                        THANK YOU                               ║
║                                                                ║
║   Questions?                                                    ║
║                                                                ║
║   ─────────────────────────────────────────────────────────   ║
║                                                                ║
║   GitHub:  github.com/rfq2boq/rfq2boq                          ║
║   Email:   srujansai@gmail.com                                  ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```