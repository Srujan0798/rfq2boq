# TASK: P3T6 — Internship Report + Slide Deck — Agent-4

**Phase:** 3 | **Effort:** 1-2 days | **Priority:** P1 (the handover deliverable)

## 1. GOAL
Produce the technical report and slide deck Srujan hands to SWA Consultancy at the end of the internship. NOT an academic paper, NOT for journal submission — this is an internal deliverable describing what was built, how it works, and how well it performs.

## 2. CONTEXT
Read first:
- `resources/RFQ to BOQ Scope Extraction using NLP system.pdf` — original SWA brief, anchor the report to this
- `resources/RESOURCES_GUIDE.md` — supporting academic references (Zhang & El-Gohary 2015 etc.)
- `docs/architecture.md` — system architecture
- `docs/HYBRID_PLAN.md` — strategic rationale
- `docs/wave_status.md` — what's done vs pending (use real numbers, not stale)
- `results/real_world_metrics.json` and `results/real_world_metrics_v2.json` — actual F1 numbers
- `results/final_model_eval.json` — fine-tuned model performance
- `data/real_rfqs/manifest.json` — real corpus size
- [docs/SCOPE_GUARD.md](../../../docs/SCOPE_GUARD.md) — drift list

This deliverable is INTERNAL to SWA Consultancy. It is NOT:
- An academic paper (no journal submission language)
- A patent disclosure (Srujan handles IP separately)
- A marketing document (no inflated claims)

## 3. DELIVERABLES
- [ ] `deliverables/report/internship_report.md` — 15-25 page technical report
- [ ] `deliverables/report/internship_report.pdf` — rendered PDF
- [ ] `deliverables/slides/presentation.md` — 12-15 slide Marp-compatible markdown
- [ ] `deliverables/slides/presentation.pdf` — rendered PDF
- [ ] `deliverables/report/figures/` — every figure embedded (architecture diagram, F1 chart, sample BOQ output)
- [ ] `deliverables/EXECUTIVE_SUMMARY.md` — 1-page summary for SWA management

## 4. STEPS
1. Read all context files. Confirm scope: SWA-internal, not academic.
2. Outline the report (15-25 pages):
   - **Cover** — Title, Srujan's name, SWA Consultancy, date
   - **Executive Summary** (0.5 pg) — problem, solution, result in plain English
   - **1. Problem & Scope** (1 pg) — what RFQ→BOQ extraction is, why it matters, the SWA brief
   - **2. Related Work** (1.5 pg) — cite Zhang & El-Gohary 2015 as the academic precedent (precision 0.969, recall 0.944); compare commercial tools (Kreo, Realx, BuildVisionAI, Nexizo) briefly
   - **3. Approach** (3 pg) — hybrid ML + rules architecture, BIOES 8-entity schema, the 7-stage pipeline
   - **4. Implementation** (3 pg) — stack, model architecture (BERT-BiLSTM-CRF), pattern matching, rule engine, ontology, OmniClass mapping
   - **5. Data** (2 pg) — synthetic generation (300 docs), real corpus (50 PDFs), annotation methodology, BIOES tagging
   - **6. Evaluation** (3 pg) — honest metrics: synthetic F1 ≈ 99%, real F1 ≈ 0.51-0.75 depending on dataset; what improved between iterations; per-entity breakdown
   - **7. Demo & Outputs** (2 pg) — Streamlit UI screenshots, CPWD-format Excel output sample, sample BOQ JSON
   - **8. Limitations & Future Work** (1.5 pg) — be honest: small real-data corpus, F1 below academic precedent, scanned PDFs require OCR, Hindi support optional
   - **9. Conclusion** (0.5 pg)
   - **References** — Zhang & El-Gohary 2015, any other cited work
3. Outline the slide deck (12-15 slides, Marp markdown):
   - 1. Title
   - 2. Problem
   - 3. Solution overview
   - 4. Pipeline diagram
   - 5. Entity + relation schema
   - 6. Architecture (hybrid ML + rules)
   - 7. Training data approach (synthetic + real)
   - 8. Results table (honest numbers)
   - 9. Demo screenshot
   - 10. Sample Excel BOQ output
   - 11. Limitations
   - 12. Future work
   - 13. Thanks/Q&A
4. Generate figures:
   - Architecture pipeline diagram (text-based ASCII or Graphviz → PNG)
   - Per-entity F1 bar chart (from results JSONs) — matplotlib
   - Sample BOQ Excel screenshot (open `data/samples/sample_boq_output.xlsx`)
   - Streamlit UI screenshot (run `make serve-ui` briefly, screenshot)
5. Write the report in markdown → render to PDF via `pandoc` or `weasyprint`
6. Write the slides in Marp markdown → render to PDF via `marp-cli` if available, else markdown only
7. Write `deliverables/EXECUTIVE_SUMMARY.md`:
   - 1 page max
   - 4 sections: Problem, What we built, Results, What's next
   - No technical jargon (assume the reader is a project manager)

## 5. VERIFICATION
```bash
# Files exist
$ test -f deliverables/report/internship_report.md && wc -w deliverables/report/internship_report.md
EXPECT: >= 4000 words

$ test -f deliverables/slides/presentation.md && grep -c "^---" deliverables/slides/presentation.md
EXPECT: >= 12 slide separators

$ ls deliverables/report/figures/*.png 2>/dev/null | wc -l
EXPECT: >= 3

$ test -f deliverables/EXECUTIVE_SUMMARY.md && wc -w deliverables/EXECUTIVE_SUMMARY.md
EXPECT: 200-500 words (concise)

# No academic/patent language
$ grep -iE "journal submission|patent filing|publish in|peer review|preprint" deliverables/report/internship_report.md deliverables/slides/presentation.md
EXPECT: (empty output)

# Honest F1 numbers (not inflated)
$ grep -E "0\.99|99\.5%" deliverables/report/internship_report.md
EXPECT: only appears in synthetic-data context (must include caveat about overfitting)

# Citation present
$ grep -i "zhang" deliverables/report/internship_report.md
EXPECT: at least one mention
```

## 6. ACCEPTANCE CRITERIA
- [ ] Report has all 9 sections + cover + references
- [ ] All real-world F1 numbers come from `results/*.json` (no fabrication)
- [ ] Synthetic F1 (≈99%) is reported WITH a caveat about training/test split overlap
- [ ] Limitations section is honest about real F1 being lower than synthetic
- [ ] Zhang & El-Gohary 2015 cited
- [ ] At least 3 figures embedded (architecture, F1 chart, output sample)
- [ ] Slides render cleanly (Marp PDF if possible, else markdown is fine)
- [ ] Executive summary fits one page, plain English
- [ ] No academic publication / patent / dataset-release language

## 7. CONSTRAINTS
- DO NOT inflate F1 numbers — report what `results/*.json` contains
- DO NOT submit to any journal/conference (this is SWA-internal)
- DO NOT add academic-publication phrasing ("we propose", "novel contribution") — keep operational tone
- DO NOT add patent/IP language
- DO NOT touch `src/`, `tests/`, `models/`, `data/` — write-only on `deliverables/`
- All imports if any use `src.` prefix
- Cite all academic references with full citation (author, title, year, venue)

## 8. DEPENDENCIES
- **Blocked by:** P3T1 (final F1 numbers must be measured)
- **Blocks:** P3T5 (demo video uses report's executive summary as script anchor)
- **Parallel-safe with:** P3T2, P3T3, P3T4

## 9. GOTCHAS
- The SWA brief is in `resources/` — DO NOT MOVE that folder, it's sacred (see CLAUDE.md §9)
- Real F1 numbers: use `results/real_world_metrics_v2.json` (31 docs, F1 ≈ 0.506) as the honest baseline. The earlier 0.67 from `real_world_metrics.json` was on only 10 docs — small sample
- The "fine-tuned" model in `final_model_eval.json` was trained on 14 gold examples — not statistically meaningful. Report this honestly
- pandoc may not be installed — `brew install pandoc` if needed
- marp-cli may not be installed — `npm install -g @marp-team/marp-cli` if needed
- If PDF rendering fails, deliver the markdown files + flag the PDF issue in REPORT — do not block on this
- Use the project brief's 70% time-reduction claim only with the caveat "potential improvement when extrapolated; measured impact varies by document complexity"

## End-of-task REPORT format

```text
## REPORT: P3T6 Internship Report

Deliverables:
- deliverables/report/internship_report.md (N words, N pages estimated)
- deliverables/report/internship_report.pdf (or note if render failed)
- deliverables/slides/presentation.md (N slides)
- deliverables/slides/presentation.pdf (or note)
- deliverables/report/figures/ (N PNGs)
- deliverables/EXECUTIVE_SUMMARY.md (N words)

Verification:
- All Section 5 commands passed: yes/no
- F1 numbers cited: synthetic X.XX, real X.XX (from real_world_metrics_v2.json)
- Zhang & El-Gohary cited: yes
- Figures embedded: N

Blockers: [none / list]
Deviations: [none / list]
Outside-spec edits: [none / list]
```
