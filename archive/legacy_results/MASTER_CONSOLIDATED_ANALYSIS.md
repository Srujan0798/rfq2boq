# MASTER CONSOLIDATED ANALYSIS — RFQ2BOQ Project

> **Generated:** 2026-07-05  
> **Source:** 86 session exports + 65 handoff files + 9 merged batches + 9 Grok handoffs + 3 major merged handoffs + 50+ git commits  
> **Purpose:** Single source of truth for all session work, contradictions, and execution plan

---

## 1. EXECUTIVE SUMMARY

### 1.1 Project State (Honest Metrics)

| Metric | Current Value | Status |
|--------|--------------|--------|
| **Entity F1 (macro, all 10 SWA)** | **44.1%** | Baseline |
| **Entity F1 (XLSX only)** | **89.0%** | Production-ready |
| **Entity F1 (PDF only)** | **14.2%** | Data-limited |
| **Row F1 (macro, XLSX proxy)** | **~89%** | Production-ready |
| **Row F1 (insulation domain)** | **21.7%** | Needs work |
| **Sacred-10 count fidelity** | **100%** (195→223, capped) | Over-capture 114.4% |
| **Anti-cheat tests** | **27/27 PASSED** | Hardened |
| **`make verify`** | Passing (with caveats) | CI gate |

### 1.2 Key Finding: Recent Fixes Working

The **uncommitted changes** (July 5, 2026) show significant improvements:
- **02_isro**: Entity F1 improved from **75% → 100%** (removed spec paragraphs)
- **Spec paragraph filtering** added to `BOQAssembler` and `XLSXRowPipeline`
- **Compliance checklist rejection** added to `TableExtractor`
- **Section header filtering** added to main pipeline
-ingest pipeline

---

## 2. COMPLETE SESSION INVENTORY (All 86 Sessions)

### 2.1 By Batch

| Batch | Sessions | Date Range | Key Themes |
|-------|----------|------------|------------|
| **A** | 10 | Early | Code review, corpus manifest, training audit, sacred-10 fidelity, XLSX fidelity, handoff consolidation, catalog matcher, OpenRouter testing |
| **B** | 10 | Jun 27 | Orchestration, insulation tender timeouts, row-gold drafting, ontology/NER integration, honest row-level eval, structure-first routing |
| **C** | 10 | Jun 27-28 | Row-gold extraction, ontology IS-code commits, Adani PDF fix, merge audits, batch pipeline runs |
| **D** | 10 | Jun 28 | Lane A anti-cheat/baseline, Lane B gold annotation, Lane C structure-first R4, Lane D ontology mining, Lane E robustness/fidelity, project handoff |
| **E** | 10 | Jun 18 | Zydus non-zero qty fix, honest eval commit, Grew Solar phantom-space fix, repo hygiene (155 files), ISRO VSSC gold flag, unit-normalizer consolidation, new tenders, GeM catalog, formula-cell verification |
| **F** | 10 | Jun 18-25 | Data/gold exploration, pipeline code exploration, NW-06 repo hygiene, model-cheating concerns, trivial OK/HELLO sessions |
| **G** | 3 | Jun 5 | Training pipeline exploration, LoRA-vs-production plan, 10-week roadmap / clean-slate tasks |
| **Grok** | 9 | Jul 2-4 | R1 fidelity, XLSX fixes, annotation pipeline (NW04), NER retrain, resource visibility, orchestration |
| **Total** | **86** | | |

### 2.2 By Workstream (Lanes)

| Lane | Focus | Sessions | Status |
|------|-------|----------|--------|
| **A** | Anti-cheat, honest baseline, merge audit | 6 | ✅ DONE |
| **B** | Insulation row-gold drafting | 4 | ⚠️ 168 rows drafted, 0 human_verified |
| **C** | Structure-first / timeout fixes | 6 | ✅ DONE (7 files <60s, 0 rows = correct) |
| **D** | Ontology / NER / GeM | 5 | ⚠️ RUNNING (53 spec PDFs mining) |
| **E** | Pipeline robustness / fidelity | 4 | ⚠️ RUNNING (unit normalizer done) |
| **Orchestration** | Project review, dispatch | 3 | ⚠️ Incomplete |

---

## 3. CONTRADICTIONS & MISLEADING CLAIMS

### 3.1 Critical Contradictions (Must Resolve)

| # | Contradiction | Sources | Resolution Needed |
|---|---------------|---------|-------------------|
| **1** | **Lane B status**: BATCH B says B2 complete (commit `88e92a6`); BATCH D says Lane B ERROR/timeout needs restart | L2A §9.1 vs D dispatch | Verify `88e92a6` exists; check `insul_03`-`insul_09` files |
| **2** | **Lane C timeouts**: BATCH B says all 7 fixed (commit `3530731`); BATCH C says 7/11 still timeout; BATCH D adds timeout wrapper (`8f9e35e`) | L2A §9.2 | Progressive fixes - verify current state |
| **3** | **05_zydus_animal rows**: BATCH A = 48 extracted (over-capture); BATCH D = 20 extracted (matches gold) | L2A §9.4 | Different pipeline versions - verify current |
| **4** | **Row F1 claims**: `FINAL_COMPLETION_SUMMARY` = 92.1% macro (9/10 at 1.0); Lane C `COMPLETE_PROJECT_HANDOFF` = 100% on ALL 10; PHASE8 = 32.3% strict | CLAUDE_MERGED §6.4 | 100% claims are RED FLAGS - trust `eval_honest_rows.json` |
| **5** | **LoRA PID 6877**: `ses_0e92c1523ffe` claimed running; `ses_0d3ad2095ffe` confirmed DEAD (epoch 2, F1 0%) | L2A §9.5 | Audit is authoritative - training dead |
| **6** | **Fidelity metrics**: Sacred-10 audit = 100% count-level; `measure_fidelity.py` = 27.9% (0 PASS) | L2A §9.7 | Different metrics - audit caps at 100%; harness fails on over-capture |

### 3.2 Misleading Claims Identified

| Claim | Source | Reality |
|-------|--------|---------|
| "COMPLETE — Ready for Handover" | `FINAL_COMPLETION_SUMMARY.md` | PDF F1 14%, external blockers remain |
| "100% row-level F1 on all 10 SWA files" | Lane C `COMPLETE_PROJECT_HANDOFF.md` | **RED FLAG** - project history of fake-100% self-comparison; strict match = 32.3% |
| "LoRA training running, 13% done" | `ses_0e92c1523ffe` | **FALSE** - PID 6877 dead, training collapsed |
| "48 rows extracted for 05_zydus_animal" | BATCH A audit | Over-capture; pipeline fix in BATCH E reduced to 20 |
| "All 7 insulation timeouts fixed" | BATCH B | True for spec-only docs; BATCH C found more timeouts on other files |

### 3.3 Duplicate Work

| Work | Sessions | Notes |
|------|----------|-------|
| Lane C timeout fix | `ses_0fd7cbb45ffes`, `ses_0fdafb620ffe`, `ses_102530d7fffe`, `ses_110081fc7ffe` | Progressive fixes across batches |
| Lane B row-gold | `ses_102f4bcbcffe`, `ses_107a0f528ffe`, `ses_0fdafba93ffe` | Same task, multiple sessions |
| `data_only=True` verification | `ses_126941f4effer`, `ses_126959a48ffe` | Identical task, both verified no change needed |
| Insulation batch run | `ses_107a0bbecffel`, `ses_107a43ba2ffeu` | Same E6 deliverables |
| Lane A merge audit | `ses_102f4b503ffe`, `ses_107a0fadaffe`, `ses_107a4c164ffef` | Same audit, multiple sessions |

---

## 4. CURRENT UNCOMMITTED STATE (July 5, 2026)

### 4.1 Modified Files (9 files, 471 insertions, 170 deletions)

| File | Key Changes | Impact |
|------|-------------|--------|
| `src/domain/boq_assembler.py` | Added `_is_spec_paragraph()`, `_is_section_header()`, `_SPEC_KEYWORDS`, `_SECTION_HEADER_MARKERS`; filters in `assemble()` | **Major** - removes spec text from BOQ |
| `src/ingest/table_extractor.py` | Added `_looks_like_compliance_checklist()` to reject checklist tables | **Major** - prevents fake BOQ rows from compliance tables |
| `src/pipeline_xlsx.py` | Enhanced spec paragraph filtering (even with item numbers if >500 chars) | **Major** - fixes XLSX over-capture |
| `src/pipeline.py` | Added spec paragraph + section header filtering in post-processing | **Major** - unified filtering |
| `scripts/eval_honest_rows.py` | Exclude rate-only/zero-qty from FP count | **Evaluation fix** - valid business rule |
| `results/eval_honest.json` | Updated with improved metrics (02_isro 100%) | **Results** |
| `results/eval_honest_rows.json` | Updated row-level results | **Results** |

### 4.2 Impact on Metrics (Preliminary)

| File | Before | After | Change |
|------|--------|-------|--------|
| 01_gsecl | 100% | 100% | = |
| 02_isro | 75% | **100%** | **+25%** |
| 03_zydus_matoda | 84.8% | ~85% | ~ |
| 04_adani | 0% (entity) | TBD | ? |
| 05_zydus_animal | 93% | TBD | ? |
| 06_avante | 78% | TBD | ? |
| 07_grew | 61.5% | TBD | ? |

---

## 5. BLOCKERS (Owner-Only vs Technical)

### 5.1 Owner-Only Blockers (Cannot Fix by Code)

| # | Blocker | Why Agents Can't Fix |
|---|---------|---------------------|
| 1 | **Push ~200+ local commits** | Only on laptop; disk failure = total loss |
| 2 | **Rotate leaked GitHub token** | Remote URL has `x-access-token:gh...` |
| 3 | **Human-verify 9 insulation gold pairs** | `results/gold_spotcheck_report.md` ready; owner must flip `human_verified: true` |
| 4 | **Collect ~100 real PDFs** | NER stuck at 14% F1; only Sales/Jineth/Softnil can provide |
| 5 | **Rebuild venv (Python 3.11-3.13)** | Current env is 3.14; typer/click break on 3.14 |
| 6 | **Decide multi-qty business rule** | 1 material × 9 qty columns → 1 row or 9 rows? SWA must decide |

### 5.2 Technical Blockers (Can Fix)

| # | Blocker | Status | Fix |
|---|---------|--------|-----|
| 1 | Anti-cheat red flags in uncommitted code | **IN PROGRESS** | Silent swallowing, hardcoded confidences, fidelity self-ref |
| 2 | 05_zydus_animal over-capture / item_no validation | **FIXED** | Non-zero TOTAL filter committed |
| 3 | 04_adani quality (28/45 low-conf) | PENDING | Needs investigation |
| 4 | Contaminated checkpoints (v5, v2-v4, swa10) | PENDING | Quarantine + provenance cards |
| 5 | Lane D ontology mining (53 PDFs) | **RUNNING** | Wait for completion |
| 6 | Lane B gold annotation loop | **ERROR/Timeout** | Needs restart |
| 7 | `measure_fidelity.py` 04_adani doc_map bug | PENDING | Add missing PDF page |
| 8 | Corpus manifest not written | PENDING | Create `corpus_manifest.json` |

---

## 6. MASTER TIMELINE (Chronological)

### Phase 0: Foundation (Pre-June 2026)
- Project initialization, basic pipeline, synthetic data generation

### Phase 1: Sacred-10 & Corpus (Early June)
- `ses_0d3ad0628ffe`: Corpus manifest proposal (113 unique docs)
- `ses_0d3ad3857ffe`: Sacred-10 fidelity verification (100% count, 114.4% raw)
- `ses_0ed1b3fabffe`: `measure_fidelity.py` hardening (27.9% honest)

### Phase 2: Wave 2 Lane Work (June 27-28)
- **Lane A**: Anti-cheat hardening, honest baseline (`ses_11008f3a1ffe`)
- **Lane B**: 9 insulation row-gold files (168 rows) (`ses_0fdafba93ffe`)
- **Lane C**: Structure-first routing, 7 timeouts fixed (`ses_0fd7cbb45ffes`)
- **Lane D**: Insulation ontology + GeM gazetteer NER (`ses_0fdafb0abffe`)
- **Lane E**: Honest insulation eval (21.7% macro F1) (`ses_0fdafa71bffe`)

### Phase 3: Consolidation & Fixes (June 28 - July 4)
- Merge audits, Adani PDF fix, batch pipeline runs
- Grok sessions: R1 fidelity, XLSX fixes, annotation pipeline, NER retrain

### Phase 4: Recent Fixes (July 5, 2026)
- Spec paragraph filtering, compliance checklist rejection, section header filtering
- 02_isro entity F1: 75% → 100%
- Evaluation improvements for rate-only rows

### Phase 5: Current (July 5, 2026)
- Uncommitted changes ready for verification
- Need `make verify` + owner actions

---

## 7. EXECUTION PLAN — 10 SUB-AGENT WORKSTREAMS

### Workstream 1: Anti-Cheat & Code Quality (CRITICAL)
**Agent:** Code Quality Specialist  
**Files:** `src/pipeline.py`, `src/nlp/patterns/dictionary.py`, `scripts/fidelity_audit.py`  
**Tasks:**
1. Fix silent exception swallowing in `src/pipeline.py` (6 locations)
2. Fix silent exception swallowing in `src/nlp/patterns/dictionary.py:209-210`
3. Replace hardcoded confidence scores (0.80, 0.70) with calibrated values
4. Fix `fidelity_audit.py` self-reference to rowgold count
5. Run `make verify` until clean

### Workstream 2: Evaluation & Metrics Validation (CRITICAL)
**Agent:** Evaluation Engineer  
**Files:** `scripts/eval_honest.py`, `scripts/eval_honest_rows.py`, `scripts/measure_fidelity.py`  
**Tasks:**
1. Run full honest evaluation on all 10 SWA files
2. Fix `measure_fidelity.py` 04_adani doc_map (add missing PDF page)
3. Validate row-level metrics against `eval_honest_rows.json`
4. Update `results/fidelity_audit_summary.txt` with audited sacred-10 table
5. Document evaluation methodology

### Workstream 3: Gold Data & Human Verification (CRITICAL)
**Agent:** Data Curator  
**Files:** `data/real_rfqs/gold/rows/*.rowgold.json`, `results/gold_spotcheck_report.md`  
**Tasks:**
1. Human-review all 9 insulation gold pairs (168 entries)
2. Fix 02_isro_vssc gold (2 non-BOQ entries)
3. Fix 05_zydus_animal gold (67 entries all qty=0)
4. Flip `human_verified: true` where correct
5. Create provenance cards for all gold files

### Workstream 4: Model Quarantine & Training (HIGH)
**Agent:** ML Engineer  
**Files:** `models/`, `scripts/train_lora_ner_real_only.py`  
**Tasks:**
1. Create `models/quarantine/` directory
2. Move contaminated checkpoints: `rfq2boq-ner-lora-v5/`, v2, v3, v4, swa10
3. Add provenance cards documenting contamination
4. Do NOT restart training until ≥30 row-gold docs / ≥1000 verified sentences
5. Keep production NER pattern-based

### Workstream 5: Corpus Manifest & Data Organization (HIGH)
**Agent:** Data Engineer  
**Files:** `data/real_rfqs/`, `data/specifications/`, `data/incoming/`  
**Tasks:**
1. Create `data/real_rfqs/corpus_manifest.json` with proposed schema
2. Implement TEST/DEV/TRAIN/EXCLUDE splits per BATCH A proposal
3. Deduplicate by SHA-256 (100 duplicate filenames, 99 SHA groups)
4. Move synthetic archive to `attic/synthetic_corpus_archived/`
5. Restore reference PDFs to `data/real_rfqs/reference_real/`

### Workstream 6: PDF Extraction Improvements (HIGH)
**Agent:** PDF Extraction Specialist  
**Files:** `src/preproc/document_structure.py`, `src/ingest/pdf_extractor.py`, `src/ingest/table_extractor.py`  
**Tasks:**
1. Improve structure extractor precision (GSECL 1281→79 sections)
2. Fix 04_adani quality (28/45 low-confidence rows)
3. Fix 07_grew_solar (phantom-space fix verified)
4. Handle Avante-style docs (no BOQ heading) - SmartSectionClassifier fallback
5. Test on 100+ real PDFs when available

### Workstream 7: XLSX Pipeline & Business Rules (HIGH)
**Agent:** XLSX Specialist  
**Files:** `src/pipeline_xlsx.py`, `src/ingest/xlsx_parser.py`  
**Tasks:**
1. Validate non-zero TOTAL filter for 05_zydus_animal (20 rows ✅)
2. Implement multi-qty column business rule (await SWA decision)
3. Verify rate-only row handling consistency
4. Test `data_only=True` formula evaluation
5. Ensure fidelity tracking works correctly

### Workstream 8: NER & Ontology Enhancement (MEDIUM)
**Agent:** NLP Engineer  
**Files:** `src/nlp/patterns/`, `data/ontology/`, `src/nlp/catalog_matcher.py`  
**Tasks:**
1. Complete Lane D ontology mining (53 spec PDFs - RUNNING)
2. Expand GeM catalog with SWA's real submitted list
3. Add more insulation material patterns
4. Improve catalog matcher evaluation
5. Validate NER smoke test passes

### Workstream 9: Infrastructure & Deployment (MEDIUM)
**Agent:** DevOps Engineer  
**Files:** `Dockerfile`, `docker-compose.yml`, `deployment/`, `.venv`  
**Tasks:**
1. Rebuild `.venv` with Python 3.12
2. Fix Docker build (Python 3.11-slim + tesseract + poppler)
3. Rotate leaked GitHub token in remote URL
4. Push ~200+ local commits to origin
5. Verify CI/CD pipelines

### Workstream 10: Documentation & Handoff (MEDIUM)
**Agent:** Technical Writer  
**Files:** `docs/`, `HANDOFF.md`, `CLAUDE.md`, `AGENTS.md`, `README.md`  
**Tasks:**
1. Update all docs with current honest metrics
2. Fix dangling prompt links in `PHASE8_UNIFIED_TIMELINE_AND_FLOW.md`
3. Consolidate remaining handoff files
4. Update demo scripts and slides
5. Create final project summary

---

## 8. IMMEDIATE NEXT ACTIONS (Priority Order)

1. **NOW**: Run `make verify` on current uncommitted changes
2. **NOW**: Human-review insulation gold pairs (blocker for honest eval)
3. **TODAY**: Fix anti-cheat red flags in uncommitted code
4. **TODAY**: Run full honest evaluation on all 10 SWA files
5. **TODAY**: Quarantine contaminated model checkpoints
6. **THIS WEEK**: Rebuild venv with Python 3.12
7. **THIS WEEK**: Push commits + rotate GitHub token
8. **THIS WEEK**: Collect 100+ real PDFs from SWA contacts
9. **ONGOING**: Complete Lane D ontology mining
10. **ONGOING**: Restart Lane B gold annotation loop

---

## 9. VERIFICATION COMMANDS

```bash
# CI gate (tests + lint + anti-cheat + git-clean)
make verify

# Honest evaluations
python3 scripts/eval_honest.py          # entity-level
python3 scripts/eval_honest_rows.py     # row-level

# Fidelity measurement
PYTHONPATH=. .venv/bin/python scripts/measure_fidelity.py

# Quick smoke test
python3 -c "from src.nlp.pipeline import NLPPipeline; p=NLPPipeline(); r=p.process('Supply 500 kg cement as per IS 456 M20 grade at ground floor'); assert len(r.entities) > 0"

# Run UI / API
streamlit run ui/app.py
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

---

## 10. SOURCE-OF-TRUTH PRECEDENCE

1. `config/constants.py` — authoritative schema
2. `docs/conventions.md` — locked code rules
3. `docs/` — operational docs
4. `prompts/wave4/` — active agent prompts (`archive/` is read-only history)
5. Agent self-reports / handoff files — least trusted; always verify
6. **JSON evaluation outputs in `results/` win over any narrative**

---

*End of Master Consolidated Analysis. This document synthesizes 86 sessions, 65 handoffs, 9 merged batches, 9 Grok handoffs, 3 major merged handoffs, and 50+ git commits into a single actionable reference.*