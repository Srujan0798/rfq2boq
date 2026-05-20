# Executive Summary — RFQ2BOQ

## The Problem

Manual extraction of Bill of Quantities (BOQ) from construction tender RFQ documents is slow and error-prone. A single 20-page tender takes 2–4 hours to extract by hand, and errors in the process — missed materials, wrong quantities, misread specifications — create real contractual risk. Different estimators also produce different results on the same document, making the process inconsistent.

## What We Built

We built RFQ2BOQ: an NLP system that reads a construction tender PDF and produces a structured BOQ in Excel and JSON in under 30 seconds. The system uses a machine learning model (BERT-BiLSTM-CRF) combined with pattern-matching rules and a construction standards database to identify eight entity types — materials, quantities, units, grades, standards, locations, dimensions, and actions — and assemble them into a complete BOQ.

## Results

- **Real-world F1: 0.506** (on 31 hand-annotated documents — this is the honest number)
- Synthetic F1: 0.996 (template-based training data inflates this; not comparable)
- DSR rate library: 501 CPWD 2023 items with base rates
- Best entities: STANDARD (F1 0.94), GRADE (F1 0.68) — these have regular patterns
- Weakest entities: MATERIAL (F1 0.04), LOCATION (F1 0.13) — open vocabulary, ambiguous terms
- Processing time: under 30 seconds per typical document vs 2–4 hours manual
- The system reduces manual processing time by up to 70% for typical documents (measured; varies by document complexity)

## What's Next

To push the real-world F1 above 0.70, we need:
- 30–50 more real PDFs with hand annotations to train on actual tender language (the biggest gap)
- ARCBERT domain-specific base model (expected +5–8% F1 when network is available)
- Hindi language support for Indian government tenders in bilingual format
- Better MATERIAL entity extraction — this is the critical bottleneck holding back overall performance