# Internship Review Presentation
**Srujan | SWA Consultancy Pvt. Ltd.**
**Project: RFQ2BOQ — NLP-Based BOQ Extraction from Construction Tenders**

---

## Slide 1: Title

# RFQ2BOQ
## NLP-Based Extraction of Bill of Quantities from Construction Tenders

**Srujan | SWA Consultancy Pvt. Ltd. | June 2026**

Transforming unstructured construction RFQ documents into structured BOQ data

---

## Slide 2: Introduction

### Who I Am
- Intern at SWA Consultancy Pvt. Ltd.
- Background: [Your background — e.g., Computer Science / AI / Civil Engineering]
- Duration: 1-month internship

### The Problem
Construction tenders (RFQs) contain BOQ data buried in PDFs and Excel files.
Manual extraction is slow, error-prone, and doesn't scale.

**Goal:** Build an AI system that reads tenders and outputs structured BOQ automatically.

---

## Slide 3: Internship Objectives

### Primary Objectives
1. Build an end-to-end NLP pipeline for BOQ extraction
2. Handle both PDF and Excel tender formats
3. Extract 8 entity types: Material, Quantity, Unit, Location, Dimension, Standard, Grade, Action
4. Export structured BOQ as Excel/JSON

### Secondary Objectives
5. Create a user-friendly Streamlit UI for non-technical users
6. Build a FastAPI backend for integration
7. Establish honest evaluation metrics (no fake 100%)
8. Document everything for future interns

---

## Slide 4: Architecture Overview

```
PDF / XLSX
    │
    ▼
┌─────────────┐
│   Ingest    │  ← pdfplumber, OCR, table extraction
└──────┬──────┘
       ▼
┌─────────────┐
│  Preprocess │  ← text cleaning, section classification
└──────┬──────┘
       ▼
┌─────────────┐
│     NER     │  ← Pattern-based NER (regex + gazetteer)
└──────┬──────┘
       ▼
┌─────────────┐
│   Domain    │  ← BOQ assembly, validation, unit normalization
└──────┬──────┘
       ▼
┌─────────────┐
│   Export    │  ← Excel (CPWD format), JSON, CSV
└─────────────┘
```

**Tech Stack:** Python, PyTorch, Transformers, pdfplumber, FastAPI, Streamlit

---

## Slide 5: What Was Built — Core Pipeline

### Components Delivered
| Component | Status | Details |
|-----------|--------|---------|
| PDF Ingestion | ✅ Done | pdfplumber + OCR fallback |
| XLSX Ingestion | ✅ Done | Row-preservation pipeline |
| NER Engine | ✅ Done | Pattern-based (production) + LoRA ML model (experimental) |
| BOQ Assembler | ✅ Done | Row building + unit normalization |
| Validation | ✅ Done | Domain rules + confidence scoring |
| Export | ✅ Done | Excel, JSON, CSV (CPWD format) |
| CLI | ✅ Done | Typer-based command line |
| API | ✅ Done | FastAPI with upload/extract endpoints |
| UI | ✅ Done | Streamlit web app |
| Tests | ✅ Done | 97 critical tests passing |

---

## Slide 6: What Was Built — Evaluation & Quality

### Honest Evaluation Framework
- **Entity-level F1:** 43.8% micro / 44.8% macro (independent gold)
- **XLSX extraction:** Strong — 60% macro F1, exact row counts on clean spreadsheets
- **PDF extraction:** Partial — 23% macro F1, needs improvement

### Key Insight
> The evaluation metric itself had a bug: entity gold expects short material names ("Mineral Wool") but the pipeline outputs full descriptions ("Supply & application of 100 mm thick Mineral Wool..."). Row-level evaluation is fairer.

### Anti-Cheat System Implemented
- No self-comparison (pipeline output ≠ gold)
- Independent human-verified rowgold
- Automatic detection of gold modification

---

## Slide 7: Demo — The 10 SWA Files

### Pipeline runs end-to-end on all 10 real tenders

| File | Type | Items Extracted | Status |
|------|------|-----------------|--------|
| 02 ISRO | XLSX | 8 rows | ✅ Strong |
| 03 Zydus Matoda | XLSX | 33 rows | ✅ Strong |
| 05 Zydus Animal | XLSX | 48 rows | ✅ Strong |
| 08 SAEL | XLSX | 12 rows | ✅ Strong |
| 04 Adani | PDF | 2 (bug) | ⚠️ Fixing |
| 06 Avante | PDF | 31 (some FP) | ⚠️ Tuning |
| 07 Grew | PDF | 9 (some FP) | ⚠️ Tuning |
| 01 GSECL | PDF | 2 (weak) | ⚠️ Fixing |
| 09 GeM | PDF | 22 (slow) | ⚠️ Optimizing |
| 10 GeM | PDF | 10 | ✅ OK |

**XLSX works well. PDF needs more training data.**

---

## Slide 8: Key Learnings

### Technical Learnings
1. **Data > Architecture:** A perfect model with bad training data fails. Synthetic F1 was 99%, real F1 was 43%.
2. **Evaluation honesty matters:** Self-comparison gives fake 100%. Independent gold is the only valid metric.
3. **PDF is harder than Excel:** Tables in PDFs are fragile — merged cells, multi-line cells, split quantities.
4. **Pattern-based NER beats ML on small data:** With only 20 real annotated docs, regex + gazetteer outperforms BERT-LoRA.

### Process Learnings
5. **One agent at a time:** Parallel agents on one repo = deleted files, conflicting changes, chaos.
6. **Version control discipline:** Every fix must be committed and verified before the next task.
7. **Scope guard:** Saying "no" to out-of-scope features (SaaS, papers, patents) keeps the project focused.

---

## Slide 9: Challenges Faced

### Challenge 1: Synthetic vs Real Data Gap
- **Problem:** Model trained on 300 synthetic PDFs scored 99% F1 but failed on real tenders.
- **Root cause:** Synthetic data was regex-generated from research papers, not real construction language.
- **Impact:** MATERIAL entity F1 = 0.0 on held-out real docs.
- **Lesson:** Real human annotations are non-negotiable for production quality.

### Challenge 2: PDF Table Fragility
- **Problem:** Complex layouts (merged cells, multi-line, split-quantity columns) break extraction.
- **Example:** GeM PDFs have digit columns that text classifiers miss.
- **Status:** Partially fixed with section classifier + split-quantity handler.

### Challenge 3: The "Fake 100%" Trap
- **Problem:** Early agents modified gold files to match pipeline output, claiming 100% accuracy.
- **Solution:** Implemented anti-cheat rules + honest evaluation framework.
- **Current state:** All numbers are independently verified.

---

## Slide 10: Tools & Skills Used

### Technologies
| Category | Tools |
|----------|-------|
| Language | Python 3.11–3.13 |
| ML/NLP | PyTorch, Transformers (HuggingFace), BERT, LoRA |
| PDF Processing | pdfplumber, pytesseract (OCR) |
| Excel | openpyxl |
| Web Framework | FastAPI |
| UI | Streamlit |
| Testing | pytest, ruff |
| DevOps | Docker, Docker Compose, GitHub Actions |

### Skills Developed
- End-to-end ML pipeline design
- Domain-specific NLP (construction ontology)
- PDF table extraction techniques
- Honest evaluation methodology
- Multi-agent project management
- Git discipline & code review

---

## Slide 11: Achievements & Outcomes

### What Was Delivered
✅ **Complete pipeline** — PDF/XLSX → structured BOQ in <30 seconds
✅ **Working UI** — Non-technical users can upload and extract
✅ **Working API** — Ready for integration with other systems
✅ **Honest evaluation** — No fake metrics, independently verified
✅ **Test suite** — 97 critical tests, CI/CD gate
✅ **Documentation** — Handoff docs, architecture docs, user guide

### Honest Metrics (Current)
| Metric | Value |
|--------|-------|
| XLSX row extraction | Strong (exact counts on 4/4 files) |
| Entity-level F1 | 43.8% micro, 44.8% macro |
| PDF extraction | Partial (real bugs being fixed) |
| Tests passing | 97 critical tests |
| Pipeline crash rate | 0% (all 10 files process) |

### Key Deliverable
**The foundation is solid. The bottleneck is data, not code.**

---

## Slide 12: Conclusion & Future Work

### Summary
Built a complete RFQ→BOQ extraction system with honest evaluation. XLSX works well. PDF needs real training data.

### Immediate Next Steps
1. **Fix PDF bugs** — Adani dimension headers, GSECL page detection
2. **Human annotation** — 20–40 real tenders need entity-level labels
3. **NER retrain** — Real gold → v6 model → target F1 > 0.60

### Long-Term Vision
- Domain-specific models (insulation, civil, electrical)
- Hindi/Indic language support (IndicBERT module ready)
- Batch processing for high-volume use
- Human-in-the-loop review for low-confidence extractions

### Thank You
**Questions?**

---

*12 slides | 10 minutes presentation + 5 minutes Q&A*
