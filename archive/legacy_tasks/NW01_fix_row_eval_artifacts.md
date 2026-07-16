# NW-01 — Fix row-level evaluation artifacts (P0, run alone)

You are working on RFQ2BOQ at /Users/srujansai/Desktop/rfq2boq, branch `phase8-clean-slate`.

## 1. GOAL
Make `scripts/eval_honest_rows.py` measure reality. Two proven artifacts make today's numbers wrong-in-both-directions. Fix the EVALUATOR — never the gold.

## 2. CONTEXT (read first)
- `scripts/eval_honest_rows.py` — the row-level evaluator
- `results/eval_honest_rows.json` — latest run (2026-06-11): overall micro F1 24.2%
- `data/real_rfqs/gold/rows/*.rowgold.json` — row gold (DO NOT EDIT)
- `src/pipeline_xlsx.py`, `src/rules/units.py` — how the pipeline emits units/quantities
- `docs/CORE_UNDERSTANDING.md` — honesty rules

## 3. THE TWO PROVEN ARTIFACTS
A. **03 Zydus scores F1=0.0% with 33 gold / 33 predicted.** Counts identical, zero matches → almost certainly unit normalization ("RMT" vs "rmt" vs "Rmt"), quantity type (str "270" vs float 270.0), or material-similarity threshold on short names ("15MM"). Diagnose by printing the first 5 gold/pred pairs side by side before changing anything.
B. **04 Adani evaluates the wrong file.** The eval runs on `BOQ PAGEadani proj.pdf` but the extraction fix targeted `BOQ PAGE2adani proj.pdf`; rowgold is for the PAGE2 file. Verify which PDF the rowgold's 45 entries actually describe (open the rowgold, compare materials against both PDFs), then point the eval at the matching source file.

## 4. STEPS
1. Reproduce: `python3 scripts/eval_honest_rows.py` — confirm 03=0.0%, 04 file used.
2. Print a diagnostic diff for 03 (gold row vs nearest pred row with similarity/qty/unit comparison values).
3. Fix evaluator-side normalization only: normalize units via ONE shared function (reuse `src/rules/units.py` canonicalizer — do not write a second table), cast quantities to float before ±5% compare, and document the material-similarity threshold (keep 0.6; do NOT lower it to inflate scores — if you change it in ANY direction, justify with 5 worked examples in the REPORT).
4. Fix the 04 file-routing bug.
5. Re-run the eval; save `results/eval_honest_rows.json`.

## 5. VERIFICATION (run, paste real output)
```bash
python3 scripts/eval_honest_rows.py
make verify
git diff --stat data/real_rfqs/gold/   # MUST be empty
```

## 6. ACCEPTANCE CRITERIA
- 03 Zydus: score reflects manual spot-check (pick 5 gold rows, show whether the pipeline genuinely produced them; the score must agree with what you show).
- 04 Adani: evaluated against the correct source PDF; report the honest number even if low.
- Zero changes under `data/real_rfqs/gold/`. `make verify` passes.
- REPORT includes the before/after summary table and the per-enquiry numbers — whatever they are.

## 7. FORBIDDEN
Editing gold. Lowering thresholds to chase a number. Using pipeline output as gold. Claiming improvement without the diagnostic diff.
