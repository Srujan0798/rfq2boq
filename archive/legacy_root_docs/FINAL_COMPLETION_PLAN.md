# FINAL_COMPLETION_PLAN.md — RFQ2BOQ

> **Role:** Final orchestration subagent  
> **Workspace:** `/Users/srujansai/Desktop/rfq2boq`  
> **Branch:** `phase8-clean-slate`  
> **Base commit:** `0a91470`  
> **Date:** 2026-07-04  
> **Sources merged:** `ULTIMATE_HANDOFF.md` (OpenCode), `GROK_MERGED_HANDOFF.md` (Grok CLI), `CLAUDE_MERGED_HANDOFF.md` (Claude Code), `kleenhand.md` (current master state)  
>
> **Instruction:** This is the single final plan. Resolve contradictions honestly, prefer evidence over claims, and never cite unverified metrics as fact.

---

## Table of Contents

1. [§0. Current Honest State](#0-current-honest-state)
2. [§1. What Is Definitively Done](#1-what-is-definitively-done)
3. [§2. What Is Blocked / Owner-Gated](#2-what-is-blocked--owner-gated)
4. [§3. Immediate Next Actions (Next 24 Hours)](#3-immediate-next-actions-next-24-hours)
5. [§4. Short-Term Actions (Next Week)](#4-short-term-actions-next-week)
6. [§5. Final Completion Gates and Acceptance Criteria](#5-final-completion-gates-and-acceptance-criteria)
7. [§6. Parallel Agent Dispatch Plan](#6-parallel-agent-dispatch-plan)
8. [§7. Risks and Anti-Cheat Reminders](#7-risks-and-anti-cheat-reminders)
9. [§8. Final Deliverables Checklist](#8-final-deliverables-checklist)

---

## §0. Current Honest State

### §0.1 Honest metrics (no fake 100%s)

| Metric | Value | Evidence / Source |
|---|---|---|
| Entity-level F1 (macro, all 10 SWA) | **44.1%** | `AGENTS.md`, `ULTIMATE_HANDOFF.md` §1.2, `results/eval_honest.json` |
| Entity-level F1 (XLSX only, 4 files) | **89.0%** | `AGENTS.md`, `CLAUDE_MERGED_HANDOFF.md` §3.1 |
| Entity-level F1 (PDF only, 6 files) | **14.2%** | `AGENTS.md`, `CLAUDE_MERGED_HANDOFF.md` §3.1 |
| Row-level F1 (canonical strict independent match) | **~37.7%** | `AGENTS.md` §1; note `PHASE8_UNIFIED` reports 32.3% strict, `FINAL_COMPLETION_SUMMARY` claims 92.1% (see §0.2) |
| Sacred-10 count-level fidelity | **100% capped** (223 extracted vs 195 source = 114.4% raw over-capture) | `ULTIMATE_HANDOFF.md` §4.5, `kleenhand.md` §3.3 |
| Anti-cheat harness | **27/27 passed** in latest clean run | `ULTIMATE_HANDOFF.md` §10.1 (`ses_11008f3a1ffeT5D3nmQGeU5edh`) |
| ML NER v5 (synthetic val) | **0.755** | `AGENTS.md`, `CLAUDE_MERGED_HANDOFF.md` §3.3 |
| ML NER v5 (held-out real) | **0.188** | `AGENTS.md`, `CLAUDE_MERGED_HANDOFF.md` §3.3 |
| LoRA real-only training | **DEAD** at epoch 2.0, best F1 **1.46%**, final F1 **0.0%** | `kleenhand.md` §3.4, `ULTIMATE_HANDOFF.md` §4.6 |

**Bottom line:** XLSX extraction is production-ready. PDF extraction is data-limited, not code-limited. The production NER is pattern-based (regex + gazetteer). Any claim of 100% row-level F1 on all 10 SWA files is a red flag and must be verified against independent row-gold before being trusted.

### §0.2 Contradictions resolved

| Contradiction | Resolution |
|---|---|
| Row-level F1 reported as 92.1% vs 37.7% vs 32.3% | These are different methodologies. **37.7%** is the project canonical macro row-level F1 (`AGENTS.md`). **32.3%** is the strict independent material+qty+unit match (`PHASE8_UNIFIED`). **92.1%** is a looser matcher result from `results/eval_honest_rows.json` but relies on row-gold that includes broken/unverified files; cite it only with caveats. |
| LaneC claimed "100% row-level F1 on all 10 SWA files" | Treated as **red flag**. Project history includes fake-100% self-comparison incidents. Do not cite without independent verification. |
| `05_zydus_animal`: 20 source rows vs 48 extracted vs 67 gold entries | Source XLSX has 20 non-zero TOTAL rows; pipeline now emits **48 rows** (20 real + 28 rate-only/low-conf flagged); gold file has **67 entries all with `qty=0`** and is flagged unreliable. Count fidelity is capped at 100%, but quality/over-capture is real. |
| LoRA PID 6877 running vs dead | **Dead.** Later audit found PID 6877 not alive, training died at epoch 2. |
| `make verify` passes vs blocked | Tests/lint/anti-cheat reportedly pass, but the **clean-tree check fails** (`kleenhand.md` §3.1: 127 untracked/modified files). Therefore `make verify` is currently blocked at step 7. |
| `manifest.csv` 18 vs 19 SWA files | Reconcile by counting actual files; see §3 action 3. |
| `reference_real/` 154 restored PDFs vs planned small subset | Verify actual directory contents; see §3 action 4. |

### §0.3 Environment and git state

- **Branch:** `phase8-clean-slate` @ `0a91470`.
- **Working tree:** Dirty — 127 untracked/modified files per `kleenhand.md`.
- **Python:** System Python 3.14 is active; project requires **3.11–3.13** (`typer`/`click` break on 3.14).
- **Git remote:** Contains a leaked `x-access-token:gh…` token; **must be rotated** before any push.
- **Local commits:** ~200+ commits exist only on this laptop; loss risk is high.

---

## §1. What Is Definitively Done

Evidence-backed deliverables that do **not** depend on owner-only actions.

| # | Deliverable | Evidence | Verification Command |
|---|---|---|---|
| 1.1 | XLSX extraction pipeline is production-ready (89% entity F1) | `src/pipeline_xlsx.py`, `results/eval_honest.json` | `python3 scripts/eval_honest.py` |
| 1.2 | Structure-first PDF routing fixes insulation tender timeouts (no-BOQ docs exit fast) | Commit `3530731`, `tests/integration/test_insulation_tender_timeouts.py` | `pytest tests/integration/test_insulation_tender_timeouts.py -q` |
| 1.3 | PDF timeout wrapper + structure extractor precision improvements | Commit `8f9e35e`, `src/preproc/document_structure.py` | `pytest tests/integration/test_real_rfq_corpus.py tests/integration/test_self_attack.py -q` |
| 1.4 | Unified unit normalizer in `src/rules/units.py` | Commit `b81b440`, 59 new tests | `pytest tests/unit/test_units_canonical.py -q` |
| 1.5 | Catalog matcher built and tested | `src/nlp/catalog_matcher.py`, 39 tests | `pytest tests/unit/test_catalog_matcher.py -q` |
| 1.6 | GeM product gazetteer integrated into NER | `src/nlp/patterns/gem_catalog.py`, commit `0739ecf` | `pytest tests/unit/test_gem_catalog.py tests/unit/test_patterns.py -q` |
| 1.7 | Insulation ontology JSON files + gazetteer patterns | `data/ontology/insulation_*.json`, commit `b38db2c` | `pytest tests/unit/test_ontology_loader.py -q` |
| 1.8 | Anti-cheat harness hardened (27/27 passed when tree clean) | `tests/unit/test_anti_cheat.py` | `pytest tests/unit/test_anti_cheat.py tests/integration/test_self_attack.py -q` |
| 1.9 | Annotation intake/review pipeline leakage-guarded | `scripts/intake_tender.py`, `scripts/review_annotation.py`, `scripts/convert_to_bioes.py` | `pytest tests/unit/test_intake.py tests/unit/test_review.py tests/unit/test_convert_to_bioes.py -q` |
| 1.10 | 9 insulation row-gold drafts created (168 rows) | `data/real_rfqs/gold/rows/insul_01_*.rowgold.json` … `insul_09_*.rowgold.json` | `python3 scripts/gold_spotcheck_report.py` |
| 1.11 | Reference PDFs restored + manifest rebuilt | Commit `fix(nw06): restore reference PDFs…`, 155 files | `ls data/real_rfqs/reference_real/ && wc -l data/real_rfqs/swa_enquiries/manifest.csv` |
| 1.12 | `data_only=True` verified for formula-cell XLSX loads | `src/pipeline_xlsx.py:56`, `src/ingest/xlsx_parser.py:31` | `grep -n "data_only=True" src/pipeline_xlsx.py src/ingest/xlsx_parser.py` |
| 1.13 | Phantom-space fix for Grew Solar PDF tables | Commit `c923e2a`, `src/ingest/table_extractor.py` | `pytest tests/integration/test_real_rfq_corpus.py -q` |
| 1.14 | Zydus Animal non-zero TOTAL filtering implemented | Pipeline extracts 20 non-zero TOTAL rows | `python3 scripts/fidelity_audit.py --enquiry 05_zydus_animal --save` |
| 1.15 | `HANDOFF.md` consolidated; old handoffs moved to `attic/` | Commit from `ses_0ed1e144effe19989GAriuUQdy` | `ls attic/ && wc -l HANDOFF.md` |
| 1.16 | `kleenhand.md` created as unified master handoff | `kleenhand.md` | `head -5 kleenhand.md` |
| 1.17 | OpenCode session artifact audit completed | 63 non-empty sessions merged into `ULTIMATE_HANDOFF.md` | `ls -la .session_merged/ .session_exports/ .session_handoffs/` |
| 1.18 | Grok + Claude handoffs merged | `GROK_MERGED_HANDOFF.md`, `CLAUDE_MERGED_HANDOFF.md` | `wc -l GROK_MERGED_HANDOFF.md CLAUDE_MERGED_HANDOFF.md` |

---

## §2. What Is Blocked / Owner-Gated

These cannot be closed by code alone. They require a human decision, external data, or infrastructure action by **Srujan**.

| # | Blocker | Why It Blocks Completion | Owner | Verification Command |
|---|---|---|---|---|
| 2.1 | **Git commit/push approval** | 127 untracked/modified files; `make verify` fails clean-tree check | Srujan | `git status --short \| wc -l` |
| 2.2 | **Rotate leaked GitHub token** | Remote URL contains `x-access-token:gh…`; security risk before push | Srujan | `git remote -v` |
| 2.3 | **Rebuild Python environment (3.14 → 3.11–3.13)** | System Python 3.14 breaks `typer`/`click`; tests may segfault | Srujan | `python3 --version` |
| 2.4 | **Human-verify 9 insulation row-gold pairs** | All 168 entries are draft (`human_verified: false`) | Srujan | `python3 scripts/gold_spotcheck_report.py` |
| 2.5 | **Fix `05_zydus_animal_pharmez` gold** | 67 gold entries all have `qty=0`; gold is unreliable | Sruhan | `python3 scripts/gold_spotcheck_report.py --enquiry 05_zydus_animal_pharmez` |
| 2.6 | **Decide multi-quantity-column business rule** | One material with N qty columns → 1 row or N rows? Blocks exact XLSX fidelity | SWA / Srujan | Review `src/pipeline_xlsx.py` output on `03_zydus_matoda` and `08_sael` |
| 2.7 | **Collect ~100 real PDFs for NER training** | PDF entity F1 14.2% cannot improve without real annotated data | SWA Sales / Jineth / Softnil | `ls data/real_rfqs/additional_real/ \| wc -l` |
| 2.8 | **Human-verify 09/10 GeM gold files** | Gold needs sign-off; do not demo 09/10 live | Srujan | `cat data/real_rfqs/gold/rows/09_gem_bid_7439924.rowgold.json` |
| 2.9 | **SWA real GeM product list** | Replace hand-built 60-product gazetteer with actual submitted catalog | Srujan / SWA | Compare `data/real_rfqs/swa_gem_catalog_full.json` to SWA export |
| 2.10 | **Clean retrain dataset ≥1,000 verified sentences / ≥30 row-gold docs** | LoRA died at epoch 2 due to only ~39 real docs | Srujan / SWA | `find data/annotations/verified/ -name "*.json" \| wc -l` |
| 2.11 | **Owner approval to quarantine contaminated models** | `models/rfq2boq-ner-lora-v5/` trained on pseudo-labels; v2/v3/v4 un-audited | Srujan | `ls models/` |
| 2.12 | **Extract / dedupe `resources/Specifications.rar`** | 25 MB RAR v5 archive with 11+ spec PDFs; intake pipeline ready but content not ingested | Srujan / agent | `ls resources/Specifications/ && unar -l resources/Specifications.rar` |

---

## §3. Immediate Next Actions (Next 24 Hours)

Do these in order. Each item has an owner and a verification command.

| # | Action | Owner | Verification Command |
|---|---|---|---|
| 3.1 | **Reconcile git state.** Run `git status` and produce a clean, categorized list of modified/untracked files. | Orchestrator | `git status --short` |
| 3.2 | **Run forbidden anti-cheat checks.** Search for filename hacks, special cases, fake claims, and test failures. | Orchestrator | `grep -r "if filename ==" src/; grep -r "_sael_scan" src/; grep -r "100% COMPLETE" docs/; pytest tests/ -q` |
| 3.3 | **Fix silent exception swallowing** in `src/pipeline.py` and `src/nlp/patterns/dictionary.py:209-210`. Replace `except Exception: pass` with proper logging or raises. | Agent (Lane A) | `grep -n "except.*pass" src/pipeline.py src/nlp/patterns/dictionary.py` |
| 3.4 | **Remove hardcoded confidence scores** (`confidence=0.80` for recovered GeM rows, `confidence=0.70` for rate-only rows). Route through `config.settings` thresholds. | Agent (Lane A) | `grep -n "confidence=0\." src/pipeline.py src/pipeline_xlsx.py` |
| 3.5 | **Fix `scripts/fidelity_audit.py` self-reference.** Ensure source-vs-output check remains independent even when row-gold exists. | Agent (Lane A) | `python3 scripts/fidelity_audit.py --enquiry 03_zydus_matoda --save` |
| 3.6 | **Re-run `make verify`.** Confirm all steps except clean-tree pass. | Orchestrator | `make verify` |
| 3.7 | **Re-run honest evaluations from scratch** (not from backup). | Orchestrator | `/usr/local/bin/python3.11 scripts/eval_honest.py` and `/usr/local/bin/python3.11 scripts/eval_honest_rows.py` |
| 3.8 | **Verify `05_zydus_animal` current state**: source rows, extracted rows, rate-only flags, gold entries. | Orchestrator | `python3 scripts/fidelity_audit.py --enquiry 05_zydus_animal --save; python3 scripts/gold_spotcheck_report.py --enquiry 05_zydus_animal_pharmez` |
| 3.9 | **Count `manifest.csv` rows vs actual SWA enquiry folders** and reconcile 18 vs 19 discrepancy. | Orchestrator | `wc -l data/real_rfqs/swa_enquiries/manifest.csv; ls data/real_rfqs/swa_enquiries/` |
| 3.10 | **Verify `reference_real/` scope**: list files and confirm none are synthetic. | Orchestrator | `ls data/real_rfqs/reference_real/ \| wc -l; head data/real_rfqs/reference_real/README.md` |
| 3.11 | **Investigate `03_zydus_matoda` anti-cheat risk** (`human_verified=True` + 100% match). Determine if leakage/hack exists. | Agent (Lane A) | `pytest tests/unit/test_anti_cheat.py -q; git log --oneline data/real_rfqs/gold/rows/03_zydus_matoda.rowgold.json` |
| 3.12 | **Srujan decision: approve commit** of the 30 tracked source/ontology/script/test fixes plus `kleenhand.md`. | Srujan | `git diff --stat` |

---

## §4. Short-Term Actions (Next Week)

| # | Action | Owner | Verification Command |
|---|---|---|---|
| 4.1 | **Commit approved changes** from §3 and push only after token rotation. | Orchestrator (after Srujan approval) | `git log --oneline -5 && git status` |
| 4.2 | **Rotate GitHub token** and update remote URL. | Srujan | `git remote -v` |
| 4.3 | **Rebuild venv** with Python 3.11 or 3.12 and reinstall project. | Srujan / Orchestrator | `python3 --version; pip install -e ".[dev]"; python -m spacy download en_core_web_sm` |
| 4.4 | **Create `data/real_rfqs/corpus_manifest.json`** with SHA256, source, client, type, and frozen TEST/DEV/TRAIN splits. Sacred 10 always TEST. | Agent (Lane B) | `cat data/real_rfqs/corpus_manifest.json` |
| 4.5 | **Extract / dedupe `resources/Specifications.rar`** and add real spec PDFs to corpus manifest (TEST split if they are client specs). | Agent (Lane B) | `ls resources/Specifications/; sha256sum resources/Specifications/*.pdf > /tmp/spec_sha256.txt` |
| 4.6 | **Quarantine contaminated checkpoints**: move `models/rfq2boq-ner-lora-v5/` and legacy v2/v3/v4 to `models/quarantine/` with provenance cards. | Agent (Lane B) after Srujan approval | `ls models/quarantine/; cat models/quarantine/README.md` |
| 4.7 | **Fix `measure_fidelity.py` `doc_map` for `04_adani`** to include both PDF pages. | Agent (Lane C) | `python3 scripts/measure_fidelity.py --enquiry 04_adani` |
| 4.8 | **Improve `04_adani` quality** (28/45 rows low-confidence). Add targeted tests; do not hardcode. | Agent (Lane C) | `pytest tests/integration/test_adani_structure.py -q` |
| 4.9 | **Run human review loop** on the ~77 non-SWA drafts using `scripts/review_annotation.py`. Promote approved to `data/annotations/verified/`. | Srujan (agent can prep UI/script) | `find data/annotations/verified/ -name "*.json" \| wc -l` |
| 4.10 | **Fix `05_zydus_animal` rowgold** by re-transcribing from source XLSX. | Srujan / agent (agent extracts, Srujan verifies) | `python3 scripts/gold_spotcheck_report.py --enquiry 05_zydus_animal_pharmez` |
| 4.11 | **Update `results/fidelity_audit_summary.txt`** with audited per-document numbers plus over-capture notes. | Agent (Lane A) | `cat results/fidelity_audit_summary.txt` |
| 4.12 | **Resolve Lane B timeout status** and confirm `insul_03`–`insul_09` rowgold files are present and committed. | Agent (Lane B) | `git log --oneline --all --grep="88e92a6"; ls data/real_rfqs/gold/rows/insul_*.rowgold.json` |
| 4.13 | **Fix `02_isro_vssc` gold issue**: either remove 2 zero-qty entries or confirm they are valid. | Srujan | `python3 scripts/fidelity_audit.py --enquiry 02_isro --save` |

---

## §5. Final Completion Gates and Acceptance Criteria

A gate is **CLOSED** only with reproducible evidence (date, command, stdout excerpt, commit hash). Agents mark **READY FOR VERIFICATION**; only the orchestrator/owner marks **CLOSED**.

### Gate 0 — Standing Anti-Cheat (re-run before every close)

- [ ] `make verify` passes including clean-tree check.
- [ ] `tests/unit/test_anti_cheat.py` + `tests/integration/test_self_attack.py` pass.
- [ ] No filename hacks, no gold edits to match output, no threshold gaming.
- [ ] Fresh-document smoke test: a PDF never in the repo produces plausible output.

**Verification:** `make verify && pytest tests/unit/test_anti_cheat.py tests/integration/test_self_attack.py -q`

### Gate 1 — Corpus Manifest + Frozen Split

- [ ] `data/real_rfqs/corpus_manifest.json` exists with SHA256, source, client, type.
- [ ] `resources/Specifications.rar` extracted and deduped by checksum.
- [ ] Frozen split: TEST (sacred 10 + ~5 fresh spec docs), DEV (~15), TRAIN (rest).
- [ ] TEST docs are not mined into gazetteer/training/silver.

**Verification:** `python3 -c "import json; m=json.load(open('data/real_rfqs/corpus_manifest.json')); print('TEST',len(m['test']),'DEV',len(m['dev']),'TRAIN',len(m['train']))"`

### Gate 2 — Human-Verified Gold Factory

- [ ] ≥1,000 verified sentences.
- [ ] ≥30 verified row-gold docs.
- [ ] Approved drafts promoted to `data/annotations/verified/` with `human_verified: true`.

**Verification:** `find data/annotations/verified/ -name "*.json" | wc -l` and token/entity count script.

### Gate 3 — Clean Retrain (Human Labels Only)

- [ ] `scripts/train_lora_ner_real_only.py` loads only verified + original gold (no silver/pseudo).
- [ ] Legacy contaminated checkpoints quarantined.
- [ ] New training run finishes and beats pattern-based baseline on held-out real data.

**Verification:** `python3 scripts/train_lora_ner_real_only.py && python3 scripts/eval_honest.py`

### Gate 4 — Frozen One-Shot Evaluation

- [ ] Full pipeline run on TEST split once.
- [ ] Per-doc entity F1, row fidelity, catalog accuracy reported to `results/`.
- [ ] Includes one document never seen by the repo.

**Verification:** `ls results/eval_honest_*.json && cat results/FINAL_HONEST_REPORT.md`

### Gate 5 — Per-Document Fidelity Sweep (R1)

- [ ] `python3 scripts/fidelity_audit.py --enquiry X --save` for every BOQ-bearing doc.
- [ ] Per-doc PASS = `captured + flagged == source AND dropped == 0 AND over_capture == 0`.
- [ ] Any FAIL fixed honestly; no aggregate netting.

**Verification:** `cat results/fidelity_audit_summary.txt`

### Gate 6 — Regression + Combination Suite

- [ ] `tests/regression/test_corpus_exact.py`: every verified doc → exact verified BOQ.
- [ ] `tests/regression/test_combinations.py`: random subsets/bundles/orderings → union invariance.
- [ ] Wired into `make verify`.

**Verification:** `pytest tests/regression/ -q`

### Gate 7 — Ship

- [ ] `deliverables/FINAL_HONEST_REPORT.md`, `EXECUTIVE_SUMMARY.md`, `HANDOFF.md` updated with real Gate 4/5/6 numbers.
- [ ] UI/CLI/API/Docker smoke-tested.
- [ ] Commits pushed with rotated token.
- [ ] Real SWA GeM export obtained.

**Verification:** `make verify; docker-compose up --build -d; curl http://localhost:8000/v1/health`

---

## §6. Parallel Agent Dispatch Plan

Use short-lived lane branches or isolated worktrees. **One agent per worktree; no parallel writes to the canonical tree.**

| Lane | Agent Role | Task | Inputs | Outputs | Dependencies |
|---|---|---|---|---|---|
| **Lane A — Anti-Cheat / Quality** | Code agent | Fix red flags: silent exceptions, hardcoded confidences, fidelity audit self-reference, 03_zydus leakage investigation. | `src/pipeline.py`, `src/pipeline_xlsx.py`, `src/nlp/patterns/dictionary.py`, `scripts/fidelity_audit.py` | Clean source + passing `make verify` | §3.1–3.3, 3.11 |
| **Lane B — Data / Corpus** | Data agent | Build `corpus_manifest.json`, extract `Specifications.rar`, reconcile `manifest.csv`, verify `reference_real/`, confirm insulation rowgold presence. | `data/real_rfqs/`, `resources/Specifications.rar` | `data/real_rfqs/corpus_manifest.json`, updated manifest | §3.9–3.10, 4.4–4.5, 4.12 |
| **Lane C — PDF / Structure** | Code agent | Fix `measure_fidelity.py` Adani `doc_map`, improve Adani low-confidence rows, harden structure extractor false positives. | `src/ingest/table_extractor.py`, `src/preproc/document_structure.py`, `scripts/measure_fidelity.py` | Passing Adani tests, improved PDF F1 | §4.7–4.8 |
| **Lane D — Ontology / Gazetteer** | Data agent | Complete spec-PDF ontology mining, clean gazetteer, ensure TEST leakage guard. | `resources/Specifications/*.pdf`, `data/ontology/` | Updated ontology JSONs | Gate 1 closed |
| **Lane E — Annotation Loop** | Human + agent | Run `scripts/review_annotation.py` on drafts; Srujan approves/corrects; agent promotes verified files. | `data/annotations/draft/*.json` | `data/annotations/verified/*.json` | Gate 2 |
| **Lane F — Training** | ML agent | Prepare clean train config; do **not** start training until Gate 2 supplies ≥30 docs / ≥1,000 sentences. | `data/annotations/verified/`, `data/real_rfqs/annotations/gold_annotations.json` | Quarantined old models, training run | Gate 2 closed |
| **Lane G — Deliverables** | Docs agent | Update `HANDOFF.md`, `deliverables/FINAL_HONEST_REPORT.md`, `EXECUTIVE_SUMMARY.md` with real numbers. | Gate 4/5/6 outputs | Final reports | Gates 4–6 closed |

**Dispatch order:**
1. Start **Lane A** immediately (§3 red flags).
2. Start **Lane B** in parallel with Lane A (no file collisions).
3. Once Lane A closes, run `make verify` and merge.
4. Start **Lane C** and **Lane D** after Gate 1.
5. **Lane E** is owner-paced; agent only provides tooling.
6. **Lane F** waits for Gate 2.
7. **Lane G** waits for Gates 4–6.

---

## §7. Risks and Anti-Cheat Reminders

### §7.1 Active risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `03_zydus_matoda` anti-cheat failure | Medium | High | Investigate before claiming any 100% match; verify gold provenance. |
| Uncommitted code with silent exceptions / hardcoded scores gets committed | High | High | Fix in §3 before any commit; re-run forbidden checks. |
| Dirty tree blocks `make verify` indefinitely | High | Medium | Srujan must approve commit; rotate token; push. |
| ~200 local commits lost due to disk failure | High | High | Push to remote after token rotation. |
| Python 3.14 segfaults during demo/training | High | High | Rebuild venv to 3.11/3.12 before any public demo. |
| Insulation rowgold drafts treated as verified | Medium | High | All 168 entries remain `human_verified: false` until Srujan reviews. |
| Contaminated LoRA v5 checkpoint accidentally used | Medium | High | Quarantine `models/rfq2boq-ner-lora-v5/` and v2/v3/v4 before any retrain. |
| Fake 100% metrics cited in deliverables | Medium | High | Use only independent metrics; flag the LaneC 100% row-F1 claim as unverified. |
| TEST docs leak into training/gazetteer | Medium | High | Enforce `_is_swa_sacred()` and manifest split; audit after every ontology change. |

### §7.2 Anti-cheat reminders (non-negotiable)

1. **Never grade the pipeline against gold the pipeline produced.**
2. **Gold must be independent + human-verified.**
3. **A sudden ~100% / perfect score is a red flag — investigate, don't celebrate.**
4. **Never modify gold files to match pipeline output.**
5. **No threshold-lowering, no `if filename ==` hacks, no hardcoded scores.**
6. **Schema is locked:** 8 entities, 6 relations, BIOES.
7. **One agent at a time on the canonical tree; finish → verify → commit → next.**
8. **`make verify` must pass before claiming completion.**
9. **Machine labels (silver/pseudo/auto) never enter training.**
10. **Fidelity is per-document; no netting over-capture against drops.**

### §7.3 Forbidden checks (run before every gate close)

```bash
grep -r "if filename ==" src/
grep -r "_sael_scan" src/
grep -r "100% COMPLETE" docs/
git status | grep -v "clean"
pytest tests/ -q
```

---

## §8. Final Deliverables Checklist

At true project completion, the following must exist and be verified:

- [ ] `FINAL_COMPLETION_PLAN.md` (this file) — completed and read.
- [ ] `data/real_rfqs/corpus_manifest.json` — frozen TEST/DEV/TRAIN split.
- [ ] `results/eval_honest.json` — entity-level macro P/R/F1 on TEST split.
- [ ] `results/eval_honest_rows.json` — row-level macro P/R/F1 on TEST split.
- [ ] `results/fidelity_audit_summary.txt` — per-document R1 fidelity, no over-capture.
- [ ] `models/quarantine/` — contaminated/un-audited checkpoints moved with provenance cards.
- [ ] `data/annotations/verified/` — ≥30 verified row-gold docs / ≥1,000 verified sentences.
- [ ] `data/real_rfqs/gold/rows/05_zydus_animal_pharmez.rowgold.json` — re-transcribed and `human_verified: true`.
- [ ] `deliverables/FINAL_HONEST_REPORT.md` — updated with real Gate 4/5/6 numbers.
- [ ] `deliverables/EXECUTIVE_SUMMARY.md` — updated.
- [ ] `HANDOFF.md` — updated.
- [ ] All commits pushed to remote with rotated token.
- [ ] Docker/UI/API smoke-tested.
- [ ] `make verify` passes clean.

---

*End of FINAL_COMPLETION_PLAN.md. This plan resolves contradictions honestly and treats unverified 100% claims as red flags. If any `results/*.json` conflicts with this document, the JSON wins until the conflict is resolved.*
