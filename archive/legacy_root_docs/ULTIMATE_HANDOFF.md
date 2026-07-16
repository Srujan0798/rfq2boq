# ULTIMATE_HANDOFF — RFQ2BOQ Project Final Merge

> **Role:** Level-3 final handoff-merge subagent  
> **Workspace:** `/Users/srujansai/Desktop/rfq2boq`  
> **Generated:** 2026-07-04  
> **Source Level-2 merges:**
> - `.session_merged/merged_L2A.md` (Batches A–D, 40 sessions)
> - `.session_merged/merged_L2B.md` (Batches E–G, 23 sessions)
>
> **Scope:** This is the FINAL merge. It preserves every session ID, deliverable, commit hash, file touched, blocker, contradiction, and metric from all 63 non-empty OpenCode sessions. No source files, gold data, or git state were modified by this merge.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Intent and Scope Guard](#2-project-intent-and-scope-guard)
3. [Complete Session Inventory](#3-complete-session-inventory)
4. [Work by Theme](#4-work-by-theme)
5. [Complete File Manifest](#5-complete-file-manifest)
6. [Commit Registry](#6-commit-registry)
7. [Contradictions and Duplicate Work](#7-contradictions-and-duplicate-work)
8. [Blockers and Running Processes](#8-blockers-and-running-processes)
9. [Uncommitted State](#9-uncommitted-state)
10. [Anti-Cheat Status](#10-anti-cheat-status)
11. [Next Actions](#11-next-actions)
12. [Appendix: Raw Session Index](#12-appendix-raw-session-index)

---

## 1. Executive Summary

This document is the ultimate handoff for the RFQ2BOQ project at `/Users/srujansai/Desktop/rfq2boq`. It merges and preserves all material from 63 non-empty OpenCode sessions across seven Level-1 batches (A–G), which were previously merged into two Level-2 documents (`merged_L2A.md` and `merged_L2B.md`).

### 1.1 Session and scale summary

| Level-1 batch | Sessions | Main models | Key themes |
|---|---|---|---|
| A | 10 | kimi-k2.7-code, mimo-v2.5-free, big-pickle, nemotron-3-ultra-free | Code review, corpus manifest, training audit, sacred-10 fidelity, XLSX fidelity, handoff consolidation, catalog matcher, OpenRouter testing |
| B | 10 | nemotron-3-ultra-free, MiniMax-M2.7, MiniMax-M2.5, MiniMax-M3 | Orchestration, insulation tender timeouts, row-gold drafting, ontology/NER integration, honest row-level eval, structure-first routing |
| C | 10 | MiniMax-M2.7, MiniMax-M3, MiniMax-M2.5, MiniMax-M2.5-highspeed, mimo-v2.5-pro | Row-gold extraction, ontology IS-code commits, Adani PDF fix, merge audits, batch pipeline runs |
| D | 10 | MiniMax-M2.5, MiniMax-M3, MiniMax-M2.7, deepseek-v4-flash-free, north-mini-code-free, big-pickle, mimo-v2.5-pro | Lane A anti-cheat/baseline, Lane B gold annotation loop, Lane C structure-first R4, Lane D ontology mining, Lane E robustness/fidelity, project handoff |
| E | 10 | nemotron-3-ultra-free, big-pickle, north-mini-code-free, deepseek-v4-flash-free | Zydus non-zero qty fix, honest eval commit, Grew Solar phantom-space fix, repo hygiene (155 files), ISRO VSSC gold flag, unit-normalizer consolidation, new tenders, GeM catalog, formula-cell verification |
| F | 10 | mimo-v2.5-free, MiniMax-M3 | Data/gold exploration, pipeline code exploration, NW-06 repo hygiene, model-cheating concerns, trivial OK/HELLO sessions |
| G | 3 | mimo-v2.5-free, nemotron-3-ultra-free | Training pipeline exploration, LoRA-vs-production plan, 10-week roadmap / clean-slate tasks |
| **Total** | **63** | — | — |

### 1.2 Honest project metrics (preserved from source handoffs)

| Metric | Value | Source |
|---|---|---|
| Entity-level F1 (macro, all 10 SWA) | **44.1%** | L2A `ses_11008f3a1ffeT5D3nmQGeU5edh`, L2A `ses_10252f5f6ffe22OwrDdIVrwya2` |
| Entity-level F1 (XLSX only) | **89.0%** | L2A (production-ready) |
| Entity-level F1 (PDF only) | **14.2%** | L2A (data-limited) |
| Row-level F1 (macro, SWA XLSX proxy) | **~92.1%** (micro F1 86.5%, macro F1 92.1%) | L2B BATCH_E `ses_1264a228effekBULGv67DcUhb8` |
| Row-level F1 (insulation domain, draft gold) | **21.7%** macro | L2A BATCH_B `ses_0fdafa71bffecXT75Te9NUysHE` |
| Sacred-10 count-level fidelity | **100%** (223 extracted vs 195 source, capped at 100%; raw over-capture 114.4%) | L2A BATCH_A `ses_0d3ad3857ffe5L8gKTNFjz04Uw` |
| Anti-cheat tests | **27/27 PASSED** | L2A BATCH_D `ses_11008f3a1ffeT5D3nmQGeU5edh` |
| `make verify` | Reported passing in multiple sessions, but contradictions exist with uncommitted red-flag code | L2A, L2B BATCH_F |

### 1.3 Current project state

**Code side:** The XLSX extraction pipeline is production-ready. Key recent fixes include non-zero TOTAL filtering for Zydus Animal Pharmez, phantom-space handling for Grew Solar PDF tables, unified unit normalization in `src/rules/units.py`, GeM catalog ingestion, and honest row-level evaluation. The anti-cheat harness is hardened and the critical test suite passes when the tree is clean.

**Data side:** PDF extraction remains severely data-limited (14.2% entity F1). The production NER is pattern-based (regex + gazetteer). LoRA training attempts have collapsed due to insufficient real annotated data. Nine insulation row-gold pairs (168 entries) are drafted but all are `human_verified: false`.

**Owner-only blockers:** Pushing ~200+ local-only commits, rotating a leaked GitHub token, human-verifying gold, providing ~100 real PDFs for training, deciding multi-qty business rules, and rebuilding the Python environment (currently 3.14, project requires 3.11–3.13).

### 1.4 Major risks

1. **Contradictory session reports** on Lane B status, Lane C timeout counts, and `05_zydus_animal` row counts must be reconciled before further work.
2. **Uncommitted code contains red flags**: silent exception swallowing, hardcoded confidence scores, and a self-referencing fidelity audit script.
3. **Training data contamination**: `models/rfq2boq-ner-lora-v5/` was trained on pseudo-labeled data and should be quarantined.
4. **Anti-cheat will likely FAIL on `03_zydus_matoda`** because it is the only file with `human_verified=True` and now reports 100% match.

---

## 2. Project Intent and Scope Guard

### 2.1 What RFQ2BOQ is

RFQ2BOQ transforms unstructured construction RFQ (Request for Quotation) tender documents into structured Bill of Quantities (BOQ) data using NLP. It is a Python-based system with a hybrid ML + rules architecture.

**Current honest metrics (from project docs and evaluations):**
- Entity-level F1 (macro): 44.1%
- Row-level F1 (macro): 37.7%
- XLSX extraction (entity): 89.0% macro F1 — production-ready
- PDF extraction (entity): 14.2% macro F1 — data-limited

**Production NER:** Pattern-based (regex + gazetteer) — more reliable than the ML model on real docs.
**ML NER v5:** Val F1=0.755, but only 0.188 on held-out real docs (overfit to synthetic).

**Bottom line from project docs:** XLSX extraction is production-ready. PDF extraction needs real human-annotated training data, not code fixes.

### 2.2 Locked conventions (non-negotiable)

- **Import root:** Use `src.` for all production imports. Do NOT use `code.`.
- **Entity types (8):** `MATERIAL`, `QUANTITY`, `UNIT`, `LOCATION`, `DIMENSION`, `STANDARD`, `ACTION`, `GRADE`.
- **Relation types (6):** `HAS_QUANTITY`, `HAS_UNIT`, `AT_LOCATION`, `OF_GRADE`, `COMPLIES_WITH`, `HAS_DIMENSION`.
- **Tagging scheme:** BIOES (not BIO).
- **Settings:** All configuration flows through `config.settings.settings` with env prefix `RFQ2BOQ_`.
- **Type hints:** Required on all new code; public APIs must have type hints.
- **Logging:** Never log PII or full document text at `INFO`+.
- **API versioning:** New endpoints under `/v1/...`.

### 2.3 Scope guard — what NOT to build

- No backwards-compatibility shims for code that hasn't shipped yet.
- No dead code or commented-out blocks.
- No speculative features.
- No mock data in production code paths.
- No silent exception swallowing (`except: pass`).
- No `assert` for production validation.
- No Python 3.14 support (typer/click break).
- No multi-language support yet (English only).
- No camelot-py for PDF tables (pdfplumber only).
- Do not add synthetic files to `data/real_rfqs/swa_enquiries/` (the 10 sacred SWA files).

### 2.4 The 10 sacred SWA files

Located in `data/real_rfqs/swa_enquiries/`:
1. `01_gsecl`
2. `02_isro_vssc`
3. `03_zydus_matoda`
4. `04_adani`
5. `05_zydus_animal_pharmez`
6. `06_avante`
7. `07_grew_solar_narmadapuram`
8. `08_sael`
9. `09_gem_bid_7439924`
10. `10_gem_bid_7552777`

These are the only real documents that matter for validation. Any change that affects their extraction or gold must be scrutinized by anti-cheat checks.

---

## 3. Complete Session Inventory

This section preserves every non-empty OpenCode session across all batches. Session IDs, titles, token counts, models, agents, worktrees, messages, files touched, commits, and outcomes are recorded exactly as found in the Level-2 merges.

> **Note on file-touch counts:** Many sessions report `Files Touched = 0` because tool-call tracking was not configured in the originating agent runs. Actual file modifications are reconstructed in the theme sections and file manifest.

### 3.1 Master session table (all 63 sessions)

| Batch | Session ID | Title / Role | Agent | Model | Worktree | Tokens (in / out) | Messages | Files Touched |
|---|---|---|---|---|---|---|---|---|
| A | `ses_0d3acedf6ffeSO63IwKxY1LOhE` | Review modified code changes (@general) | general | kimi-k2.7-code | `/Users/srujansai/Desktop/rfq2boq` | 36,119 / 3,243 | 15 | 0 |
| A | `ses_0d3ad0628ffeTgnlCBLzMf3biy` | Build corpus manifest (@general) | general | kimi-k2.7-code | `/Users/srujansai/Desktop/rfq2boq` | 45,950 / 8,777 | 17 | 0 |
| A | `ses_0d3ad2095ffewtQmOj1SE6IOd2` | Audit training checkpoint (@general) | general | kimi-k2.7-code | `/Users/srujansai/Desktop/rfq2boq` | 33,856 / 1,918 | 11 | 0 |
| A | `ses_0d3ad3857ffe5L8gKTNFjz04Uw` | Verify sacred 10 fidelity (@general) | general | kimi-k2.7-code | `/Users/srujansai/Desktop/rfq2boq` | 36,670 / 2,301 | 8 | 0 |
| A | `ses_0e92c1523ffepJfa6dVTqzYdCa` | Complete project using kleenhand.md | build | big-pickle | `/Users/srujansai/Desktop/rfq2boq` | 32,073,942 / 48,033 | 359 | 0 |
| A | `ses_0ed1b3fabffeJpdYlmo7lCL6wQ` | Fix XLSX fidelity issues (@general) | general | mimo-v2.5-free | `/Users/srujansai/Desktop/rfq2boq` | 18,706 / 4,621 | 20 | 0 |
| A | `ses_0ed1e144effe19989GAriuUQdy` | Consolidate handoff files (@general) | general | mimo-v2.5-free | `/Users/srujansai/Desktop/rfq2boq` | 33,121 / 5,794 | 13 | 0 |
| A | `ses_0ed24165fffeROPQ4ohziwXQ5B` | Gold spot-check report (@general) | general | mimo-v2.5-free | `/Users/srujansai/Desktop/rfq2boq` | 35,983 / 8,376 | 24 | 0 |
| A | `ses_0ed242b65ffezeyDwKYvN55OKU` | Build catalog matcher + eval (@general) | general | mimo-v2.5-free | `/Users/srujansai/Desktop/rfq2boq` | 76,848 / 12,480 | 26 | 0 |
| A | `ses_0f87ec8dfffeFNQxeYiOiYgGXa` | OpenRouter free models testing and fix | build | nemotron-3-ultra-free | `/Users/srujansai/Desktop/rfq2boq` | 2,932,889 / 12,327 | 78 | 0 |
| B | `ses_0f88770ecffe5aQldCdtAqaT62` | New session - 2026-06-27T05:06:09.303Z | build | nemotron-3-ultra-free | `/Users/srujansai/Desktop/rfq2boq` | 6,408,835 / 11,228 | 78 | 0 |
| B | `ses_0fd7cbb45ffesQQ71OIbB5fK6h` | Fixing insulation tender timeout issues | build | MiniMax-M2.7 | `/Users/srujansai/Desktop/rfq2boq-laneC` | 59,290 / 20,915 | 53 | 0 |
| B | `ses_0fdafa71bffecXT75Te9NUysHE` | Honest row-level eval for insulation domain | build | MiniMax-M2.5 | `/Users/srujansai/Desktop/rfq2boq-laneE` | 59,922 / 7,809 | 35 | 0 |
| B | `ses_0fdafb0abffeoBynJcvQwOZBAf` | Wave 2: Integrate insulation ontology into NER | build | MiniMax-M2.7 | `/Users/srujansai/Desktop/rfq2boq-laneD` | 33,771 / 16,078 | 67 | 0 |
| B | `ses_0fdafb620ffeHQjGRROrcwnHu4` | Fix insulation tender timeout errors | build | MiniMax-M2.5 | `/Users/srujansai/Desktop/rfq2boq-laneC` | 10,855 / 469 | 3 | 0 |
| B | `ses_0fdafba93ffe3VQZOnW49H6WvS` | Drafting row-gold for remaining insulation BOQ pairs | build | MiniMax-M3 | `/Users/srujansai/Desktop/rfq2boq-laneB` | 64,469 / 45,370 | 75 | 0 |
| B | `ses_10252f5f6ffe22OwrDdIVrwya2` | Final honest project status (Lane A) | build | MiniMax-M2.7 | `/Users/srujansai/Desktop/rfq2boq-laneA` | 9,658 / 9,962 | 43 | 0 |
| B | `ses_10252fd6fffeMeuwcwdVnlJ3aX` | Insulation domain honest row-level evaluation | build | MiniMax-M2.5 | `/Users/srujansai/Desktop/rfq2boq-laneE` | 23,625 / 859 | 8 | 0 |
| B | `ses_10252fefbffel0FKlMI9pKBWmy` | Wave 2 NER insulation ontology integration | build | MiniMax-M2.7 | `/Users/srujansai/Desktop/rfq2boq-laneD` | 10,473 / 1,346 | 7 | 0 |
| B | `ses_102530d7fffeVftN5PF8U6msRR` | Structure-first routing fixes insulation tender timeouts | build | MiniMax-M2.5 | `/Users/srujansai/Desktop/rfq2boq-laneC` | 28,206 / 1,255 | 8 | 0 |
| C | `ses_102531233ffeMwYlu3ZxQNBFCg` | Drafting row-gold for remaining insulation BOQ pairs | build | MiniMax-M3 | `/Users/srujansai/Desktop/rfq2boq-laneB` | 33,302 / 892 | 7 | 0 |
| C | `ses_102c97e68ffeRWt9w2TSsVFyV5` | Audit lane D after b38db2c | build | MiniMax-M2.7 | `/Users/srujansai/Desktop/rfq2boq-laneA` | 12,678 / 3,126 | 9 | 0 |
| C | `ses_102c9870bffeiw9AtrrRkADdM1` | Finish Lane B row-gold extraction and commit | build | MiniMax-M3 | `/Users/srujansai/Desktop/rfq2boq-laneB` | 47,081 / 9,120 | 25 | 0 |
| C | `ses_102f4a325ffelqG9k9gJhkVa1o` | Lane D: ontology commit + insulation IS-codes | build | MiniMax-M2.5-highspeed | `/Users/srujansai/Desktop/rfq2boq-laneD` | 7,699 / 9,386 | 30 | 0 |
| C | `ses_102f4aa1cffesD2HuwJap6tx0Y` | Adani PDF structure-first extraction fix | build | MiniMax-M2.5 | `/Users/srujansai/Desktop/rfq2boq-laneC` | 158,320 / 7,816 | 39 | 0 |
| C | `ses_102f4b503ffeMAjBB5eagKAf1v` | Lane A merge audit C/D/E | build | MiniMax-M2.7 | `/Users/srujansai/Desktop/rfq2boq-laneA` | 19,333 / 15,089 | 56 | 0 |
| C | `ses_102f4bcbcffeQlEvknhz4Q1NWF` | Insulation tender extraction + draft row-gold (Lane B1) | build | MiniMax-M3 | `/Users/srujansai/Desktop/rfq2boq-laneB` | 42,627 / 10,918 | 27 | 0 |
| C | `ses_107326f60ffey4di2lse0VcP2o` | RFQ2BOQ multi-agent dispatch hitting credit limits | build | mimo-v2.5-pro | `/Users/srujansai/Desktop/rfq2boq` | 77,225 / 314 | 3 | 0 |
| C | `ses_107a0bbecffelXrQdEq7MIz82f` | Insulation tender batch pipeline run | build | MiniMax-M2.5 | `/Users/srujansai/Desktop/rfq2boq-laneE` | 162,442 / 14,995 | 72 | 0 |
| C | `ses_107a0f528ffe0LbXtl6kPcssjS` | Insulation tender extraction + draft row-gold | build | MiniMax-M3 | `/Users/srujansai/Desktop/rfq2boq-laneB` | 96,707 / 13,808 | 43 | 0 |
| D | `ses_107a0fadaffeWtp4UJEDCeOgxc` | Lane A merge audit C/D/E | build | MiniMax-M3 | `/Users/srujansai/Desktop/rfq2boq-laneA` | 36,458 / 4,416 | 18 | 0 |
| D | `ses_107a43ba2ffeuIDC04zVtKIFVo` | Insulation batch run — fidelity reports for 11 tenders | build | MiniMax-M2.5 | `/Users/srujansai/Desktop/rfq2boq-laneE` | 22,286 / 327 | 4 | 0 |
| D | `ses_107a4c164ffefepVNT453HPKwO` | Lane A5 merge audit (C/D/E) | build | MiniMax-M3 | `/Users/srujansai/Desktop/rfq2boq-laneA` | 12,048 / 756 | 3 | 0 |
| D | `ses_11006afa2ffeHDdIZ3bISAO921` | Explore PDF ingested content (@explore) | explore | deepseek-v4-flash-free | `/Users/srujansai/Desktop/rfq2boq-laneA` | 28,435 / 10,507 | 7 | 0 |
| D | `ses_1100731e2ffeLO6D49XlhnJhBh` | Lane E pipeline robustness and fidelity | build | mimo-v2.5-free | `/Users/srujansai/Desktop/rfq2boq-laneE` | 399,801 / 31,219 | 115 | 0 |
| D | `ses_11007b70fffekB26BFLAMNlTAz` | Lane D ontology + GeM reference (R2) | build | north-mini-code-free | `/Users/srujansai/Desktop/rfq2boq-laneD` | 2,671,055 / 18,728 | 68 | 0 |
| D | `ses_110081fc7ffeGxIasPR52AvQro` | Lane C structure-first extraction R4 | build | big-pickle | `/Users/srujansai/Desktop/rfq2boq-laneC` | 85,482 / 12,121 | 45 | 0 |
| D | `ses_1100865ffffeXBUIp4Vx6Aidex` | Lane B insulation gold annotation loop setup | build | nemotron-3-ultra-free | `/Users/srujansai/Desktop/rfq2boq-laneB` | 87,860 / 524 | 7 | 0 |
| D | `ses_11008f3a1ffeT5D3nmQGeU5edh` | Lane A anti-cheat & honest baseline | build | deepseek-v4-flash-free | `/Users/srujansai/Desktop/rfq2boq-laneA` | 224,631 / 32,126 | 94 | 0 |
| D | `ses_1115553a6ffeR4s6IEmUn3Mg63` | Complete and hand off project sessions with analysis | build | mimo-v2.5-pro | `/Users/srujansai/Desktop/rfq2boq` | 4,024,883 / 27,362 | 184 | 0 |
| E | `ses_1264a012affeRHj6w08eOvWTpx` | Fix pipeline extraction for Zydus non-zero qty rows | build | nemotron-3-ultra-free | `/Users/srujansai/Desktop/rfq2boq` | 1,510,272 / 7,608 | — | 0 |
| E | `ses_1264a228effekBULGv67DcUhb8` | Honest evaluation run and commit results | build | north-mini-code-free | `/Users/srujansai/Desktop/rfq2boq` | 251,562 / 992 | — | 0 |
| E | `ses_1264a3a58ffeDzcnix7Aumg4Gl` | Fix 07 Grew Solar missing row | build | big-pickle | `/Users/srujansai/Desktop/rfq2boq` | 76,801 / 14,837 | — | 0 |
| E | `ses_1265a99deffe5aXI1BUOhOjZ6K` | Repo hygiene fixes: restore PDFs, update docs, rebuild manifest | build | north-mini-code-free | `/Users/srujansai/Desktop/rfq2boq` | 458,193 / 1,244 | — | 0 |
| E | `ses_1265ac970ffeFnUi7jnm7d994s` | Fix 02 ISRO VSSC missing 2 rows | build | deepseek-v4-flash-free | `/Users/srujansai/Desktop/rfq2boq` | 47,014 / 4,873 | — | 0 |
| E | `ses_1265af65bffeL58pbBwiAZOMgs` | NW-05: Consolidate unit normalizers into one | build | big-pickle | `/Users/srujansai/Desktop/rfq2boq` | 50,007 / 13,401 | — | 0 |
| E | `ses_12693d3a5ffe4g4hp2xGkYTSBt` | Update gold flag and run pipeline on 2 new tenders | build | deepseek-v4-flash-free | `/Users/srujansai/Desktop/rfq2boq` | 27,633 / 1,423 | — | 0 |
| E | `ses_12693fee0ffeljUnjpZfU7KhPP` | Add SWA GeM catalog with validation | build | big-pickle | `/Users/srujansai/Desktop/rfq2boq` | 21,926 / 1,741 | — | 0 |
| E | `ses_126941f4efferQ3FEVE3JnlSX1` | Add data_only=True to openpyxl loads for formula evaluation | build | big-pickle | `/Users/srujansai/Desktop/rfq2boq` | 172,710 / 517 | — | 0 |
| E | `ses_126959a48ffe0Xj8aFjythvq3g` | Fix XLSX pipeline formula cell handling with data_only=True | build | big-pickle | `/Users/srujansai/Desktop/rfq2boq` | 170,197 / 520 | — | 0 |
| F | `ses_155dd541cffenOtFZ8LrTqLAik` | Explore data and gold files (@explore subagent) | explore | mimo-v2.5-free | `/Users/srujansai/Desktop/rfq2boq` | 157,656 / 4,806 | 6 | 0 |
| F | `ses_155dd5ee9ffe3fQj9ASNArlHQE` | Explore extraction pipeline code (@explore subagent) | explore | mimo-v2.5-free | `/Users/srujansai/Desktop/rfq2boq` | 91,121 / 10,340 | 8 | 0 |
| F | `ses_148f386efffeFhGl97ZKifyHpx` | NW-06 Repo Hygiene & Docs cleanup | build | mimo-v2.5-free | `/Users/srujansai/Desktop/rfq2boq` | 12,119,246 / 89,330 | 231 | 0 |
| F | `ses_14655c5e3ffedVq2vCzwqqzEup` | Concerns about AI agent cheating during model development | build | MiniMax-M3 | `/Users/srujansai/Desktop/rfq2boq` | 21,180,363 / 95,931 | 177 | 0 |
| F | `ses_12699751dffeElVqfcwzqhklQz` | New session - 2026-06-18T06:23:56.642Z | build | mimo-v2.5-free | `/Users/srujansai/Desktop/rfq2boq` | 11,653 / 4 | 2 | 0 |
| F | `ses_126999169ffehldjRQb62n5RGt` | OK only reply | build | north-mini-code-free | `/Users/srujansai/Desktop/rfq2boq` | 11,142 / 1 | 2 | 0 |
| F | `ses_12699b2deffe89kaev8PsqCJU5` | New session - 2026-06-18T06:23:40.834Z | build | big-pickle | `/Users/srujansai/Desktop/rfq2boq` | 12,538 / 2 | 2 | 0 |
| F | `ses_12699df61ffeGPrgCMZhswLbZV` | New session - 2026-06-18T06:23:29.438Z | build | nemotron-3-ultra-free | `/Users/srujansai/Desktop/rfq2boq` | 12,986 / 2 | 2 | 0 |
| F | `ses_12699fdc0ffe9Kp8d6zaAePzFt` | New session - 2026-06-18T06:23:21.663Z | build | deepseek-v4-flash-free | `/Users/srujansai/Desktop/rfq2boq` | 12,546 / 2 | 2 | 0 |
| F | `ses_1269a7946ffesVlYNiZeqYOP8V` | New session - 2026-06-18T06:22:50.041Z | build | deepseek-v4-flash-free | `/Users/srujansai/Desktop/rfq2boq` | 12,552 / 4 | 2 | 0 |
| G | `ses_155dd6af8ffekYYXldimJRnCGj` | Explore training pipeline code (@explore subagent) | explore | mimo-v2.5-free | `/Users/srujansai/Desktop/rfq2boq` | 76,799 / 6,884 | 8 | 0 |
| G | `ses_167aacf62ffeDLFxLQh1pD3VVg` | LoRA training vs production 0.43 F1 | plan | nemotron-3-ultra-free | `/Users/srujansai/Desktop/rfq2boq` | 10,229,535 / 133,146 | 389 | 0 |
| G | `ses_167acb83cffe49VU1lhkjiW3Ee` | New session - 2026-06-05T15:07:35.235Z | plan | nemotron-3-ultra-free | `/Users/srujansai/Desktop/rfq2boq` | 16,205,463 / 74,604 | 238 | 0 |

### 3.2 Batch A sessions

Batch A focused on project-wide review, corpus manifest planning, training checkpoint audit, sacred-10 fidelity verification, XLSX fidelity fixes, handoff consolidation, catalog matcher construction, and OpenRouter model testing.

| Session ID | Title | Model | Tokens (in / out) | Key outcome / deliverable |
|---|---|---|---|---|
| `ses_0d3acedf6ffeSO63IwKxY1LOhE` | Review modified code changes | kimi-k2.7-code | 36,119 / 3,243 | Reviewed uncommitted changes; identified silent exception swallowing, hardcoded confidences, fidelity-audit self-reference as red flags. |
| `ses_0d3ad0628ffeTgnlCBLzMf3biy` | Build corpus manifest | kimi-k2.7-code | 45,950 / 8,777 | Proposed `data/real_rfqs/corpus_manifest.json`; not yet written. |
| `ses_0d3ad2095ffewtQmOj1SE6IOd2` | Audit training checkpoint | kimi-k2.7-code | 33,856 / 1,918 | PID 6877 dead; LoRA training died at epoch 2.0; best F1 1.46%, final F1 0.0; only 39 real/human-verified docs available. |
| `ses_0d3ad3857ffe5L8gKTNFjz04Uw` | Verify sacred 10 fidelity | kimi-k2.7-code | 36,670 / 2,301 | Sacred-10 count fidelity 100%; raw over-capture 114.4%; 63 low-conf rows. |
| `ses_0e92c1523ffepJfa6dVTqzYdCa` | Complete project using kleenhand.md | big-pickle | 32,073,942 / 48,033 | Listed critical pending work; falsely claimed LoRA PID 6877 running; noted leaked GitHub token. |
| `ses_0ed1b3fabffeJpdYlmo7lCL6wQ` | Fix XLSX fidelity issues | mimo-v2.5-free | 18,706 / 4,621 | Hardened `measure_fidelity.py`: now fails on dropped rows or fidelity >110%; overall 0 PASS, 10 FAIL, 27.9%. |
| `ses_0ed1e144effe19989GAriuUQdy` | Consolidate handoff files | mimo-v2.5-free | 33,121 / 5,794 | Created `HANDOFF.md`; `git mv` 5 files to `attic/`. |
| `ses_0ed24165fffeROPQ4ohziwXQ5B` | Gold spot-check report | mimo-v2.5-free | 35,983 / 8,376 | Created `scripts/gold_spotcheck_report.py` and `results/gold_spotcheck_report.md`; all 168 insulation entries `human_verified: false`. |
| `ses_0ed242b65ffezeyDwKYvN55OKU` | Build catalog matcher + eval | mimo-v2.5-free | 76,848 / 12,480 | Created `src/nlp/catalog_matcher.py`; 39 tests passed; output `results/eval_catalog_match.json`. |
| `ses_0f87ec8dfffeFNQxeYiOiYgGXa` | OpenRouter free models testing and fix | nemotron-3-ultra-free | 2,932,889 / 12,327 | Truncated/abandoned; no deliverable recorded. |

### 3.3 Batch B sessions

Batch B initiated Wave 2 lane work, focusing on insulation tender timeouts, row-gold drafting, ontology/NER integration, honest evaluation, and structure-first routing.

| Session ID | Title | Model | Tokens (in / out) | Key outcome / deliverable |
|---|---|---|---|---|
| `ses_0f88770ecffe5aQldCdtAqaT62` | New session - 2026-06-27T05:06:09.303Z | nemotron-3-ultra-free | 6,408,835 / 11,228 | Orchestration attempt; identified Avante-style docs lacking explicit BOQ headings. |
| `ses_0fd7cbb45ffesQQ71OIbB5fK6h` | Fixing insulation tender timeout issues | MiniMax-M2.7 | 59,290 / 20,915 | Commit `3530731` — structure-first routing fixes timeouts. |
| `ses_0fdafa71bffecXT75Te9NUysHE` | Honest row-level eval for insulation domain | MiniMax-M2.5 | 59,922 / 7,809 | Commit `396d884` — insulation domain macro F1 21.7%. |
| `ses_0fdafb0abffeoBynJcvQwOZBAf` | Wave 2: Integrate insulation ontology into NER | MiniMax-M2.7 | 33,771 / 16,078 | Commit `7a2007c` — NER pattern/gazetteer integration. |
| `ses_0fdafb620ffeHQjGRROrcwnHu4` | Fix insulation tender timeout errors | MiniMax-M2.5 | 10,855 / 469 | Very short; no final output preserved; grouped under C7. |
| `ses_0fdafba93ffe3VQZOnW49H6WvS` | Drafting row-gold for remaining insulation BOQ pairs | MiniMax-M3 | 64,469 / 45,370 | Commit `88e92a6` — created `insul_03`–`insul_09` rowgold files (168 total rows). |
| `ses_10252f5f6ffe22OwrDdIVrwya2` | Final honest project status (Lane A) | MiniMax-M2.7 | 9,658 / 9,962 | Commit `2407fab` (amended) — `results/PROJECT_HONEST_STATUS_2026-06-25.md`. |
| `ses_10252fd6fffeMeuwcwdVnlJ3aX` | Insulation domain honest row-level evaluation | MiniMax-M2.5 | 23,625 / 859 | Early exploration; grouped under E7. |
| `ses_10252fefbffel0FKlMI9pKBWmy` | Wave 2 NER insulation ontology integration | MiniMax-M2.7 | 10,473 / 1,346 | Early exploration; grouped under D3. |
| `ses_102530d7fffeVftN5PF8U6msRR` | Structure-first routing fixes insulation tender timeouts | MiniMax-M2.5 | 28,206 / 1,255 | Early exploration; grouped under C7. |

### 3.4 Batch C sessions

Batch C continued lane work with row-gold extraction, ontology IS-code commits, Adani PDF fixes, merge audits, and batch pipeline runs.

| Session ID | Title | Model | Tokens (in / out) | Key outcome / deliverable |
|---|---|---|---|---|
| `ses_102531233ffeMwYlu3ZxQNBFCg` | Drafting row-gold for remaining insulation BOQ pairs | MiniMax-M3 | 33,302 / 892 | Handoff truncated; outcome unknown per BATCH C. |
| `ses_102c97e68ffeRWt9w2TSsVFyV5` | Audit lane D after b38db2c | MiniMax-M2.7 | 12,678 / 3,126 | Commit `b49f62d` — re-audit Lane D after ontology commit. |
| `ses_102c9870bffeiw9AtrrRkADdM1` | Finish Lane B row-gold extraction and commit | MiniMax-M3 | 47,081 / 9,120 | Commit `73489c8` — `insul_01_tender.rowgold.json` (23 rows) and `insul_02_swpl.rowgold.json` (19 rows). |
| `ses_102f4a325ffelqG9k9gJhkVa1o` | Lane D: ontology commit + insulation IS-codes | MiniMax-M2.5-highspeed | 7,699 / 9,386 | Implied commit `b38db2c` — GeM gazetteer + insulation ontology (D1-D2). |
| `ses_102f4aa1cffesD2HuwJap6tx0Y` | Adani PDF structure-first extraction fix | MiniMax-M2.5 | 158,320 / 7,816 | Created `tests/integration/test_adani_structure.py`; claimed 45 rows matching gold; commit unconfirmed. |
| `ses_102f4b503ffeMAjBB5eagKAf1v` | Lane A merge audit C/D/E | MiniMax-M2.7 | 19,333 / 15,089 | Commit `c0a7477` — `results/lane_merge_audit_2026-06-22.md`. |
| `ses_102f4bcbcffeQlEvknhz4Q1NWF` | Insulation tender extraction + draft row-gold (Lane B1) | MiniMax-M3 | 42,627 / 10,918 | Handoff truncated; likely same task as `ses_107a0f528ffe0LbXtl6kPcssjS`. |
| `ses_107326f60ffey4di2lse0VcP2o` | RFQ2BOQ multi-agent dispatch hitting credit limits | mimo-v2.5-pro | 77,225 / 314 | Identified 25 MB RAR v5 archive; installed `rar`/`unar`; listed 11 spec PDFs; did NOT extract into repo. |
| `ses_107a0bbecffelXrQdEq7MIz82f` | Insulation tender batch pipeline run | MiniMax-M2.5 | 162,442 / 14,995 | Created `scripts/run_insulation_batch.py`, batch results, no-crash test; 7 timeouts reported; commit unconfirmed. |
| `ses_107a0f528ffe0LbXtl6kPcssjS` | Insulation tender extraction + draft row-gold | MiniMax-M3 | 96,707 / 13,808 | Handoff truncated/incomplete. |

### 3.5 Batch D sessions

Batch D finalized lane work with anti-cheat/baseline hardening, Lane C R4 extraction, Lane D ontology mining, Lane E robustness, and project-wide handoff analysis.

| Session ID | Title | Model | Tokens (in / out) | Key outcome / deliverable |
|---|---|---|---|---|
| `ses_107a0fadaffeWtp4UJEDCeOgxc` | Lane A merge audit C/D/E | MiniMax-M3 | 36,458 / 4,416 | No completion captured. |
| `ses_107a43ba2ffeuIDC04zVtKIFVo` | Insulation batch run — fidelity reports for 11 tenders | MiniMax-M2.5 | 22,286 / 327 | No completion captured; expected same E6 deliverables. |
| `ses_107a4c164ffefepVNT453HPKwO` | Lane A5 merge audit (C/D/E) | MiniMax-M3 | 12,048 / 756 | No completion captured. |
| `ses_11006afa2ffeHDdIZ3bISAO921` | Explore PDF ingested content | deepseek-v4-flash-free | 28,435 / 10,507 | No files touched; extracted content from `04_adani`, `09_gem`, `10_gem` ingested JSONs and gold. |
| `ses_1100731e2ffeLO6D49XlhnJhBh` | Lane E pipeline robustness and fidelity | mimo-v2.5-free | 399,801 / 31,219 | Modified `src/rules/units.py`, `src/pipeline_xlsx.py`, `Makefile`, tests; reported passing `make verify`. |
| `ses_11007b70fffekB26BFLAMNlTAz` | Lane D ontology + GeM reference (R2) | north-mini-code-free | 2,671,055 / 18,728 | Status **RUNNING** — mining 53 spec PDFs in `resources/Specifications/`; no completion captured. |
| `ses_110081fc7ffeGxIasPR52AvQro` | Lane C structure-first extraction R4 | big-pickle | 85,482 / 12,121 | Commit `8f9e35e` — 5 files changed, 99+/−4; 95 critical tests pass. |
| `ses_1100865ffffeXBUIp4Vx6Aidex` | Lane B insulation gold annotation loop setup | nemotron-3-ultra-free | 87,860 / 524 | Status **ERROR / Timeout — needs restart**. |
| `ses_11008f3a1ffeT5D3nmQGeU5edh` | Lane A anti-cheat & honest baseline | deepseek-v4-flash-free | 224,631 / 32,126 | Anti-cheat tests hardened; `make verify` passes 7 steps clean; reported entity F1 44.1%. |
| `ses_1115553a6ffeR4s6IEmUn3Mg63` | Complete and hand off project sessions with analysis | mimo-v2.5-pro | 4,024,883 / 27,362 | Multi-lane status table: Lane A DONE, Lane C DONE, Lane B ERROR/timeout, Lane D RUNNING, Lane E RUNNING. |

### 3.6 Batch E sessions

Batch E delivered concrete XLSX/table fixes, honest evaluation commits, repo hygiene, unit-normalizer consolidation, and GeM catalog ingestion.

| Session ID | Title | Model | Tokens (in / out) | Key outcome / deliverable |
|---|---|---|---|---|
| `ses_1264a012affeRHj6w08eOvWTpx` | Fix pipeline extraction for Zydus non-zero qty rows | nemotron-3-ultra-free | 1,510,272 / 7,608 | Zydus Animal Pharmez now extracts exactly 20 non-zero TOTAL rows. |
| `ses_1264a228effekBULGv67DcUhb8` | Honest evaluation run and commit results | north-mini-code-free | 251,562 / 992 | Commit `eval: updated honest baseline after nw05/nw06/gem fixes`; macro F1 92.1%. |
| `ses_1264a3a58ffeDzcnix7Aumg4Gl` | Fix 07 Grew Solar missing row | big-pickle | 76,801 / 14,837 | Commit `c923e2a` — phantom-space fix in `src/ingest/table_extractor.py`; 100% F1. |
| `ses_1265a99deffe5aXI1BUOhOjZ6K` | Repo hygiene fixes: restore PDFs, update docs, rebuild manifest | north-mini-code-free | 458,193 / 1,244 | Commit with 155 files — restored 154 reference PDFs, rebuilt `manifest.csv`, fixed `MASTER_HANDOFF.md`. |
| `ses_1265ac970ffeFnUi7jnm7d994s` | Fix 02 ISRO VSSC missing 2 rows | deepseek-v4-flash-free | 47,014 / 4,873 | Gold file flagged as unreliable; no pipeline change. |
| `ses_1265af65bffeL58pbBwiAZOMgs` | NW-05: Consolidate unit normalizers into one | big-pickle | 50,007 / 13,401 | Commit `b81b440` — unified `src/rules/units.py`; 59 new tests. |
| `ses_12693d3a5ffe4g4hp2xGkYTSBt` | Update gold flag and run pipeline on 2 new tenders | deepseek-v4-flash-free | 27,633 / 1,423 | Commits `c001ef8`, `6fc9bfa` — flagged 05 Zydus Animal gold, ran 2 incoming tenders. |
| `ses_12693fee0ffeljUnjpZfU7KhPP` | Add SWA GeM catalog with validation | big-pickle | 21,926 / 1,741 | Commit `0739ecf` — created `src/nlp/patterns/gem_catalog.py`. |
| `ses_126941f4efferQ3FEVE3JnlSX1` | Add data_only=True to openpyxl loads for formula evaluation | big-pickle | 172,710 / 517 | Verified no change needed; `src/pipeline_xlsx.py:56` and `src/ingest/xlsx_parser.py:31` already use `data_only=True`. |
| `ses_126959a48ffe0Xj8aFjythvq3g` | Fix XLSX pipeline formula cell handling with data_only=True | big-pickle | 170,197 / 520 | Duplicate verification; no change needed. |

### 3.7 Batch F sessions

Batch F was largely exploratory and planning-focused, with two deep-dive explore sessions, a large repo-hygiene planning session, a model-cheating concern session, and six trivial OK/HELLO sessions.

| Session ID | Title | Model | Tokens (in / out) | Key outcome / deliverable |
|---|---|---|---|---|
| `ses_155dd541cffenOtFZ8LrTqLAik` | Explore data and gold files | mimo-v2.5-free | 157,656 / 4,806 | Comprehensive data/gold/annotation report (truncated at line 212). |
| `ses_155dd5ee9ffe3fQj9ASNArlHQE` | Explore extraction pipeline code | mimo-v2.5-free | 91,121 / 10,340 | Complete extraction pipeline report (truncated at line 162). |
| `ses_148f386efffeFhGl97ZKifyHpx` | NW-06 Repo Hygiene & Docs cleanup | mimo-v2.5-free | 12,119,246 / 89,330 | Honest status: code done, project blocked on owner-only actions. |
| `ses_14655c5e3ffedVq2vCzwqqzEup` | Concerns about AI agent cheating during model development | MiniMax-M3 | 21,180,363 / 95,931 | Agent agreed to train honestly on 10 SWA resources; no further tool calls recorded. |
| `ses_12699751dffeElVqfcwzqhklQz` | New session - 2026-06-18T06:23:56.642Z | mimo-v2.5-free | 11,653 / 4 | Output: `OK` |
| `ses_126999169ffehldjRQb62n5RGt` | OK only reply | north-mini-code-free | 11,142 / 1 | Output: `OK` |
| `ses_12699b2deffe89kaev8PsqCJU5` | New session - 2026-06-18T06:23:40.834Z | big-pickle | 12,538 / 2 | Output: `OK` |
| `ses_12699df61ffeGPrgCMZhswLbZV` | New session - 2026-06-18T06:23:29.438Z | nemotron-3-ultra-free | 12,986 / 2 | Output: `OK` |
| `ses_12699fdc0ffe9Kp8d6zaAePzFt` | New session - 2026-06-18T06:23:21.663Z | deepseek-v4-flash-free | 12,546 / 2 | Output: `OK` |
| `ses_1269a7946ffesVlYNiZeqYOP8V` | New session - 2026-06-18T06:22:50.041Z | deepseek-v4-flash-free | 12,552 / 4 | Output: `HELLO` |

### 3.8 Batch G sessions

Batch G focused on training pipeline exploration, LoRA-vs-production planning, and the 10-week roadmap / clean-slate tasks.

| Session ID | Title | Model | Tokens (in / out) | Key outcome / deliverable |
|---|---|---|---|---|
| `ses_155dd6af8ffekYYXldimJRnCGj` | Explore training pipeline code | mimo-v2.5-free | 76,799 / 6,884 | Read-only map of NER training; identified 3 training scripts, base-model mismatch (cased vs uncased). |
| `ses_167aacf62ffeDLFxLQh1pD3VVg` | LoRA training vs production 0.43 F1 | nemotron-3-ultra-free | 10,229,535 / 133,146 | Task R3 to run LoRA training; reported `HANDOFF.md` modified/uncommitted; Git HEAD `2d3bf6f`; planned 40 RFQ annotations. |
| `ses_167acb83cffe49VU1lhkjiW3Ee` | New session - 2026-06-05T15:07:35.235Z | nemotron-3-ultra-free | 16,205,463 / 74,604 | Tasks R1/R2 — clean-slate reorg, 03 Zydus honest fix; warned anti-cheat will FAIL on 03 Zydus; 8-task Phase 0 plan. |

---

## 4. Work by Theme

This section reorganizes the same session content by technical theme. Details are preserved; sessions are cross-referenced.

### 4.1 Orchestration / Dispatch / Handoff

| Session | Batch | Focus | Outcome |
|---|---|---|---|
| `ses_0e92c1523ffepJfa6dVTqzYdCa` | A | Complete project using `kleenhand.md` | Listed critical pending work; falsely claimed LoRA PID 6877 running; noted leaked GitHub token. |
| `ses_0ed1e144effe19989GAriuUQdy` | A | Consolidate handoff files | Created `HANDOFF.md` (289 lines); `git mv` 5 files to `attic/`. |
| `ses_0f88770ecffe5aQldCdtAqaT62` | B | Orchestrate 20–30 subagents | Interrupted; identified Avante-style docs lacking explicit BOQ headings. |
| `ses_107326f60ffey4di2lse0VcP2o` | C | Multi-agent dispatch + `Specifications.rar` intake | Identified 25 MB RAR v5 archive; installed `rar`/`unar`; listed 11 spec PDFs; did NOT extract into repo. |
| `ses_1115553a6ffeR4s6IEmUn3Mg63` | D | Complete and hand off all project sessions | Multi-lane status table: Lane A DONE, Lane C DONE, Lane B ERROR/timeout, Lane D RUNNING, Lane E RUNNING. |
| `ses_0f87ec8dfffeFNQxeYiOiYgGXa` | A | OpenRouter free models testing | Truncated/abandoned; no deliverable. |
| `ses_148f386efffeFhGl97ZKifyHpx` | F | NW-06 Repo Hygiene & Docs cleanup | Honest status: code done, project blocked on owner-only actions; listed 6 owner-only blockers. |
| `ses_14655c5e3ffedVq2vCzwqqzEup` | F | Model-cheating concerns | Agent agreed to train honestly on 10 SWA resources; no subsequent file changes. |
| `ses_167aacf62ffeDLFxLQh1pD3VVg` | G | LoRA training vs production | Plan to run LoRA only if it beats 0.43 F1 on held-out real data; `HANDOFF.md` reported modified/uncommitted. |
| `ses_167acb83cffe49VU1lhkjiW3Ee` | G | 10-week roadmap / clean-slate | Phase 0–7 plan; 4 user decisions needed; warned 03 Zydus anti-cheat failure. |

### 4.2 PDF / Structure / Timeout Fixes

| Session | Batch | Focus | Files touched | Commit / outcome |
|---|---|---|---|---|
| `ses_0d3acedf6ffeSO63IwKxY1LOhE` | A | Review modified code changes / GeM recovery paths | `src/pipeline.py`, `src/ingest/pdf_extractor.py` | Reviewed layered GeM recovery; red flags identified. |
| `ses_0fd7cbb45ffesQQ71OIbB5fK6h` | B | Fixing insulation tender timeout issues | `src/pipeline.py`, `tests/integration/test_insulation_tender_timeouts.py` | `3530731` — structure-first routing fixes timeouts (C7). |
| `ses_0fdafb620ffeHQjGRROrcwnHu4` | B | Fix insulation tender timeout errors | (none captured) | Very short; grouped under C7. |
| `ses_102530d7fffeVftN5PF8U6msRR` | B | Structure-first routing fixes timeouts | (none captured) | Early exploration; grouped under C7. |
| `ses_102f4aa1cffesD2HuwJap6tx0Y` | C | Adani PDF structure-first extraction fix | `tests/integration/test_adani_structure.py` | Claimed 45 rows matching gold; commit unconfirmed. |
| `ses_110081fc7ffeGxIasPR52AvQro` | D | Lane C structure-first extraction R4 | `src/preproc/document_structure.py`, `src/ingest/table_extractor.py` | `8f9e35e` — 5 files, 99+/−4; 95 critical tests pass. |
| `ses_11006afa2ffeHDdIZ3bISAO921` | D | Explore PDF ingested content | 0 | Extracted content from 04_adani, 09_gem, 10_gem ingested JSONs and gold. |
| `ses_1264a3a58ffeDzcnix7Aumg4Gl` | E | Fix 07 Grew Solar missing row | `src/ingest/table_extractor.py` | `c923e2a` — phantom-space fix; 100% F1. |
| `ses_1265ac970ffeFnUi7jnm7d994s` | E | Fix 02 ISRO VSSC missing 2 rows | `data/real_rfqs/gold/rows/02_isro_vssc.rowgold.json` | Gold flagged; no pipeline change. |

**Detailed PDF/timeout fixes:**

1. **Structure-first routing (Lane C7, commit `3530731`):** Fast PyMuPDF outline scan before expensive pdfplumber extraction; early-exit `NO_BOQ_SECTION_FOUND` for spec-only docs. Result: all 7 previously timing-out insulation tender PDFs complete under 60s (0 rows each because they are spec-only).

2. **PDF timeout wrapper (Lane C R4, commit `8f9e35e`):** Added `timeout_sec` parameter with `ThreadPoolExecutor` wrapper in `TableExtractor.extract()`.

3. **Structure extractor precision (Lane C R4):** Added 5 heading-rejection rules in `src/preproc/document_structure.py`; requires ≥10 alpha chars, ≤48 chars, >88% uppercase for ALL CAPS. Reduced GSECL false positives from 1281 to 79 sections.

4. **GeM recovery paths (reviewed in A):** `src/pipeline.py` has 6+ layered GeM PDF recovery/fallback paths with content-based GeM detection (`"GEM/"`, `"bonded"`, `"wool"`, `"mattress"`). Recovered rows force `unit="no."`, `action="supply"`, `confidence=0.80`.

5. **Phantom-space fix (E, commit `c923e2a`):** In `src/ingest/table_extractor.py:map_to_boq_rows`, cross-reference Camelot-extracted tables with pdfplumber cell text keyed by content (without spaces) for material/description columns (columns 0-1). Quantity/unit columns excluded to avoid pdfplumber space-in-quantity artifacts (e.g., `"1 ,976.00"`).

### 4.3 XLSX / Table / Unit Normalization

| Session | Batch | Focus | Files touched | Commit / outcome |
|---|---|---|---|---|
| `ses_0ed1b3fabffeJpdYlmo7lCL6wQ` | A | Fix XLSX fidelity issues | `scripts/measure_fidelity.py` | Hardened pass/fail criteria. |
| `ses_1100731e2ffeLO6D49XlhnJhBh` | D | Lane E pipeline robustness and fidelity | `src/rules/units.py`, `src/pipeline_xlsx.py`, `Makefile`, tests | Unified unit normalizer; XLSX fidelity tracking; rate-only row flagging. |
| `ses_1264a012affeRHj6w08eOvWTpx` | E | Fix Zydus non-zero qty rows | `src/pipeline_xlsx.py` | Pipeline extracts exactly 20 non-zero TOTAL rows. |
| `ses_126941f4efferQ3FEVE3JnlSX1` | E | Verify `data_only=True` | `src/pipeline_xlsx.py`, `src/ingest/xlsx_parser.py` | No change needed; already correct. |
| `ses_126959a48ffe0Xj8aFjythvq3g` | E | Verify `data_only=True` | `src/pipeline_xlsx.py`, `src/ingest/xlsx_parser.py` | Duplicate verification; no change needed. |
| `ses_1265af65bffeL58pbBwiAZOMgs` | E | Consolidate unit normalizers | `src/rules/units.py`, `src/ingest/text_boq_extractor.py`, `src/domain/boq_assembler.py`, `src/unit_normalization.py`, `tests/unit/test_units_canonical.py` | Commit `b81b440`; 59 new tests. |
| `ses_12693d3a5ffe4g4hp2xGkYTSBt` | E | Run pipeline on 2 new tenders | `data/real_rfqs/gold/rows/05_zydus_animal_pharmez.rowgold.json`, `results/new_tenders_2026-06-18.json` | Commits `c001ef8`, `6fc9bfa`. |

**Detailed XLSX/unit fixes:**

1. **Zydus Animal Pharmez non-zero TOTAL filtering (E):** Source file `data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx` has a consolidated TOTAL column. Pipeline previously extracted all rows including `0` and `"R.O."`, producing 48 items. Fix in `src/pipeline_xlsx.py` emits only rows where `TOTAL > 0` (numeric). Result: exactly 20 items.

2. **Rate-only row handling (D):** `src/pipeline_xlsx.py` stopped dropping XLSX rows with `TOTAL <= 0`; emits them as `rate_only=True` rows with `confidence=0.70`; added `fidelity_report` tracking. **Note:** This conflicts with the later E fix that filters Zydus to non-zero TOTAL rows. The two behaviors may coexist via business-rule flags, but this needs verification.

3. **Unit-normalizer consolidation (E, commit `b81b440`):**
   - `src/rules/units.py`: renamed `_EXTRA_ALIASES` → `UNIT_ALIASES`; expanded with aliases from `src/ingest/text_boq_extractor.py` and `src/domain/boq_assembler.py`; `_lookup` checks `UNIT_ALIASES` before `CANONICAL_UNITS`; added `to_float_qty(val) -> float | None`.
   - `src/ingest/text_boq_extractor.py`: removed 64-line local `_UNIT_MAP`; imports `normalize_unit` from `src.rules.units`.
   - `src/domain/boq_assembler.py`: removed 44-line local `unit_map`; uses central `normalize_unit` fallback.
   - `src/unit_normalization.py`: updated to handle `None` return from `to_float_qty`.
   - New test: `tests/unit/test_units_canonical.py` with 59 cases.

4. **Formula-cell handling (E):** Verified `src/pipeline_xlsx.py:56` and `src/ingest/xlsx_parser.py:31` already call `openpyxl.load_workbook(..., data_only=True)`. No code changes required in two duplicate verification sessions.

### 4.4 Ontology / NER / Catalog / Gazetteer

| Session | Batch | Focus | Files touched | Commit / outcome |
|---|---|---|---|---|
| `ses_0ed242b65ffezeyDwKYvN55OKU` | A | Build catalog matcher + eval | `src/nlp/catalog_matcher.py`, `results/eval_catalog_match.json`, `tests/unit/test_catalog_matcher.py` | Catalog matcher with cascade; 39 tests passed. |
| `ses_0fdafb0abffeoBynJcvQwOZBAf` | B | Wave 2: Integrate insulation ontology into NER | `src/nlp/patterns/dictionary.py`, `src/nlp/patterns/regex_patterns.py`, `src/nlp/pipeline.py`, `tests/unit/test_patterns.py` | Commit `7a2007c` (D3). |
| `ses_10252fefbffel0FKlMI9pKBWmy` | B | Wave 2 NER insulation ontology integration | (none captured) | Early exploration; grouped under D3. |
| `ses_102f4a325ffelqG9k9gJhkVa1o` | C | Lane D: ontology commit + insulation IS-codes | `data/ontology/insulation_materials.json`, `data/ontology/insulation_standards.json`, `data/ontology/insulation_units.json`, `src/nlp/patterns/gem_catalog.py`, `src/ontology/loader.py`, tests | Implied commit `b38db2c` (D1-D2). |
| `ses_102c97e68ffeRWt9w2TSsVFyV5` | C | Audit lane D after b38db2c | (audit deliverable) | Commit `b49f62d`. |
| `ses_11007b70fffekB26BFLAMNlTAz` | D | Lane D ontology + GeM reference (R2) | `data/ontology/insulation_materials.json` (continued enrichment) | Status **RUNNING** — mining 53 spec PDFs. |
| `ses_12693fee0ffeljUnjpZfU7KhPP` | E | Add SWA GeM catalog with validation | `src/nlp/patterns/gem_catalog.py` | Commit `0739ecf`; 13 unique products from 20 JSON entries. |
| `ses_155dd6af8ffekYYXldimJRnCGj` | G | Explore training pipeline code | 0 | Read-only map of NER training scripts and architectures. |

**Detailed ontology/NER changes:**

1. **Insulation ontology JSON files:**
   - `data/ontology/insulation_materials.json`: 26–27 materials; PIR added from RPMS PDF; source fields added.
   - `data/ontology/insulation_standards.json`: 11 standards; IS 11239 confirmed with source attribution.
   - `data/ontology/insulation_units.json`: 13 units.

2. **NER pattern/gazetteer integration:**
   - `src/nlp/patterns/dictionary.py`: loads insulation ontology and `insulation_gazetteer_mined.json`; swallows load errors silently (**red flag**).
   - `src/nlp/patterns/regex_patterns.py`: added 30+ insulation material patterns (nitrile rubber, rock/mineral wool, XLPE, class O, PIR, NBR, PUF, Armaflex, K-Flex, etc.) and broader ASTM/IS standard patterns.
   - `src/nlp/pipeline.py`: wired `GeMCatalogGazetteer` into NER pipeline for MATERIAL extraction.
   - `src/nlp/patterns/gem_catalog.py`: GeM gazetteer module.
   - `src/ontology/loader.py`: loads insulation ontology.
   - `tests/unit/test_patterns.py`: new insulation NER tests.
   - `tests/unit/test_gem_catalog.py`: 28 tests.
   - `tests/unit/test_ontology_loader.py`: passing.

3. **Catalog matcher (A):** New `src/nlp/catalog_matcher.py` with cascade: exact → alias exact → token overlap Jaccard → substring/keyword → Levenshtein. Catalog: `data/real_rfqs/swa_gem_catalog_full.json` (19 products, 13 unique) + `data/ontology/insulation_materials.json`. Output: `results/eval_catalog_match.json`. 39 tests passed; ruff clean.

4. **GeM catalog ingestion (E, commit `0739ecf`):** New `src/nlp/patterns/gem_catalog.py` containing `SWA_GEM_PUBLISHED` dict keyed by canonical product name (loaded from `data/real_rfqs/swa_gem_catalog_full.json`), `validate_gem_extraction(text, threshold=0.75)` using `difflib.SequenceMatcher`, and provenance comment.

5. **Terms proven to be tagged:** `nitrile rubber`, `rock wool`, `mineral wool`, `PIR`, `NBR`, `PUF`, `Armaflex`, `K-Flex` (MATERIAL); `IS 8183`, `IS 9842`, `IS 11433`, `IS 15577`, `IS 11239` (STANDARD); `Rmt`, `sqm`, `running metre` (UNIT).

### 4.5 Evaluation / Fidelity / Metrics

| Session | Batch | Focus | Deliverables | Key metrics |
|---|---|---|---|---|
| `ses_0d3ad3857ffe5L8gKTNFjz04Uw` | A | Verify sacred 10 fidelity | Sacred-10 fidelity table | Count fidelity 100%; raw over-capture 114.4%; 63 low-conf rows. |
| `ses_0ed1b3fabffeJpdYlmo7lCL6wQ` | A | Fix XLSX fidelity issues | `scripts/measure_fidelity.py` | 0 PASS, 10 FAIL, overall 27.9%. |
| `ses_0ed24165fffeROPQ4ohziwXQ5B` | A | Gold spot-check report | `scripts/gold_spotcheck_report.py`, `results/gold_spotcheck_report.md` | 168 insulation entries, all `human_verified: false`. |
| `ses_0fdafa71bffecXT75Te9NUysHE` | B | Honest row-level eval for insulation domain | `results/insulation_eval_2026-06-26.md`, `results/insulation_eval_raw.json`, `results/insulation_pipeline_output.json` | Macro F1 21.7% (`insul_01` 43.5%, `insul_02` 0.0%). |
| `ses_10252fd6fffeMeuwcwdVnlJ3aX` | B | Insulation domain honest row-level evaluation | (grouped under E7) | Early exploration. |
| `ses_10252f5f6ffe22OwrDdIVrwya2` | B | Final honest project status (Lane A) | `results/PROJECT_HONEST_STATUS_2026-06-25.md` | Entity F1 44.1%; XLSX 89.0%; PDF 14.2%; anti-cheat 27/27. |
| `ses_107a0bbecffelXrQdEq7MIz82f` | C | Insulation tender batch pipeline run | `scripts/run_insulation_batch.py`, `results/insulation_batch_run_2026-06-22.*`, `tests/integration/test_insulation_batch_no_crash.py` | 11/11 attempted; 0 crashes; 7 timeouts. |
| `ses_107a43ba2ffeuIDC04zVtKIFVo` | D | Insulation batch run — fidelity reports for 11 tenders | (same E6 deliverables) | No completion captured. |
| `ses_11008f3a1ffeT5D3nmQGeU5edh` | D | Lane A anti-cheat & honest baseline | Anti-cheat hardening | Entity F1 44.1%; anti-cheat 27/27; `make verify` passes. |
| `ses_1264a228effekBULGv67DcUhb8` | E | Honest evaluation run and commit results | `results/eval_honest_rows.json`, `results/eval_honest_rows_2026-06-18.txt` | Micro P 90.6%, R 82.8%, F1 86.5%; macro P 94.7%, R 90.2%, F1 92.1%. |
| `ses_167aacf62ffeDLFxLQh1pD3VVg` | G | LoRA training vs production 0.43 F1 | Plan only | Entity-level micro F1 ~42.6% target from `scripts/eval_honest.py`. |

**Detailed evaluation findings:**

1. **Sacred-10 fidelity (A):**

| Enquiry | Src | Ext | Miss | LowConf | Fidelity |
|---|---|---:|---:|---:|---:|
| 01_gsecl | 3 | 3 | 0 | 0 | 100% |
| 02_isro | 5 | 5 | 0 | 1 | 100% |
| 03_zydus_matoda | 33 | 33 | 0 | 3 | 100% |
| 04_adani | 45 | 45 | 0 | 28 | 100% |
| 05_zydus_animal | 20 | 48 | 0 | 28 | 100% |
| 06_avante | 31 | 31 | 0 | 0 | 100% |
| 07_grew | 9 | 9 | 0 | 0 | 100% |
| 08_sael | 17 | 17 | 0 | 3 | 100% |
| 09_gem | 22 | 22 | 0 | 0 | 100% |
| 10_gem | 10 | 10 | 0 | 0 | 100% |
| **TOTAL** | **195** | **223** | **0** | **63** | **100%** |

- Raw extraction vs source = 223 / 195 = **114.4%**; fidelity capped at `min(1.0, …)`.
- Anomalies: `05_zydus_animal` over-capture (48 vs 20); `04_adani` 28/45 low-confidence; OCR artifacts on 09/10_gem; `measure_fidelity.py` under-reports 04_adani due to `doc_map` omitting one PDF page.

2. **`measure_fidelity.py` fixes (A):** PASS criteria now FAIL if `dropped_rows > 0` OR `fidelity > 110%` (over-capture). Added `run_pdf_extraction()` that actually runs `Pipeline.run()` and counts `boq_items`. Added `OVER_CAPTURE_THRESHOLD = 1.10`. Added Status column with reason. Result after fix: **0 PASS, 10 FAIL**; overall fidelity **27.9%** (was previously inflated).

3. **Insulation domain evaluation (B):**

| Document | Gold Rows | Pred Rows | TP | FP | FN | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `insul_01_tender` | 23 | 23 | 10 | 13 | 13 | 43.5% | 43.5% | 43.5% |
| `insul_02_swpl` | 19 | 2 | 0 | 2 | 19 | 0.0% | 0.0% | 0.0% |
| **Macro** | | | | | | **21.7%** | **21.7%** | **21.7%** |

Caveats: gold is draft-only (`human_verified: false`); `insul_02_swpl` shows severe table-extraction failure (2 vs 19 rows).

4. **Honest row-level evaluation (E, commit `eval: updated honest baseline after nw05/nw06/gem fixes`):**
- `micro_precision`: 0.905829596412556
- `micro_recall`: 0.8278688524590164
- `micro_f1`: 0.8650963597430408
- `macro_precision`: 0.9472222222222222
- `macro_recall`: 0.9021085050935798
- `macro_f1`: 0.9209178743961353
- `total_gold`: 244
- `total_pred`: 223

Note: `scripts/eval_honest_rows.py` timed out after 2 minutes; final numbers were restored from a backup file.

5. **Anti-cheat / quality findings on extraction changes (A):**
- Red flags: silent exception swallowing in `src/pipeline.py` and `src/nlp/patterns/dictionary.py:209-210`; hardcoded confidence scores (`confidence=0.80` for recovered GeM rows, `confidence=0.70` for rate-only rows); `scripts/fidelity_audit.py` self-references rowgold count when rowgold exists, collapsing independent source-vs-output check.
- Checks that passed: no filename-specific hacks; no gold edits to match output; conventions OK. Relevant tests passed: `test_anti_cheat` (15), `test_convert_to_bioes` (13), `test_intake` (11), `test_xlsx_row_preservation_e2e` (9), `test_self_attack` (17).

### 4.6 Training / ML / LoRA

| Session | Batch | Focus | Key findings |
|---|---|---|---|
| `ses_0d3ad2095ffewtQmOj1SE6IOd2` | A | Audit training checkpoint | PID 6877 dead; training died at epoch 2.0; best F1 1.46%, final F1 0.0; only ~33 training examples. |
| `ses_0e92c1523ffepJfa6dVTqzYdCa` | A | Complete project using kleenhand.md | Falsely claimed PID 6877 running. |
| `ses_14655c5e3ffedVq2vCzwqqzEup` | F | Concerns about AI agent cheating | Agreed to train honestly on 10 SWA resources. |
| `ses_155dd6af8ffekYYXldimJRnCGj` | G | Explore training pipeline code | Identified 3 training scripts; base-model mismatch (cased vs uncased). |
| `ses_167aacf62ffeDLFxLQh1pD3VVg` | G | LoRA training vs production 0.43 F1 | Plan to run LoRA only if F1 > 0.43 on held-out real data. |
| `ses_167acb83cffe49VU1lhkjiW3Ee` | G | 10-week roadmap | Phase 0 clean-slate tasks; requires manual annotation of 40 RFQs. |

**Detailed training findings:**

1. **LoRA real-only training audit (A):**
   - PID 6877: **Not alive**.
   - Planned epochs: 15; reached: epoch 2.0 (global_step 110 of 825).
   - Latest checkpoint: `checkpoint-110`; best checkpoint: `checkpoint-55` (best_global_step 55).
   - Best eval F1: 0.0146 (1.46%); final eval F1: 0.0.
   - Training loss: 6.63 → 1.42; eval loss: 2.78 → 0.95.
   - Verdict: Not converged and not usable. With only ~33 training examples after 85/15 split, model overfits / learns background tokens.
   - Data-source audit: `data/real_rfqs/annotations/gold_annotations.json` (20 docs) + `data/annotations/verified/*.json` (19 docs, all `human_verified: true`) = 39 real/human-verified docs. Silver/pseudo paths skipped by default.
   - Recommendation: Do not resume. Restart only after Gate 2 supplies ≥30 row-gold docs / ≥1,000 verified sentences. Keep production NER pattern-based.

2. **Contaminated / un-audited checkpoints (A):**

| Checkpoint | Issue |
|---|---|
| `models/rfq2boq-ner-lora-v5/` | Trained on `data/annotations/pseudo_labeled_clean.json` (machine-labeled); not quarantined. |
| `models/rfq2boq-ner-lora-v2/` | Un-audited; provenance unknown. |
| `models/rfq2boq-ner-lora-v3/` | Un-audited; provenance unknown. |
| `models/rfq2boq-ner-lora-v4/` | Un-audited; provenance unknown. |
| `models/rfq2boq-ner-lora-swa10/` | Un-audited; provenance unknown. |

Suggested action: Move `rfq2boq-ner-lora-v5/` (and preferably v2/v3/v4) into `models/quarantine/` and add provenance cards.

3. **Training scripts referenced:**
   - `scripts/train_lora_ner_real_only.py`: Silver and pseudo labels quarantined by default; loads only gold + `data/annotations/verified/*.json` unless env flags set. (Modified in A.)
   - `scripts/convert_to_bioes.py`: Added strict provenance-aware `_is_swa_sacred()` guard to keep SWA sacred docs out of train/val. (Modified in A.)
   - `scripts/train_lora_ner.py`: Trains LoRA adapter on `data/real_rfqs/annotations/gold_annotations.json` excluding SWA files; base model `models/rfq2boq-ner-real-only-v2/final_model`; r=16, alpha=32, dropout=0.1; target modules `query`, `value`; 20 epochs; output `models/rfq2boq-ner-lora-v2/`. (Explored in G.)
   - `src/nlp/train_ner.py`: Original BERT fine-tuning on synthetic `data/nerAnnotations.json` (legacy, not found). (Explored in G.)
   - `src/nlp/ner/trainer.py`: Custom BiLSTM-CRF trainer. (Explored in G.)

4. **10-week roadmap (G):**
   - Phase 0 (Week 1): Clean slate — strip filename hacks, remove LoRA wiring from `src/nlp/pipeline.py`, archive dead models, audit training scripts for SWA leakage, consolidate handoff docs, restore corrupted rowgold, add CI gate `make verify`, branch discipline.
   - Phase 1 (Weeks 2-3): Insulation-domain training data — filter 168 `additional_real/` files for insulation keywords, annotate 80 train + 20 val + 20 test files (~5000 entities).
   - Phase 2 (Week 4): Clean model training from scratch (no pre-trained RFQ2BOQ weights) → F1 > 0.60.
   - Phase 3 (Week 5): Robust pipeline — pure header inference, improved PDF table handling, section classifier, BOQ assembly.
   - Phase 4 (Week 6): Honest evaluation — 10 SWA held-out XLSX ≥80%, PDF ≥50% row-match; entity F1 ≥0.70; 30 unseen files ≥80% produce ≥3 valid rows.
   - Phase 5 (Weeks 7-8): Iterate.
   - Phase 6 (Week 9): Production — CLI, Streamlit UI, Docker, CI/CD.
   - Phase 7 (Week 10): Handover.

### 4.7 Documentation / Repo Hygiene

| Session | Batch | Focus | Files touched | Commit / outcome |
|---|---|---|---|---|
| `ses_0ed1e144effe19989GAriuUQdy` | A | Consolidate handoff files | `HANDOFF.md`, moved 5 files to `attic/` | Consolidated `HANDOFF.md` (289 lines). |
| `ses_0ed24165fffeROPQ4ohziwXQ5B` | A | Gold spot-check report | `scripts/gold_spotcheck_report.py`, `results/gold_spotcheck_report.md` | 168 insulation entries checked. |
| `ses_10252f5f6ffe22OwrDdIVrwya2` | B | Final honest project status (Lane A) | `results/PROJECT_HONEST_STATUS_2026-06-25.md` | Commit `2407fab`. |
| `ses_102f4b503ffeMAjBB5eagKAf1v` | C | Lane A merge audit C/D/E | `results/lane_merge_audit_2026-06-22.md` | Commit `c0a7477`. |
| `ses_1265a99deffe5aXI1BUOhOjZ6K` | E | Repo hygiene fixes: restore PDFs, update docs, rebuild manifest | `data/real_rfqs/reference_real/*.pdf` (154), `data/real_rfqs/reference_real/README.md`, `data/real_rfqs/swa_enquiries/manifest.csv`, `MASTER_HANDOFF.md` | Commit with 155 files. |
| `ses_148f386efffeFhGl97ZKifyHpx` | F | NW-06 Repo Hygiene & Docs cleanup | 0 (planning) | Honest status report; 6 owner-only blockers. |

**Detailed docs/hygiene changes:**

1. **Handoff consolidation (A):** Created `HANDOFF.md`; moved `HANDOFF_FOR_NEXT_AGENT.md`, `MASTER_HANDOFF.md`, `COMPLETE_PROJECT_HANDOFF.md`, `FINAL_ORCHESTRATION.md`, `PROJECT_MAP.md` to `attic/` via `git mv`. Kept `CLAUDE.md` and `AGENTS.md` separate.

2. **Repo hygiene commit (E, 155 files):** Commit message `fix(nw06): restore reference PDFs, fix MASTER_HANDOFF paths, rebuild manifest.csv`. Restored 154 real reference PDFs from `attic/data_purged_2026_06_11/additional_real/` to `data/real_rfqs/reference_real/`. Created `data/real_rfqs/reference_real/README.md`: "These are real (non-synthetic) reference PDFs for eval/demo. NOT training data. NOT SWA enquiries. Source: SWA project materials." Rebuilt `data/real_rfqs/swa_enquiries/manifest.csv` with columns `id`, `client`, `filename`, `type`, `sha256`; cataloged 18 files. Fixed `MASTER_HANDOFF.md` path references (`src/ingest/xlsx_pipeline.py` → `src/pipeline_xlsx.py`) and added Python 3.11–3.13 note.

3. **NW-06 repo hygiene planning (F):** Task file `tasks/NW06_repo_hygiene_and_docs.md`. Requested steps:
   - Create `data/real_rfqs/reference_real/` from genuinely real non-SWA files only.
   - Port phase8 prompts: `git checkout main-clean -- prompts/phase8/`, `git mv prompts/phase8 prompts/archive/phase8_sprint_2026-06-03/`.
   - Fix `MASTER_HANDOFF.md`.
   - Fix `deliverables/slides/DEMO_SCRIPT.md` paths.
   - Rebuild `manifest.csv` to list all 19 SWA source files.
   - Run `make verify`.
   - Constraints: FORBIDDEN to restore synthetic data, merge `main-clean` code (prompts only), touch gold, or rewrite `HANDOFF.md` numbers.
   - Honest status: code done, project NOT complete; owner-only blockers: push commits, rotate GitHub token, human-verify 9 gold pairs, get ~100 real PDFs, rebuild venv (Python 3.14 → 3.11–3.13), decide multi-qty rule.

4. **Manifest.csv row-count discrepancy:** BATCH_E reports 18 SWA files catalogued; BATCH_F planned for 19. This is a contradiction to resolve.

5. **Reference_real restoration scope conflict:** BATCH_E committed 154 restored PDFs; BATCH_F planned only a small subset. Verify actual directory contents.

---

## 5. Complete File Manifest

This manifest consolidates every production source file, script, test, data/ontology file, model checkpoint, result/report, documentation file, and build/config file referenced across all 63 sessions.

### 5.1 Production source code

- `src/pipeline.py`
- `src/pipeline_xlsx.py`
- `src/boq_generator.py`
- `src/logging_config.py`
- `src/unit_normalization.py`
- `src/ingest/pdf_extractor.py`
- `src/ingest/table_extractor.py`
- `src/ingest/ocr_processor.py`
- `src/ingest/preprocessor.py`
- `src/ingest/layout_analyzer.py`
- `src/ingest/pdf_extractor_bbox.py`
- `src/ingest/xlsx_parser.py`
- `src/ingest/text_boq_extractor.py`
- `src/preproc/document_structure.py`
- `src/preproc/sections.py`
- `src/preproc/normalize.py`
- `src/preproc/sentence.py`
- `src/nlp/pipeline.py`
- `src/nlp/catalog_matcher.py`
- `src/nlp/train_ner.py`
- `src/nlp/patterns/dictionary.py`
- `src/nlp/patterns/regex_patterns.py`
- `src/nlp/patterns/gem_catalog.py`
- `src/nlp/ner/bert_ner.py`
- `src/nlp/ner/trainer.py`
- `src/nlp/ner/dataset.py`
- `src/nlp/ner/inference.py`
- `src/ontology/loader.py`
- `src/domain/models.py`
- `src/domain/boq_assembler.py`
- `src/domain/validator.py`
- `src/domain/confidence.py`
- `src/domain/variance.py`
- `src/domain/risk_engine.py`
- `src/domain/xlsx_column_mapper.py`
- `src/rules/units.py`
- `src/rules/conflict.py`
- `src/rules/conflict_strategies.py`
- `src/rules/scope_gap.py`
- `src/rules/standards.py`
- `src/risk/engine.py`
- `src/confidence/calibration.py`
- `src/export/excel_generator.py`
- `src/export/json_formatter.py`
- `src/export/csv_exporter.py`
- `src/export/report.py`
- `src/export/risk_report.py`
- `src/api/main.py`
- `src/api/schemas.py`
- `src/api/dependencies.py`
- `src/api/routes/upload.py`
- `src/api/routes/review.py`
- `src/cli/main.py`
- `config/constants.py`
- `config/settings.py`

### 5.2 Scripts

- `scripts/fidelity_audit.py`
- `scripts/measure_fidelity.py`
- `scripts/train_lora_ner_real_only.py`
- `scripts/train_lora_ner.py`
- `scripts/convert_to_bioes.py`
- `scripts/intake_tender.py`
- `scripts/review_annotation.py`
- `scripts/eval_honest_v2.py`
- `scripts/eval_honest.py`
- `scripts/eval_honest_rows.py`
- `scripts/eval_catalog_match.py`
- `scripts/gold_spotcheck_report.py`
- `scripts/draft_insulation_rowgold.py`
- `scripts/extract_insulation_corpus.py`
- `scripts/run_insulation_batch.py`
- `scripts/check_gold_provenance.py`
- `scripts/check_eval_hacks.py`
- `scripts/annotate_rfq.py`
- `scripts/build_row_gold.py`
- `scripts/validate_product.py`
- `scripts/demo.py`

### 5.3 Tests

- `tests/unit/test_anti_cheat.py`
- `tests/unit/test_boq_assembler.py`
- `tests/unit/test_pipeline_xlsx.py`
- `tests/unit/test_final_model.py`
- `tests/unit/test_validator.py`
- `tests/unit/test_ui_app.py`
- `tests/unit/test_convert_to_bioes.py`
- `tests/unit/test_intake.py`
- `tests/unit/test_catalog_matcher.py`
- `tests/unit/test_patterns.py`
- `tests/unit/test_gem_catalog.py`
- `tests/unit/test_ontology_loader.py`
- `tests/unit/test_units_unified.py`
- `tests/unit/test_units_canonical.py`
- `tests/unit/test_models.py`
- `tests/unit/test_export_validation.py`
- `tests/unit/test_pipeline_xlsx_fidelity.py`
- `tests/integration/test_xlsx_row_preservation_e2e.py`
- `tests/integration/test_self_attack.py`
- `tests/integration/test_real_rfq_corpus.py`
- `tests/integration/test_insulation_tender_timeouts.py`
- `tests/integration/test_adani_structure.py`
- `tests/integration/test_insulation_batch_no_crash.py`
- Held-out provenance tests
- Intake span-guard tests
- (OCR and BERT NER unit tests are skipped by default per project config.)

### 5.4 Data / ontology / annotations / gold

- `data/real_rfqs/annotations/gold_annotations.json`
- `data/real_rfqs/annotations/gold_annotation_template.json`
- `data/real_rfqs/annotations/manifest.csv`
- `data/real_rfqs/annotations/real_rfq_samples.json`
- `data/annotations/verified/*.json`
- `data/annotations/pseudo_labeled_clean.json`
- `data/real_rfqs/annotated/rfq_sample_simple.json`
- `data/real_rfqs/annotated/rfq_sample_medium.json`
- `data/real_rfqs/annotated/rfq_sample_complex.json`
- `data/real_rfqs/annotated/cpwd_Guidelines...json`
- `data/real_rfqs/annotated/ireps_bc341034058b.json`
- `data/real_rfqs/annotated/ireps_2724bb1eff78.json`
- `data/real_rfqs/annotated/delhi_pwd_Tender.json`
- `data/real_rfqs/swa_gem_catalog_full.json`
- `data/ontology/materials.json`
- `data/ontology/standards.json`
- `data/ontology/units.json`
- `data/ontology/insulation_materials.json`
- `data/ontology/insulation_standards.json`
- `data/ontology/insulation_units.json`
- `data/real_rfqs/gold/rows/insul_01_tender.rowgold.json`
- `data/real_rfqs/gold/rows/insul_02_swpl.rowgold.json`
- `data/real_rfqs/gold/rows/insul_03_boq_page.rowgold.json`
- `data/real_rfqs/gold/rows/insul_04_boq_page_003.rowgold.json`
- `data/real_rfqs/gold/rows/insul_05_copy_of_boq.rowgold.json`
- `data/real_rfqs/gold/rows/insul_06_insulation_boq_1.rowgold.json`
- `data/real_rfqs/gold/rows/insul_07_insulation_boq_2.rowgold.json`
- `data/real_rfqs/gold/rows/insul_08_boq_insulation_compliance.rowgold.json`
- `data/real_rfqs/gold/rows/insul_09_pipe_insulation_compliance.rowgold.json`
- `data/real_rfqs/gold/rows/_insul_draft_summary.json`
- `data/real_rfqs/gold/rows/01_gsecl.rowgold.json`
- `data/real_rfqs/gold/rows/02_isro_vssc.rowgold.json`
- `data/real_rfqs/gold/rows/03_zydus_matoda.rowgold.json`
- `data/real_rfqs/gold/rows/04_adani.rowgold.json`
- `data/real_rfqs/gold/rows/05_zydus_animal_pharmez.rowgold.json`
- `data/real_rfqs/gold/rows/06_avante.rowgold.json`
- `data/real_rfqs/gold/rows/07_grew_solar_narmadapuram.rowgold.json`
- `data/real_rfqs/gold/rows/08_sael.rowgold.json`
- `data/real_rfqs/gold/rows/09_gem_bid_7439924.rowgold.json`
- `data/real_rfqs/gold/rows/10_gem_bid_7552777.rowgold.json`
- `data/real_rfqs/swa_enquiries/01_*` through `10_*`
- `data/real_rfqs/swa_enquiries/ingested/04_adani.json`
- `data/real_rfqs/swa_enquiries/ingested/09_gem_bid_7439924.json`
- `data/real_rfqs/swa_enquiries/ingested/10_gem_bid_7552777.json`
- `data/real_rfqs/swa_enquiries/manifest.csv`
- `data/real_rfqs/raw/insulation_hvac/` (11 tender PDFs + 9 BOQ refs)
- `data/real_rfqs/additional_real/` (168 PDFs per explore session)
- `data/real_rfqs/reference_real/*.pdf` (154 restored PDFs)
- `data/real_rfqs/reference_real/README.md`
- `data/real_rfqs/corpus_manifest.json` (proposed, not yet written)
- `data/incoming/40_vssc_acoustic_boq.xlsx`
- `data/incoming/R3_zydus_matoda_osd.xlsx`
- `data/specifications/` (recursive)
- `data/incoming/` (recursive)
- `data/real_rfqs/raw/` (recursive)
- `data/real_rfqs/raw/synthetic_archive/`
- `resources/Specifications.rar`
- `resources/Specifications/` (53 spec PDFs)

### 5.5 Models / checkpoints

- `models/rfq2boq-ner-lora-real/` (checkpoint-55, checkpoint-110)
- `models/rfq2boq-ner-lora-v5/` (contaminated — pseudo-labeled data)
- `models/rfq2boq-ner-lora-v2/`
- `models/rfq2boq-ner-lora-v3/`
- `models/rfq2boq-ner-lora-v4/`
- `models/rfq2boq-ner-lora-swa10/`
- `models/rfq2boq-ner-real-only-v2/final_model`
- `models/ner_model/final_model/`
- `models/ner_model/tokenizer/`
- `models/ner_model/checkpoint-26/`
- `models/rfq2boq-ner-genuine-v1-lora/` (planned)
- `models/quarantine/` (suggested, may not exist)

### 5.6 Results / reports

- `results/fidelity_audit_summary.txt` (stale)
- `results/eval_catalog_match.json`
- `results/gold_spotcheck_report.md`
- `results/PROJECT_HONEST_STATUS_2026-06-25.md`
- `results/lane_merge_audit_2026-06-22.md`
- `results/insulation_eval_2026-06-26.md`
- `results/insulation_eval_raw.json`
- `results/insulation_pipeline_output.json`
- `results/insulation_batch_run_2026-06-22.json`
- `results/insulation_batch_run_2026-06-22.md`
- `results/honest_baseline_2026-06-22.md`
- `results/eval_honest.json`
- `results/eval_honest_rows.json`
- `results/eval_honest_rows_2026-06-18.txt`
- `results/new_tenders_2026-06-18.json`

### 5.7 Documentation

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `HANDOFF.md` (consolidated)
- `ULTIMATE_HANDOFF.md` (this file)
- `PROJECT_MAP.md` (moved into `HANDOFF.md` / `attic/`)
- `HANDOFF_FOR_NEXT_AGENT.md` (moved to `attic/`)
- `MASTER_HANDOFF.md` (moved to `attic/`; modified in E)
- `COMPLETE_PROJECT_HANDOFF.md` (moved to `attic/`)
- `FINAL_ORCHESTRATION.md` (moved to `attic/`)
- `kleenhand.md`
- `docs/ANNOTATION_WORKFLOW.md`
- `docs/ULTRA_PLAN_WEEK_2026-06-22.md`
- `docs/SCOPE_GUARD.md`
- `docs/conventions.md`
- `docs/wave_status.md`
- `docs/architecture.md`
- `docs/api.md`
- `docs/PHASE8_UNIFIED_TIMELINE_AND_FLOW.md`
- `docs/CORPUS_FILTER.md` (planned)
- `docs/TRAINING_CORPUS.md` (planned)
- `docs/ANNOTATION_GUIDELINES.md` (planned)
- `prompts/wave4/INDEX.md`
- `prompts/wave4/TASK_TEMPLATE.md`
- `prompts/archive/phase8_sprint_2026-06-03/` (planned)
- `tasks/NW06_repo_hygiene_and_docs.md`

### 5.8 Build / config / logs

- `Makefile`
- `.gitignore`
- `.pre-commit-config.yaml`
- `pyproject.toml`
- `.env.example`
- `docker-compose.yml`
- `Dockerfile`
- `deployment/`
- `/tmp/train_lora_real.log`

---

## 6. Commit Registry

This registry preserves every commit hash, branch, message, originating session(s), and verification status found across both Level-2 merges.

| Hash | Branch | Message | Session(s) | Status |
|---|---|---|---|---|
| `0a91470` | `phase8-clean-slate` | Base commit at audit time | A | confirmed base |
| `2407fab` | `phase8-laneA` | `docs: final honest project status (A6)` | B `ses_10252f5f6ffe22OwrDdIVrwya2` | confirmed |
| `88e92a6` | `phase8-laneB` | `feat(data): draft row-gold for remaining insulation BOQ pairs (B2)` | B `ses_0fdafba93ffe3VQZOnW49H6WvS` | confirmed in B, disputed in C/D |
| `73489c8` | `phase8-laneB` | `feat(data): extract insulation corpus + draft row-gold for 2 pairs (B1)` | C `ses_102c9870bffeiw9AtrrRkADdM1` | confirmed |
| `3530731` | `phase8-laneC` | `fix(ingest): structure-first routing fixes insulation tender timeouts (C7)` | B `ses_0fd7cbb45ffesQQ71OIbB5fK6h` et al. | confirmed |
| `8f9e35e` | `phase8-laneC` | Lane C structure-first extraction R4 (5 files, 99+/−4) | D `ses_110081fc7ffeGxIasPR52AvQro` | confirmed |
| `7a2007c` | `phase8-laneD` | `feat(nlp): integrate insulation ontology+GeM gazetteer into NER (D3)` | B `ses_0fdafb0abffeoBynJcvQwOZBAf` | confirmed |
| `b38db2c` | `phase8-laneD` | `feat(ontology): GeM gazetteer + insulation domain ontology (D1-D2)` | C `ses_102f4a325ffelqG9k9gJhkVa1o` / `ses_102c97e68ffeRWt9w2TSsVFyV5` | confirmed |
| `396d884` | `phase8-laneE` | `eval: honest insulation-domain row-level evaluation (E7)` | B `ses_0fdafa71bffecXT75Te9NUysHE` | confirmed |
| `c0a7477` | `phase8-laneA` | `audit: lane merge audit A5 — C/D/E verdict` | C `ses_102f4b503ffeMAjBB5eagKAf1v` | confirmed |
| `b49f62d` | `phase8-laneA` | `audit: re-audit lane D after commit b38db2c` | C `ses_102c97e68ffeRWt9w2TSsVFyV5` | confirmed |
| `c923e2a` | (not specified) | `fix: 07 Grew Solar missing row, 88.9%->100%` | E `ses_1264a3a58ffeDzcnix7Aumg4Gl` | confirmed |
| `b81b440` | (not specified) | `refactor(nw05): consolidate all unit normalizers into src/rules/units.py` | E `ses_1265af65bffeL58pbBwiAZOMgs` | confirmed |
| `c001ef8` | (not specified) | `docs(gold): flag 05_zydus_animal gold as unreliable - all qty=0, needs human review` | E `ses_12693d3a5ffe4g4hp2xGkYTSBt` | confirmed |
| `6fc9bfa` | (not specified) | `data: run pipeline on 2 new incoming tenders, record results` | E `ses_12693d3a5ffe4g4hp2xGkYTSBt` | confirmed |
| `0739ecf` | (not specified) | `feat(gem): ingest SWA published GeM catalog with full specs and validate_gem_extraction()` | E `ses_12693fee0ffeljUnjpZfU7KhPP` | confirmed |
| (nw06 hygiene commit) | `phase8-clean-slate` | `fix(nw06): restore reference PDFs, fix MASTER_HANDOFF paths, rebuild manifest.csv` | E `ses_1265a99deffe5aXI1BUOhOjZ6K` | confirmed, 155 files |
| (honest eval commit) | (not specified) | `eval: updated honest baseline after nw05/nw06/gem fixes` | E `ses_1264a228effekBULGv67DcUhb8` | confirmed |
| (ISRO gold note commit) | (not specified) | `fix(nw-isro): fix 02 ISRO VSSC missing 2 rows, F1 83.3%->target 100%` | E `ses_1265ac970ffeFnUi7jnm7d994s` | confirmed |
| (Zydus non-zero qty commit) | (not specified) | `fix(05-zydus): pipeline correctly extracts non-zero qty rows from multi-column XLSX` | E `ses_1264a012affeRHj6w08eOvWTpx` | confirmed |
| `2d3bf6f` | (not specified) | `PHASE 6+7: Production hardening + honest handoff` | G `ses_167aacf62ffeDLFxLQh1pD3VVg` | reported as Git HEAD |
| (unconfirmed) | `phase8-laneC` | `feat(ingest): structure-first routing improves Adani PDF extraction (C6)` | C `ses_102f4aa1cffesD2HuwJap6tx0Y` | unconfirmed |
| (unconfirmed) | `phase8-laneE` | `eval: insulation batch run — fidelity + no-crash test (E6)` | C `ses_107a0bbecffelXrQdEq7MIz82f`, D `ses_107a43ba2ffeuIDC04zVtKIFVo` | unconfirmed |

---

## 7. Contradictions and Duplicate Work

This section preserves every contradiction, overlap, and duplicate-effort finding from both Level-2 merges, with source sessions and recommended resolution.

### 7.1 Lane B insulation row-gold status — CONTRADICTION

- **BATCH B (`ses_0fdafba93ffe3VQZOnW49H6WvS`)** reports B2 complete with commit `88e92a6`, creating `insul_03`–`insul_09` rowgold files (168 total rows).
- **BATCH C (`ses_102531233ffeMwYlu3ZxQNBFCg`)** reports B2 as truncated/incomplete, outcome unknown.
- **BATCH D (`ses_1100865ffffeXBUIp4Vx6Aidex` / dispatch `ses_1115553a6ffeR4s6IEmUn3Mg63`)** reports Lane B status: **ERROR / Timeout — needs restart**.

**Resolution needed:** Verify whether commit `88e92a6` exists and whether `insul_03`–`insul_09` files are present and committed. The timeout report in D may refer to a later restart attempt or a different sub-task (BIOES gold loop vs row-gold drafting).

### 7.2 Lane C timeout resolution — DUPLICATE / PROGRESSIVE

- **BATCH B (`ses_0fd7cbb45ffesQQ71OIbB5fK6h`)** reports structure-first routing fix with commit `3530731`, all 7 timeout files complete under 60s.
- **BATCH C (`ses_107a0bbecffelXrQdEq7MIz82f`)** reports 7 of 11 insulation tender PDFs still timed out during batch run.
- **BATCH D (`ses_110081fc7ffeGxIasPR52AvQro`)** reports Lane C R4 with commit `8f9e35e`, adding `ThreadPoolExecutor` timeout wrapper and structure extractor precision improvements.

**Interpretation:** The fixes are progressive. B's structure-first routing handles the no-BOQ case; D R4 adds timeout wrapper and section-heading precision. The C batch run may have occurred before D R4 was applied or in a different worktree.

### 7.3 Adani extraction — CONTRADICTORY FRAMING

- **BATCH C (`ses_102f4aa1cffesD2HuwJap6tx0Y`)** reports Adani "12 vs 45" discrepancy resolved without code changes; structure-first extractor already working; 45 rows matching gold.
- **BATCH A (`ses_0d3ad3857ffe5L8gKTNFjz04Uw`)** reports `04_adani` count fidelity 100% but 28/45 rows low-confidence.

**Both can be true:** row count matches gold, but many rows have missing quantities or confidence < 0.5. Quality is low even though count fidelity is high.

### 7.4 05_zydus_animal — CONTRADICTORY NUMBERS

- **BATCH A** reports 20 source rows, 48 extracted rows (over-capture).
- **BATCH D** reports 05 Zydus Animal: 20 rows extracted, gold has 20 entries (row count matches).
- **BATCH B** notes `05_zydus_animal` item_no validation error as HIGH priority.
- **BATCH E** confirms the source XLSX has 20 non-zero TOTAL rows and the pipeline now extracts exactly 20 items; existing gold has 67 entries all with `qty=0` and is flagged unreliable.

**Resolution needed:** Verify current state of `05_zydus_animal` extraction and gold. Numbers differ across batches because different pipeline versions / fixes were applied and the gold file is auto-generated/not human-verified.

### 7.5 LoRA training PID 6877 — CONTRADICTION

- **BATCH A older session (`ses_0e92c1523ffepJfa6dVTqzYdCa`)** claimed PID 6877 running, 13% done, ETA 10–15 h.
- **BATCH A audit (`ses_0d3ad2095ffewtQmOj1SE6IOd2`)** confirmed PID 6877 **dead**, training died at epoch 2 with F1 collapsed to 0.

**Resolution:** The audit is later and authoritative; training is dead and not usable.

### 7.6 Lane D ontology commits — CROSS-REFERENCE

- **BATCH B (`ses_0fdafb0abffeoBynJcvQwOZBAf`)** commit `7a2007c` integrates insulation ontology into NER.
- **BATCH C (`ses_102f4a325ffelqG9k9gJhkVa1o`)** implied commit `b38db2c` creates/updates insulation ontology JSON files and GeM gazetteer.
- **BATCH D (`ses_11007b70fffekB26BFLAMNlTAz`)** is a later RUNNING session mining 53 spec PDFs.

**Interpretation:** `b38db2c` likely precedes `7a2007c`; D is a continuation/enrichment effort.

### 7.7 `measure_fidelity.py` vs sacred-10 audit — APPARENT CONTRADICTION

- **BATCH A sacred-10 audit** reports 100% count-level fidelity.
- **BATCH A `measure_fidelity.py` fix** reports 0 PASS, 10 FAIL, overall 27.9%.

**Resolution:** The fixed `measure_fidelity.py` now fails on dropped rows and over-capture (>110%), which the sacred-10 audit caps at 100%. They measure different things: the audit reports "did we extract at least as many rows as source?"; the fixed harness reports "did we exactly match source without drops or over-capture?".

### 7.8 Insulation batch run deliverables — DUPLICATE

- **BATCH C (`ses_107a0bbecffelXrQdEq7MIz82f`)** and **BATCH D (`ses_107a43ba2ffeuIDC04zVtKIFVo`)** both target the same E6 deliverables (`scripts/run_insulation_batch.py`, `results/insulation_batch_run_2026-06-22.*`, `tests/integration/test_insulation_batch_no_crash.py`).
- C reports partial completion (11 attempted, 7 timeouts); D reports no completion captured.

**Likely explanation:** C's session produced the deliverables; D's session was a separate dispatch that did not finish.

### 7.9 `data_only=True` formula-cell handling — DUPLICATE WORK

- **BATCH E sessions `ses_126941f4efferQ3FEVE3JnlSX1` and `ses_126959a48ffe0Xj8aFjythvq3g`** independently verified that `openpyxl.load_workbook()` is called with `data_only=True` in `src/pipeline_xlsx.py:56` and `src/ingest/xlsx_parser.py:31`.
- Both concluded no code changes were required; no commits made.

### 7.10 `reference_real/` restoration scope conflict

- **BATCH E (`ses_1265a99deffe5aXI1BUOhOjZ6K`)** committed 154 restored PDFs to `data/real_rfqs/reference_real/`.
- **BATCH F (`ses_148f386efffeFhGl97ZKifyHpx`)** planned to restore only a small subset of genuinely real non-SWA files: `rfq_road_RFQ9740_050.pdf`, the 2 `ireps_*.pdf`s, `delhi_pwd_*.pdf`, `cpwd_Guidelines_*.pdf`.

**Resolution needed:** Verify actual `data/real_rfqs/reference_real/` contents against the planned subset and the BATCH_E commit.

### 7.11 `manifest.csv` row-count mismatch

- **BATCH E (`ses_1265a99deffe5aXI1BUOhOjZ6K`)** reports 18 SWA files catalogued.
- **BATCH F (`ses_148f386efffeFhGl97ZKifyHpx`)** planned for 19 SWA source files.

**Resolution needed:** Count current rows in `data/real_rfqs/swa_enquiries/manifest.csv` and reconcile with actual SWA enquiry folders.

### 7.12 `HANDOFF.md` vs `MASTER_HANDOFF.md` confusion

- **BATCH E (`ses_1265a99deffe5aXI1BUOhOjZ6K`)** reports modifying `MASTER_HANDOFF.md`.
- **BATCH G (`ses_167aacf62ffeDLFxLQh1pD3VVg`)** reports `HANDOFF.md` as modified but not committed.

**Resolution needed:** Run `git status` to verify current uncommitted state of `HANDOFF.md` and `MASTER_HANDOFF.md`.

### 7.13 Zydus gold-quality inconsistency

- **BATCH E** flags `05_zydus_animal_pharmez` gold as unreliable (67 entries, all `qty=0`, auto-generated).
- **BATCH G** notes `03_zydus_matoda` is `human_verified=True` with 100% match and will likely trigger anti-cheat failure.

**Resolution needed:** Human-review both gold files. Do not trust F1 for 05 until manually verified. Investigate whether 03's 100% match is genuine or a leakage/hack.

### 7.14 Honest-evaluation metric mismatch

- **BATCH E** uses row-level macro F1 (`scripts/eval_honest_rows.py`) and reports macro F1 92.1%.
- **BATCH G** references entity-level micro F1 (`scripts/eval_honest.py`) and reports ~42.6%.
- **L2A** reports entity-level macro F1 44.1%.

**Resolution:** These are different scripts measuring different things. Do not compare directly. Always label which script produced a metric.

### 7.15 Honest-evaluation timeout

- **BATCH E (`ses_1264a228effekBULGv67DcUhb8`)** reports `scripts/eval_honest_rows.py` timed out after 2 minutes; final numbers restored from backup.
- This conflicts with the claim that the honest baseline is fully trustworthy until re-run successfully.

### 7.16 `make verify` / "code done" vs pending Phase 0 tasks

- **BATCH F (`ses_148f386efffeFhGl97ZKifyHpx`)** reports `make verify` passes and the tree is clean.
- **BATCH G (`ses_167acb83cffe49VU1lhkjiW3Ee`)** lists Phase 0 clean-slate tasks as still pending (filename hacks, LoRA wiring removal, dead model archive, rowgold restore, CI gate, branch discipline).

**Resolution needed:** Re-run forbidden checks and `make verify` to confirm current state.

### 7.17 Training-data quantity gap — CONSENSUS

All batches agree: production PDF NER F1 is ~14.2% and will not improve without real human-annotated PDFs from SWA Sales/Jineth/Softnil. No contradiction; this is the central blocker.

---

## 8. Blockers and Running Processes

### 8.1 Confirmed blockers

| # | Blocker | Severity | Source Sessions | Notes |
|---|---|---|---|---|
| 1 | **LoRA real-only model not usable** — training died at epoch 2 with F1 0. Need ≥30 row-gold docs / ≥1,000 verified sentences before retraining. | High | A `ses_0d3ad2095ffewtQmOj1SE6IOd2` | Keep production NER pattern-based. |
| 2 | **Anti-cheat red flags in uncommitted code** — silent exception swallowing, hardcoded confidences, fidelity audit self-reference. Must fix before commit. | High | A `ses_0d3acedf6ffeSO63IwKxY1LOhE` | Located in `src/pipeline.py`, `src/pipeline_xlsx.py`, `src/nlp/patterns/dictionary.py`, `scripts/fidelity_audit.py`. |
| 3 | **05_zydus_animal over-capture / validation error / unreliable gold** — numbers vary across batches (48 vs 20 vs 67 gold entries); item_no validation error. | High | A, B, D, E | Gold has 67 entries all `qty=0`; pipeline now extracts 20 non-zero TOTAL rows. |
| 4 | **04_adani quality** — count-level 100%, but 28/45 rows low-confidence / missing quantities. | Medium-High | A, C | Quality low despite count match. |
| 5 | **Contaminated / un-audited checkpoints** — `rfq2boq-ner-lora-v5/` uses pseudo labels; v2/v3/v4/swa10 lack provenance. | High | A | Suggest moving to `models/quarantine/`. |
| 6 | **Lane B status unclear** — BATCH B says B2 complete; BATCH D says Lane B ERROR/timeout needs restart. | Medium | B, D | Verify commit `88e92a6` and files. |
| 7 | **Lane D ontology mining still RUNNING** in D (`ses_11007b70fffekB26BFLAMNlTAz`). | Medium | D | Mining 53 spec PDFs. |
| 8 | **Lane E6 insulation batch run completion unconfirmed** in D. | Medium | C, D | Verify deliverables and no-crash test. |
| 9 | **9 insulation gold pairs unverified** — all 168 entries `human_verified: false`. | High | A, B, C, D | Owner must review. |
| 10 | **Corpus manifest not yet written** — only proposed in A. | Low | A `ses_0d3ad0628ffeTgnlCBLzMf3biy` | Create `data/real_rfqs/corpus_manifest.json`. |
| 11 | **Leaked GitHub token in remote URL**. | High | A `ses_0e92c1523ffepJfa6dVTqzYdCa`, F `ses_148f386efffeFhGl97ZKifyHpx` | Remote URL contains `x-access-token:gh…`. |
| 12 | **System Python 3.14 breaks pipelines** — must use `/usr/local/bin/python3.11` or `.venv-lora` (Python 3.12). | High | A, B, C, D, E, F | Project charter requires 3.11–3.13. |
| 13 | **`measure_fidelity.py` 04_adani `doc_map` omits one PDF page**. | Medium | A | Causes under-reporting. |
| 14 | **02 ISRO VSSC cannot reach 100% F1 automatically** — gold is `human_verified: false` and contains 2 entries the pipeline correctly filters. | Medium | E `ses_1265ac970ffeFnUi7jnm7d994s` | Human must remove entries or confirm zero-qty validity. |
| 15 | **03_zydus_matoda anti-cheat failure risk** — only file with `human_verified=True` and 100% match. | Medium | G `ses_167acb83cffe49VU1lhkjiW3Ee` | Investigate for leakage/hack. |
| 16 | **~200+ commits only on local laptop** — risk of total loss. | High | F `ses_148f386efffeFhGl97ZKifyHpx` | Owner must push. |
| 17 | **Multi-qty business rule undecided** — when 1 material has 9 qty columns, emit 1 row or 9 rows? | Medium | F `ses_148f386efffeFhGl97ZKifyHpx` | SWA must decide. |
| 18 | **Honest evaluation timeout** — `scripts/eval_honest_rows.py` timed out; numbers from backup. | Medium | E `ses_1264a228effekBULGv67DcUhb8` | Re-run when performance fixed. |
| 19 | **Dangling prompt links** in `docs/PHASE8_UNIFIED_TIMELINE_AND_FLOW.md`. | Low | G `ses_167acb83cffe49VU1lhkjiW3Ee` | Repoint to `prompts/wave4/` or remove. |
| 20 | **Synthetic archive not yet moved / gitignored** — planned `git mv data/synthetic_archive/ attic/synthetic_corpus_archived/`. | Low | G `ses_167acb83cffe49VU1lhkjiW3Ee` | Pending Phase 0. |

### 8.2 Running / incomplete processes

| Process | Status | Source | Notes |
|---|---|---|---|
| LoRA real-only training PID 6877 | **DEAD** | A `ses_0d3ad2095ffewtQmOj1SE6IOd2` | Training died at epoch 2. |
| Python 3.14 data query PID 19087 | Unknown (non-critical) | A | Non-critical. |
| Lane D ontology mining (`ses_11007b70fffekB26BFLAMNlTAz`) | **RUNNING** | D | Mining 53 spec PDFs in `resources/Specifications/`. |
| Lane E robustness/fidelity (`ses_1100731e2ffeLO6D49XlhnJhBh`) | **RUNNING** | D | Reported passing `make verify`. |
| Lane B gold annotation loop (`ses_1100865ffffeXBUIp4Vx6Aidex`) | **ERROR / Timeout — needs restart** | D | Per dispatch session `ses_1115553a6ffeR4s6IEmUn3Mg63`. |
| OpenRouter testing | **Incomplete / abandoned** | A `ses_0f87ec8dfffeFNQxeYiOiYgGXa` | No deliverable. |

---

## 9. Uncommitted State

### 9.1 Modified files (from BATCH B and A)

- `.gitignore`
- `data/ontology/insulation_materials.json`
- `data/ontology/insulation_standards.json`
- `data/ontology/insulation_units.json`
- `data/ontology/materials.json`
- `data/real_rfqs/gold/rows/insul_01_tender.rowgold.json` through `insul_09_pipe_insulation_compliance.rowgold.json`
- `docs/ANNOTATION_WORKFLOW.md`
- `results/eval_honest.json`
- `results/eval_honest_rows.json`
- `scripts/convert_to_bioes.py`
- `scripts/fidelity_audit.py`
- `scripts/intake_tender.py`
- `scripts/review_annotation.py`
- `scripts/train_lora_ner_real_only.py`
- `src/ingest/pdf_extractor.py`
- `src/nlp/patterns/dictionary.py`
- `src/nlp/patterns/regex_patterns.py`
- `src/pipeline.py`
- `src/pipeline_xlsx.py`
- `tests/integration/test_xlsx_row_preservation_e2e.py`
- `tests/unit/test_convert_to_bioes.py`
- `tests/unit/test_intake.py`
- `tests/unit/test_pipeline_xlsx.py`

### 9.2 Untracked file

- `kleenhand.md`

### 9.3 Possibly modified/uncommitted (from BATCH G)

- `HANDOFF.md` — reported as modified but not committed by `ses_167aacf62ffeDLFxLQh1pD3VVg`.

### 9.4 Base commit at audit time

- `0a91470` on `phase8-clean-slate` (per L2A).

### 9.5 Other state notes

- L2B BATCH_E reports no uncommitted changes for its sessions; all code/data changes that required commits were committed.
- L2B BATCH_F reports no explicit uncommitted changes, but notes ~200+ commits are only on the local laptop (committed locally, not pushed).
- L2B BATCH_G reports `HANDOFF.md` modified but uncommitted.

**Verification command:** `git status` should be run immediately to reconcile these reports.

---

## 10. Anti-Cheat Status

### 10.1 Anti-cheat tests

| Source Session | Result | Details |
|---|---|---|
| `ses_11008f3a1ffeT5D3nmQGeU5edh` (D) | **27/27 PASSED** | Anti-cheat tests hardened; `make verify` passes 7 steps clean. |

### 10.2 Anti-cheat red flags requiring attention

| # | Red flag | Location | Source |
|---|---|---|---|
| 1 | Silent exception swallowing (`except Exception: pass`) | `src/pipeline.py` recovery blocks | A `ses_0d3acedf6ffeSO63IwKxY1LOhE` |
| 2 | Silent exception swallowing | `src/nlp/patterns/dictionary.py:209-210` | A `ses_0d3acedf6ffeSO63IwKxY1LOhE` |
| 3 | Hardcoded confidence score | `src/pipeline.py` recovered GeM rows `confidence=0.80` | A `ses_0d3acedf6ffeSO63IwKxY1LOhE` |
| 4 | Hardcoded confidence score | `src/pipeline_xlsx.py` rate-only rows `confidence=0.70` | A `ses_0d3acedf6ffeSO63IwKxY1LOhE` |
| 5 | Fidelity audit self-reference | `scripts/fidelity_audit.py` collapses independent source-vs-output check when rowgold exists | A `ses_0d3acedf6ffeSO63IwKxY1LOhE` |
| 6 | Potential anti-cheat failure | `03_zydus_matoda` — only file with `human_verified=True` and 100% match | G `ses_167acb83cffe49VU1lhkjiW3Ee` |

### 10.3 Anti-cheat forbidden checks (Phase 0)

From BATCH G `ses_167acb83cffe49VU1lhkjiW3Ee`:

```bash
grep -r "if filename ==" src/        # filename hacks
grep -r "_sael_scan" src/            # special cases
grep -r "100% COMPLETE" docs/        # fake claims
git status | grep -v "clean"         # dirty tree
pytest tests/ -q                     # any failure
```

These should be run before claiming the tree is clean.

### 10.4 Checks that passed (A review)

- No filename-specific hacks.
- No gold edits made to match output.
- Conventions (`src.` imports, `config.settings`, BIOES, type hints) OK.
- Relevant tests passed: `test_anti_cheat` (15), `test_convert_to_bioes` (13), `test_intake` (11), `test_xlsx_row_preservation_e2e` (9), `test_self_attack` (17).

---

## 11. Next Actions

### 11.1 Immediate (before any commit)

1. **Run `git status`** to reconcile uncommitted-state reports from L2A and L2B.
2. **Run forbidden checks** from Phase 0:
   ```bash
   grep -r "if filename ==" src/
   grep -r "_sael_scan" src/
   grep -r "100% COMPLETE" docs/
   git status | grep -v "clean"
   pytest tests/ -q
   ```
3. **Fix anti-cheat red flags** in uncommitted code:
   - Replace silent exception swallowing with proper logging/raises.
   - Replace hardcoded confidence scores with configurable thresholds from `config.settings`.
   - Fix `scripts/fidelity_audit.py` self-reference so source-vs-output check remains independent.
4. **Resolve contradictions first:**
   - Verify whether `insul_03`–`insul_09` rowgold files and commit `88e92a6` exist.
   - Verify Lane B timeout status.
   - Reconcile `05_zydus_animal` numbers (source 20, extracted 20/48, gold 67 all `qty=0`).
   - Reconcile `manifest.csv` row count (18 vs 19).
   - Verify `reference_real/` restoration scope (154 PDFs vs planned subset).

### 11.2 Short-term (this week)

5. **Replace stale `results/fidelity_audit_summary.txt`** with audited sacred-10 table plus over-capture notes.
6. **Fix `measure_fidelity.py` 04_adani `doc_map`** to include both PDF pages.
7. **Investigate 03_zydus_matoda** 100% match + `human_verified=True` for anti-cheat leakage.
8. **Human-review 9 insulation gold pairs** and flip `human_verified` to `true` where correct.
9. **Quarantine contaminated checkpoints** (`models/rfq2boq-ner-lora-v5/` and legacy v2/v3/v4) and add provenance cards.
10. **Create `data/real_rfqs/corpus_manifest.json`** per BATCH A proposal.
11. **Finalize Lane A5 merge audit** once Lane D commits.
12. **Confirm Lane E6 insulation batch run** deliverables and no-crash test pass.

### 11.3 Medium-term (requires owner)

13. **Push ~200+ local commits** to remote to prevent disk-loss catastrophe.
14. **Rotate leaked GitHub token** in remote URL.
15. **Provide ~100 real PDFs** for NER training (SWA Sales/Jineth/Softnil).
16. **Rebuild venv** to Python 3.11–3.13 (avoid system Python 3.14).
17. **Decide multi-qty business rule** (1 row vs 9 rows for 9 qty columns).
18. **Review and sign off 09/10 GeM gold files** (~30 min).
19. **Do not restart LoRA training** until Gate 2 supplies ≥30 row-gold docs / ≥1,000 verified sentences.

### 11.4 Verification

20. **Run `make verify`** after all fixes.
21. **Re-run `scripts/eval_honest_rows.py`** from scratch (not backup) to confirm honest metrics.
22. **Run `scripts/eval_honest.py`** to capture entity-level micro F1 for comparison.

---

## 12. Appendix: Raw Session Index

This appendix preserves per-session narratives in compact form so that no detail from the Level-2 merges is lost.

### A.1 Batch A raw session details

**`ses_0d3acedf6ffeSO63IwKxY1LOhE` — Review modified code changes**
- Model: kimi-k2.7-code
- Tokens: 36,119 / 3,243
- Messages: 15
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Reviewed modified code changes. Identified red flags in uncommitted code: silent exception swallowing in `src/pipeline.py` and `src/nlp/patterns/dictionary.py:209-210`; hardcoded confidence scores (`confidence=0.80` for recovered GeM rows, `confidence=0.70` for rate-only rows); `scripts/fidelity_audit.py` self-references rowgold count when rowgold exists, collapsing independent source-vs-output check. Verified no filename-specific hacks, no gold edits to match output, conventions OK. Relevant tests passed: `test_anti_cheat` (15), `test_convert_to_bioes` (13), `test_intake` (11), `test_xlsx_row_preservation_e2e` (9), `test_self_attack` (17).

**`ses_0d3ad0628ffeTgnlCBLzMf3biy` — Build corpus manifest**
- Model: kimi-k2.7-code
- Tokens: 45,950 / 8,777
- Messages: 17
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Proposed `data/real_rfqs/corpus_manifest.json`; not yet written.

**`ses_0d3ad2095ffewtQmOj1SE6IOd2` — Audit training checkpoint**
- Model: kimi-k2.7-code
- Tokens: 33,856 / 1,918
- Messages: 11
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: PID 6877 dead; LoRA training died at epoch 2.0; best F1 1.46%, final F1 0.0; only 39 real/human-verified docs available. Contaminated checkpoints identified: `models/rfq2boq-ner-lora-v5/` trained on pseudo labels; v2/v3/v4/swa10 un-audited. Suggested quarantine.

**`ses_0d3ad3857ffe5L8gKTNFjz04Uw` — Verify sacred 10 fidelity**
- Model: kimi-k2.7-code
- Tokens: 36,670 / 2,301
- Messages: 8
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Sacred-10 count fidelity 100% (223 extracted vs 195 source, capped); raw over-capture 114.4%; 63 low-confidence rows. Noted `05_zydus_animal` over-capture (48 vs 20) and `04_adani` 28/45 low-confidence.

**`ses_0e92c1523ffepJfa6dVTqzYdCa` — Complete project using kleenhand.md**
- Model: big-pickle
- Tokens: 32,073,942 / 48,033
- Messages: 359
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Listed critical pending work; falsely claimed LoRA PID 6877 running (later audit found it dead); noted leaked GitHub token in remote URL.

**`ses_0ed1b3fabffeJpdYlmo7lCL6wQ` — Fix XLSX fidelity issues**
- Model: mimo-v2.5-free
- Tokens: 18,706 / 4,621
- Messages: 20
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Hardened `scripts/measure_fidelity.py`: PASS now fails on dropped rows or fidelity >110%; added `run_pdf_extraction()`; added `OVER_CAPTURE_THRESHOLD = 1.10`; added Status column. Result: 0 PASS, 10 FAIL, overall 27.9%.

**`ses_0ed1e144effe19989GAriuUQdy` — Consolidate handoff files**
- Model: mimo-v2.5-free
- Tokens: 33,121 / 5,794
- Messages: 13
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Created `HANDOFF.md` (289 lines); `git mv` 5 files to `attic/` (`HANDOFF_FOR_NEXT_AGENT.md`, `MASTER_HANDOFF.md`, `COMPLETE_PROJECT_HANDOFF.md`, `FINAL_ORCHESTRATION.md`, `PROJECT_MAP.md`). Kept `CLAUDE.md` and `AGENTS.md` separate.

**`ses_0ed24165fffeROPQ4ohziwXQ5B` — Gold spot-check report**
- Model: mimo-v2.5-free
- Tokens: 35,983 / 8,376
- Messages: 24
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Created `scripts/gold_spotcheck_report.py` and `results/gold_spotcheck_report.md`. Loaded all 9 `insul_*.rowgold.json` files (168 entries total). All entries `human_verified: false`.

**`ses_0ed242b65ffezeyDwKYvN55OKU` — Build catalog matcher + eval**
- Model: mimo-v2.5-free
- Tokens: 76,848 / 12,480
- Messages: 26
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Created `src/nlp/catalog_matcher.py` with cascade (exact → alias exact → token overlap Jaccard → substring/keyword → Levenshtein). Catalog sources: `data/real_rfqs/swa_gem_catalog_full.json` (19 products, 13 unique) + `data/ontology/insulation_materials.json`. Output `results/eval_catalog_match.json`. 39 tests passed; ruff clean.

**`ses_0f87ec8dfffeFNQxeYiOiYgGXa` — OpenRouter free models testing and fix**
- Model: nemotron-3-ultra-free
- Tokens: 2,932,889 / 12,327
- Messages: 78
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Truncated/abandoned; no deliverable recorded.

### A.2 Batch B raw session details

**`ses_0f88770ecffe5aQldCdtAqaT62` — New session - 2026-06-27T05:06:09.303Z**
- Model: nemotron-3-ultra-free
- Tokens: 6,408,835 / 11,228
- Messages: 78
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Orchestration attempt to complete project using subagents. Interrupted; identified Avante-style documents lacking explicit BOQ headings as a root-cause issue.

**`ses_0fd7cbb45ffesQQ71OIbB5fK6h` — Fixing insulation tender timeout issues**
- Model: MiniMax-M2.7
- Tokens: 59,290 / 20,915
- Messages: 53
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneC`
- Summary: Commit `3530731` — `fix(ingest): structure-first routing fixes insulation tender timeouts (C7)`. Modified `src/pipeline.py`; created `tests/integration/test_insulation_tender_timeouts.py`. All 7 previously timing-out insulation tender PDFs now complete under 60s (0 rows each, spec-only docs).

**`ses_0fdafa71bffecXT75Te9NUysHE` — Honest row-level eval for insulation domain**
- Model: MiniMax-M2.5
- Tokens: 59,922 / 7,809
- Messages: 35
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneE`
- Summary: Commit `396d884` — `eval: honest insulation-domain row-level evaluation (E7)`. Deliverables: `results/insulation_eval_2026-06-26.md`, `results/insulation_eval_raw.json`, `results/insulation_pipeline_output.json`. Macro F1 21.7% (`insul_01` 43.5%, `insul_02` 0.0%). Gold is draft-only.

**`ses_0fdafb0abffeoBynJcvQwOZBAf` — Wave 2: Integrate insulation ontology into NER**
- Model: MiniMax-M2.7
- Tokens: 33,771 / 16,078
- Messages: 67
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneD`
- Summary: Commit `7a2007c` — `feat(nlp): integrate insulation ontology+GeM gazetteer into NER (D3)`. Modified `src/nlp/patterns/dictionary.py`, `src/nlp/patterns/regex_patterns.py`, `src/nlp/pipeline.py`, `tests/unit/test_patterns.py`. Added 30+ insulation material patterns and wired GeM gazetteer into NER.

**`ses_0fdafb620ffeHQjGRROrcwnHu4` — Fix insulation tender timeout errors**
- Model: MiniMax-M2.5
- Tokens: 10,855 / 469
- Messages: 3
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneC`
- Summary: Very short session; no final output preserved. Grouped under C7 commit `3530731`.

**`ses_0fdafba93ffe3VQZOnW49H6WvS` — Drafting row-gold for remaining insulation BOQ pairs**
- Model: MiniMax-M3
- Tokens: 64,469 / 45,370
- Messages: 75
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneB`
- Summary: Commit `88e92a6` — `feat(data): draft row-gold for remaining insulation BOQ pairs (B2)`. Created `insul_03` through `insul_09` rowgold files plus `_insul_draft_summary.json`; extended `scripts/draft_insulation_rowgold.py`. Total 168 rows across 9 insulation pairs.

**`ses_10252f5f6ffe22OwrDdIVrwya2` — Final honest project status (Lane A)**
- Model: MiniMax-M2.7
- Tokens: 9,658 / 9,962
- Messages: 43
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneA`
- Summary: Commit `2407fab` (amended) — `docs: final honest project status (A6)`. Deliverable `results/PROJECT_HONEST_STATUS_2026-06-25.md`. Reported entity F1 44.1%, XLSX 89.0%, PDF 14.2%, anti-cheat 27/27.

**`ses_10252fd6fffeMeuwcwdVnlJ3aX` — Insulation domain honest row-level evaluation**
- Model: MiniMax-M2.5
- Tokens: 23,625 / 859
- Messages: 8
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneE`
- Summary: Early exploration; grouped under E7 commit `396d884`.

**`ses_10252fefbffel0FKlMI9pKBWmy` — Wave 2 NER insulation ontology integration**
- Model: MiniMax-M2.7
- Tokens: 10,473 / 1,346
- Messages: 7
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneD`
- Summary: Early exploration; grouped under D3 commit `7a2007c`.

**`ses_102530d7fffeVftN5PF8U6msRR` — Structure-first routing fixes insulation tender timeouts**
- Model: MiniMax-M2.5
- Tokens: 28,206 / 1,255
- Messages: 8
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneC`
- Summary: Early exploration; grouped under C7 commit `3530731`.

### A.3 Batch C raw session details

**`ses_102531233ffeMwYlu3ZxQNBFCg` — Drafting row-gold for remaining insulation BOQ pairs**
- Model: MiniMax-M3
- Tokens: 33,302 / 892
- Messages: 7
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneB`
- Summary: Handoff truncated; outcome unknown per BATCH C. Same B2 task as `ses_0fdafba93ffe3VQZOnW49H6WvS`.

**`ses_102c97e68ffeRWt9w2TSsVFyV5` — Audit lane D after b38db2c**
- Model: MiniMax-M2.7
- Tokens: 12,678 / 3,126
- Messages: 9
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneA`
- Summary: Commit `b49f62d` — `audit: re-audit lane D after commit b38db2c`. Verified Lane D ontology commit.

**`ses_102c9870bffeiw9AtrrRkADdM1` — Finish Lane B row-gold extraction and commit**
- Model: MiniMax-M3
- Tokens: 47,081 / 9,120
- Messages: 25
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneB`
- Summary: Commit `73489c8` — `feat(data): extract insulation corpus + draft row-gold for 2 pairs (B1)`. Files: `insul_01_tender.rowgold.json` (23 rows) and `insul_02_swpl.rowgold.json` (19 rows). Also created `scripts/extract_insulation_corpus.py`.

**`ses_102f4a325ffelqG9k9gJhkVa1o` — Lane D: ontology commit + insulation IS-codes**
- Model: MiniMax-M2.5-highspeed
- Tokens: 7,699 / 9,386
- Messages: 30
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneD`
- Summary: Implied commit `b38db2c` — `feat(ontology): GeM gazetteer + insulation domain ontology (D1-D2)`. Modified `data/ontology/insulation_materials.json`, `data/ontology/insulation_standards.json`, created `data/ontology/insulation_units.json`, modified `src/nlp/patterns/gem_catalog.py`, `src/ontology/loader.py`, tests.

**`ses_102f4aa1cffesD2HuwJap6tx0Y` — Adani PDF structure-first extraction fix**
- Model: MiniMax-M2.5
- Tokens: 158,320 / 7,816
- Messages: 39
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneC`
- Summary: Created `tests/integration/test_adani_structure.py`. Claimed 45 rows extracted matching gold. Commit status **unconfirmed** in BATCH C.

**`ses_102f4b503ffeMAjBB5eagKAf1v` — Lane A merge audit C/D/E**
- Model: MiniMax-M2.7
- Tokens: 19,333 / 15,089
- Messages: 56
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneA`
- Summary: Commit `c0a7477` — `audit: lane merge audit A5 — C/D/E verdict`. Deliverable `results/lane_merge_audit_2026-06-22.md`. Verdict: 3/3 merged (B version).

**`ses_102f4bcbcffeQlEvknhz4Q1NWF` — Insulation tender extraction + draft row-gold (Lane B1)**
- Model: MiniMax-M3
- Tokens: 42,627 / 10,918
- Messages: 27
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneB`
- Summary: Handoff truncated; likely same B1 task as `ses_102c9870bffeiw9AtrrRkADdM1` / `ses_107a0f528ffe0LbXtl6kPcssjS`.

**`ses_107326f60ffey4di2lse0VcP2o` — RFQ2BOQ multi-agent dispatch hitting credit limits**
- Model: mimo-v2.5-pro
- Tokens: 77,225 / 314
- Messages: 3
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Identified 25 MB RAR v5 archive (`resources/Specifications.rar`); installed `rar`/`unar`; listed 11 spec PDFs inside; did NOT extract into repo.

**`ses_107a0bbecffelXrQdEq7MIz82f` — Insulation tender batch pipeline run**
- Model: MiniMax-M2.5
- Tokens: 162,442 / 14,995
- Messages: 72
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneE`
- Summary: Created `scripts/run_insulation_batch.py`, `results/insulation_batch_run_2026-06-22.json`, `results/insulation_batch_run_2026-06-22.md`, `tests/integration/test_insulation_batch_no_crash.py`. 11/11 PDFs attempted; 0 crashes; 7 timeouts. Commit status unconfirmed.

**`ses_107a0f528ffe0LbXtl6kPcssjS` — Insulation tender extraction + draft row-gold**
- Model: MiniMax-M3
- Tokens: 96,707 / 13,808
- Messages: 43
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneB`
- Summary: Handoff truncated/incomplete. Same B1 task.

### A.4 Batch D raw session details

**`ses_107a0fadaffeWtp4UJEDCeOgxc` — Lane A merge audit C/D/E**
- Model: MiniMax-M3
- Tokens: 36,458 / 4,416
- Messages: 18
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneA`
- Summary: No completion captured; expected `results/lane_merge_audit_2026-06-22.md`.

**`ses_107a43ba2ffeuIDC04zVtKIFVo` — Insulation batch run — fidelity reports for 11 tenders**
- Model: MiniMax-M2.5
- Tokens: 22,286 / 327
- Messages: 4
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneE`
- Summary: No completion captured; expected same E6 deliverables as `ses_107a0bbecffelXrQdEq7MIz82f`.

**`ses_107a4c164ffefepVNT453HPKwO` — Lane A5 merge audit (C/D/E)**
- Model: MiniMax-M3
- Tokens: 12,048 / 756
- Messages: 3
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneA`
- Summary: No completion captured; expected `results/lane_merge_audit_2026-06-22.md`.

**`ses_11006afa2ffeHDdIZ3bISAO921` — Explore PDF ingested content**
- Model: deepseek-v4-flash-free
- Tokens: 28,435 / 10,507
- Messages: 7
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneA`
- Summary: No files touched; extracted content from `04_adani`, `09_gem_bid_7439924`, `10_gem_bid_7552777` ingested JSONs and gold files.

**`ses_1100731e2ffeLO6D49XlhnJhBh` — Lane E pipeline robustness and fidelity**
- Model: mimo-v2.5-free
- Tokens: 399,801 / 31,219
- Messages: 115
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneE`
- Summary: Modified `src/rules/units.py`, `src/pipeline_xlsx.py`, `Makefile`, and several test files. Unified unit normalizer; XLSX fidelity tracking; rate-only row flagging. Reported passing `make verify`; all 487 unit tests pass.

**`ses_11007b70fffekB26BFLAMNlTAz` — Lane D ontology + GeM reference (R2)**
- Model: north-mini-code-free
- Tokens: 2,671,055 / 18,728
- Messages: 68
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneD`
- Summary: Status **RUNNING** — mining 53 spec PDFs in `resources/Specifications/` for ontology enrichment. No completion captured.

**`ses_110081fc7ffeGxIasPR52AvQro` — Lane C structure-first extraction R4**
- Model: big-pickle
- Tokens: 85,482 / 12,121
- Messages: 45
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneC`
- Summary: Commit `8f9e35e` on `phase8-laneC`. Modified `src/preproc/document_structure.py` and `src/ingest/table_extractor.py`; 5 files changed, 99 insertions, 4 deletions; 95 critical tests pass. Added PDF timeout wrapper and structure extractor precision rules.

**`ses_1100865ffffeXBUIp4Vx6Aidex` — Lane B insulation gold annotation loop setup**
- Model: nemotron-3-ultra-free
- Tokens: 87,860 / 524
- Messages: 7
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneB`
- Summary: Status: **ERROR / Timeout — needs restart** per dispatch session `ses_1115553a6ffeR4s6IEmUn3Mg63`.

**`ses_11008f3a1ffeT5D3nmQGeU5edh` — Lane A anti-cheat & honest baseline**
- Model: deepseek-v4-flash-free
- Tokens: 224,631 / 32,126
- Messages: 94
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq-laneA`
- Summary: Reported done and committed; `make verify` passes 7 steps clean. Anti-cheat tests hardened. Reported entity F1 44.1%, XLSX 89.0%, PDF 14.2%, anti-cheat 27/27.

**`ses_1115553a6ffeR4s6IEmUn3Mg63` — Complete and hand off project sessions with analysis**
- Model: mimo-v2.5-pro
- Tokens: 4,024,883 / 27,362
- Messages: 184
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Produced multi-lane status table: Lane A DONE, Lane C DONE, Lane B ERROR/timeout, Lane D RUNNING, Lane E RUNNING.

### A.5 Batch E raw session details

**`ses_1264a012affeRHj6w08eOvWTpx` — Fix pipeline extraction for Zydus non-zero qty rows**
- Model: nemotron-3-ultra-free
- Tokens: 1,510,272 / 7,608
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Fixed XLSX pipeline for `05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx`. Previously extracted all rows including TOTAL=0 and "R.O.", producing 48 items. Fix emits only rows where TOTAL > 0 (numeric). Result: exactly 20 items matching source. Commit: `fix(05-zydus): pipeline correctly extracts non-zero qty rows from multi-column XLSX`.

**`ses_1264a228effekBULGv67DcUhb8` — Honest evaluation run and commit results**
- Model: north-mini-code-free
- Tokens: 251,562 / 992
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Ran `python3 scripts/eval_honest_rows.py 2>&1`. Script timed out after 2 minutes; results restored from backup. Committed `results/eval_honest_rows.json` and `results/eval_honest_rows_2026-06-18.txt`. Macro F1 92.1%, micro F1 86.5%, total_gold 244, total_pred 223.

**`ses_1264a3a58ffeDzcnix7Aumg4Gl` — Fix 07 Grew Solar missing row**
- Model: big-pickle
- Tokens: 76,801 / 14,837
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: `07_grew_solar_narmadapuram` was at 88.9% F1 due to Camelot inserting phantom spaces. Fix in `src/ingest/table_extractor.py:map_to_boq_rows` cross-references Camelot tables with pdfplumber cell text for material/description columns. Result: 100% F1 (9/9). Commit `c923e2a`.

**`ses_1265a99deffe5aXI1BUOhOjZ6K` — Repo hygiene fixes: restore PDFs, update docs, rebuild manifest**
- Model: north-mini-code-free
- Tokens: 458,193 / 1,244
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Branch `phase8-clean-slate`. Commit with 155 files: restored 154 real reference PDFs to `data/real_rfqs/reference_real/`, created `README.md`, rebuilt `data/real_rfqs/swa_enquiries/manifest.csv` (18 files), fixed `MASTER_HANDOFF.md` paths and added Python version note.

**`ses_1265ac970ffeFnUi7jnm7d994s` — Fix 02 ISRO VSSC missing 2 rows**
- Model: deepseek-v4-flash-free
- Tokens: 47,014 / 4,873
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Gold entries 4 and 7 are spec paragraph and note disclaimer; pipeline correctly filters them. Conclusion: gold is wrong (`human_verified: false`), not pipeline. Added document-level `notes` field in `data/real_rfqs/gold/rows/02_isro_vssc.rowgold.json`. No pipeline change.

**`ses_1265af65bffeL58pbBwiAZOMgs` — NW-05: Consolidate unit normalizers into one**
- Model: big-pickle
- Tokens: 50,007 / 13,401
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Replaced scattered local unit normalizers with single source of truth in `src/rules/units.py`. Removed 64-line `_UNIT_MAP` from `src/ingest/text_boq_extractor.py` and 44-line `unit_map` from `src/domain/boq_assembler.py`. Added `to_float_qty`. New test `tests/unit/test_units_canonical.py` with 59 cases. Commit `b81b440`.

**`ses_12693d3a5ffe4g4hp2xGkYTSBt` — Update gold flag and run pipeline on 2 new tenders**
- Model: deepseek-v4-flash-free
- Tokens: 27,633 / 1,423
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Added `gold_quality_note` to `05_zydus_animal_pharmez.rowgold.json` (commit `c001ef8`). Ran pipeline on `data/incoming/40_vssc_acoustic_boq.xlsx` (5 items) and `data/incoming/R3_zydus_matoda_osd.xlsx` (33 items); wrote `results/new_tenders_2026-06-18.json` (commit `6fc9bfa`).

**`ses_12693fee0ffeljUnjpZfU7KhPP` — Add SWA GeM catalog with validation**
- Model: big-pickle
- Tokens: 21,926 / 1,741
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Created `src/nlp/patterns/gem_catalog.py` with `SWA_GEM_PUBLISHED` dict loaded from `data/real_rfqs/swa_gem_catalog_full.json`, `validate_gem_extraction()` using `difflib.SequenceMatcher`, provenance comment. Deduplicated to 13 unique products from 20 entries. Commit `0739ecf`.

**`ses_126941f4efferQ3FEVE3JnlSX1` — Add data_only=True to openpyxl loads for formula evaluation**
- Model: big-pickle
- Tokens: 172,710 / 517
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Verified `src/pipeline_xlsx.py:56` and `src/ingest/xlsx_parser.py:31` already use `openpyxl.load_workbook(..., data_only=True)`. No code change needed.

**`ses_126959a48ffe0Xj8aFjythvq3g` — Fix XLSX pipeline formula cell handling with data_only=True**
- Model: big-pickle
- Tokens: 170,197 / 520
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Duplicate verification; no code change needed.

### A.6 Batch F raw session details

**`ses_155dd541cffenOtFZ8LrTqLAik` — Explore data and gold files**
- Agent: explore
- Model: mimo-v2.5-free
- Tokens: 157,656 / 4,806
- Messages: 6
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Comprehensive data/gold/annotation report. Key findings: `data/real_rfqs/additional_real/` contains 168 PDFs, zero XLSX. Entity gold format inspected for `swa_02_isro_vssc` (1,078 tokens, 28 entities, 2 relations). Row-gold format inspected (7 entries, all auto-converted, `human_verified: false`). `data/real_rfqs/annotations/` has 4 files including `gold_annotations.json` (5 synthetic docs), `manifest.csv` (118 rows, 4 real PDFs, 114 synthetic). `data/real_rfqs/annotated/` has 7 files including synthetic samples and 4 real PDFs annotated all "O". Report truncated at line 212.

**`ses_155dd5ee9ffe3fQj9ASNArlHQE` — Explore extraction pipeline code**
- Agent: explore
- Model: mimo-v2.5-free
- Tokens: 91,121 / 10,340
- Messages: 8
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Complete extraction pipeline report. Pipeline spans 30+ files across `src/pipeline.py`, `src/pipeline_xlsx.py`, `src/ingest/`, `src/preproc/`, `src/nlp/`, `src/domain/`, `src/rules/`, `src/risk/`, `src/confidence/`, `src/export/`, `config/constants.py`. Domain model highlights: `BoqRow` fields, validation checks, entity/relation schema (8 entities, 6 relations). Report truncated at line 162.

**`ses_148f386efffeFhGl97ZKifyHpx` — NW-06 Repo Hygiene & Docs cleanup**
- Agent: build
- Model: mimo-v2.5-free
- Tokens: 12,119,246 / 89,330
- Messages: 231
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Task file `tasks/NW06_repo_hygiene_and_docs.md`. Planned steps: restore reference PDFs (only genuinely real non-SWA files), port phase8 prompts to archive, fix `MASTER_HANDOFF.md`, fix `deliverables/slides/DEMO_SCRIPT.md` paths, rebuild `manifest.csv` (19 files), run `make verify`. Constraints: forbidden to restore synthetic data, merge main-clean code, touch gold, rewrite `HANDOFF.md` numbers. Honest status: code done, project NOT complete; owner-only blockers: push commits, rotate GitHub token, human-verify 9 gold pairs, get ~100 real PDFs, rebuild venv, decide multi-qty rule.

**`ses_14655c5e3ffedVq2vCzwqqzEup` — Concerns about AI agent cheating during model development**
- Agent: build
- Model: MiniMax-M3
- Tokens: 21,180,363 / 95,931
- Messages: 177
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: User expressed concerns about AI agents faking/cheating with BERT model and pre-stored data. Agent acknowledged and agreed to train honestly on 10 SWA resources only. No further tool calls or file changes recorded.

**`ses_12699751dffeElVqfcwzqhklQz` — New session - 2026-06-18T06:23:56.642Z**
- Agent: build
- Model: mimo-v2.5-free
- Tokens: 11,653 / 4
- Messages: 2
- Files touched: 0
- Prompt: "Reply with OK only"
- Last output: `OK`

**`ses_126999169ffehldjRQb62n5RGt` — OK only reply**
- Agent: build
- Model: north-mini-code-free
- Tokens: 11,142 / 1
- Messages: 2
- Files touched: 0
- Prompt: "Reply with OK only"
- Last output: `OK`

**`ses_12699b2deffe89kaev8PsqCJU5` — New session - 2026-06-18T06:23:40.834Z**
- Agent: build
- Model: big-pickle
- Tokens: 12,538 / 2
- Messages: 2
- Files touched: 0
- Prompt: "Reply with OK only"
- Last output: `OK`

**`ses_12699df61ffeGPrgCMZhswLbZV` — New session - 2026-06-18T06:23:29.438Z**
- Agent: build
- Model: nemotron-3-ultra-free
- Tokens: 12,986 / 2
- Messages: 2
- Files touched: 0
- Prompt: "Reply with OK only"
- Last output: `OK`

**`ses_12699fdc0ffe9Kp8d6zaAePzFt` — New session - 2026-06-18T06:23:21.663Z**
- Agent: build
- Model: deepseek-v4-flash-free
- Tokens: 12,546 / 2
- Messages: 2
- Files touched: 0
- Prompt: "Reply with OK only"
- Last output: `OK`

**`ses_1269a7946ffesVlYNiZeqYOP8V` — New session - 2026-06-18T06:22:50.041Z**
- Agent: build
- Model: deepseek-v4-flash-free
- Tokens: 12,552 / 4
- Messages: 2
- Files touched: 0
- Prompt: "Say HELLO in one word only" then "test"
- Last output: `HELLO`

### A.7 Batch G raw session details

**`ses_155dd6af8ffekYYXldimJRnCGj` — Explore training pipeline code**
- Agent: explore
- Model: mimo-v2.5-free
- Tokens: 76,799 / 6,884
- Messages: 8
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Read-only exploration of training/NER code. Objectives: read `scripts/train_lora_ner.py`, `src/nlp/pipeline.py`, all `src/nlp/` files, `models/`, `data/annotations/`, `config/constants.py`, `data/real_rfqs/gold/`. Identified 8 entity types, 6 relation types, BIOES 33 labels. Identified three training scripts with different architectures: `scripts/train_lora_ner.py` (LoRA, base `models/rfq2boq-ner-real-only-v2/final_model`, r=16, alpha=32, dropout=0.1, target modules query/value, 20 epochs), `src/nlp/train_ner.py` (original BERT fine-tuning on synthetic `data/nerAnnotations.json`, not found), `src/nlp/ner/trainer.py` (custom BiLSTM-CRF). Noted mismatch between cased (`bert-base-cased`) and uncased (`bert-base-uncased`) models across scripts.

**`ses_167aacf62ffeDLFxLQh1pD3VVg` — LoRA training vs production 0.43 F1**
- Agent: plan
- Model: nemotron-3-ultra-free
- Tokens: 10,229,535 / 133,146
- Messages: 389
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Task R3 — run LoRA training. Goal: adopt LoRA only if it beats production 0.43 F1 on held-out real data. Prerequisites: `swa_10` leak fixed, `pip install peft datasets`, Python 3.11–3.13 (NOT 3.14). Command: `python3 scripts/train_lora_ner.py`. Evaluation plan: frozen held-out real test set, confirm 10 SWA excluded, report per-entity + micro F1, verify `check_split_leakage`, adopt only if F1 > 0.43. Final state reported: Git HEAD `2d3bf6f`, rowgold restored (10 files), LoRA models `rfq2boq-ner-lora-v2/` and `v3/` exist, `HANDOFF.md` modified (uncommitted). Immediate next steps: verify scripts, run honest baseline (`python3 scripts/eval_honest.py` → expected micro F1 ~42.6%, XLSX ~60%, PDF ~23%), check training pipeline, start annotating 40 RFQs (25 insulation + 10 HVAC + 5 general). Open questions: annotation start today?, vendor test access?, pipeline fixes first or annotation first?

**`ses_167acb83cffe49VU1lhkjiW3Ee` — New session - 2026-06-05T15:07:35.235Z**
- Agent: plan
- Model: nemotron-3-ultra-free
- Tokens: 16,205,463 / 74,604
- Messages: 238
- Files touched: 0
- Worktree: `/Users/srujansai/Desktop/rfq2boq`
- Summary: Tasks R1/R2. R1: clean-slate reorg — fix 3 dangling prompt links in `docs/PHASE8_UNIFIED_TIMELINE_AND_FLOW.md` (repoint to `prompts/wave4/` or remove), `git mv data/synthetic_archive/ attic/synthetic_corpus_archived/`, add `data/synthetic_archive/` and `data/synthetic/` to `.gitignore`, verify with grep and import checks. R2: 03 Zydus Matoda honest fix — run `validate_product.py --enquiry 03`, inspect per-row mismatch, diagnose gold-side vs extraction-side, fix extraction if needed or build independent rowgold via `build_row_gold.py` (gold never from pipeline), commit honest result. Final state check: NOT 100% complete. Table: 02 ISRO 57.1% (false), 03 Zydus 100% (true, anti-cheat passes ⚠️), 05 Zydus Animal 32.2% (false), 08 SAEL 82.4% (false), PDFs unknown. Warning: anti-cheat test will FAIL on 03 because it is the only file with `human_verified=True` and 100% match. Phase 0 clean-slate tasks (8 tasks) listed with verification commands. Phase 3 robust pipeline fixes. Phase 4 honest evaluation targets: XLSX ≥80%, PDF ≥50% row-match, entity F1 ≥0.70, 30 unseen files ≥80% produce ≥3 valid rows. Four user decisions needed: timeline, annotation resources, compute budget, 09/10 gold sign-off. Forbidden checks: filename hacks, `_sael_scan`, `100% COMPLETE`, dirty tree, pytest failures.

---

## 13. Expanded Session-to-File Cross-Reference Matrix

This matrix maps every significant file mentioned across the 63 sessions to the session IDs that created, modified, or inspected it. It is provided to make lineage explicit and to support audit/replay.

### 13.1 Production source code cross-reference

| File | Created by | Modified by | Inspected by |
|---|---|---|---|
| `src/pipeline.py` | — | A `ses_0d3acedf6ffeSO63IwKxY1LOhE`, B `ses_0fd7cbb45ffesQQ71OIbB5fK6h` | F `ses_155dd5ee9ffe3fQj9ASNArlHQE` |
| `src/pipeline_xlsx.py` | — | D `ses_1100731e2ffeLO6D49XlhnJhBh`, E `ses_1264a012affeRHj6w08eOvWTpx` | E `ses_126941f4efferQ3FEVE3JnlSX1`, E `ses_126959a48ffe0Xj8aFjythvq3g`, F `ses_155dd5ee9ffe3fQj9ASNArlHQE` |
| `src/ingest/pdf_extractor.py` | — | A `ses_0d3acedf6ffeSO63IwKxY1LOhE` | F `ses_155dd5ee9ffe3fQj9ASNArlHQE` |
| `src/ingest/table_extractor.py` | — | D `ses_110081fc7ffeGxIasPR52AvQro`, E `ses_1264a3a58ffeDzcnix7Aumg4Gl` | F `ses_155dd5ee9ffe3fQj9ASNArlHQE` |
| `src/preproc/document_structure.py` | — | D `ses_110081fc7ffeGxIasPR52AvQro` | F `ses_155dd5ee9ffe3fQj9ASNArlHQE` |
| `src/nlp/patterns/dictionary.py` | — | A `ses_0d3acedf6ffeSO63IwKxY1LOhE`, B `ses_0fdafb0abffeoBynJcvQwOZBAf` | F `ses_155dd5ee9ffe3fQj9ASNArlHQE` |
| `src/nlp/patterns/regex_patterns.py` | — | B `ses_0fdafb0abffeoBynJcvQwOZBAf` | F `ses_155dd5ee9ffe3fQj9ASNArlHQE` |
| `src/nlp/patterns/gem_catalog.py` | C `ses_102f4a325ffelqG9k9gJhkVa1o`, E `ses_12693fee0ffeljUnjpZfU7KhPP` | C, E | F `ses_155dd5ee9ffe3fQj9ASNArlHQE` |
| `src/nlp/catalog_matcher.py` | A `ses_0ed242b65ffezeyDwKYvN55OKU` | A | — |
| `src/nlp/pipeline.py` | — | B `ses_0fdafb0abffeoBynJcvQwOZBAf` | F `ses_155dd5ee9ffe3fQj9ASNArlHQE`, G `ses_155dd6af8ffekYYXldimJRnCGj` |
| `src/ontology/loader.py` | — | C `ses_102f4a325ffelqG9k9gJhkVa1o` | — |
| `src/rules/units.py` | — | D `ses_1100731e2ffeLO6D49XlhnJhBh`, E `ses_1265af65bffeL58pbBwiAZOMgs` | F `ses_155dd5ee9ffe3fQj9ASNArlHQE` |
| `src/ingest/text_boq_extractor.py` | — | E `ses_1265af65bffeL58pbBwiAZOMgs` | F `ses_155dd5ee9ffe3fQj9ASNArlHQE` |
| `src/domain/boq_assembler.py` | — | E `ses_1265af65bffeL58pbBwiAZOMgs` | F `ses_155dd5ee9ffe3fQj9ASNArlHQE` |
| `src/unit_normalization.py` | — | E `ses_1265af65bffeL58pbBwiAZOMgs` | — |

### 13.2 Scripts cross-reference

| File | Created by | Modified by | Inspected by |
|---|---|---|---|
| `scripts/measure_fidelity.py` | — | A `ses_0ed1b3fabffeJpdYlmo7lCL6wQ` | — |
| `scripts/fidelity_audit.py` | — | A `ses_0d3acedf6ffeSO63IwKxY1LOhE` | — |
| `scripts/train_lora_ner_real_only.py` | — | A `ses_0d3ad2095ffewtQmOj1SE6IOd2` | G `ses_155dd6af8ffekYYXldimJRnCGj` |
| `scripts/convert_to_bioes.py` | — | A `ses_0d3ad2095ffewtQmOj1SE6IOd2` | — |
| `scripts/intake_tender.py` | — | A `ses_0d3acedf6ffeSO63IwKxY1LOhE` | — |
| `scripts/review_annotation.py` | — | A `ses_0d3acedf6ffeSO63IwKxY1LOhE` | — |
| `scripts/gold_spotcheck_report.py` | A `ses_0ed24165fffeROPQ4ohziwXQ5B` | A | — |
| `scripts/draft_insulation_rowgold.py` | B `ses_0fdafba93ffe3VQZOnW49H6WvS` | B | — |
| `scripts/extract_insulation_corpus.py` | C `ses_102c9870bffeiw9AtrrRkADdM1` | C | — |
| `scripts/run_insulation_batch.py` | C `ses_107a0bbecffelXrQdEq7MIz82f` | C | — |
| `scripts/eval_honest_rows.py` | — | E `ses_1264a228effekBULGv67DcUhb8` | G `ses_155dd6af8ffekYYXldimJRnCGj` |
| `scripts/eval_honest.py` | — | — | G `ses_167aacf62ffeDLFxLQh1pD3VVg` |
| `scripts/train_lora_ner.py` | — | — | G `ses_155dd6af8ffekYYXldimJRnCGj` |
| `scripts/annotate_rfq.py` | — | — | G `ses_167aacf62ffeDLFxLQh1pD3VVg` |
| `scripts/validate_product.py` | — | — | G `ses_167acb83cffe49VU1lhkjiW3Ee` |
| `scripts/build_row_gold.py` | — | — | G `ses_167acb83cffe49VU1lhkjiW3Ee` |

### 13.3 Tests cross-reference

| File | Created by |
|---|---|
| `tests/integration/test_insulation_tender_timeouts.py` | B `ses_0fd7cbb45ffesQQ71OIbB5fK6h` |
| `tests/integration/test_adani_structure.py` | C `ses_102f4aa1cffesD2HuwJap6tx0Y` |
| `tests/integration/test_insulation_batch_no_crash.py` | C `ses_107a0bbecffelXrQdEq7MIz82f` |
| `tests/unit/test_units_canonical.py` | E `ses_1265af65bffeL58pbBwiAZOMgs` |
| `tests/unit/test_catalog_matcher.py` | A `ses_0ed242b65ffezeyDwKYvN55OKU` |
| `tests/unit/test_patterns.py` | B `ses_0fdafb0abffeoBynJcvQwOZBAf` |
| `tests/unit/test_gem_catalog.py` | C `ses_102f4a325ffelqG9k9gJhkVa1o` |
| `tests/unit/test_ontology_loader.py` | C `ses_102f4a325ffelqG9k9gJhkVa1o` |

### 13.4 Data / ontology / gold cross-reference

| File | Created by | Modified by |
|---|---|---|
| `data/ontology/insulation_materials.json` | C `ses_102f4a325ffelqG9k9gJhkVa1o` | A, B, C, D |
| `data/ontology/insulation_standards.json` | C `ses_102f4a325ffelqG9k9gJhkVa1o` | C |
| `data/ontology/insulation_units.json` | C `ses_102f4a325ffelqG9k9gJhkVa1o` | C |
| `data/ontology/materials.json` | — | B |
| `data/real_rfqs/gold/rows/insul_01_tender.rowgold.json` | C `ses_102c9870bffeiw9AtrrRkADdM1` | B/C |
| `data/real_rfqs/gold/rows/insul_02_swpl.rowgold.json` | C `ses_102c9870bffeiw9AtrrRkADdM1` | B/C |
| `data/real_rfqs/gold/rows/insul_03_boq_page.rowgold.json` through `insul_09_pipe_insulation_compliance.rowgold.json` | B `ses_0fdafba93ffe3VQZOnW49H6WvS` | B/C |
| `data/real_rfqs/gold/rows/02_isro_vssc.rowgold.json` | — | E `ses_1265ac970ffeFnUi7jnm7d994s` |
| `data/real_rfqs/gold/rows/05_zydus_animal_pharmez.rowgold.json` | — | E `ses_12693d3a5ffe4g4hp2xGkYTSBt` |
| `data/real_rfqs/swa_enquiries/manifest.csv` | E `ses_1265a99deffe5aXI1BUOhOjZ6K` | E |
| `data/real_rfqs/reference_real/*.pdf` (154) | E `ses_1265a99deffe5aXI1BUOhOjZ6K` | E |
| `data/real_rfqs/reference_real/README.md` | E `ses_1265a99deffe5aXI1BUOhOjZ6K` | E |
| `results/eval_honest_rows.json` | E `ses_1264a228effekBULGv67DcUhb8` | E |
| `results/eval_honest_rows_2026-06-18.txt` | E `ses_1264a228effekBULGv67DcUhb8` | E |
| `results/new_tenders_2026-06-18.json` | E `ses_12693d3a5ffe4g4hp2xGkYTSBt` | E |
| `results/insulation_eval_2026-06-26.md` | B `ses_0fdafa71bffecXT75Te9NUysHE` | B |
| `results/insulation_eval_raw.json` | B `ses_0fdafa71bffecXT75Te9NUysHE` | B |
| `results/insulation_pipeline_output.json` | B `ses_0fdafa71bffecXT75Te9NUysHE` | B |
| `results/insulation_batch_run_2026-06-22.json` | C `ses_107a0bbecffelXrQdEq7MIz82f` | C |
| `results/insulation_batch_run_2026-06-22.md` | C `ses_107a0bbecffelXrQdEq7MIz82f` | C |
| `results/PROJECT_HONEST_STATUS_2026-06-25.md` | B `ses_10252f5f6ffe22OwrDdIVrwya2` | B |
| `results/lane_merge_audit_2026-06-22.md` | C `ses_102f4b503ffeMAjBB5eagKAf1v` | C |
| `results/gold_spotcheck_report.md` | A `ses_0ed24165fffeROPQ4ohziwXQ5B` | A |
| `results/eval_catalog_match.json` | A `ses_0ed242b65ffezeyDwKYvN55OKU` | A |

### 13.5 Documentation cross-reference

| File | Created by | Modified by | Moved to attic by |
|---|---|---|---|
| `HANDOFF.md` | A `ses_0ed1e144effe19989GAriuUQdy` | G `ses_167aacf62ffeDLFxLQh1pD3VVg` (uncommitted) | — |
| `MASTER_HANDOFF.md` | — | E `ses_1265a99deffe5aXI1BUOhOjZ6K` | A `ses_0ed1e144effe19989GAriuUQdy` |
| `PROJECT_MAP.md` | — | — | A `ses_0ed1e144effe19989GAriuUQdy` |
| `HANDOFF_FOR_NEXT_AGENT.md` | — | — | A `ses_0ed1e144effe19989GAriuUQdy` |
| `COMPLETE_PROJECT_HANDOFF.md` | — | — | A `ses_0ed1e144effe19989GAriuUQdy` |
| `FINAL_ORCHESTRATION.md` | — | — | A `ses_0ed1e144effe19989GAriuUQdy` |
| `docs/ANNOTATION_WORKFLOW.md` | — | A `ses_0d3acedf6ffeSO63IwKxY1LOhE` | — |
| `docs/PHASE8_UNIFIED_TIMELINE_AND_FLOW.md` | — | — | — (dangling links to be fixed per G) |

---

## 14. Per-Session Deliverable Registry

This registry lists every concrete deliverable (file, commit, report, fix, test) produced by each session, preserving granularity.

### A sessions

| Session | Deliverable(s) |
|---|---|
| `ses_0d3acedf6ffeSO63IwKxY1LOhE` | Code-review red-flag list; test pass confirmations |
| `ses_0d3ad0628ffeTgnlCBLzMf3biy` | Proposal for `data/real_rfqs/corpus_manifest.json` |
| `ses_0d3ad2095ffewtQmOj1SE6IOd2` | Training audit findings; contaminated checkpoint list |
| `ses_0d3ad3857ffe5L8gKTNFjz04Uw` | Sacred-10 fidelity table |
| `ses_0e92c1523ffepJfa6dVTqzYdCa` | Critical-pending-work list; leaked-token alert |
| `ses_0ed1b3fabffeJpdYlmo7lCL6wQ` | Hardened `scripts/measure_fidelity.py` |
| `ses_0ed1e144effe19989GAriuUQdy` | `HANDOFF.md`; `attic/` moves of 5 files |
| `ses_0ed24165fffeROPQ4ohziwXQ5B` | `scripts/gold_spotcheck_report.py`; `results/gold_spotcheck_report.md` |
| `ses_0ed242b65ffezeyDwKYvN55OKU` | `src/nlp/catalog_matcher.py`; `results/eval_catalog_match.json`; `tests/unit/test_catalog_matcher.py` |
| `ses_0f87ec8dfffeFNQxeYiOiYgGXa` | None (abandoned) |

### B sessions

| Session | Deliverable(s) |
|---|---|
| `ses_0f88770ecffe5aQldCdtAqaT62` | Avante-style doc issue identification |
| `ses_0fd7cbb45ffesQQ71OIbB5fK6h` | Commit `3530731`; `tests/integration/test_insulation_tender_timeouts.py` |
| `ses_0fdafa71bffecXT75Te9NUysHE` | Commit `396d884`; insulation eval reports |
| `ses_0fdafb0abffeoBynJcvQwOZBAf` | Commit `7a2007c`; NER pattern/ontology integration |
| `ses_0fdafb620ffeHQjGRROrcwnHu4` | None captured (grouped under C7) |
| `ses_0fdafba93ffe3VQZOnW49H6WvS` | Commit `88e92a6`; `insul_03`–`insul_09` rowgold files; `_insul_draft_summary.json`; extended `scripts/draft_insulation_rowgold.py` |
| `ses_10252f5f6ffe22OwrDdIVrwya2` | Commit `2407fab`; `results/PROJECT_HONEST_STATUS_2026-06-25.md` |
| `ses_10252fd6fffeMeuwcwdVnlJ3aX` | None (grouped under E7) |
| `ses_10252fefbffel0FKlMI9pKBWmy` | None (grouped under D3) |
| `ses_102530d7fffeVftN5PF8U6msRR` | None (grouped under C7) |

### C sessions

| Session | Deliverable(s) |
|---|---|
| `ses_102531233ffeMwYlu3ZxQNBFCg` | None (truncated) |
| `ses_102c97e68ffeRWt9w2TSsVFyV5` | Commit `b49f62d`; re-audit of Lane D |
| `ses_102c9870bffeiw9AtrrRkADdM1` | Commit `73489c8`; `insul_01`/`insul_02` rowgold files; `scripts/extract_insulation_corpus.py` |
| `ses_102f4a325ffelqG9k9gJhkVa1o` | Implied commit `b38db2c`; insulation ontology JSON files; GeM gazetteer updates |
| `ses_102f4aa1cffesD2HuwJap6tx0Y` | `tests/integration/test_adani_structure.py` (commit unconfirmed) |
| `ses_102f4b503ffeMAjBB5eagKAf1v` | Commit `c0a7477`; `results/lane_merge_audit_2026-06-22.md` |
| `ses_102f4bcbcffeQlEvknhz4Q1NWF` | None (truncated) |
| `ses_107326f60ffey4di2lse0VcP2o` | RAR archive inventory; 11 spec PDFs listed (not extracted) |
| `ses_107a0bbecffelXrQdEq7MIz82f` | `scripts/run_insulation_batch.py`; batch run results; no-crash test (commit unconfirmed) |
| `ses_107a0f528ffe0LbXtl6kPcssjS` | None (truncated) |

### D sessions

| Session | Deliverable(s) |
|---|---|
| `ses_107a0fadaffeWtp4UJEDCeOgxc` | None (no completion) |
| `ses_107a43ba2ffeuIDC04zVtKIFVo` | None (no completion) |
| `ses_107a4c164ffefepVNT453HPKwO` | None (no completion) |
| `ses_11006afa2ffeHDdIZ3bISAO921` | PDF ingested content extraction (no files) |
| `ses_1100731e2ffeLO6D49XlhnJhBh` | Unit-normalizer/XLSX robustness changes; `make verify` pass reported |
| `ses_11007b70fffekB26BFLAMNlTAz` | RUNNING: ontology enrichment from 53 spec PDFs |
| `ses_110081fc7ffeGxIasPR52AvQro` | Commit `8f9e35e`; structure-first R4 changes |
| `ses_1100865ffffeXBUIp4Vx6Aidex` | ERROR/timeout — needs restart |
| `ses_11008f3a1ffeT5D3nmQGeU5edh` | Anti-cheat hardening; honest baseline report |
| `ses_1115553a6ffeR4s6IEmUn3Mg63` | Multi-lane status table |

### E sessions

| Session | Deliverable(s) |
|---|---|
| `ses_1264a012affeRHj6w08eOvWTpx` | Zydus non-zero TOTAL fix (20 rows) |
| `ses_1264a228effekBULGv67DcUhb8` | Updated honest row-level eval results |
| `ses_1264a3a58ffeDzcnix7Aumg4Gl` | Commit `c923e2a`; Grew Solar 100% F1 fix |
| `ses_1265a99deffe5aXI1BUOhOjZ6K` | 155-file repo hygiene commit |
| `ses_1265ac970ffeFnUi7jnm7d994s` | ISRO gold flag/note |
| `ses_1265af65bffeL58pbBwiAZOMgs` | Commit `b81b440`; unified unit normalizer; 59 new tests |
| `ses_12693d3a5ffe4g4hp2xGkYTSBt` | Commits `c001ef8`, `6fc9bfa`; 05 Zydus Animal gold flag; 2 new tender results |
| `ses_12693fee0ffeljUnjpZfU7KhPP` | Commit `0739ecf`; `src/nlp/patterns/gem_catalog.py` |
| `ses_126941f4efferQ3FEVE3JnlSX1` | Verification: `data_only=True` already present |
| `ses_126959a48ffe0Xj8aFjythvq3g` | Duplicate verification: `data_only=True` already present |

### F sessions

| Session | Deliverable(s) |
|---|---|
| `ses_155dd541cffenOtFZ8LrTqLAik` | Data/gold/annotation exploration report (truncated) |
| `ses_155dd5ee9ffe3fQj9ASNArlHQE` | Extraction pipeline exploration report (truncated) |
| `ses_148f386efffeFhGl97ZKifyHpx` | NW-06 repo-hygiene plan; owner-only blockers list |
| `ses_14655c5e3ffedVq2vCzwqqzEup` | Agreement to train honestly on 10 SWA resources |
| `ses_12699751dffeElVqfcwzqhklQz` | Output `OK` |
| `ses_126999169ffehldjRQb62n5RGt` | Output `OK` |
| `ses_12699b2deffe89kaev8PsqCJU5` | Output `OK` |
| `ses_12699df61ffeGPrgCMZhswLbZV` | Output `OK` |
| `ses_12699fdc0ffe9Kp8d6zaAePzFt` | Output `OK` |
| `ses_1269a7946ffesVlYNiZeqYOP8V` | Output `HELLO` |

### G sessions

| Session | Deliverable(s) |
|---|---|
| `ses_155dd6af8ffekYYXldimJRnCGj` | Training/NER architecture exploration report |
| `ses_167aacf62ffeDLFxLQh1pD3VVg` | LoRA-vs-production plan; `HANDOFF.md` modified (uncommitted) |
| `ses_167acb83cffe49VU1lhkjiW3Ee` | 10-week roadmap; Phase 0 clean-slate tasks; 03 Zydus anti-cheat warning |

---

## Document Integrity Statement

This `ULTIMATE_HANDOFF.md` was generated by the Level-3 final handoff-merge subagent on 2026-07-04. It is the result of merging `.session_merged/merged_L2A.md` (Batches A–D, 40 sessions) and `.session_merged/merged_L2B.md` (Batches E–G, 23 sessions). No source files, gold data, or git state were modified during this merge. The document preserves every session ID, deliverable, commit hash, file touched, blocker, contradiction, and metric identified in the source Level-2 merges.

*End of ULTIMATE_HANDOFF.md*















