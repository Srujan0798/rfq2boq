# Inventor Declaration — RFQ2BOQ Patent

**Date:** May 17, 2026
**Project:** RFQ to BOQ Scope Extraction using NLP

---

## Inventor Information

| Field | Value |
|-------|-------|
| **Full Name** | Srujan Karna |
| **Email** | srujan@example.com |
| **Phone** | +91-XXXXXXXXXX |
| **Affiliation** | B.Tech Final Year, Department of Civil Engineering, IIT Hyderabad |
| **Role** | Student Researcher (sole inventor) |

---

## Contribution Breakdown

| Contribution | Percentage | Description |
|-------------|-----------|-------------|
| System Architecture | 40% | Designed the NLP pipeline (BERT-BiLSTM-CRF, SpERT joint model, ontology validation, LLM ambiguity resolver) |
| Implementation | 30% | Wrote core code in `src/nlp/`, `src/domain/`, `src/rules/`, `src/llm/` |
| Dataset & Evaluation | 15% | Built synthetic data generator, evaluation framework, real RFQ annotation pipeline |
| Patent Documentation | 15% | Drafted claims, prior art analysis, technical contributions document |

---

## Invention Disclosure

**Title:** System and Method for Automated Bill of Quantities Extraction from Construction Tender Documents using Hybrid Machine Learning and Domain Ontology

**Date of Conception:** January 2026 (evidenced by git commit `cbefee3` dated earlier)

**Description:**
An automated system that extracts structured Bill of Quantities (BOQ) from construction RFQ/tender PDFs using:
1. BERT-BiLSTM-CRF named entity recognition with BIOES tagging
2. Construction-specific ontology (249+ materials, Indian Standard codes)
3. LLM-based ambiguity resolution for low-confidence predictions
4. Active learning loop with drift detection for continuous improvement

---

## IP Ownership Declaration

- [x] This invention was developed as part of academic research at IIT Hyderabad
- [x] No external company or third-party funding was involved
- [x] All code is original work of the inventor
- [x] No proprietary data or patented methods were incorporated

---

## Contact for Patent Correspondence

**Primary Contact:** Srujan Karna
**Address:** Department of Civil Engineering, IIT Hyderabad, Telangana 502285, India
**Email:** srujan@example.com
**Phone:** +91-XXXXXXXXXX

---

## For Attorney Use

- **Client Matter No.:** RFQ2BOQ-2026-001
- **Invention Disclosure Date:** May 17, 2026
- **Related GitHub Repo:** https://github.com/rfq2boq/rfq2boq
- **Demonstration Video URL:** (to be added)
- **Lab Notebook Reference:** (to be added)