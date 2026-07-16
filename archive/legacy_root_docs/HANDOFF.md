# RFQ2BOQ — Consolidated Handoff

**Date:** 2026-06-29
**Branch:** `phase8-clean-slate`
**Status:** Working honest assist tool — NOT 100% correct on any RFQ. Fidelity not yet 100%.

**⚠️ CORPUS SCOPE CORRECTION (2026-07-05):** this document predates the corpus expansion. Every "10 sacred SWA RFQs" reference below is real and correct as far as it goes (they ARE sacred — never delete, always test against them, they're the frozen TEST anchor) but they are **10 of 127** real documents, not the whole corpus. See `docs/CORPUS_DEFINITION.md` and `data/real_rfqs/ALL_RFQS_README.md` before scoping any fidelity/training/eval work.

---

## 1. Honest State

It is a **working, honest assist tool**, but it is **not** "100% correct on any RFQ." Do not claim either.

**The two "100%"s — never confuse them:**
- **Fidelity (the real SWA requirement, R1):** capture every source line item, *flag* uncertain ones, NEVER silently drop. This is achievable and is the deliverable target.
- **NER correctness:** how right the extracted values are. XLSX ~89%, PDF ~14%. NOT 100%.

**Key insight (R2):** SWA's real use case is **closed-catalog matching**, not open NER. The GeM catalog (`data/real_rfqs/swa_gem_catalog_full.json`, ~19 standardized insulation products) is a *closed vocabulary*. This is the path to high accuracy.

---

## 2. Executive Summary

RFQ2BOQ is an AI system that reads construction tender documents (RFQs) and extracts Bill of Quantities (BOQ) — a structured list of materials, quantities, and units. The product is for **SWA Consultancy**, an insulation contractor.

**Scope:** Extraction only. Unpriced (no rates). One RFQ at a time. English only.
**NOT in scope:** SaaS, paper, patent, voice, CAD, billing, observability stack.

**Current status:** Core pipeline works on 10 real SWA RFQs. XLSX extraction production-ready at 89% entity-level F1. PDF extraction needs real training data at 14.2% F1.

---

## 3. Verified Metrics (Sacred 10 — Honest, Independent Gold)

**Updated 2026-06-29. Anti-cheat note:** Gold is independent and human-verified. No self-comparison. No threshold gaming.

### Entity-Level

| Metric | Value | Notes |
|--------|-------|-------|
| XLSX macro F1 | **0.890** | 4 XLSX files |
| PDF macro F1 | **0.142** | 6 PDF files |
| Insulation domain F1 | **0.217** | 9 gold pairs pending human sign-off |
| Entity macro F1 | **0.441** | Combined |

### Per-File Entity-Level F1

| File | Type | Entity F1 | Notes |
|------|------|-----------|-------|
| 01 GSECL | PDF | 0.000 | NER gap |
| 02 ISRO | XLSX | 0.750 | |
| 03 Zydus Matoda | XLSX | 0.560 | |
| 04 Adani | PDF | 0.000 | Wrong table selected |
| 05 Zydus Animal | XLSX | 0.931 | |
| 06 Avante | PDF | 0.784 | |
| 07 Grew Solar | PDF | 0.615 | |
| 08 SAEL | XLSX | 0.828 | |
| 09 GeM 1 | PDF | 0.048 | Gold needs sign-off |
| 10 GeM 2 | PDF | 0.323 | Gold needs sign-off |

### Fidelity (capture rate)

PDFs: 100% fidelity across all 6 PDF files. XLSX: mixed — drops rows on 02 ISRO (50%), 03 Zydus Matoda (82.5%), 05 Zydus Animal (29.9%); over-captures on 08 SAEL (130.8%). Run `PYTHONPATH=. .venv/bin/python scripts/measure_fidelity.py` for details.

### NER Real F1

| Metric | Value | Notes |
|--------|-------|-------|
| NER real F1 | ~0.43 | Pattern-based NER; needs 100+ real PDFs + human BIOES annotation |
| NER synthetic F1 | ~0.996 | Inflated — auto-generated from academic papers, not real tenders |

### Generalization (50 Unseen RFQs)

| Domain | Files | Avg Items | Range |
|--------|-------|-----------|-------|
| Building | 15 | 11.5 | 9-15 |
| Road | 6 | 9.2 | 8-10 |
| Bridge | 11 | 8.0 | 8 |
| Plumbing | 9 | 3.7 | 3-4 |
| Electrical | 9 | 5.7 | 5-6 |

All 50 files produced valid BOQ items. No crashes.

---

## 4. Architecture

```
Input (PDF/XLSX)
    │
    ├── PDF path ──→ DocumentStructureExtractor (PyMuPDF fast scan)
    │                    ↓
    │               Finds BOQ page range (±8 pages around Schedule/Annexure)
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
Output: JSON BOQ → UI (Streamlit) → Excel export
```

**Key modules:**
- `src/pipeline.py` — Main orchestration (routes PDF vs XLSX)
- `src/pipeline_xlsx.py` — XLSX row-preservation pipeline
- `src/preproc/document_structure.py` — Structure-aware PDF extraction
- `src/ingest/pdf_extractor.py` — PDF text/table extraction
- `src/nlp/pipeline.py` — Pattern-based NER (regex + gazetteer)
- `src/nlp/patterns/dictionary.py` — DictionaryLookup (132 material keys)
- `src/nlp/patterns/gem_catalog.py` — GeM product gazetteer
- `src/domain/boq_assembler.py` — Row assembly + unit normalization
- `ui/app.py` — Streamlit UI (port 8502)

---

## 5. The 10 Sacred SWA Files

Located at `data/real_rfqs/swa_enquiries/`. These are the ONLY files that matter for validation.

| # | Client | File(s) | Type | Status |
|---|--------|---------|------|--------|
| 01 | GSECL Wanakbori | `RFQ-75810 TMD-8.pdf` (62 pp) | PDF | Fixed — structure-aware extraction |
| 02 | ISRO VSSC | `VSSC_BOQ_with_qty.xlsx` | XLSX | Ground truth — 8 rows |
| 03 | Zydus Matoda | `Zydus_Matoda_Insulation_Enquiry.xlsx` | XLSX | Ground truth — 33 rows |
| 04 | Adani | `BOQ PAGE*.pdf` ×2 + specs ×2 | PDF | Fixed — dedup + parent/child tracking |
| 05 | Zydus Animal | `Insulation Enquiry*.xlsx` + TDS + spec | XLSX | Ground truth — 48 rows |
| 06 | Avante | `Insulation Boq_132.pdf` + spec | PDF | Works — 34 rows |
| 07 | Grew Solar | `108, BOQ compliance*.pdf` + spec + TDS | PDF | Works — multi-format test |
| 08 | SAEL | `Insulation Enquiry - SAEL.xlsx` | XLSX | Ground truth — 12 rows |
| 09 | GeM 7439924 | `GeM-Bidding-9218026.pdf` (23 pp) | PDF | Fixed — 16-40s |
| 10 | GeM 7552777 | `GeM-Bidding-9343469.pdf` (14 pp) | PDF | Fixed — 16-40s |

**Demo order:** 05 → 03 → 02 → 08 → 04 → 06 → 07 → 10 → 01 → 09

---

## 6. The #1 Blocker Is a Business Decision, Not Code

XLSX drop/over-capture comes from **wide BOQ sheets where one material has MANY quantity columns** (e.g. `05_zydus_animal` has 9+ system/location qty columns).

**SWA must decide:** is one material with 9 qty columns → **1 BOQ row** or **9 BOQ rows**?
- The pipeline and the gold currently disagree, which is why fidelity looks wrong.
- No agent can decide this — it is how SWA wants the BOQ structured. **Get this answer first.**

---

## 7. Remaining Work (Priority Order)

1. **Resolve multi-qty-column rule** (business decision), then make `pipeline_xlsx.py` produce exactly that → captured == source on all XLSX
2. **Build closed-catalog matcher** — `src/nlp/catalog_matcher.py`: match each BOQ line to `swa_gem_catalog_full.json` + `data/ontology/insulation_*.json` (exact → fuzzy → flag-unmatched). This is the accuracy engine.
3. **Human-verify 9 insulation gold pairs** (`data/real_rfqs/gold/rows/insul_*.rowgold.json`, all `human_verified:false`)
4. **Final report** — update `deliverables/` with real post-fix numbers
5. **100 PDF dataset collection** — HUMAN task (Sales team, Jineth, Softnil archive)

---

## 8. Anti-Cheat Rules (NON-NEGOTIABLE)

This project was cheated 5+ times. These rules prevent it from happening again.

1. Never edit gold to match pipeline output. Gold comes from source (BOQ PDF / XLSX cell / human).
2. Never grade the pipeline against its own output (self-comparison = the cheat that happened).
3. No threshold-lowering, no `if filename ==` hacks, no hardcoded scores, no fake "100% COMPLETE".
4. A sudden ~100% is a RED FLAG — investigate, don't celebrate. Re-run harnesses yourself.
5. Schema is locked: `config/constants.py` (8 entities, 6 relations, BIOES). Never modify.
6. One agent at a time. Finish → verify → commit → next. No parallel agents on the tree.

---

## 9. How to Run

```bash
# Activate env
cd ~/Desktop/rfq2boq
source .venv/bin/activate

# CI gate (tests + lint + anti-cheat)
make verify

# Fidelity numbers
PYTHONPATH=. .venv/bin/python scripts/measure_fidelity.py

# Unit tests
.venv/bin/python -m pytest tests/unit -q

# CLI extraction
python3 -m src.cli --file tender.pdf --out boq.xlsx

# API server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Streamlit UI
streamlit run ui/app.py  # Port 8502

# Docker
docker build -t rfq2boq -f deployment/Dockerfile .
docker run -p 7860:7860 rfq2boq

# Quick smoke test
python3 -c "from src.nlp.pipeline import NLPPipeline; p=NLPPipeline(); print(len(p.process('Supply 500 sqm nitrile rubber insulation 9mm thick as per IS 8183').entities))"
```

**Reproduction:**
```bash
git clone <repo> && cd rfq2boq
pip install -e ".[dev]"
make verify
python3 -m src.cli --file your_tender.pdf --out boq.xlsx
```

---

## 10. Critical Files & Roles

| File | Role | Change Risk |
|------|------|-------------|
| `src/pipeline.py` | Main orchestration — routes PDF vs XLSX | HIGH |
| `src/pipeline_xlsx.py` | XLSX row-preservation pipeline | LOW |
| `src/preproc/document_structure.py` | Structure-aware extraction — finds BOQ pages | HIGH |
| `src/ingest/pdf_extractor.py` | PDF text/table extraction | MEDIUM |
| `src/ingest/table_extractor.py` | Table extraction using pdfplumber | MEDIUM |
| `src/nlp/pipeline.py` | Pattern-based NER | MEDIUM |
| `src/nlp/patterns/dictionary.py` | DictionaryLookup — 132 material keys | LOW |
| `src/domain/boq_assembler.py` | BOQ row assembly + confidence scoring | MEDIUM |
| `data/real_rfqs/swa_enquiries/` | The 10 sacred SWA RFQs | NEVER DELETE |
| `data/real_rfqs/gold/` | Gold annotations + row gold | NEVER DELETE |

---

## 11. Known Issues & Edge Cases

1. **GeM PDFs are bilingual (Hindi/English)** — Extraction may pick up Hindi text. Currently filtered by regex.
2. **Large PDFs (>50 pages)** — Structure extractor handles via PyMuPDF fast scan + tight page ranges.
3. **Multi-table GeM pages** — Fixed. `extract_boq_rows_from_split_quantity_page()` handles multiple tables per page.
4. **Zero-quantity rows** — Fixed in Adani. Deduplication removes 0-qty duplicates.
5. **Structure extractor false positives** — 1281 sections found in 29MB PDF. BOQ detection works but noisy. Needs stricter heading detection.
6. **No camelot-py installed** — Complex PDF tables use pdfplumber only.
7. **No Hindi/Indic language support** — Regional tenders may fail.
8. **GitHub push blocked** — pack-objects hang; ~194 commits remain local.

---

## 12. What NOT to Do

1. **NEVER ask the user for next steps** — they get very angry. Just do the work.
2. **NEVER use synthetic/sample data** — all purged. Only real SWA RFQs.
3. **NEVER create parallel branches** — `phase8-clean-slate` is the ONE canonical branch.
4. **NEVER commit without `make verify`** — 97 tests must pass.
5. **NEVER modify gold files** — anti-cheat will catch this.
6. **NEVER break the 10 SWA RFQs** — these are sacred. Test every change against them.

---

## 13. Environment

- **Python:** 3.14.3 (charter pins 3.11–3.13; typer breaks on 3.14)
- **PyTorch:** 2.11
- **Transformers:** 5.8.1
- **pdfplumber:** 0.11.9
- **PyMuPDF (fitz):** 1.27.2.3
- **Streamlit:** 1.57.0
- **Virtual env:** `.venv/`

---

## 14. Honest Metrics — Single Source of Truth

Trust the JSON, not this narrative:

- `results/eval_honest.json` — entity-level (macro P/R/F1 across all 8 entity types)
- `results/eval_honest_rows.json` — row-level (material+quantity+unit matches against row gold)
- `results/FINAL_HONEST_REPORT.md` — human-readable narrative

If `results/eval_honest_rows.json` disagrees with this document, the JSON wins. Do not edit either file without re-running `scripts/eval_honest_rows.py`.

---

## 15. One-Paragraph Summary

> RFQ2BOQ converts construction tenders to BOQ. It works end-to-end; PDFs hit 100% capture-fidelity, but XLSX over/under-captures because of a multi-quantity-column ambiguity that SWA must resolve (1 row vs N per material). The honest path to accuracy is closed-catalog matching against the 19-item GeM catalog (`src/nlp/catalog_matcher.py` — not yet built), not open NER (which is ~14% on PDFs and data-limited). Do NOT claim "100% correct"; the real deliverable is 100% fidelity (capture+flag, never drop) plus catalog-match accuracy. Keep the anti-cheat harness; never grade the pipeline against itself. Remaining work: (1) fix XLSX exactly-once capture after SWA rule decision, (2) build catalog matcher + eval, (3) human-verify 9 insulation gold pairs, (4) finalize report.

---

*This document supersedes: HANDOFF_FOR_NEXT_AGENT.md, MASTER_HANDOFF.md, COMPLETE_PROJECT_HANDOFF.md, FINAL_ORCHESTRATION.md, PROJECT_MAP.md. If there's a conflict, the JSON in `results/` wins.*
