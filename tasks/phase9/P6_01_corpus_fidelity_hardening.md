# TASK: Corpus Fidelity Hardening — Agent-P6-A

## 1. GOAL
Raise the broader-corpus fidelity pass rate above the current 13/33, and fix the `07_grew_solar_narmadapuram` regression (previously verified 100%, now failing at 9/11 captured).

## 2. CONTEXT
Files to read FIRST:
- `docs/CORE_UNDERSTANDING.md` — why fidelity is measured this way, and why gaming it is worthless
- `src/pipeline.py` — the extraction entrypoint; look at `_run_impl` and the `extract_column_aware` vs `extract` comparison logic (was the site of the last regression, in `04_adani`)
- `src/ingest/pdf_extractor.py` — table/row extraction logic, especially `extract_position_aware_rows`, `extract_digit_columns`, `extract_boq_rows_from_split_quantity_page`
- `data/real_rfqs/source_truth.json` — the independent ground-truth row counts per document; this is what you are graded against, never edit it to make a doc "pass"
- `results/fidelity/summary.json` — current pass/fail state (regenerate it yourself first, don't trust a stale copy)

Current state:
- Sacred-10 reference set: 01, 02, 03, 05, 09, 10 PASS; **04, 06, 07, 08 FAIL** (rows going missing, not just flagged)
- Broader 33-doc corpus: 13 PASS / 20 FAIL
- `07_grew_solar_narmadapuram` specifically regressed from a previously-verified 100% to 9/11 — find out what changed and why; check `git log -p -- src/pipeline.py src/ingest/pdf_extractor.py` for anything touching this path since the last time it passed.

## 3. DELIVERABLES
- [ ] Root-cause analysis written to `results/fidelity/P6_01_root_cause.md` — one paragraph per failing sacred-10 doc (04, 06, 07, 08) explaining *why* rows are missing, with line numbers
- [ ] Fixes in `src/pipeline.py` and/or `src/ingest/pdf_extractor.py` — no changes to `data/real_rfqs/source_truth.json` unless you find and can prove a genuine ground-truth error (if so, document the proof: page number, exact row count, screenshot-equivalent evidence)
- [ ] `tests/integration/test_sacred10_fidelity.py` — updated only if the fix legitimately changes expected behavior (not to make a broken test "pass")

## 4. STEPS
1. Run `PYTHONPATH=. python3.12 scripts/audit_fidelity_per_doc.py --all` to get the current true baseline — do not trust any previously-reported number.
2. For each of 04, 06, 07, 08: open the actual source PDF and the audit's per-doc report in `results/fidelity/<doc_id>.audit.md`, find exactly which rows are missing and why.
3. Fix the root cause in the extraction code — not by special-casing a doc_id, but by fixing the general logic that fails for that row shape/layout.
4. Re-run the audit after each fix. Do not move to the next doc until the current one is verified fixed by the audit tool itself.
5. Once sacred-10 is clean, re-run `--all` and see how many of the other 23 broader-corpus docs also improved as a side effect (a good sign the fix was general, not a special case).

## 5. VERIFICATION
```bash
PYTHONPATH=. python3.12 scripts/audit_fidelity_per_doc.py --all
EXPECT: sacred-10 subset (01,02,03,04,05,06,07,08,09,10) — all 10 PASS
EXPECT: broader corpus pass count >= 13 (must not regress below current baseline)

PYTHONPATH=. python3.12 -m pytest tests/integration/test_sacred10_fidelity.py -v
EXPECT: all tests pass

PYTHONPATH=. python3.12 -m pytest tests/ --tb=no -q
EXPECT: no new failures vs the pre-task baseline (run this once before starting to get the baseline)

ruff check src/pipeline.py src/ingest/pdf_extractor.py
EXPECT: All checks passed!
```

## 6. ACCEPTANCE CRITERIA
- [ ] All 10 sacred-reference docs PASS via `scripts/audit_fidelity_per_doc.py --doc <id>`
- [ ] Broader-corpus pass count did not regress (>= 13/33), ideally improved
- [ ] `results/fidelity/P6_01_root_cause.md` explains the actual bug for each of 04/06/07/08 with evidence, not guesses
- [ ] Zero edits to `data/real_rfqs/source_truth.json` without documented proof of a genuine ground-truth error
- [ ] Full test suite has no new failures

## 7. CONSTRAINTS
- Never edit `source_truth.json`, `config/constants.py`, or `tests/` fixtures just to make a number look better
- Never grade against the pipeline's own prior output — always against `source_truth.json` via the audit tool
- All imports use `src.` prefix
- Do not touch `src/api/` (a separate task owns that)

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** P6_04 (final docs audit needs the true final fidelity number)
- **Parallel-safe with:** P6_02, P6_03
- **Shared files:** None overlapping with P6_02/P6_03

## 9. GOTCHAS
- `pdfplumber` `extract_words`/`chars` can hang on certain malformed PDFs — if a test run stalls, check `tests/integration/test_sacred10_fidelity.py` for the specific doc and consider a per-call timeout rather than removing the test
- The `extract_column_aware` vs `extract` comparison in `pipeline.py` was the exact site of the last regression (04_adani, then apparently 07_grew) — read the existing comparison logic carefully before changing it again, it's fragile
- `doc_id` matching in the audit script strips trailing parenthetical suffixes (bundle/spec-split disambiguation) — don't reintroduce that bug
