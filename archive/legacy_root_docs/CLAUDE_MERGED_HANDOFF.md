# CLAUDE_MERGED_HANDOFF.md — RFQ2BOQ Consolidated Handoff

> **Purpose:** Merge the content of the root-level and Lane-C handoff files into one
> organized reference. This file notes contradictions between sources but does not
> replace them. For ground-truth metrics, trust the JSON files in `results/` over
> any narrative.
>
> **Merged from:**
> - `/Users/srujansai/Desktop/rfq2boq/CLAUDE.md`
> - `/Users/srujansai/Desktop/rfq2boq/HANDOFF.md`
> - `/Users/srujansai/Desktop/rfq2boq/AGENT_TASKS.md`
> - `/Users/srujansai/Desktop/rfq2boq/FINAL_COMPLETION_SUMMARY.md`
> - `/Users/srujansai/Desktop/rfq2boq/HIERARCHY.md` (deprecated)
> - `/Users/srujansai/Desktop/rfq2boq/docs/CORE_UNDERSTANDING.md`
> - `/Users/srujansai/Desktop/rfq2boq/docs/SWA_REQUIREMENTS_2026-06-11.md`
> - `/Users/srujansai/Desktop/rfq2boq/docs/wave_status.md`
> - `/Users/srujansai/Desktop/rfq2boq/docs/PHASE8_UNIFIED_TIMELINE_AND_FLOW.md`
> - `/Users/srujansai/Desktop/rfq2boq-laneC/CLAUDE.md`
> - `/Users/srujansai/Desktop/rfq2boq-laneC/HANDOFF.md`
> - `/Users/srujansai/Desktop/rfq2boq-laneC/MASTER_HANDOFF.md`
> - `/Users/srujansai/Desktop/rfq2boq-laneC/PROJECT_MAP.md`
> - `/Users/srujansai/Desktop/rfq2boq-laneC/COMPLETE_PROJECT_HANDOFF.md`
> - `/Users/srujansai/Desktop/rfq2boq-laneC/FINAL_ORCHESTRATION.md`
>
> **Generated:** 2026-07-04 by handoff-merge subagent.
> **No source handoff files were modified.**

---

## 1. Project Charter (What This Project Is / Is Not)

**Product:** RFQ2BOQ is Srujan's internship project at SWA Consultancy. It converts
unstructured Indian construction RFQ / tender documents (PDF and XLSX) into a
structured Bill of Quantities (BOQ) in Excel + JSON.

**Pipeline (all sources agree):**

```text
PDF/OCR/XLSX → ingest/tables → NER → relation extraction → rules/ontology
               → BOQ assembly → confidence/validation → export (Excel/JSON/CSV)
```

**Locked schema (all sources agree):**

- **8 entities:** MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE
- **6 relations:** HAS_QUANTITY, HAS_UNIT, AT_LOCATION, OF_GRADE, COMPLIES_WITH, HAS_DIMENSION
- **Tagging scheme:** BIOES (`config.constants.BIOES_LABELS`)
- **Language:** English (Hindi/IndicBERT optional, currently blocked)

**Explicitly out of scope (SCOPE_GUARD / CLAUDE.md):**

- SaaS, multi-tenancy, billing, Stripe
- Academic paper / patent / public dataset / public benchmark
- Voice input, CAD/drawing analysis, sub-domain specialized models
- MLflow tracking server, A/B routing, observability stack (Prometheus/Grafana/Loki/Tempo/Sentry)
- Outbound communication automation (Slack, email, Notion)
- ERP for the startup (R6 — separate repo)
- Mutation/chaos/load testing, OWASP audit, MFA, ClamAV

**Scope note:** Unpriced BOQ only (no Rate/Amount/cost/DSR fields). Only real
RFQs in `data/real_rfqs/`. Synthetic/sample/demo data has been purged to `attic/`.

---

## 2. Source-of-Truth Precedence

All sources agree on the following order (and this merge preserves it):

1. `config/constants.py` — authoritative schema
2. `docs/conventions.md` — locked code rules
3. `docs/` — operational docs
4. `prompts/wave4/` — active agent prompts (`archive/` is read-only history)
5. Agent self-reports / handoff files — least trusted; always verify
6. JSON evaluation outputs in `results/` win over any narrative

**Where truth lives for metrics:**

- `results/eval_honest.json` — entity-level macro P/R/F1
- `results/eval_honest_rows.json` — row-level F1
- `results/eval_honest_v2.json` — Z1 matcher numbers
- `results/eval_honest_rows_after_z2.json` — row-level after Z2 source fix
- `results/FINAL_HONEST_REPORT.md` — human-readable report

If any handoff contradicts these JSON files, the JSON wins.

---

## 3. Current Honest Metrics (with contradictions noted)

### 3.1 Entity-level F1

| Source | Date | XLSX F1 | PDF F1 | Combined macro F1 | Notes |
|--------|------|---------|--------|-------------------|-------|
| HANDOFF.md (root) | 2026-06-29 | 0.890 | 0.142 | 0.441 | 4 XLSX / 6 PDF, independent gold |
| FINAL_COMPLETION_SUMMARY.md | 2026-06-30 | 0.890 | 0.142 | 0.441 | Same as HANDOFF |
| wave_status.md (C8) | 2026-06-27 | 0.890 | 0.142 | 0.441 | C8 final integrated state |
| AGENTS.md | 2026-07-04 | 0.890 | 0.142 | 0.441 | Latest environment guidance |
| AGENT_TASKS.md | 2026-06-11 | 0.667–0.931 per file | 0.0–0.784 per file | 44.8% macro / 43.8% micro | Pre-Z1/Z2 numbers, details per file |
| laneC HANDOFF.md | 2026-06-27 | 0.890 | 0.142 | 0.441 | Same |
| laneC COMPLETE_PROJECT_HANDOFF.md | 2026-06-22 | — | — | 0.584 entity macro (Z1+Z2) | Informational entity metric |
| PHASE8_UNIFIED | 2026-06-03 | 0.580 → 0.767 | 0.233 → 0.462 | 0.372 → 0.584 | Baseline vs Z1/Z2 matcher |

**Per-file entity F1 (root HANDOFF.md, 2026-06-29):**

| # | File | Type | Entity F1 | Notes |
|---|------|------|-----------|-------|
| 01 | GSECL | PDF | 0.000 | NER gap / only 2 items extracted |
| 02 | ISRO | XLSX | 0.750 | |
| 03 | Zydus Matoda | XLSX | 0.560 | |
| 04 | Adani | PDF | 0.000 | Wrong table selected (Z2 later fixed source file) |
| 05 | Zydus Animal | XLSX | 0.931 | |
| 06 | Avante | PDF | 0.784 | |
| 07 | Grew Solar | PDF | 0.615 | |
| 08 | SAEL | XLSX | 0.828 | |
| 09 | GeM 1 | PDF | 0.048 | Gold needs human sign-off |
| 10 | GeM 2 | PDF | 0.323 | Gold needs human sign-off |

**Contradiction / nuance:** The 0.000 values for 01/04/09/10 are partly an
*evaluation mismatch* (gold expects short material names; pipeline outputs full
descriptions). Z1 introduced an asymmetric matcher that raised entity macro F1
from 0.372 to 0.584, but HANDOFF.md (2026-06-29) reverted to the canonical
0.441 combined number. Row-level evaluation is considered the more honest
production metric.

### 3.2 Row-level F1

| Source | Date | Row macro F1 | PDF row F1 | XLSX row F1 | Notes |
|--------|------|--------------|------------|-------------|-------|
| HANDOFF.md (root) | 2026-06-29 | — | 100% fidelity | mixed (drops/over-captures) | Fidelity framing, not strict row F1 |
| FINAL_COMPLETION_SUMMARY.md | 2026-06-30 | 0.921 | 0.981 | 0.830 | 9/10 files at 1.000 |
| wave_status.md Z2 | 2026-06-12 | 0.921 | 0.981 | 0.830 | 9/10 files at 1.000 |
| PHASE8_UNIFIED | 2026-06-03 | 0.323 canonical | — | 36.4/5.1/43.8/70.6% | Strict independent row-gold match |
| laneC COMPLETE_PROJECT_HANDOFF.md | 2026-06-22 | **1.000** | 1.000 | 1.000 | Claims all 10 at 100% |

**Major contradiction:** `FINAL_COMPLETION_SUMMARY.md` and `wave_status.md` report
row-level macro F1 = 0.921 (9/10 files at 1.000, only 05_zydus_animal at 0.487
due to broken rowgold). `COMPLETE_PROJECT_HANDOFF.md` (laneC, 2026-06-22) claims
**100% row-level F1 on all 10 files**. This 100% claim is flagged in
`PHASE8_UNIFIED_TIMELINE_AND_FLOW.md` and `docs/CORE_UNDERSTANDING.md` as a
red-flag pattern — the project has a history of fake-100% self-comparison
incidents. The canonical honest strict row match from PHASE8 is **32.3%**
(material + quantity + unit per row against independent row-gold), with a looser
material-name overlap of ~73–100% for the strong XLSX files.

**Recommended citation:** Use the row-level numbers from `results/eval_honest_rows.json`
and the narrative in `results/FINAL_HONEST_REPORT.md`. Do not cite the laneC
"100% row F1" without independent verification.

### 3.3 NER F1

| Metric | Value | Source |
|--------|-------|--------|
| Pattern-based NER real F1 | ~0.43 | HANDOFF.md, wave_status.md, CORE_UNDERSTANDING |
| ML NER v5 synthetic val F1 | 0.755 | laneC HANDOFF.md, AGENTS.md |
| ML NER v5 sacred-10 F1 | 0.188 | laneC HANDOFF.md, AGENTS.md |
| MATERIAL F1 (v5 held-out) | 0.000 | laneC HANDOFF.md |
| Synthetic/auto-generated training F1 | ~0.996 | CORE_UNDERSTANDING, AGENT_TASKS |

**Consensus:** The ML NER model overfits to synthetic data. Production uses
pattern-based NER (regex + gazetteer). Real improvement requires human-annotated
real tender data, not code fixes.

### 3.4 Fidelity (R1 framing)

- **PDF fidelity:** HANDOFF.md reports 100% capture-fidelity across 6 PDF files
  (i.e., no source row is silently dropped; uncertain rows are flagged).
- **XLSX fidelity:** Mixed — drops rows on 02 ISRO (50%), 03 Zydus Matoda
  (82.5%), 05 Zydus Animal (29.9%); over-captures on 08 SAEL (130.8%). The root
  cause is a business-rule ambiguity: one material with multiple quantity/system
  columns can be interpreted as 1 row or N rows. SWA must decide.

---

## 4. Architecture

All sources describe the same high-level architecture:

```text
Input (PDF/XLSX)
    │
    ├── PDF path ──→ DocumentStructureExtractor (PyMuPDF fast scan)
    │                    ↓
    │               Finds BOQ page range (Schedule/Annexure/Appendix)
    │                    ↓
    │               PDFExtractor ──→ text + tables
    │                    ↓
    │               GeM check (split quantity tables)
    │                    ↓
    │               RowExtractor ──→ BOQ rows
    │
    └── XLSX path ──→ XLSXRowPipeline ──→ structured rows
    │
    ↓
Confidence Scorer / Validator
    ↓
Output: JSON BOQ → UI (Streamlit) / Excel / CSV
```

**Key modules (agreed across sources):**

- `src/pipeline.py` — Main orchestration, routes PDF vs XLSX
- `src/pipeline_xlsx.py` — XLSX row-preservation pipeline
- `src/preproc/document_structure.py` / `src/preproc/sections.py` — Structure-aware extraction
- `src/ingest/pdf_extractor.py` — PDF text/table extraction
- `src/ingest/table_extractor.py` — pdfplumber-based table extraction
- `src/ingest/text_boq_extractor.py` — Text fallback
- `src/nlp/pipeline.py` — Pattern-based NER (production)
- `src/nlp/patterns/dictionary.py` — DictionaryLookup (~132 material keys)
- `src/nlp/patterns/gem_catalog.py` — GeM product gazetteer (~60 products)
- `src/domain/boq_assembler.py` — BOQ row assembly + unit normalization + confidence
- `src/export/excel_generator.py` — CPWD-format Excel export
- `ui/app.py` — Streamlit UI

**Deprecated note:** `HIERARCHY.md` (root, 2026-05-17) is explicitly marked
DEPRECATED; use `PROJECT_MAP.md` / `docs/PHASE8_UNIFIED_TIMELINE_AND_FLOW.md`
instead.

---

## 5. SWA Requirements (2026-06-11 Review)

| Req | Summary | Status / Owner |
|-----|---------|----------------|
| **R1** | 100% data-conversion fidelity: capture every source line item, **flag** uncertain rows, never silently drop. | Engineering target; fidelity audit tooling future work. XLSX multi-qty-column rule pending SWA decision. |
| **R2** | GeM portal catalogs are authoritative NER reference (closed vocabulary). | Initial 60-product gazetteer integrated; waiting on SWA's real submitted GeM list. |
| **R3** | ~100 real PDFs incoming; intake/annotation loop must be ready. | 1 extra doc received; collection is owner-only (Sales/Jineth/Softnil). |
| **R4** | Structure-first extraction for large PDFs (outline → BOQ section → targeted extraction). | Implemented; false-positive filtering and multi-range support remain. |
| **R5** | Hybrid orchestration method: owner assigns tasks, agents implement, owner verifies. | Protocol live in `tasks/NEXT_WAVE.md` / `docs/PHASE8_UNIFIED_TIMELINE_AND_FLOW.md`. |
| **R6** | ERP project is a separate repo; never build it here. | Out of scope. |

**Critical R1 nuance:** R1 is a *fidelity/completeness* requirement, not a claim
that NER is 100% correct. The honest deliverable is "capture + flag, never drop."

---

## 6. Wave Status / Completion Claims

### 6.1 Root project state (HANDOFF.md, 2026-06-29)

> "Working honest assist tool — NOT 100% correct on any RFQ. Fidelity not yet 100%."

Remaining work (priority order):

1. Resolve multi-qty-column business rule, then fix XLSX exact-once capture.
2. Build closed-catalog matcher (`src/nlp/catalog_matcher.py`) against GeM catalog.
3. Human-verify 9 insulation gold pairs.
4. Update deliverables with post-fix numbers.
5. Collect 100 real PDFs (human/SWA task).

### 6.2 Root project state (FINAL_COMPLETION_SUMMARY.md, 2026-06-30)

> "✅ COMPLETE — Ready for Handover"

Claims all verification gates pass (103 critical tests, lint, anti-cheat, gold
unmodified, git clean, `make verify` passed). Lists remaining items as external
dependencies: ARCBERT/IndicBERT download blocked, 9 insulation gold pairs
sign-off, 05_zydus_animal rowgold re-transcribe, 46 more real PDFs, GitHub push
blocked, Python 3.14 segfault.

### 6.3 Lane C state (laneC handoff files, 2026-06-11 to 2026-06-27)

- `FINAL_ORCHESTRATION.md` (2026-06-11): Architecture complete, data is the
  bottleneck, honest F1 43.8% micro / 44.8% macro entity-level.
- `MASTER_HANDOFF.md` (2026-06-11): 97 tests pass, structure extractor added,
  GeM gazetteer integrated, 100 PDF collection is P0 human task.
- `COMPLETE_PROJECT_HANDOFF.md` (2026-06-22): Claims **100% row-level F1** on all
  10 SWA files and "ready for scaling."
- `HANDOFF.md` (laneC, 2026-06-27): Same entity metrics as root (XLSX 89%, PDF
  14%, combined 44.1%), but repeats the 100% row F1 claim.

### 6.4 Key contradiction summary

| Claim | Source | Trust level | Why |
|-------|--------|-------------|-----|
| "NOT 100% correct; fidelity not yet 100%" | root HANDOFF.md (2026-06-29) | High | Matches anti-cheat doctrine |
| "COMPLETE — Ready for Handover" | FINAL_COMPLETION_SUMMARY.md (2026-06-30) | Partial | Gates pass, but PDF F1 14% and external blockers remain |
| "100% row-level F1 on all 10 SWA files" | laneC COMPLETE_PROJECT_HANDOFF.md / laneC HANDOFF.md | Treat as red flag | Project history of fake-100% self-comparison; canonical strict match is 32.3% |
| Row-level macro F1 = 0.921, 9/10 at 1.000 | FINAL_COMPLETION_SUMMARY.md / wave_status.md Z2 | Medium-high | Documented methodology, but 05_zydus_animal rowgold is broken (qty=0) |
| Canonical strict row match = 32.3% | PHASE8_UNIFIED_TIMELINE_AND_FLOW.md | High | Independent row-gold, material+qty+unit, anti-cheat compliant |

**Bottom line:** The codebase is functional and quality-gated, but PDF extraction
accuracy is low (14% entity F1) and the 100% row-F1 claim from Lane C should be
verified against `results/eval_honest_rows.json` before being trusted.

---

## 7. Active Blockers

### 7.1 Business / human blockers (cannot be fixed by code)

1. **Multi-quantity-column XLSX rule** — SWA must decide whether one material
   with N quantity columns becomes 1 BOQ row or N rows. This drives the fidelity
   over/under-capture on 02/03/05/08.
2. **9 insulation gold pairs pending human sign-off** — Owner review needed for
   `data/real_rfqs/gold/swa_09_*.json` and `swa_10_*.json`.
3. **05_zydus_animal rowgold is broken** — All 67 entries have `quantity="0"`;
   needs re-transcription from the source XLSX.
4. **~100 real PDF dataset collection** — Human coordination task (Sales,
   Jineth, Softnil archive, government portals).
5. **SWA's real GeM product list** — Replace/extend the hand-built 60-product
   gazetteer.

### 7.2 Technical / environment blockers

1. **ML NER needs real annotated data** — Pattern-based NER ~0.43 F1; v5 model
   overfits to synthetic (sacred-10 F1 0.188). No code fix substitutes for data.
2. **ARCBERT / IndicBERT downloads blocked** — Network blocked from this machine;
   SciBERT fallback in place.
3. **GitHub push blocked** — `pack-objects` hangs; ~31–194 unpushed commits +
   `v1.0-handover` tag remain local (counts vary by source/date).
4. **Python 3.14 instability** — Charter pins 3.11–3.13; typer/click/Pillow have
   issues on 3.14. Some threaded tests skip or segfault.
5. **Large PDF false positives** — Structure extractor finds 1281 candidate
   sections in a 29 MB PDF; needs stricter heading detection.
6. **No camelot-py** — Complex PDF tables rely on pdfplumber only.
7. **No Hindi/Indic language support** — Regional bilingual tenders may fail.

---

## 8. The 10 Sacred SWA Files

Located at `data/real_rfqs/swa_enquiries/`. These are the only documents that
matter for validation. Do not add synthetic files here.

| # | Client | File(s) | Type | Demo strength | Notes |
|---|--------|---------|------|---------------|-------|
| 01 | GSECL Wanakbori | `RFQ-75810 TMD-8.pdf` (62 pp) | PDF | ⚠️ Weak | 2 items; structure-aware extraction finds page 61 |
| 02 | ISRO VSSC | `VSSC_BOQ_with_qty.xlsx` | XLSX | ✅ Lead | 8 rows, instant |
| 03 | Zydus Matoda | `Zydus_Matoda_Insulation_Enquiry.xlsx` | XLSX | ✅ Strong | 33 rows, instant |
| 04 | Adani | `BOQ PAGE*.pdf` ×2 + specs | PDF | ⚠️ Bug fixed | Pipe vs duct table source confusion resolved in Z2 |
| 05 | Zydus Animal | `Insulation Enquiry*.xlsx` + TDS + spec | XLSX | ✅ Strongest | 48 rows, instant; rowgold qty=0 needs fix |
| 06 | Avante | `Insulation Boq_132.pdf` + spec | PDF | ⚠️ Over-extracts | 14 items + junk FP |
| 07 | Grew Solar | `108, BOQ compliance*.pdf` + spec + TDS | PDF | ⚠️ Over-extracts | 23 items + junk FP |
| 08 | SAEL | `Insulation Enquiry - SAEL.xlsx` | XLSX | ✅ Clean | 12 rows, instant |
| 09 | GeM 7439924 | `GeM-Bidding-9218026.pdf` (23 pp) | PDF | 🔴 Slow | 16–40 s; gold needs sign-off; do not live demo |
| 10 | GeM 7552777 | `GeM-Bidding-9343469.pdf` (14 pp) | PDF | ⚠️ Slow | 16–40 s; gold needs sign-off |

**Demo order (strongest first):** 05 → 03 → 02 → 08 → 04 → 06 → 07 → 10 → 01 → 09

---

## 9. Verification Commands

```bash
# CI gate (tests + lint + anti-cheat + git-clean)
make verify

# Honest evaluations
python3 scripts/eval_honest.py          # entity-level
python3 scripts/eval_honest_rows.py     # row-level
python3 scripts/eval_honest_v2.py       # Z1 matcher

# Fidelity measurement
PYTHONPATH=. .venv/bin/python scripts/measure_fidelity.py

# Quick smoke test
python3 -c "from src.nlp.pipeline import NLPPipeline; p=NLPPipeline(); r=p.process('Supply 500 kg cement as per IS 456 M20 grade at ground floor'); assert len(r.entities) > 0"

# Run UI / API
streamlit run ui/app.py
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

---

## 10. Anti-Cheat Rules (Non-Negotiable)

Repeated across `HANDOFF.md`, `PHASE8_UNIFIED_TIMELINE_AND_FLOW.md`,
`docs/CORE_UNDERSTANDING.md`, and `AGENT_TASKS.md`:

1. Never grade the pipeline against gold the pipeline produced.
2. Gold must be independent + human-verified.
3. A sudden ~100% / perfect score is a red flag — investigate, don't celebrate.
4. Never modify gold files to match pipeline output.
5. No threshold-lowering, no `if filename ==` hacks, no hardcoded scores.
6. Schema is locked: 8 entities, 6 relations, BIOES.
7. One agent at a time on the canonical tree; finish → verify → commit → next.
8. `make verify` must pass before claiming completion.

---

## 11. What NOT to Do

1. Never ask the user for next steps.
2. Never use synthetic/sample data in production paths.
3. Never create parallel branches — `phase8-clean-slate` is canonical.
4. Never commit without `make verify`.
5. Never modify gold files.
6. Never break the 10 SWA RFQs.
7. Never move/rename/archive the `resources/` folder (sacred SWA brief + papers).

---

## 12. One-Paragraph Honest Summary

> RFQ2BOQ converts construction tenders to structured BOQ. The architecture is
> complete and the pipeline runs end-to-end on all 10 SWA tenders without
> crashing. XLSX extraction is strong (~89% entity F1, exact row counts on the
> lead files). PDF extraction is weak (~14% entity F1) because the NER model was
> trained on synthetic academic prose, not real tenders. The real path to higher
> accuracy is human-annotated real RFQs plus closed-catalog matching against the
> GeM catalog. Do not claim "100% correct"; the honest deliverable is 100%
> fidelity (capture + flag, never drop) and independently verified metrics. The
> laneC "100% row-level F1" claim should be treated as a red flag and verified
> against `results/eval_honest_rows.json`.

---

*End of merged handoff. Source files remain intact. Verify all numbers against
`results/` JSON before citing them.*
