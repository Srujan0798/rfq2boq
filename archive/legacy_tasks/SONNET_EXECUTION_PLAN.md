# SONNET EXECUTION PLAN — sequential, evidence-gated, no deviation

**Issued:** 2026-07-04 by the orchestrator (Fable), from a live audit run this day.
**Constitution:** `tasks/ETERNAL_PROTOCOL.md` (v2) — its Discipline Rules and Honesty Contract bind every task below. Read it first.
**Branch:** `phase8-clean-slate` only. One task at a time, in order. REPORT with real command output after each.

---

## CORPUS DEFINITION (read this twice — past agents got it wrong)

**"The RFQs" = EVERY client document we hold, not just the sacred 10.** The full corpus:

1. The **sacred 10** SWA enquiries (`data/real_rfqs/`) — held-out TEST anchor.
2. **Specifications batch 1** (`data/specifications/Specifications/`, ≈51 docs; same content as `resources/Specifications.rar` — dedupe by sha256).
3. **Specification 2** (`data/specifications/Specification 2/`, ≈42 docs incl. XLSX BOQs).
4. **Email enquiry bundles** (Grew Solar / SAEL / AVANTE / Adani / Zydus folders) — real spec+BOQ+TDS triples.

≈105+ documents total. ALL of them are SWA RFQ-family documents. ALL enter the manifest (T3), the annotation factory (T5), training via their human-verified labels (T6, TRAIN split only), the per-doc fidelity sweep (T4b), and the regression + combination suites (T7b). Any agent that scopes work to "the 10" has misread the project — the meeting requirement (R3) is exactly this ~100-doc dataset as the training/validation foundation, and the client's bar (R1: every detail captured, zero loss; R2: GeM catalog reference) applies to EVERY document and EVERY combination of them.

---

## AUDITED TRUTH (2026-07-04 — the baseline you start from; do not trust anything rosier)

1. **No trained model is in production.** `src/nlp/pipeline.py:63-66` is pattern-only BY DESIGN ("No LoRA, no pre-trained models… until a genuine model"). Every output so far = regex + gazetteer + table extraction.
2. **Overall capture fidelity TODAY: 27%** (829 source rows, 223 extracted, 637 missing — `results/fidelity_audit_summary.txt`). Per-doc: 01_gsecl 1%, 09_gem 14%, 10_gem 12%, 07_grew 43%, 06_avante 72%, 04_adani 83%; only 02/03/05/08 (XLSX) at 100% — and 05's "100%" hides over-capture (48 extracted vs 20 source).
3. **The ruler itself is broken:** source-row counts changed massively between runs (01: 3→397; 09: 22→157; 10: 10→85; 04: 45→54; 06: 31→43; 07: 9→21). Until source counts are frozen and owner-verified, every fidelity % is noise.
4. **28 gold files carry `human_verified:true` stamped by agent commits** (986d88c, 03d3459) — UNTRUSTED (incident-#4 pattern) until Srujan personally re-confirms each.
5. **Model checkpoints** (v2/v3/v5/swa10/lora-real) are experiments; none promoted; `lora-real` (trained Jul 3–4) has NO training-data provenance → quarantined by default. Trainer still contains an env-gated silver path (`RFQ2BOQ_ALLOW_SILVER`).

---

## HARD RULES (violating any = stop, report, revert)

- Machine labels (silver/pseudo/auto) never train anything. Delete the `RFQ2BOQ_ALLOW_SILVER` path in T6 — until then never set it.
- Never edit gold or source-truth counts to make a number pass. Gold changes = Srujan only.
- Fidelity is per-document: PASS = captured+flagged == source AND dropped == 0 AND over-capture == 0. No totals-netting.
- ~100% correctness claims on held-out data = you cheated. Stop and report instead.
- Only mark tasks "READY FOR VERIFICATION" — orchestrator/owner closes them after re-running your commands.
- Append every action to the ETERNAL_PROTOCOL ledger: date + command + stdout excerpt + commit. One entry per real action.

---

## TASKS (strict order)

### T0 — Freeze motion (½ hr)
Kill any running training jobs. Move `models/rfq2boq-ner-lora-real` → `models/quarantine/`. Commit nothing else.
**Accept:** no training processes; quarantine dir exists; ledger entry.

### T1 — FREEZE THE RULER: owner-verified source truth (the keystone)
For each sacred-10 doc, produce `data/real_rfqs/source_truth.json`: `{doc_id, source_row_count, method, page/sheet refs}`. Machine-count as DRAFT; **Srujan confirms each count by opening the document** (esp. 01_gsecl 3-vs-397 and 09/10 GeM). `measure_fidelity`/`fidelity_audit` must read ONLY this file for source counts thereafter.
**Accept:** file committed with `owner_confirmed:true` per doc (Srujan's action); both harnesses read it; re-run shows stable counts twice.

### T2 — Gold trust reset
List all 28 `human_verified:true` files with their stamping commit. Any not personally reviewed by Srujan → flip to `false` (keep content as draft). Extend `check_gold_provenance.py`: `true` requires `reviewer:"srujan"` + date.
**Accept:** zero unaudited `true` flags; provenance check green.

### T3 — Corpus manifest + frozen split (Gate 1)
`corpus_manifest.json` over ALL docs (105+ specifications, sacred 10, bundles): sha256, source, client, type, format. Freeze TRAIN/DEV/TEST (`split_test.json` = sacred 10 + 5 never-processed Spec-2 docs; split by client-project). Add CI `test_no_test_split_leakage`. Re-audit gazetteer: remove TEST-only-mined terms.
**Accept:** manifest complete; split committed; leakage test green in `make verify`.

### T4 — Extraction to 100% capture-or-flag (pattern path, no ML)
**T4a — sacred 10 first** (they have frozen source truth from T1). Fix per-doc, worst first: 01_gsecl (multi-page Schedule-B), 09/10 GeM (structure-first multi-range + section false-positive filter), 07_grew, 06_avante, 04_adani, 05 over-capture (configurable multi-qty rule + dedupe). Zero silent drops — flag what you can't parse.
**T4b — then the WHOLE corpus:** extend `source_truth.json` (machine-draft + owner confirm, batched) and the fidelity sweep to every BOQ-bearing doc in Specifications 1 + Specification 2 + bundles. Same per-doc PASS bar.
**Accept:** per-doc PASS on all 10, then on every BOQ-bearing corpus doc (or documented blocker Srujan accepts); fidelity harness output committed; run twice, stable.

### T5 — Human-gold factory (Gate 2 — owner-gated)
Batch the 429 draft sentences + doc drafts through `review_annotation.py` side-by-side reports for Srujan's sign-off, prioritizing TRAIN-split BOQ-bearing docs and MATERIAL-rich sentences. Row gold with page/cell provenance.
**Accept:** ≥1,000 verified sentences + ≥30 verified row-gold docs, every one `reviewer:"srujan"`. Agents cannot close this task.

### T6 — Genuine training (Gate 3)
Delete the silver/pseudo code paths from `train_lora_ner_real_only.py` entirely. Train on `human_verified:true` TRAIN split only; tune on DEV only; log every run (data-manifest hash → `results/training_log.md`). Promote into the pipeline ONLY if it beats pattern-NER on DEV; else patterns stay production and say so.
**Accept:** trainer has no machine-label path (grep proves it); training log with manifest hash; promotion decision recorded with DEV numbers.

### T7 — Honest eval + eternal guarantee (Gates 4+6)
(a) One-shot full-pipeline run on frozen TEST + one never-seen doc from Srujan → per-doc entity F1, row fidelity, catalog accuracy → `results/`, verbatim, better or worse. No fix-rerun loops on TEST.
(b) Build `tests/regression/test_corpus_exact.py` (every owner-verified doc → its exact BOQ) and `tests/regression/test_combinations.py` (seeded subsets/bundles/orderings → union invariance, order-independence, no cross-doc bleed). Wire both into `make verify`.
**Accept:** TEST numbers committed; both suites green twice from clean checkout.

### T8 — Ship (Gate 7)
Update `deliverables/` + `HANDOFF.md` with T7's exact numbers; demo flow verified (upload real tender → BOQ + flags + catalog matches); UI/CLI/API/Docker smoke-tested.
**Owner-only checklist for Srujan:** push commits + set default branch; rotate embedded GitHub token; T1/T2/T5 sign-offs; obtain SWA's real GeM export; chase remaining R3 PDFs.
**Accept:** all gates CLOSED in ETERNAL_PROTOCOL ledger with reproduced evidence.

---

## COMPLETION CLAIM (the only one allowed)
"100% capture-or-flag fidelity per document on owner-verified source truth; corpus regression + combination invariance enforced in CI; honest held-out F1 = X; catalog accuracy = Y; non-cheating proven by fresh-document audit." Fill X and Y with whatever T7 actually produces.
