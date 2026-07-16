# RFQ to BOQ Project - Complete Resources Guide

**Generated from:** `/resources/` folder analysis
**Date:** May 16, 2026
**Purpose:** Single reference document for all project research materials

---

## 📋 MAIN PROJECT DOCUMENT
**File:** `RFQ to BOQ Scope Extraction using NLP system.pdf` (3 pages, 324KB)

### Overview
The RFQ to BOQ Scope Extraction using NLP system is an automated solution that transforms unstructured tender documents into structured Bill of Quantities (BOQ) data, significantly improving efficiency and accuracy in construction estimation workflows.

**Key Technologies:**
- Named Entity Recognition (NER)
- Semantic parsing
- Text classification
- Transformer-based language models
- Knowledge bases and ontology models

**Workflow:**
1. Document ingestion (PDF/OCR)
2. Entity and relation extraction
3. Rule-based validation
4. Structured output generation

**Benefits:**
- Reduces manual processing time by up to 70%
- Minimizes risks: scope omission, misinterpretation, contractual disputes
- Enhances decision-making, consistency, and scalability

---

## 📄 ACADEMIC PAPERS

### 1. Zhang & El-Gohary (2015) - Semantic NLP-Based Information Extraction
**File:** `Semantic-NLP-Based-Information-Extraction-from-Construction-Regulatory-Documents-for-Automated-Compliance-Checking.pdf`
**Pages:** 42 | **Size:** 1.3MB
**Published:** Journal of Computing in Civil Engineering, ASCE
**DOI:** 10.1061/(ASCE)CP.1943-5487.0000346

**Authors:**
- Jiansong Zhang (Graduate Student, University of Illinois at Urbana-Champaign)
- Nora M. El-Gohary (Assistant Professor, University of Illinois at Urbana-Champaign)

**Abstract:**
Automated regulatory compliance checking requires automated extraction of requirements from regulatory textual documents and formalization in a computer-processable rule representation. This paper proposes a semantic, rule-based NLP approach for automated information extraction from construction regulatory documents.

**Methodology:**
- Pattern-matching-based IE rules
- Conflict resolution (CR) rules
- Syntactic (grammar-related) text features
- Semantic (meaning/context-related) text features
- Phrase structure grammar (PSG)-based phrasal tags
- Ontology for semantic text feature recognition

**Results:**
- Precision: 0.969
- Recall: 0.944
- Tested on 2009 International Building Code

**Key Insight:** Separation and sequencing of semantic information elements reduces number of needed patterns.

---

### 2. Sousa et al. (2024) - NLP in Construction Budgeting
**File:** `ci-12-2022-0315.pdf`
**Pages:** 27 | **Size:** 1.0MB
**Published:** Construction Innovation, Vol. 24 No. 7, pp. 292-318
**DOI:** 10.1108/CI-12-2022-0315

**Authors:**
- Luís Jacques de Sousa, João Poças Martins (University of Porto)
- Luís Sanhudo (BUILT CoLAB)
- João Santos Baptista (University of Porto)

**Purpose:**
Review recent advances towards implementation of ANN and NLP applications during the budgeting phase of construction. Quantity surveyors assess scope and map client's expectations to internal database of tasks, resources, and costs - manually, with little computer aid, under time constraints.

**Methodology:**
- Systematic Literature Review (PRISMA guidelines)
- Survey of machine learning and NLP applications in AEC sector
- Focus on text classification (TC) for budgeting in construction

**Key Findings:**
1. Need to develop datasets representing variety of construction tasks
2. Achieve higher accuracy algorithms
3. Widen scope of application
4. Reduce need for expert validation

**Conclusion:** Full automation not reachable short-term, but TC algorithms can provide helpful support tools.

---

### 3. Nabavi et al. (2023) - NLP for BIM Information Extraction
**File:** `2023_13-ITcon-Nabavi.pdf`
**Pages:** 20 | **Size:** 792KB
**Published:** Journal of Information Technology in Construction (ITcon)
**DOI:** 10.36680/j.itcon.2023.013

**Authors:**
- Armin Nabavi (K.N. Toosi University of Technology)
- Issa Ramaji (Roger Williams University)
- Naimeh Sadeghi (K.N. Toosi University of Technology)
- Anne Anderson (Roger Williams University)

**Problem:**
Building Information Modeling (BIM) provides significant benefits but accessing information could be tedious for non-technical users who lack knowledge of BIM software.

**Proposed Framework:**
1. **SVM (Support Vector Machine)** - determines user's question type
2. **NLP for syntactic analysis** - finds main keywords
3. **Ontology database (IfcOWL)** - semantic understanding
4. **Latent Semantic Analysis (LSA)** - semantic understanding
5. **Navisworks API** - extracts results from BIM

**Results:**
- Speed up to 5x faster than manual expert use
- Maintains high accuracy
- Speech recognition module for user-friendly interface

**Keywords:** BIM, NLP, Ontology, SVM, Question Answering platform

---

### 4. Yan et al. (2022) - Text Mining in Construction
**File:** `Overview_and_analysis_of_the_text_mining_applications_in_the_construction_industry.pdf`
**Pages:** 16 | **Size:** 2.2MB
**Published:** Heliyon

**Authors:**
- Hang Yan, Chao Dong (Wuhan University of Technology)
- Mingxue Ma (Western Sydney University)
- Ying Wu (Chongqing University)
- Hongqin Fan (Hong Kong Polytechnic University)

**Purpose:**
Comprehensive review of text mining (TM) applications in AEC domain. Data generation has increased dramatically, with text documents (contracts, change orders, design reports, field reports, accident records) being crucial but largely unstructured.

**Methodology:**
- Systematic review (2000-2021)
- VOSviewer software for visualization
- Qualitative-quantitative analysis

**Eight Prime Application Fields of TM:**
1. Construction management
2. Safety management
3. Contract management
4. Cost estimation
5. Quality management
6. Information retrieval
7. Risk assessment
8. Sustainability analysis

**Text Mining Process:**
1. **Text Preprocessing:**
   - Tokenization
   - Stop words removal
   - Stemming
   - Document-term matrix
   - Feature selection/dimension reduction (LSI, PLSA, LDA)

2. **Knowledge Extraction:**
   - Text classification
   - Text clustering
   - Information extraction
   - Information retrieval

**Five Key Challenges:**
1. Data quality and availability
2. Domain-specific features
3. Integration with existing systems
4. Evaluation metrics
5. Scalability

**Three Future Directions:**
1. Deep learning integration
2. Real-time processing
3. Multi-language support

---

## 🌐 WEB RESOURCES

### Technical Source 4: Helium42 - AI for Construction BOQ
**URL:** https://helium42.com/blog/ai-for-construction-boq
**Author:** Peter Vogel
**Date:** April 1, 2026

### KEY STATISTICS:
| Metric | Value |
|--------|-------|
| UK construction pages/year | 2.1 billion |
| Manual BOQ time | 40-59 hours/tender |
| AI processing time | 10-15 hours (70% reduction) |
| Error rate (manual) | 8-12% |
| Error rate (AI+human) | 0.5-1.5% |
| First-pass AI accuracy | 83-89% |
| NRM3 classification | 87-91% |
| LLM hallucination | 9-14% |
| Payback period | 1.8-5 months |
| Annual savings | £100k-£176k |

### AI DOCUMENT PARSING PIPELINE:
```
Stage 1: Document Ingestion (OCR)
        ↓
Stage 2: Layout Analysis (tables, columns, line breaks)
        ↓
Stage 3: Item Extraction (quantities, descriptions, rates)
        ↓
Stage 4: Classification (NRM3/NBS codes)
```

### Accuracy by Document Type:
| Document Type | Accuracy |
|---------------|----------|
| Typed documents (OCR) | 98-99% |
| Poor quality scans | 78-85% |
| Layout analysis (typed) | 91-96% |
| Layout analysis (scanned) | 62-78% |
| Item extraction | 88-94% |

### NRM3 Standards:
- 71% of UK firms formally adopt NRM3
- Only 23% of AI tools offer native NRM3 compliance
- Scottish firms use different cost code hierarchies

### ⚠️ LLM HALLUCINATION WARNING:
- General LLMs show 9-14% hallucination rate on construction docs
- Fabricate quantities, rates, or line items
- Should only be used as preliminary extraction layer
- Always apply deterministic validation + human review

---

### Industry Insight 9: AEC Contracts - Scope Extraction
**URL:** https://aeccontracts.com/tender-document-ai-scope-extraction/
**Author:** Rana
**Date:** January 23, 2026

### Why Scope Extraction Fails:
- **Cognitive overload issue**, not skill issue
- Experienced estimators rely on pattern recognition
- Subtle deviations in documents cause risk
- Modified clauses, shifted boundaries, hybrid scopes
- Intentionally vague language

### Where Scope Hides:
- General conditions
- Employer requirements
- Appendices
- Performance clauses
- Interface descriptions
- Footnotes and exclusions

### Manual Process Problems:
- Highlighting PDFs fragments understanding
- One person sees drawings, another specs, third contracts
- No one sees the whole picture

### Missing Scope vs Extra Scope:
- **Extra scope:** Can be negotiated or value-engineered
- **Missing scope:** Unpriced obligation, dispute trigger, margin leak

### AI Scope Extraction - What It Does:
- Identifies scope-related language
- Maps recurring obligations
- Cross-references mentions across documents
- Highlights inconsistencies
- Flags undefined responsibilities

### AI Scope Extraction - What It Doesn't:
- **NOT a decision** - it's visibility
- Humans still decide: include/exclude, clarify, price as risk

---

### Survey Paper: Document-Level Information Extraction
**URL:** https://arxiv.org/abs/2309.13249
**Authors:** Hanwen Zheng, Sijia Wang, Lifu Huang
**Date:** September 23, 2023

**Abstract:**
Document-level information extraction (IE) is a crucial task in NLP. This paper conducts a systematic review of recent document-level IE literature.

### KEY CHALLENGES IDENTIFIED:
1. **Labeling noises** - Severely affect performance
2. **Entity coreference resolution** - Difficult at document level
3. **Lack of reasoning** - Limits accuracy

---

### NLP Foundation 6: GeeksforGeeks - Named Entity Recognition
**URL:** https://geeksforgeeks.org/nlp/named-entity-recognition/

### NER STEPS:
1. Analyzing Text - Locate entities
2. Finding Sentence Boundaries
3. Tokenizing + POS Tagging
4. Entity Detection and Classification
5. Model Training and Refinement
6. Adapting to New Contexts

### NER METHODS:

#### 1. Lexicon Based
- Dictionary lookup
- Requires constant updating

#### 2. Rule Based
- Pattern-based rules (word structure)
- Context-based rules (surrounding words)
- Most accurate when combined

#### 3. Machine Learning Based
- **Multi-Class Classification:** Trains on labeled examples
- **CRF (Conditional Random Field):** Understands sequence and context

#### 4. Deep Learning Based
- Word Embeddings
- Automatic learning (no manual feature engineering)
- Higher accuracy on large datasets

### Implementation (spaCy):
```python
import spacy
nlp = spacy.load("en_core_web_sm")
doc = nlp(text)
for ent in doc.ents:
    print(ent.text, ent.label_)
```

---

### NLP Foundation 7: Microsoft NLP Recipes - NER with BERT
**URL:** https://microsoft.github.io/nlp-recipes/examples/named_entity_recognition/

### Approach:
- Fine-tune pretrained BERT for token classification
- State-of-the-art: LSTM-CRF + pretrained language models (BERT)

### Labeling Scheme:
- O = Not an entity
- I-LOC = Location
- I-ORG = Organization
- I-PER = Person

### Dataset: wikigold (English)

---

## 📺 VIDEO RESOURCES (9 Videos)

### 1. AI Document Processing (RFQ → BOQ Core Concept)
- **URL:** https://www.youtube.com/watch?v=T1M7QZ3oE8s
- **Title:** "AI in Document Processing Explained | OCR, NLP & Automation for Beginners"
- **Content:** Explains OCR + NLP + document automation pipeline for converting unstructured documents to structured data

### 2. PDF → Structured Data (RFQ Parsing)
- **URL:** https://www.youtube.com/watch?v=aafTVJuGCtc
- **Title:** "Convert Any PDF Into Structured Data Using AI (OCR + LLM Pipeline Explained)"
- **Content:** End-to-end pipeline: PDF → OCR → structured JSON/data

- **URL:** https://www.youtube.com/watch?v=HSFBJM9dspw
- **Title:** "Nanonets AI Tutorial - Convert PDF to Structured Data Automatically"
- **Content:** AI tool demo converting PDF to Excel/structured outputs

### 3. NLP Information Extraction (Entity + Relation Extraction)
- **URL:** https://www.youtube.com/watch?v=nPy65qysWok
- **Title:** "Data Science Project - Name Entity Recognition with Bert"
- **Content:** NER using BERT for extracting entities like material, quantity, location

- **URL:** https://www.youtube.com/watch?v=dzyDHMycx_c
- **Title:** "Fine Tuning BERT for Named Entity Recognition (NER)"
- **Content:** Practical implementation of BERT-based entity extraction workflow

### 4. NLP Fundamentals
- **URL:** https://www.youtube.com/watch?v=Rj-OtK2n5jU
- **Title:** "Natural Language Processing (NLP) Full Course - Beginner to Advanced [2026]"
- **Content:** Complete NLP course covering tokenization, parsing, classification

### 5. BOQ Automation & Construction AI
- **URL:** https://www.youtube.com/watch?v=JwSRdfc8s4s
- **Title:** "How to Use AI for Takeoffs & BOQ Estimates in 2026 | Civils.ai Tutorial"
- **Content:** AI-driven BOQ generation from drawings using natural language

- **URL:** https://www.youtube.com/watch?v=bENhZT2pMdk
- **Title:** "Manual to AI Automation BOQ in 3 Minutes"
- **Content:** Real-world demo: Manual BOQ → AI automation workflow

### 6. End-to-End AI + BOQ Pipeline
- **URL:** https://www.youtube.com/watch?v=Lgh6ncd6TPc
- **Title:** "AI + BOQ + BIM Full Pipeline Demo - NexAI Labs"
- **Content:** Full pipeline: BIM/Docs → AI extraction → BOQ → risk/analysis

---

## ⚠️ NOTES ON BROKEN LINKS

The following links are blocked or unavailable:

| Link | Issue | Alternative |
|------|-------|-------------|
| designdrafter.com/... | Website timed out | PDF not available |
| ResearchGate papers (3) | Requires login | PDFs for Zhang & Nabavi available locally |
| Emerald (Sousa et al.) | Paywall | Journal article reference available |

**Note:** PDFs for Zhang, Nabavi, and Yan papers ARE available locally in resources folder.

---

## 🎯 PROJECT RELEVANCE SUMMARY

### For RFQ to BOQ System:

| Resource | Relevance | Key Takeaway |
|----------|-----------|--------------|
| Zhang & El-Gohary | HIGH | Semantic NLP, pattern-matching IE, precision 0.969/0.944 |
| Sousa et al. | HIGH | Text classification for budgeting, systematic review findings |
| Nabavi et al. | MEDIUM | NLP+ontology for BIM, SVM+LSA+API approach |
| Yan et al. | HIGH | Text mining in construction, 8 application fields, TM process |
| Helium42 | HIGH | ROI metrics, pipeline stages, accuracy data, LLM caution |
| AEC Contracts | HIGH | Scope extraction risks, where scope hides, manual vs AI |
| arXiv survey | MEDIUM | Document-level IE challenges |
| GeeksforGeeks | HIGH | NER methods, spaCy implementation |
| Microsoft | HIGH | BERT fine-tuning for NER |

### Key Technical Approaches Found:

1. **Pattern-matching + semantic rules** (Zhang & El-Gohary)
2. **SVM + NLP + Ontology** (Nabavi et al.)
3. **Text classification for budgeting** (Sousa et al.)
4. **TM process: preprocessing → extraction** (Yan et al.)
5. **BERT fine-tuning for token classification** (Microsoft)
6. **spaCy rule-based NER** (GeeksforGeeks)

---

## 📊 KEY METRICS FROM ALL RESOURCES

| Metric | Value | Source |
|--------|-------|--------|
| Manual BOQ time | 40-59 hours/tender | Helium42 |
| AI processing time | 10-15 hours (70% reduction) | Helium42 |
| Error rate (manual) | 8-12% | Helium42 |
| Error rate (AI+human) | 0.5-1.5% | Helium42 |
| First-pass AI accuracy | 83-89% | Helium42 |
| NRM3 classification | 87-91% | Helium42 |
| LLM hallucination | 9-14% | Helium42 |
| BIM query speedup | 5x faster | Nabavi et al. |
| IE Precision | 0.969 | Zhang & El-Gohary |
| IE Recall | 0.944 | Zhang & El-Gohary |
| UK construction pages/year | 2.1 billion | Helium42 |
| Payback period | 1.8-5 months | Helium42 |
| Annual savings | £100k-£176k | Helium42 |

---

**End of Complete Resources Guide**
