# TASK: Academic Paper — You + Agent-4

**Wave:** 5 | **Tier:** D | **Priority:** P3

## 1. GOAL
Write a publishable paper on hybrid BERT-BiLSTM-CRF + ontology validation for BOQ extraction. Target: ITcon (J. Information Tech. in Construction) or ASCE J. Computing in Civil Engineering.

## 2. CONTEXT
Read first:
- `report/technical_report.md` — existing technical report (basis for paper)
- `results/` — all metrics files
- `models/ner-bert-bilstm-crf-v1/metrics.json`
- [docs/conventions.md](../../docs/conventions.md)

Current state: Technical report exists. No formal paper.

## 3. DELIVERABLES
- [ ] `paper/draft.tex` — LaTeX paper (~10-12 pages)
- [ ] `paper/references.bib` — BibTeX bibliography (≥30 refs)
- [ ] `paper/figures/` — all figures in PDF
- [ ] `paper/tables/` — tables in LaTeX
- [ ] `paper/COVER_LETTER.md` — submission cover letter
- [ ] `paper/RESPONSE_TEMPLATE.md` — template for reviewer responses

## 4. STEPS
1. **Title:** "Hybrid BERT-BiLSTM-CRF with Ontology Validation for Automated BOQ Extraction from Construction RFQ Documents: A Case Study on Indian Tenders"
2. **Abstract** (250 words): problem, method, results, contributions
3. **Introduction** (1.5 pages): construction RFQ context, problem, contributions, paper structure
4. **Related Work** (1.5 pages): NLP in AEC, NER methods, ontology in construction
5. **Methodology** (3 pages): pipeline, NER architecture (BERT+BiLSTM+CRF), pattern matching, RE rules, ontology
6. **Dataset** (1 page): synthetic generation, BIOES annotation, real-world subset, statistics
7. **Experiments** (2 pages): baselines (gazetteer, BERT-linear), ablations, training setup
8. **Results** (2 pages): F1 per entity, ablation table, real-world performance, error analysis
9. **Discussion** (1 page): limitations (synthetic overfitting), generalizability, deployment
10. **Conclusion** (0.5 pages): contributions, future work
11. **References:** 30+ BibTeX entries
12. ITcon template or generic IEEE/ACM template
13. Plagiarism check before submission

## 5. VERIFICATION
```bash
$ test -f paper/draft.tex
EXPECT: exists

$ pdflatex paper/draft.tex 2>&1 | grep -c "Error"
EXPECT: 0

$ wc -l paper/references.bib
EXPECT: ≥150 lines (~30+ entries)

$ test -d paper/figures
EXPECT: exit 0
```

## 6. ACCEPTANCE CRITERIA
- [ ] Compiles to PDF without errors
- [ ] ≥10 pages, ≤14 pages (conference length)
- [ ] ≥30 references
- [ ] Figures + tables present
- [ ] Abstract under 250 words
- [ ] Plagiarism scan passes (use turnitin or similar)
- [ ] Cover letter written

## 7. CONSTRAINTS
- Honest reporting: include the synthetic-overfitting limitation prominently
- Cite all baselines fairly
- Open-source code link + dataset link in paper
- Use ITcon template if targeting ITcon

## 8. DEPENDENCIES
- **Blocked by:** D1 (dataset release for citation)
- **Blocks:** None
- **Parallel-safe with:** D3, D4

## 9. GOTCHAS
- LaTeX warnings about overfull boxes — usually fine, but check
- Figure resolutions: 300 DPI minimum
- ITcon/ASCE templates have specific bibliography formats — verify
- Reviewer suggestions for venue: cite recent (2023-2025) NLP+construction work
- Be honest about real-world F1 of 67% — don't inflate
- Co-author approval needed before submission
