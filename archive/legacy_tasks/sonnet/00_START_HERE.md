# START HERE — Sonnet completion workspace for RFQ2BOQ

**You are the execution agent.** This folder is your entire world. Work the tasks in numeric order, one at a time, on branch `phase8-clean-slate`, from `/Users/srujansai/Desktop/rfq2boq`. Do not invent scope. Do not skip verification. Do not touch anything marked owner-only.

## The mission (from the SWA brief + 2026-06-11 meeting — verbatim intent)
Transform unstructured construction tender documents (RFQ PDFs/XLSX) into structured Bill of Quantities: extract material, quantity, unit, location, dimension, standard, action, grade; link relations; rule-validate; export Excel/JSON. Client bar: **R1 — every detail in the source captured or flagged, zero loss; R2 — GeM catalog as closed NER reference; R3 — the ~100-doc dataset is the training/validation foundation; R4 — structure-first extraction on large PDFs.**

## THE CORPUS (misread by every previous agent — read twice)
"The RFQs" = **ALL ~105+ client documents**, not the sacred 10 alone:
1. Sacred 10 enquiries — `data/real_rfqs/` (held-out TEST anchor)
2. Specifications batch 1 — `data/specifications/Specifications/` (≈51 docs; same content as `resources/Specifications.rar`, dedupe by sha256)
3. Specification 2 — `data/specifications/Specification 2/` (≈42 docs incl. XLSX BOQs)
4. Email enquiry bundles — Grew Solar / SAEL / AVANTE / Adani / Zydus folders under `data/specifications/`

Everything you build — manifest, annotation, training, fidelity, regression, combinations — covers the FULL corpus.

## Audited ground truth as of 2026-07-04 (your starting point — trust nothing rosier)
- **No trained model is in production.** `src/nlp/pipeline.py:63-66` is pattern-only by design. All output so far = regex + gazetteer + tables.
- **Overall capture fidelity = 27%** (829 src rows, 223 extracted, 637 missing — `results/fidelity_audit_summary.txt`). Per-doc: 01_gsecl 1%, 09_gem 14%, 10_gem 12%, 07 43%, 06 72%, 04 83%; 02/03/05/08 XLSX "100%" (05 hides 48-vs-20 over-capture).
- **The ruler is unstable:** source-row counts changed run-to-run (01: 3→397; 09: 22→157→207). Fidelity % is meaningless until T1 freezes source truth.
- **28 gold files stamped `human_verified:true` by agent commits — UNTRUSTED** until owner re-confirms (T2).
- **Checkpoints exist (v2/v3/v5/swa10/lora-real) — none promoted, none trusted.** `lora-real` has no data provenance → quarantine (T0).

## How you work (the loop — every task, no exceptions)
1. Read `RULES.md` (again).
2. Open the next `T*.md` file. Execute its STEPS exactly.
3. Run its VERIFICATION commands. Paste real output into your REPORT.
4. Append one evidenced entry to `LEDGER.md` (date · command · stdout excerpt · commit hash).
5. Mark the task **READY FOR VERIFICATION** in the ledger. STOP. The orchestrator/owner re-runs your commands and marks CLOSED. Only then take the next task.
6. Owner-gated tasks (T1 confirmations, T2, T5 sign-offs) cannot be closed by you — prepare the materials, request review, stop.

## Task index
| File | Task | Gate | Owner-gated? |
|---|---|---|---|
| `T0_freeze_motion.md` | Kill training runs, quarantine unproven model | 0 | no |
| `T1_freeze_ruler_source_truth.md` | Owner-verified source-row truth (the keystone) | 1 | **confirm step** |
| `T2_gold_trust_reset.md` | Audit the 28 `human_verified:true` stamps | 1 | **yes** |
| `T3_corpus_manifest_split.md` | Full-corpus manifest + frozen TRAIN/DEV/TEST | 1 | no |
| `T4a_fidelity_sacred10.md` | 100% capture-or-flag on sacred 10 | 5 | no |
| `T4b_fidelity_full_corpus.md` | Same bar, whole corpus | 5 | confirm step |
| `T5_human_gold_factory.md` | ≥1,000 verified sentences, ≥30 row-gold docs | 2 | **yes** |
| `T6_genuine_training.md` | Train on human labels only; promote only if it wins | 3 | no |
| `T7_eval_and_eternal_guarantee.md` | One-shot TEST eval + regression/combination CI | 4+6 | fresh doc from owner |
| `T8_ship.md` | Deliverables, demo, handoff, owner checklist | 7 | **checklist** |

**Constitution:** `tasks/ETERNAL_PROTOCOL.md` (v2) — audit history, requirement ladder, discipline rules. This folder is its execution form.
