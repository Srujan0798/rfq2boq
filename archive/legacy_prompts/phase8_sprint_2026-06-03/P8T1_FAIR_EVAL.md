# TASK: P8T1 — Fair End-to-End Product Evaluation — Agent-Eval

**Phase:** 8 | **Priority:** P0 (without this we cannot measure real progress) | **Effort:** 1 day

## 1. GOAL
Replace the unfair row-match metric (gold and predicted segmented by different algorithms → 1.8% that understates quality) with an **honest, fair** product evaluation where **gold is produced independently of the prediction pipeline**, and report it via one reproducible command.

## 2. CONTEXT
Current `scripts/validate_product.py` compares:
- gold = human entity-gold → `BOQAssembler` (one segmentation),
- predicted = `XLSXRowPipeline` (different segmentation).
They rarely align 1:1 even when extraction is fine → 1.8%, which is misleading. (An earlier agent "fixed" this by making gold = the pipeline's own output → fake 100%. **That is the cheat. Do not do that.**)

The fair approach has two honest options — implement BOTH levels:
- **Row-level:** build an **independent** canonical row-gold for the 4 XLSX enquiries — a transcription of the estimator's filled XLSX into `BoqRow`s — produced by a **dedicated, simple, deterministic transcriber that does NOT import or call `src.pipeline`/`XLSXRowPipeline`/`BOQAssembler`**. Store as committed gold artifacts. Compare pipeline output against THAT.
- **Entity-level (product):** score the pipeline's extracted entities against the human entity-gold (precision/recall/F1 per entity type) for all enquiries with gold. This is robust to segmentation.

Read first: `scripts/validate_product.py`, `data/real_rfqs/gold/swa_0{2,3,5,8}*.json`, the 4 source XLSX, `src/eval/boq_row_matcher.py`, `config/constants.py`.

## 3. DELIVERABLES
- [ ] `scripts/build_row_gold.py` — reads each XLSX, emits `data/real_rfqs/gold/rows/<id>.rowgold.json` (canonical BoqRows). **Must NOT import `src.pipeline`, `src.pipeline_xlsx`, or `src.domain.boq_assembler`.** Human reviews/corrects the output before it is treated as gold (status field `human-verified`).
- [ ] `scripts/eval_product.py` — single entry point that reports BOTH:
  - row-level match rate per XLSX enquiry vs the independent row-gold,
  - entity-level P/R/F1 per type vs human entity-gold (all gold enquiries).
  Writes `results/PRODUCT_EVAL.md` + `results/product_eval.json`.
- [ ] `tests/unit/test_eval_product.py` — incl. a test asserting the gold builder does **not** import the prediction pipeline (guard against the self-comparison cheat).
- [ ] `results/PRODUCT_EVAL.md` committed with honest numbers + a clear statement of method and independence.

## 4. STEPS
1. `brainstorming`: agree the canonical BoqRow schema and what counts as a TP at row + entity level.
2. Build `build_row_gold.py` (deterministic XLSX → rows). Have the owner spot-check 1–2 files; mark `human-verified`.
3. Build `eval_product.py` reporting both levels. Reuse `BOQRowMatcher` (do NOT change its thresholds).
4. TDD the tests, including the import-independence guard.
5. Run it; commit honest `PRODUCT_EVAL.md`.

## 5. VERIFICATION
```bash
# Independence guard — gold builder must not touch the prediction path
grep -nE "src\.pipeline|XLSXRowPipeline|BOQAssembler" scripts/build_row_gold.py
EXPECT: empty

python3 scripts/eval_product.py --all 2>&1 | tee /tmp/eval.txt
grep -E "row-level|entity-level|F1|match rate" results/PRODUCT_EVAL.md | head
EXPECT: two honest blocks (row-level + entity-level), reproducible

python3 -m pytest tests/unit/test_eval_product.py -v
EXPECT: pass, incl. test_gold_builder_does_not_import_pipeline
```

## 6. ACCEPTANCE CRITERIA
- [ ] Row-gold is provably independent of the pipeline (grep + test).
- [ ] One command prints both row-level and entity-level honest scores with per-enquiry/per-type breakdown.
- [ ] No matcher thresholds changed; no gold-from-prediction; numbers reproducible.
- [ ] `PRODUCT_EVAL.md` states the method and that gold is independent.

## 7. CONSTRAINTS
- The row-gold builder must be deterministic and independent; if a row is ambiguous, leave it for human review, do not guess to match the pipeline.
- Do NOT delete the existing entity-gold; this adds an independent row-gold alongside it.
- No threshold tuning, no per-enquiry hardcoding.

## 8. DEPENDENCIES
- **Blocked by:** P8T0. **Blocks:** P8T4 (extraction work needs an honest yardstick), P8T8.

## 9. GOTCHAS
- 05 Zydus Animal is a wide matrix (many system qty columns + TOTAL) — decide explicitly how the human-verified row-gold represents it; document the choice.
- A row-level result near 100% is suspicious — verify the gold wasn't accidentally derived from the pipeline.
