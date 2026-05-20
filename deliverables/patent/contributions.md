# Patent Documentation - RFQ2BOQ Novel Contributions

**Date:** May 16, 2026
**Project:** RFQ to BOQ Scope Extraction using NLP

---

## Novel Contributions for Patent Protection

### 1. Hybrid ML + Rule Conflict Resolution Algorithm

**Description:** A system and method for resolving conflicts between machine learning NER predictions and domain-specific ontological constraints in construction document processing.

**Key Innovation:**
- When BERT confidence < 0.5, the system queries an LLM (Claude API) for ambiguity resolution
- The resolver constructs prompts containing sentence, entity, and context
- Agreement rate between BERT and LLM is tracked to calibrate confidence thresholds
- This differs from prior art which relies solely on either ML or rules

**Claims:**
1. A method for entity type ambiguity resolution combining neural network confidence scoring with large language model verification
2. The system of claim 1 wherein the ambiguity resolution is triggered only when neural confidence falls below a predetermined threshold
3. A computer-readable medium storing instructions that, when executed, perform the method of claim 1

### 2. BIOES-Tagged Synthetic RFQ Generator

**Description:** A method for generating synthetic training data using construction-specific templates with proper BIOES tagging schemes.

**Key Innovation:**
- Generates synthetic RFQ text using templates covering common construction patterns
- Includes Indian construction-specific terminology (bags, cum, sqm, M25, Fe500)
- Produces BIOES-formatted annotations for NER training
- Enables rapid model adaptation to new project types without manual annotation

**Claims:**
1. A method for generating synthetic training data for named entity recognition in construction documents
2. The method of claim 1 wherein the synthetic data incorporates domain-specific unit formats and material grade notations
3. A system employing synthetic training data generation for training NER models on limited annotated corpora

### 3. Construction-Specific Entity Ontology (249+ Materials)

**Description:** A hierarchical ontology of construction materials with attributes including typical units, grade ranges, standard references, and co-occurrence patterns.

**Key Innovation:**
- 249 construction materials organized hierarchically
- Each material has: typical units, grade ranges, standard references, co-occurrence patterns
- Supports real-time validation against construction business rules
- Enables entity linking between extracted entities and canonical material definitions

**Claims:**
1. An ontology database comprising 249+ construction materials with hierarchical relationships and attribute data
2. A method for validating extracted entities against a domain-specific ontology
3. The ontology of claim 1 wherein materials include co-occurrence patterns for relation extraction

### 4. Real-Time Uncertainty-Driven Active Learning Loop

**Description:** A system and method for improving model performance by identifying and prioritizing uncertain predictions for human review.

**Key Innovation:**
- Identifies predictions with confidence below threshold (0.6)
- Routes uncertain predictions to human review queue
- Incorporates human corrections back into training data
- Implements drift detection (KS test) on input distributions to trigger model retraining

**Claims:**
1. A method for active learning in construction document NER using confidence-based sample selection
2. The method of claim 1 further comprising automated model retraining triggered by data distribution drift
3. A system for continuous improvement of NER models through human-in-the-loop correction

---

## Prior Art Analysis

### Existing Patents/Publications

1. **Zhang & El-Gohary (2015)** - Semantic NLP for regulatory documents
   - Does not address construction-specific entity types (grades, Indian units)
   - No conflict resolution mechanism between ML and ontology

2. **Sousa et al. (2024)** - NLP for construction budgeting
   - General text classification, not entity extraction
   - No domain ontology integration

3. **Nabavi et al. (2023)** - NLP for BIM information extraction (ITcon)
   - Focuses on BIM integration, not RFQ-to-BOQ extraction
   - No synthetic data generation method

4. **General NER Patents (Google, Microsoft)**
   - Do not address construction domain specificity
   - No ontology validation step

### Distinction from Prior Art

| Aspect | Prior Art | RFQ2BOQ Innovation |
|--------|-----------|-------------------|
| Entity Types | General (PER, LOC, ORG) | Construction-specific (MATERIAL, GRADE, STANDARD) |
| Training Data | Manual annotation | Synthetic generation with BIOES templates |
| Validation | Rule-based post-processing | Ontology-based with 249+ materials |
| Ambiguity Resolution | Discard low-confidence | LLM-based verification |
| Active Learning | Random sampling | Confidence-based selection |
| Domain Focus | General | Indian construction |

---

## Patent Filing Recommendations

### Option 1: Self-Filed Provisional Patent (~$300)
- File provisional application citing items 1-4 above
- Buys 12 months to assess commercial value
- Requires formal patent application within 12 months

### Option 2: University IP Office (Recommended if affiliated)
- Consult IIT Hyderabad Technology Transfer Office
- Typical cost: ~$3000 with attorney
- Enables licensing to construction firms

### Option 3: Software Prior Art (No Cost)
- Document innovations as trade secrets
- Publish source code on GitHub with appropriate license
- Establishes prior art date

---

## Implementation Evidence

The following files demonstrate reduction to practice:

1. **Conflict Resolution**: `src/llm/client.py` - AmbiguityResolver class
2. **Synthetic Data Generator**: `src/data/dataset.py` - RFQBoqDataset class
3. **Ontology**: `src/ontology/` - 249+ material definitions
4. **Active Learning**: `scripts/detect_drift.py` - KS test implementation

---

## Freedom to Operate

No known patents blocking RFQ2BOQ implementation. The construction NER domain is sufficiently different from general NER patents that infringement risk is low. Recommend patent search via USPTO and Google Patents before commercialization.

---

## Recommendations

1. **Immediate**: File provisional patent if commercializing
2. **Short-term**: Publish code under permissive license (MIT) to establish prior art
3. **Long-term**: Pursue patent protection for items 1 and 4 (most novel) if commercial value justifies $3000+ cost