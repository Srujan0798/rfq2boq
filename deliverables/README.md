# RFQ2BOQ Internship Deliverables

## Overview

This folder contains the internship deliverables for the RFQ2BOQ project at SWA Consultancy.

---

## 1. Report — `report/internship_report.md`

**Word count:** ~4,365 words (~18 pages at 250 words/page)

A complete 15–25 page internship report covering:

| Section | Content |
|---------|---------|
| Abstract | Project summary, method, key results (F1 0.523) |
| 1. Introduction | Problem statement, research context (Zhang & El-Gohary 2015) |
| 2. Literature Review | NLP in construction, NER approaches, hybrid ML+rules |
| 3. System Architecture | 7-stage pipeline diagram, module roles, design decisions |
| 4. Methodology | BIOES tagging, 8 entities, BERT-BiLSTM-CRF, conflict resolution |
| 5. Results | Synthetic F1 0.996, **Real F1 0.5227**, per-entity breakdown, CPWD export |
| 6. Limitations & Future Work | Gold corpus size, MATERIAL bottleneck, ARCBERT, Hindi |
| 7. Conclusion | Achievements, what works, what needs data |
| References | Zhang & El-Gohary, Lin et al., Lample, Devlin, et al. |
| Appendices | Entity schema, BIOES examples, DSR coverage, per-document results |

**Key claims (all verifiable from source files):**
- Real-world micro F1 = 0.5227 (from `results/real_world_metrics_v2.json`)
- Synthetic F1 = 0.996 (from `README.md`)
- 31 gold-annotated documents evaluated
- 8 entity types, 33 BIOES labels (from `config/constants.py`)
- CPWD DSR 2023: 507 items, 83% coverage (from `docs/wave_status.md`)

---

## 2. Slides — `slides/presentation.md`

**Word count:** ~1,119 words (~12–14 slides)

A Marp markdown slide deck for presentation:

| Slide | Topic |
|-------|-------|
| 1 | Title: RFQ to BOQ — NLP-Based Construction Tender Analysis |
| 2 | Problem: Manual extraction is slow, error-prone, costly |
| 3 | Solution: Automated RFQ → BOQ pipeline overview |
| 4 | Entity & relation schema (8 entities, 6 relations, BIOES) |
| 5 | NER architecture: BERT-BiLSTM-CRF |
| 6 | Hybrid approach: ML + patterns + ontology + conflict resolution |
| 7 | Results: Real-world F1 = 0.52 (honest vs synthetic 0.996) |
| 8 | Per-entity breakdown (STANDARD 0.942 best, MATERIAL 0.037 worst) |
| 9 | CPWD Excel output (trade grouping, DSR lookup, GST, confidence) |
| 10 | Streamlit UI demo |
| 11 | Processing speed (~30s typical document) |
| 12 | Limitations (MATERIAL bottleneck, small gold set, no ARCBERT) |
| 13 | Future work: gold annotations, ARCBERT, active learning |
| 14 | Thank you / Q&A |

---

## Files

```
deliverables/
├── README.md                  ← this file
├── report/
│   ├── internship_report.md   ← full internship report (4365 words)
│   ├── technical_report.md    ← prior technical report (existing)
│   ├── BUSINESS_CASE.md       ← prior business case (existing)
│   ├── EXECUTIVE_SUMMARY.md   ← prior executive summary (existing)
│   └── figures/               ← charts and diagrams
└── slides/
    ├── presentation.md       ← Marp slide deck (1119 words)
    └── PRESENTATION_SLIDES.md ← prior slides (existing)
```

---

## How to Present

**Report:** Open `report/internship_report.md` in any Markdown viewer (Typora, VS Code, Obsidian, GitHub).

**Slides:** Convert with Marp CLI:
```bash
marp slides/presentation.md --output slides/
# or for HTML output:
marp slides/presentation.md --html --output slides/
```

Or open directly in Marp for VS Code / Marp Web.

---

## Source Files for Verification

| Claim | Source |
|-------|--------|
| Real F1 0.5227 | `results/real_world_metrics_v2.json` |
| Synthetic F1 0.996 | `README.md` |
| 31 gold documents | `results/real_world_metrics_v2.json` |
| 507 DSR items | `docs/wave_status.md` |
| 8 entity types | `config/constants.py` |
| BERT-BiLSTM-CRF | `docs/model_card.md`, `docs/architecture.md` |
| Conflict strategies | `docs/conflict_resolution.md` |
| Zhang & El-Gohary citation | Literature review (source: academic database) |