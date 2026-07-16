# TASK 6 — Final Honest Report & HANDOFF Update (P1)

You are working on the RFQ2BOQ project at /Users/srujansai/Desktop/rfq2boq.

## Task

Create the final honest report and update HANDOFF.md with real numbers.

## What to Do

### 1. Create `results/FINAL_HONEST_REPORT.md`

Run both evaluations and document the results:
```bash
cd /Users/srujansai/Desktop/rfq2boq
python3 scripts/eval_honest.py > results/entity_eval.txt
python3 scripts/eval_honest_rows.py > results/row_eval.txt
```

Create a markdown report with:
- **Executive Summary**: What the project does + current honest state
- **Per-File Breakdown**: All 10 SWA files with:
  - File name, type (PDF/XLSX)
  - Entity-level F1 (from eval_honest.py)
  - Row-level F1 (from eval_honest_rows.py)
  - Number of items extracted
  - Known issues
- **Root Cause Analysis**: Why scores are what they are
  - Evaluation mismatch (entity vs row)
  - Real bugs (04 Adani, 01 GSECL)
  - Over-extraction (06 Avante, 07 Grew)
- **What Was Fixed**: List of fixes applied
- **What Remains**: Known limitations
- **Next Steps**: What needs human annotation vs code

### 2. Update `HANDOFF.md`

Replace the fake numbers with honest ones:
- Remove ALL "100%" claims unless verified
- Replace "Verified total: 153/153 = 100%" with actual numbers
- Document both entity-level and row-level scores
- Add a "Known Limitations" section that is honest
- Add "How to Improve" with realistic steps

### 3. Update `README.md`

- Fix the Results table with honest numbers
- Remove outdated model references
- Add link to FINAL_HONEST_REPORT.md

## Acceptance Criteria

1. `results/FINAL_HONEST_REPORT.md` exists and is readable
2. `HANDOFF.md` has no unverified 100% claims
3. `README.md` has honest metrics
4. `make verify` passes
5. Git tree is clean

## DO NOT

- Invent numbers
- Claim improvements that weren't made
- Remove working features

## Return

The report file path + a summary of what you changed.
