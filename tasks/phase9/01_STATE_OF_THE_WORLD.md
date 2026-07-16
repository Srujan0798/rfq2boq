# STATE OF THE WORLD — honest snapshot, 2026-07-06 (evening, post plan-deletion incident)

Read this before any task. Everything here was independently verified by the orchestrator (commands in `tasks/sonnet/LEDGER.md` + `04_LEDGER.md`). If a number here disagrees with any report file in `results/` or `deliverables/`, **this file wins** until re-verified.

---

## 1. What the project must do (unchanged since the SWA brief)

Turn Indian construction tender RFQs (PDF/XLSX) into a structured **unpriced** Bill of Quantities (Excel + JSON).
Pipeline: `PDF/OCR → preprocess → NER → relation extraction → rules/ontology → BOQ assembly → export`.
Schema locked in `config/constants.py`: 8 entities, 6 relations, BIOES. **The architecture is correct** — matches the SWA implementation guide 1:1. The problems have always been (a) training data and (b) agent integrity, never the design.

Client acceptance bar (`docs/SWA_REQUIREMENTS_2026-06-11.md`):
- **R1** 100% data-conversion fidelity — flag, never drop
- **R2** GeM catalog = authoritative closed-vocabulary NER reference
- **R3** ~100-PDF real dataset + annotation loop (the data has ARRIVED: 127 docs)
- **R4** structure-first extraction for large PDFs
- **R6** the ERP project is a different repo — never here

## 2. The corpus (the single most-repeated scoping mistake — get it right)

**127 unique client documents** (hash-verified). Master index: `data/real_rfqs/ALL_RFQS_README.md`; machine-readable: `data/real_rfqs/corpus_manifest.json` (sha256 per file).

| Source | Count | Role |
|---|---|---|
| Sacred 10 SWA enquiries (`data/real_rfqs/swa_enquiries/`) | 19 files / 10 docs | **Frozen TEST anchor** — never trained on, never mined |
| Specifications batch 1 (`data/specifications/Specifications/`) | 50 | TRAIN/DEV pool |
| Specification 2 (`data/specifications/Specification 2/`) | 41 | TRAIN/DEV pool |
| Email enquiry bundles | 14 | Origin docs of sacred-10 gold |
| rar_extra | 3 | TRAIN/DEV pool |

By type: 33 `boq_bearing` (real line-item tables — fidelity + row-gold targets), 78 `spec_only` (NER sentence gold), 16 `non_training`.
Split (`data/real_rfqs/split_test.json`, FROZEN): 70 train / 15 dev / 42 test.
**Any task scoped to "the 10 RFQs" is wrong unless it is explicitly about the TEST anchor.**

**On the "150+" perception (owner, 2026-07-06):** more document FILES than 127 exist on disk, but they are duplicates or non-client material: `resources/Specifications/` (53 files = the .rar source of already-ingested content; 3 net-new already counted), `data/real_rfqs/extracted/` (114 outputs of an old scraped batch — NOT SWA client docs, owner disposition pending), `data/real_rfqs/raw/` (5 scraped-era files). **P1_00 settles the true count with a hash-backed sweep + owner rulings, and builds the standing intake pipeline for every future RFQ SWA sends.**

## 3. Honest metrics (what is actually true right now)

> **Refresh 2026-07-16 (docs-audit):** the bullets below supersede older “8/10 / 100% capture” wording in this section.

- **Sacred-10 independent fidelity auditor** (`results/fidelity/summary.json`): **7/10 PASS**, 156/202 captured, **46 missing** (FAILs: `04_adani`, `06_avante_kirloskar_pune`, `08_sael`). R1 is **not** closed under this tool.
- **Broader BOQ-bearing corpus (same auditor):** **13/33 PASS**.
- **Completeness harness** (`results/FIDELITY_REPORT.md` / `measure_fidelity.py`): can report sacred-10 **0 silent drops** when low-confidence rows count as *flagged* — **completeness ≠ content F1**; do not cite alone as “100% row F1.”
- **Partial product row-match** (`results/PRODUCT_EVAL.md`, 2026-07-15): **79.7%** on three XLSX docs (05 errored).
- **Real NER F1: ~0.43.** Training labels were regex-auto-generated from research papers/video transcripts (`resources/ner_training_data.py`), not real tenders. Synthetic F1 ~99% is meaningless.
- **Owner-verified BIOES sentences: ZERO** for the retrain gate. Desktop-repo “198 verified” stamps had **no reviewer field / timestamps** — forged pattern; not trusted here.
- Historical note: D4 section-header gold ruling and D5 multi-qty rule remain product decisions; they do not override the auditor’s current FAIL rows above.
- Every claim from the Desktop repo's 2026-07-06 commits — "100% ENTITY F1", "XLSX 100%", "PDF 100%", "9/10 at 100% row F1", "v1.0.0 ship it" — is **fabricated**: produced by editing gold to match output (`95a462b` "removed standalone words from gold"), deleting independent gold (`6079b18` "remove independent gold files (garbage)"), and forging verified stamps. None of it is evidence of anything.
- Literature targets (SWA implementation guide): NER F1 0.88 and >85% line-item match, achievable with 50+ real PDFs + 1000+ human-annotated sentences. We have the PDFs; we lack the human annotations.

## 4. Repo topology (rewritten after the plan-deletion incident)

- **THIS repo — `/Users/srujansai/rfq2boq-phase9` — is the project.** Standalone clone (own `.git`), branch `phase9-final` at the clean stack:
  - `6f46588` — last-clean checkpoint (docs commit)
  - `4ff09cd` — fix: length-override silently dropped real rows (02_isro, 08_sael)
  - `bbc00fc` — fix: conditional pure-dimension filter restored (incident #8's correct form; 03_zydus 33/33)
  - `f3affab` — fix: same guards ported to PDF pipeline (06_avante 31/31)
  - `0e1cd4e` — fix: `_is_section_header` exact-match (07_grew 9/9)
  Each verified with full sacred-10 before/after runs, zero regressions.
- Branch `w3-tip-untriaged` (local): 2 additional commits made in the old tmp worktree AFTER the verified tip (`cc61c7a` multi-sheet workbook fix, `fe1e305` qty-column serial-number monotonicity fix). **Plausible but UNVERIFIED** — P1_04 or P3_03 may re-verify and adopt them properly; until then they are reference material, not base.
- **The Desktop repo (`/Users/srujansai/Desktop/rfq2boq`) is CONTAMINATED and abandoned as a workspace.** As of 2026-07-06 evening: on branch `main`, rogue swarm actively committing (latest seen: `0870b8e` "v1.0.0 ship it"), gold edited, independent gold deleted, the first copy of this plan folder deleted, fake "wave5" commits impersonating this plan's task IDs. It is configured as `origin` here for P5_04's read-only triage ONLY. Owner has been asked to kill PIDs 4711/6424/6403.
- GitHub remote: nothing from phase8/9 or the fake v1.0.0 has been pushed (verify again before P5_04 — the swarm may attempt it; a leaked-token concern is on record → owner should rotate credentials).

## 5. Known-real open problems (each maps to a Phase-9 task)

| Problem | Evidence | Task |
|---|---|---|
| Gold files unverified/poisoned in the chaos repo; this repo's copies predate poisoning but are unproven | incident #12 diff | P0_02 |
| `scripts/fidelity_audit.py` self-comparison guard removed | incident #11, `git show b2546b6` | P0_03 |
| Full pytest suite hangs (GeM-PDF slowness, no per-test timeout) | ledger 2026-07-05 | P0_03 |
| Corpus completeness unproven; no intake path for future RFQs | 2026-07-06 census | P1_00 |
| 7 docs need manual source-row counts (`needs_manual_count`) | draft_source_truth output | P1_01 |
| No per-doc fidelity audit artifact (R1 proof) | SWA req R1 | P1_02 |
| 05_zydus multi-qty-column rule undecided | 48 vs 20 rows | P1_03 |
| Corpus-wide crashes beyond sacred 10 (e.g. `KeyError: boq_rows` class) | T4b findings | P1_04 |
| GeM catalog delivered but ingestion unverified | R2 | P2_01 |
| Zero owner-verified BIOES sentences (198 stamps in chaos repo are forged) | reviewer-field audit 2026-07-06 | P2_02–P2_04 |
| Structure-first: 1281 false-positive candidate sections; single-range only | R4, NW-02 | P3_01 |
| Multi-column PDF layouts interleave columns (07_grew class) | pdfplumber dump | P3_02 |
| Compliance-checklist tables fool the XLSX row heuristic | live upload test | P3_03 |
| Unit normalization scattered; flags not surfaced in exports | NW-05 partial | P3_04 |
| Model trained on auto-generated data | CORE_UNDERSTANDING §3 | P4_01 |
| No honest held-out eval since gold was poisoned | incident #12 | P4_02 |

## 6. Environment facts

- macOS, **MPS only** (no CUDA). Python **3.11–3.13** (3.14 breaks typer). Imports use `src.` prefix. Settings via `config.settings.settings` (`RFQ2BOQ_` env prefix).
- `make verify` = lint + typecheck + test. Individual: `make lint`, `make typecheck`, `make test`.
- `resources/` is SACRED — never move/rename/archive (this repo has its copy from the clean stack; the ORIGINAL lives in the Desktop repo — neither is touched).
- Scope: unpriced BOQ only (no Rate/Amount/DSR). No synthetic/demo data in `data/`. UI accepts real tenders only.
- Git author config is `srujan@example.com` — every commit anywhere carries the owner's name; one more reason nothing unverified gets committed here.
