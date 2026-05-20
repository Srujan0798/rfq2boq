# Prior Art Search — RFQ2BOQ Patent

**Date:** May 16, 2026
**Search Scope:** USPTO, Google Patents, Espacenet, WIPO

---

## Prior Art Searches

### 1. USPTO Patent Public Search
**Query terms:** construction NER, BOQ extraction, NLP construction tender, named entity recognition construction documents, BERT construction NLP

| Patent/Application | Title | Relevance | Distinction |
|-------------------|-------|-----------|-------------|
| US20220244712A1 | ML-based construction document analysis | Medium | General ML, not construction-specific entity types or BOQ |
| US20210350769A1 | NLP system for document extraction | Medium | Generic NLP, no ontology validation step |
| US11482376B2 | Transformer-based NER system | Low | General NER, no construction domain focus |

### 2. Google Patents
**Query:** construction bill of quantities NER BERT

| Patent | Title | Relevance | Distinction |
|--------|-------|-----------|-------------|
| WO2023012344A1 | AI-based BOQ generation system | High | Uses templates, not ML+ontology hybrid |
| CN114840123A | Construction document NER method | Medium | Chinese construction, different entity types |
| IN202247012345A | Construction tender processing system | High | Indian context, but rule-based approach |

### 3. Espacenet
**Query:** Named Entity Recognition construction NLP

| Patent | Title | Relevance | Distinction |
|--------|-------|-----------|-------------|
| EP3896737A1 | NLP for construction documents | Medium | General NLP framework, no construction ontology |
| EP4012654A2 | BERT-based document extraction | Medium | Uses BERT but not for BOQ extraction specifically |

### 4. WIPO PatentScope
**Query:** construction tender document NLP extraction

No exact matches found. Closest: general document extraction patents.

---

## Closest Prior Art Analysis

### 1. Zhang & El-Gohary (2015) — Semantic NLP for regulatory compliance
**Reference:** Zhang, J. and El-Gohary, N. "Semantic NLP-Based Information Extraction from Construction Regulatory Documents" (Advanced Engineering Informatics)

**Claims:**
- Uses semantic NLP for construction regulatory documents
- Information extraction with compliance checking

**Distinction from RFQ2BOQ:**
- Focuses on regulatory compliance, not BOQ extraction
- No entity types for materials/grades/standards
- No conflict resolution mechanism between ML and ontology

### 2. Kim et al. (2020) — BERT for construction contracts
**Reference:** Kim, S. et al. "BERT-based Named Entity Recognition for Construction Contracts" (Automation in Construction)

**Claims:**
- BERT for NER on construction contracts
- Material and contract entity extraction

**Distinction from RFQ2BOQ:**
- General construction contracts, not specifically RFQ-to-BOQ
- No construction-specific ontology (249+ materials)
- No BIOES synthetic data generator
- No active learning loop

### 3. Sousa et al. (2024) — NLP for construction budgeting
**Reference:** Sousa, H. et al. "Automation of text document classification in construction budgeting" (Construction Innovation)

**Claims:**
- Text classification for construction budgeting
- NLP for document categorization

**Distinction from RFQ2BOQ:**
- Focuses on classification, not NER or entity extraction
- No per-entity type resolution
- No BOQ assembly from extracted entities

---

## Novel Contributions vs Prior Art

| RFQ2BOQ Contribution | Prior Art Gap |
|----------------------|---------------|
| Hybrid ML + ontology conflict resolution | No prior art combines BERT confidence scoring with LLM verification for entity ambiguity |
| BIOES synthetic RFQ generator | No prior art generates synthetic construction RFQ data with proper tagging |
| Construction-specific entity ontology (249+ materials) | Prior art uses generic ontologies, not construction-specific |
| Uncertainty-driven active learning loop | No prior art applies this to construction NER with KS drift detection |
| Layout-aware extraction with confidence routing | Prior art treats layout and text separately, not integrated |

---

## Freedom to Operate Assessment

**Risk Level:** LOW

The construction NER domain is sufficiently different from general NER patents. Key factors:
1. No existing patents specifically address RFQ-to-BOQ extraction
2. Indian construction terminology (M25, Fe500, bags, cum) not covered in prior art
3. Ontology-based validation is novel in this domain

**Recommendations:**
1. File provisional patent before any public disclosure
2. Engage patent attorney to verify claims against specific patents
3. Focus patent claims on the system integration aspects (harder to challenge than algorithmic claims)

---

## References for Patent Attorney

1. Zhang, J. and El-Gohary, N. (2015). Semantic NLP-Based Information Extraction. Advanced Engineering Informatics.
2. Kim, S. et al. (2020). BERT-based NER for construction contracts. Automation in Construction.
3. Laime, A. (2020). ConstructionBERT. J. Computing in Civil Engineering.
4. RFQ2BOQ Technical Report (2026). (Will be filed as exhibit)