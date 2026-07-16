# TASK: Complete Final Integration Test Suite — Agent-G6

## 1. GOAL
Create a comprehensive integration test that verifies the entire pipeline end-to-end on all 10 SWA enquiries, with honest metrics reporting, so we know exactly what works and what doesn't before handover.

## 2. CONTEXT
Files to read FIRST (in order):
- `tests/e2e/test_all_enquiries.py` — current e2e tests (basic smoke tests)
- `tests/e2e/test_full_pipeline.py` — full pipeline tests
- `scripts/eval_product.py` — evaluation script
- `scripts/final_integration_test.py` — may already exist
- `src/pipeline.py` — main pipeline
- `data/real_rfqs/swa_enquiries/MANIFEST.md` — list of all 10 enquiries

Current state:
- e2e tests verify "no crash" and "items > 0" but don't verify correctness
- No single command runs all 10 enquiries and reports honest match rates
- Evaluation is scattered across multiple scripts
- Need a unified test that: runs all 10, compares to gold, reports per-enquiry metrics

## 3. DELIVERABLES
Create or modify EXACTLY these files:
- [ ] `scripts/final_integration_test.py` — COMPLETE: run all 10 enquiries, compare to gold, report metrics
- [ ] `tests/e2e/test_all_enquiries.py` — add correctness assertions (not just "no crash")
- [ ] `tests/e2e/test_match_rates.py` — NEW: test that match rates meet minimum thresholds
- [ ] `docs/TEST_RESULTS.md` — NEW: living document with latest test results

## 4. STEPS
1. Read context files (Section 2)
2. Design `scripts/final_integration_test.py`:
   - Load all 10 enquiries from `data/real_rfqs/swa_enquiries/`
   - For each: run `Pipeline().run()`, save results
   - For XLSX enquiries (02, 03, 05, 08): compare extracted rows to XLSX ground truth
   - For PDF enquiries (01, 04, 06, 07, 09, 10): compare to entity gold or row gold if available
   - Report per-enquiry: items extracted, items in gold, match rate, precision, recall, F1
   - Report overall: average match rate, weighted average
   - Save results to `results/final_integration_results.json`
3. Implement the script with clear output:
   ```
   === RFQ2BOQ Final Integration Test ===

   01 GSECL (PDF):  2/?? items, match: N/A (no gold)
   02 ISRO (XLSX):  8/8 items,  match: 36.4%
   03 Zydus Matoda: 33/33 items, match: 5.1%
   04 Adani (PDF):  12/?? items, match: N/A
   05 Zydus Animal:  48/48 items, match: 43.8%
   06 Avante (PDF):  14/?? items, match: N/A
   07 Grew (PDF):    23/?? items, match: N/A
   08 SAEL (XLSX):  12/12 items, match: 70.6%
   09 GeM (PDF):     ??/?? items, match: N/A (currently hangs)
   10 GeM (PDF):     54/?? items, match: N/A

   Average match rate (XLSX with gold): 38.975%
   ```
4. Add `tests/e2e/test_match_rates.py`:
   - Test that 02 ISRO match rate >= 30%
   - Test that 05 Zydus Animal match rate >= 35%
   - Test that 08 SAEL match rate >= 60%
   - Skip 03 (known low match rate — G4 will fix)
5. Create `docs/TEST_RESULTS.md` template
6. Run verification (Section 5)

## 5. VERIFICATION
Run these commands. Each must produce the expected output:

```bash
# Final integration test runs
$ python3 scripts/final_integration_test.py
EXPECT: completes for all 10 enquiries, prints per-enquiry metrics

# Match rate tests pass (where applicable)
$ python3 -m pytest tests/e2e/test_match_rates.py -v
EXPECT: >= 2 passed, 1 skipped (03), 0 failed

# All e2e tests still pass
$ python3 -m pytest tests/e2e/test_full_pipeline.py -v
EXPECT: 11 passed

# No regressions
$ python3 -m pytest tests/unit/ -q --tb=no
EXPECT: >= 200 passed, 0 failed
```

## 6. ACCEPTANCE CRITERIA
- [ ] `scripts/final_integration_test.py` runs all 10 enquiries without crashing
- [ ] Per-enquiry metrics are reported honestly
- [ ] XLSX enquiries show match rates against ground truth
- [ ] Results saved to `results/final_integration_results.json`
- [ ] `docs/TEST_RESULTS.md` created with template
- [ ] Match rate tests pass for 02, 05, 08
- [ ] All existing tests still pass
- [ ] No ruff errors

## 7. CONSTRAINTS
- All imports use `src.` prefix
- Honest metrics only — never grade pipeline against itself
- Do NOT modify `config/constants.py`
- Keep test runtime reasonable (skip 09 if it still hangs, with clear documentation)

## 8. DEPENDENCIES
- **Blocked by:** G1 (09 GeM hang fix — if 09 still hangs, skip it in integration test)
- **Blocks:** P8T8 (final handover)
- **Parallel-safe with:** G2, G3, G4, G5
- **Shared files:** `tests/e2e/test_all_enquiries.py`

## 9. GOTCHAS
- 09 GeM may still hang — handle gracefully with timeout and skip
- 01 GSECL may still produce only 2 items — report honestly, don't fake numbers
- Row gold for PDFs may not exist — report "N/A" for match rate, not 0%
- The integration test should be FAST to run — don't retrain models, use cached ones
- Results file should be gitignored or updated with each run
