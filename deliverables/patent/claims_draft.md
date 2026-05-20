# Draft Claims — RFQ2BOQ Patent

**Version:** 1.0
**Date:** May 16, 2026
**Prepared for:** University IP Office / Patent Attorney

---

## Independent Claims

### Claim 1 (System)
A computer-implemented system for extracting Bill of Quantities (BOQ) entities from construction Request for Quotation (RFQ) documents, comprising:

a) a memory storing instructions;
b) a processor executing the instructions to:
   - receive an RFQ document as input;
   - extract text from the RFQ document using optical character recognition (OCR);
   - apply a named entity recognition (NER) model to the extracted text to generate entity predictions with associated confidence scores;
   - identify entity predictions where the confidence score falls below a predetermined threshold;
   - for each identified low-confidence entity prediction, query a large language model (LLM) with a prompt comprising the entity text, surrounding context, and construction domain rules to resolve entity type ambiguity;
   - validate the resolved entity predictions against a construction-specific ontology database comprising at least 200 construction materials organized hierarchically;
   - resolve conflicts between the NER model predictions and the ontology validation using a hybrid resolution algorithm;
   - assemble the validated entity predictions into a structured BOQ format comprising material type, quantity, unit, and location for each item.

### Claim 2 (Method)
A computer-implemented method for resolving entity type ambiguities in construction document named entity recognition, comprising:

a) receiving, by a processor, a text passage from a construction document;
b) applying, by the processor, a neural network-based named entity recognition model to the text passage to generate entity predictions with confidence scores;
c) identifying, by the processor, entity predictions where the confidence score is below a first threshold;
d) for each entity prediction below the first threshold, constructing, by the processor, a prompt comprising:
   - the text passage containing the entity;
   - the entity text;
   - a list of valid entity types specific to construction documents;
   - context information from the text passage;
e) sending, by the processor, the constructed prompt to a large language model (LLM);
f) receiving, by the processor, an entity type classification from the LLM;
g) replacing, by the processor, the original entity prediction with the LLM-provided entity type when the LLM confidence exceeds a second threshold;
h) tracking, by the processor, an agreement rate between the NER model and the LLM over multiple entity predictions;
i) adjusting, by the processor, the first threshold based on the tracked agreement rate.

### Claim 3 (Computer-Readable Medium)
A non-transitory computer-readable medium storing instructions that, when executed by a processor, cause the processor to:

- extract text from construction RFQ documents using OCR;
- apply BERT-based named entity recognition with BiLSTM and CRF layers;
- identify entity predictions with confidence below 0.5;
- resolve entity type ambiguities using a large language model (LLM);
- validate extracted entities against a construction ontology;
- assemble validated entities into a BOQ structure;
- monitor model performance using KS test on input distribution;
- trigger active learning when data drift is detected.

---

## Dependent Claims

### Claim 4
The system of claim 1, wherein the construction-specific ontology database comprises at least 249 construction materials organized hierarchically, each material having associated attributes including typical units, grade ranges, standard references, and co-occurrence patterns.

### Claim 5
The system of claim 1, wherein the NER model comprises a BERT embedding layer, a BiLSTM layer with 256 hidden units, and a CRF decoding layer for sequence labeling using BIOES tag format.

### Claim 6
The system of claim 1, wherein the predetermined threshold for low-confidence entity identification is 0.5.

### Claim 7
The system of claim 1, wherein the large language model is Claude API (Anthropic) or equivalent, configured with temperature 0.1 for deterministic entity type classification.

### Claim 8
The method of claim 1, wherein the construction document is a tender document from the Indian construction industry, and the valid entity types comprise MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, ACTION, GRADE, and STANDARD.

### Claim 9
The method of claim 1, wherein the MATERIAL entity type includes construction materials selected from the group consisting of: cement, steel, brick, concrete, sand, aggregate, plywood, tile, paint, pipe, and wiring.

### Claim 10
The method of claim 1, wherein the GRADE entity type includes Indian construction grade notations including M25, M30, M35, Fe500, Fe415, and Class A.

### Claim 11
The method of claim 1, wherein the UNIT entity type includes Indian construction unit notations including bags, kg, sqm, cum, no., m, and liter.

### Claim 12
The method of claim 1, further comprising:
- generating synthetic training data using BIOES-tagged templates;
- the synthetic training data comprising at least 2000 annotated RFQ documents covering common construction item patterns.

### Claim 13
The method of claim 1, further comprising:
- detecting data distribution drift using a Kolmogorov-Smirnov (KS) test on input text features;
- alerting when average KS statistic exceeds 0.15;
- triggering model retraining when drift is sustained.

### Claim 14
The method of claim 1, further comprising:
- routing uncertain entity predictions to a human review queue;
- incorporating human corrections back into training data;
- implementing active learning for continuous model improvement.

### Claim 15
The system of claim 1, further comprising a layout-aware extraction module using LayoutLMv3 for processing documents with visual layout information including bounding boxes.

### Claim 16
The method of claim 1, wherein the conflict resolution algorithm:
- compares entity type from NER model with entity type from ontology validation;
- assigns a higher weight to the entity type with higher confidence score;
- uses LLM verification when confidence scores are within a predetermined range.

### Claim 17
The computer-readable medium of claim 3, wherein the instructions further cause the processor to:
- export the BOQ in multiple formats including JSON, Excel, CSV, and IFC;
- integrate with BIM systems via IFC format export;
- integrate with ERP systems via SAP XML and Primavera XER formats.

### Claim 18
The computer-readable medium of claim 3, wherein the KS test monitors drift in:
- text length distribution;
- entity type distribution;
- confidence score distribution.

### Claim 19
The system of claim 1, wherein the RFQ document is in PDF format, and the OCR extracts text with position information including bounding boxes.

### Claim 20
The system of claim 1, further comprising:
- a PostgreSQL database for storing extraction jobs and results;
- a Redis cache for caching ontology lookups and model predictions;
- a Neo4j graph database for storing entity relationships.

---

## Claims Notes for Attorney

1. Claims are drafted to emphasize the SYSTEM INTEGRATION aspect, which is harder to challenge under abstract idea rejections.

2. The LLM-based ambiguity resolution (Claims 2, 6-7) is the key differentiator from prior art.

3. The construction-specific ontology (Claim 4, 8-11) provides domain specificity that differentiates from generic NER patents.

4. Active learning loop with drift detection (Claims 13-14) addresses model maintenance, a practical concern not addressed in prior art.

5. Multi-format export (Claim 17) addresses practical deployment needs.

**Recommended Filing Strategy:**
1. File provisional patent immediately (before any public disclosure)
2. Focus on Claims 1, 2, 4, 6, 7, 16 as core innovation
3. Request expedited examination if available