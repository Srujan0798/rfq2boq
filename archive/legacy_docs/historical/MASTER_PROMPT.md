# RFQ2BOQ — MASTER PROMPT
## Complete Project Execution Framework

```
You are leading an NLP/AI project: "RFQ to BOQ Scope Extraction using NLP system"
Your setup: Claude Opus as orchestrator (GURU) + 3-4 MiniMax agents as workers
Your workflow: Master Prompt → 9-Step Plan → Brutal Verification → Reverse Role Check

GOAL: Build an automated system that transforms unstructured RFQ (Request for Quote)
documents into structured Bill of Quantities (BOQ) data for construction estimation.

CORE PIPELINE:
PDF/OCR → NLP (NER, Relation Extraction) → Rule Validation → BOQ Generation
```

## PROJECT CONTEXT

**What is RFQ to BOQ?**
- RFQ (Request for Quote): Unstructured tender document with specifications, quantities, materials
- BOQ (Bill of Quantities): Structured table listing items, quantities, unit rates, totals
- Problem: Manual extraction is slow (70% time savings with automation), error-prone

**Key Technologies:**
- NLP: NER (BERT/RoBERTa), Relation Extraction, Semantic Parsing
- PDF Processing: OCR (Tesseract), Layout Analysis
- Validation: Rule-based + Cross-reference with knowledge base
- Output: Structured JSON/Excel matching BOQ format

**Reference Papers/Sources** (from project scope):
- Zhang & El-Gohary (2015) — Semantic NLP-Based Information Extraction
- Sousa et al. (2024) — NLP in Construction Budgeting
- Nabavi et al. (2023) — NLP for BIM Information Extraction
- Microsoft NLP Recipes — NER using BERT
- AEC Contracts — Scope Extraction Risks

---

## 9-STEP EXECUTION PLAN

### PHASE 1: PROJECT SETUP (Steps 1-2)
**Step 1: Environment & Architecture**
- [ ] Create project structure (prompts/, docs/, src/, tests/, results/, verification/)
- [ ] Set up Python environment (python 3.10+, pip, venv)
- [ ] Install dependencies: transformers, torch, pdfplumber/pypdf2, spaCy, scikit-learn
- [ ] Design pipeline architecture: PDF → Preprocess → NER → Relation → Validation → BOQ
- [ ] Create data directory structure

**Step 2: Data Collection & Understanding**
- [ ] Gather sample RFQ documents (real construction tender PDFs)
- [ ] Analyze document structure: sections, tables, common patterns
- [ ] Define BOQ schema: item_code, description, unit, quantity, material_type, location, standards
- [ ] Create entity taxonomy: MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD
- [ ] Map relations: ITEM_HAS_MATERIAL, ITEM_HAS_QUANTITY, ITEM_HAS_LOCATION

### PHASE 2: CORE DEVELOPMENT (Steps 3-5)
**Step 3: PDF Processing & Preprocessing**
- [ ] Implement PDF text extraction (pdfplumber for layout-aware)
- [ ] OCR integration for scanned documents (Tesseract)
- [ ] Section identification: find specifications, items list, scope sections
- [ ] Table extraction: identify BOQ-like tables in RFQ
- [ ] Text cleaning: normalize units, handle special characters

**Step 4: NER Implementation**
- [ ] Fine-tune BERT/RoBERTa for construction domain NER
- [ ] Train on labeled RFQ data (or use pre-trained + domain adaptation)
- [ ] Entity types: MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ITEM_DESCRIPTION
- [ ] Confidence thresholds and fallback rules
- [ ] Evaluate with precision/recall/F1 per entity type

**Step 5: Relation Extraction & Validation**
- [ ] Implement relation extraction (BERT classifier or transformer encoder)
- [ ] Relation types: HAS_UNIT, HAS_QUANTITY, HAS_MATERIAL, HAS_LOCATION, HAS_STANDARD
- [ ] Rule-based validation: unit-quantity consistency, required fields check
- [ ] Cross-reference with construction knowledge base
- [ ] Ambiguity resolution for missing/incomplete fields

### PHASE 3: INTEGRATION & OUTPUT (Steps 6-7)
**Step 6: BOQ Generation & Formatting**
- [ ] Map extracted entities to BOQ schema
- [ ] Handle quantity calculations (running meters, area formulas)
- [ ] Generate structured JSON output
- [ ] Export to Excel/CSV format
- [ ] Include confidence scores and validation flags

**Step 7: Testing & Evaluation**
- [ ] Create test dataset (50+ RFQ samples with manual annotations)
- [ ] Evaluate NER: Precision, Recall, F1 per entity type
- [ ] Evaluate relation extraction: accuracy
- [ ] Evaluate end-to-end: BOQ completeness, accuracy vs manual
- [ ] Benchmark: processing time per page

### PHASE 4: REFINEMENT (Steps 8-9)
**Step 8: Error Analysis & Improvement**
- [ ] Analyze failure cases: missed entities, wrong relations, parsing errors
- [ ] Improve handling of: tables with merged cells, multi-column layouts, non-standard formats
- [ ] Add support for: variations in unit notation, currency, measurement systems
- [ ] Fine-tune on project-specific patterns

**Step 9: Documentation & Handoff**
- [ ] Write technical documentation (README, API docs)
- [ ] Create user guide: how to run the system
- [ ] Document limitations and known issues
- [ ] Prepare presentation for stakeholders
- [ ] Final verification against requirements

---

## ORCHESTRATION WORKFLOW

```
CLAUDE OPUS (GURU/ORCHESTRATOR)
├── Analyzes RFQ scope document
├── Breaks down into tasks for agents
├── Assigns to MiniMax agents (3-4 workers)
├── Reviews agent outputs
├── Validates against verification checklist
└── Iterates until acceptable

MINIMAX AGENTS (WORKERS)
├── Agent-1: PDF Processing & Text Extraction
├── Agent-2: NER Model Training & Inference
├── Agent-3: Relation Extraction & Validation
└── Agent-4: BOQ Generation & Output Formatting
```

## PROMPTS YOU NEED

| Prompt | Purpose | File |
|--------|---------|------|
| ORC_PROMPT | Professor simulation, brutal review | prompts/archive/ORC_PROMPT.md |
| GURU_PROMPT | Orchestrator instructions | prompts/archive/GURU_PROMPT.md |
| VERIFICATION_PROMPT | Line-by-line code + theory check | prompts/archive/VERIFICATION_PROMPT.md |
| AGENT_PROMPTS | Per-agent task definitions | prompts/agent_*.md |
| MASTER_PROMPT | This file — overall guidance | MASTER_PROMPT.md |

## SUCCESS CRITERIA

| Metric | Target |
|--------|--------|
| NER F1 Score | > 85% |
| Relation Extraction Accuracy | > 80% |
| BOQ Completeness | > 90% of items extracted |
| Processing Time | < 30 sec per page |
| Manual Time Savings | > 70% |

## IMPORTANT REMINDERS

1. **Claude Opus is your GURU** — ask it to explain concepts, validate approaches
2. **MiniMax agents do the work** — assign tasks, they report back
3. **Verification is NON-NEGOTIABLE** — never skip the brutal verification step
4. **Reverse role before submission** — pretend you're the critic, find every flaw
5. **Document everything** — prompts, decisions, failures, solutions

---

## STARTING CHECKLIST

Before assigning work to agents, ensure:
- [ ] Project structure created
- [ ] Python environment set up
- [ ] Dependencies installed
- [ ] Sample RFQ data obtained
- [ ] BOQ schema defined
- [ ] Claude Opus briefed on project scope

Once ready: "Claude, let's begin Phase 1. Start with environment setup and data collection."
