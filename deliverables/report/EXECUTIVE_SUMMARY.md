# Executive Summary

## Problem
Construction tender documents (RFQs/Request for Quotation) contain bill of quantities (BOQ) in unstructured text that must be manually converted into structured data. This manual extraction is slow, error-prone, and requires domain expertise in reading IS codes and construction terminology.

## Solution
RFQ2BOQ is an AI-powered system that automatically extracts BOQ data from construction tender documents. It uses NLP to identify 8 entity types (materials, quantities, grades, locations, etc.) and links them into structured BOQ rows ready for estimation software.

**Key capability**: Upload a PDF or paste text → Get structured Excel BOQ in seconds.

## Results

| Metric | Value |
|--------|-------|
| **Synthetic F1** | 99.6% (300 synthetic test documents) |
| **Real-world F1** | 33.7% (5 real CPWD tenders) |
| **Entities extracted** | 8 types (MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE) |
| **Coverage** | Indian construction (IS codes), English language |
| **Processing time** | <30s for 10-page PDF |
| **Model size** | 433 MB (BERT-BiLSTM-CRF) |

## Current Status: **EXPERIMENTAL** ⚠️

The model was trained on synthetic data and has NOT been validated on real construction tenders. Real-world F1 (33.7%) is significantly lower than synthetic F1 (99.6%).

**Required before production**: Retrain on 20+ manually annotated real RFQs.

## What We Built

1. **NER Model** — BERT-BiLSTM-CRF trained on 300 synthetic RFQ documents
2. **NLP Pipeline** — Entity extraction → Relation linking → BOQ row construction
3. **Construction Ontology** — 251 materials, 81 Indian standards, 65 units, 60 locations
4. **API** — FastAPI with rate limiting, health checks, Prometheus metrics
5. **Web UI** — Streamlit interface for non-technical users
6. **CLI** — Batch processing for automation

## Architecture

```
PDF → OCR/Text Extraction → NLP Pipeline → Rule-based Validation → BOQ Export
                              ↓
                    BERT-BiLSTM-CRF NER
                    (8 entity types, BIOES)
                              ↓
                    Construction Ontology
                    (Materials, Standards, Units)
```

## Deployment

- **Local**: Docker Compose (`docker-compose up -d`)
- **Cloud**: HuggingFace Spaces, AWS ECS, DigitalOcean
- **API**: `POST /api/extract` for text, `POST /api/upload` for PDF

## Next Steps (Priority Order)

| Priority | Action | Timeline |
|----------|--------|----------|
| P0 | Collect 20+ real RFQs from CPWD portal | 1 week |
| P0 | Manually annotate 20 RFQs with BIOES | 1 week |
| P0 | Retrain model on mixed synthetic + real | 2-3 days |
| P1 | Evaluate real-world F1 improvement | 1 day |
| P2 | Add multi-page batch processing | 1 week |
| P3 | Hindi/regional language support | 2 weeks |

## Team

Built with Python 3.11, HuggingFace Transformers, FastAPI, Streamlit.

**Note**: This is an academic project demonstrating NLP applied to construction domain. Production deployment requires real-world validation on domain-specific tender formats.