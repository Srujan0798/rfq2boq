# TASK P4_02: The honest evaluation — frozen TEST split, once, reported as-is — Agent-P4-2

## 1. GOAL
Produce the project's headline numbers the only way they can be trusted: the retrained model + full pipeline evaluated ONCE against the frozen 42-doc TEST split with owner-verified gold, reported exactly as measured — the numbers that go into the internship report and to SWA.

## 2. CONTEXT
Files to read FIRST (in order):
- `tasks/phase9/02_ANTI_CHEAT_PROTOCOL.md` — Rules 1, 2, 5, 6, 8 all converge on this task
- `scripts/eval_ner.py`, `scripts/eval_honest_rows.py` (FROZEN — you run them, never edit them)
- `data/real_rfqs/split_test.json` — the 42 TEST docs; `data/real_rfqs/gold/` — sentence gold (sacred 10) + rowgold
- `models/ner_real_v1/TRAINING_MANIFEST.json` — what you're evaluating
- `docs/CORE_UNDERSTANDING.md` §2 — the targets table (0.88 NER F1 / >85% row match at data maturity)

Current state:
- Sentence-level NER gold exists for the sacred 10 (restored + locked in P0_02). The other 32 TEST docs have NO sentence gold — entity-level eval runs where gold exists; that limitation is REPORTED, not papered over. Row-level fidelity covers all TEST boq_bearing docs via source_truth (P1_01).
- Baseline for comparison: the old auto-trained model's ~0.43 real F1 (from CORE_UNDERSTANDING; re-measure it in this same run so old-vs-new is apples-to-apples).

## 3. DELIVERABLES
- [ ] `results/final_eval/EVAL_REPORT.md` — the canonical honest numbers:
  - Entity-level: P/R/F1 micro + macro + per-type, on sacred-10 sentence gold — for BOTH old model and `ner_real_v1` (same script, same gold, same run)
  - Row-level: FidelityAuditor verdicts + capture/extra/flag counts for every TEST boq_bearing doc
  - End-to-end: per-doc processing time (the <60s target), flag statistics
  - Limitations section: gold coverage (10 of 42 docs for entities), starved entity types, anything anomalous
- [ ] `results/final_eval/raw/` — every command's full stdout, saved verbatim (the audit trail)
- [ ] `scripts/run_final_eval.py` — one-command reproduction: runs everything above from scratch, asserts frozen-hash + provenance gates first, writes both deliverables
- [ ] If any number looks "too good" (per-type F1 > 0.95, any 100%): a written investigation in the report (Rule 2 red-flag discipline) — find the cause (small support? leakage? bug?) before publishing

## 4. STEPS
1. Read context; verify gates: `check_frozen_hashes.py`, `check_gold_provenance.py`, `check_split_leakage.py` all green — paste outputs.
2. Build `run_final_eval.py` (orchestrates the FROZEN eval scripts; it may add orchestration but NEVER re-implements scoring).
3. Dry-run the harness on TRAIN-pool docs to shake out crashes (results discarded; TEST stays untouched until the real run).
4. THE run: single execution over TEST. Save everything under `results/final_eval/raw/`.
5. Write the report; run the red-flag review on your own numbers; commit.
6. REPORT verbatim key numbers to orchestrator (who reproduces via `run_final_eval.py` before acceptance — expect identical output; nondeterminism must be eliminated or explained).

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 scripts/run_final_eval.py                     # EXPECT: completes; writes results/final_eval/
diff <(python3 scripts/run_final_eval.py --print-summary) <(grep -A20 "SUMMARY" results/final_eval/EVAL_REPORT.md | head -25)   # EXPECT: numbers match
python3 scripts/check_frozen_hashes.py                # EXPECT: intact (you changed no ruler)
git diff HEAD~1 --stat -- scripts/eval_*.py scripts/measure_*.py data/real_rfqs/   # EXPECT: empty
make lint && python3 -m pytest tests/unit tests/integration -q
```

## 6. ACCEPTANCE CRITERIA
- [ ] Old-vs-new comparison on identical gold/script/run — the improvement claim is internally controlled
- [ ] Every reported number traceable to a raw stdout file
- [ ] Limitations section complete (an expert reading ONLY the report understands exactly what was and wasn't measured)
- [ ] Zero edits to frozen eval code/gold/split (Gate 5 diff check empty)
- [ ] Whatever the numbers are, they are published — a disappointing F1 with a clear data-volume explanation is an acceptable outcome; a massaged one is project failure

## 7. CONSTRAINTS
- ONE evaluated configuration: no cherry-picking across checkpoints/thresholds after seeing TEST numbers (model selection happened on val in P4_01). If the run reveals a genuine BUG (crash, wiring), fix + re-run is fine — but log both runs in raw/ and explain
- DEV docs: usable for a pre-flight sanity pass if needed; say so in the report if used
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P4_01; P1_01/P1_02 (row ruler); P0_02/P0_03 (locked gold + ruler)
- **Blocks:** P5_03 (the report consumes these numbers)
- **Parallel-safe with:** P5_01
- **Shared files:** none writable (that's the point)

## 9. GOTCHAS
- The old model may fail to even load if quarantine touched its path — the baseline comparison then uses the documented historical ~0.43 with a note, rather than resurrecting a quarantined checkpoint into the pipeline.
- Entity eval on 10 docs has wide confidence intervals — report support counts next to every F1 so nobody over-reads a per-type number with n=12.
- `eval_honest_rows.py` may still contain the incident-#10 methodology change (rate-only exclusion) — whatever P0_03 found: the report must STATE which methodology the frozen script implements, so the number is interpretable.
- Runtime: 42 docs incl. big GeM PDFs — budget an hour+; the structure-first routing (P3_01) is what makes the <60s/doc target plausible; report per-doc times honestly either way.
