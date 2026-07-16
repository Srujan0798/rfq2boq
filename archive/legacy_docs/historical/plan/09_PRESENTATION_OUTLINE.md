# PRESENTATION + REPORT OUTLINE
## What gets handed to the mentor at internship end

---

## A. TECHNICAL REPORT — 20-25 pages

Target audience: technical mentor + academic committee.

```
1. Abstract                                                            (½ p)
2. Introduction                                                        (1 p)
   2.1 Problem: scope omission cost in tendering
   2.2 Why this is hard (cited from AEC Contracts ref)
   2.3 Contributions (4–5 bullets)
3. Related Work                                                        (2 p)
   3.1 NLP in construction (Yan 2022, Sousa 2024)
   3.2 IE for regulatory / technical text (Zhang & El-Gohary 2015)
   3.3 BIM/IFC-aligned NLP (Nabavi 2023)
   3.4 Doc-level IE (Zheng 2023)
   3.5 Industry tools (Helium42, DesignDrafter)
4. System Architecture                                                  (3 p)
   4.1 Pipeline overview (Fig 1: dataflow)
   4.2 Ingestion (Fig 2: layout sample)
   4.3 NER (Fig 3: BERT-BiLSTM-CRF)
   4.4 Relation Extraction
   4.5 Rule + Ontology validator
   4.6 Canonical schema + exporter
5. Dataset                                                              (2 p)
   5.1 Sources, splits, IAA
   5.2 Annotation guide highlights
   5.3 Synthetic augmentation
6. Methods                                                              (3 p)
   6.1 Training procedure
   6.2 Hyperparameters
   6.3 Inference + ONNX
   6.4 Ontology + rules
7. Results                                                              (4 p)
   7.1 Baselines table
   7.2 NER per-type F1
   7.3 RE F1 (intra vs cross-sentence)
   7.4 End-to-end BOQ metrics
   7.5 Ablations
   7.6 Latency + reproducibility
8. Error Analysis                                                       (2 p)
   8.1 Top error categories
   8.2 Pareto chart
   8.3 Three case studies
9. Discussion                                                           (2 p)
   9.1 What worked
   9.2 What didn't
   9.3 Threats to validity
   9.4 Limitations
10. Future Work                                                         (1 p)
    10.1 LLM-RAG hybrid (post-MVP)
    10.2 BIM/IFC export
    10.3 Active learning loop
    10.4 Multilingual expansion
11. Conclusion                                                          (½ p)
12. References                                                          (1-2 p, all 10 from PDF + addl. cited works)
Appendices                                                              (n p)
   A. Full hyperparameter sweep table
   B. Annotation guide excerpt
   C. Ontology snapshot
   D. Example RFQ → BOQ end-to-end
   E. Deploy runbook
```

---

## B. PRESENTATION DECK — 12-15 slides

| # | Slide | Key visual |
|---|---|---|
| 1 | Title + author + mentor + date | logo |
| 2 | Problem framing (cost of scope omission) | $$ chart |
| 3 | What we built (one-sentence + one screenshot) | demo gif |
| 4 | System architecture (single diagram) | pipeline figure |
| 5 | Entity ontology + BIOES example | annotated paragraph |
| 6 | Model: BERT + BiLSTM + CRF | architecture diagram |
| 7 | Rules + Ontology validator (and why we need them) | example with warning |
| 8 | Dataset + annotation pipeline | corpus stats table |
| 9 | Headline results (table: span-F1, RE-F1, end-to-end completeness) | table |
| 10 | Baseline comparison | bar chart |
| 11 | Error analysis (top failure modes) | pareto |
| 12 | Live demo (or video fallback) | demo |
| 13 | Limitations + lessons learned | bullet list |
| 14 | Roadmap (next 3-6 months) | quarter chart |
| 15 | Thanks + Q&A | contact + repo link |

---

## C. DEMO (3-5 min screencast)

Storyboard:
1. (0-15s) Show RFQ PDF (mixed digital + scanned).
2. (15-45s) Upload via web UI → progress bar.
3. (45s-2m) Show resulting BOQ table — point to confidence column and warnings.
4. (2m-3m) Show review-queue: edit a low-confidence row → re-export.
5. (3m-3:30) Show Excel output side-by-side with manual BOQ from same RFQ.
6. (3:30-4m) Show under-the-hood: stage outputs persisted (`doc.json`, `spans.json`, …).
7. (4m-4:30) Show CI passing + tests green + Docker rebuild.
8. (4:30-5m) "Why it matters" closer.

---

## D. STAKEHOLDER COMMUNICATION

| Audience | Artifact | Length |
|---|---|---|
| Mentor (technical) | Report PDF + repo | ~25 p |
| Mentor (managerial) | Slide deck | 15 min talk |
| Committee | Slide deck + demo | 30 min total |
| Self / future readers | README + ADRs | indefinite |

---

**Status:** Outline locked. Report scaffolding committed in W1; sections filled progressively, finalized W10.
