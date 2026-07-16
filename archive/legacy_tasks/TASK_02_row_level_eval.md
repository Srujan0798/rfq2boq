# TASK 2 — Create Row-Level Evaluation Script (P1)

You are working on the RFQ2BOQ project at /Users/srujansai/Desktop/rfq2boq.

## Problem

Current `scripts/eval_honest.py` compares pipeline `boq_items[i].material` (full descriptions like "Supply & application of 100 mm thick Mineral Wool mattresses...") against entity-level gold `MATERIAL` entities (short strings like "Mineral Wool"). This causes artificial 0% F1 even when the pipeline extracts correct rows.

For example:
- 01 GSECL: pipeline gets 3 correct rows, entity gold has 3 MATERIAL entities, but F1=0% because text doesn't match
- 09 GeM: pipeline gets 22 correct rows, entity gold has 102 individual words, F1=0%

## Row-Level Gold Exists

`data/real_rfqs/gold/rows/*.rowgold.json` contains complete row data:
```json
{
  "entries": [
    {"item_no": 1, "material": "...", "quantity": "1600", "unit": "sqm"},
    ...
  ]
}
```

## What to Create

Create `scripts/eval_honest_rows.py` that:
1. Loads rowgold files from `data/real_rfqs/gold/rows/`
2. Runs pipeline on each of the 10 SWA files
3. Matches predicted rows to gold rows by:
   - Material similarity >= 0.6 (using `difflib.SequenceMatcher`)
   - Quantity matches (exact or ±5%)
   - Unit matches (normalized)
4. Reports per-file and overall F1
5. Saves results to `results/eval_honest_rows.json`

## Also Fix

- `data/real_rfqs/gold/swa_01_gsecl_wanakbori_tmd8.json`: Only 1 MATERIAL entity exists, but the PDF has 3 BOQ items. Add MATERIAL entities for the first 2 items.
- `data/real_rfqs/gold/swa_02_isro_vssc.json`: Remove non-material junk entries "Structure & civil" and "Note: Area and rates are subject to revision."

## Reproduction

```bash
cd /Users/srujansai/Desktop/rfq2boq
python3 scripts/eval_honest.py  # Shows broken scores
# After your fix:
python3 scripts/eval_honest_rows.py  # Should show honest row-level scores
```

## Acceptance Criteria

1. `eval_honest_rows.py` runs without errors
2. 01 GSECL shows >= 90% F1 (3 correct rows)
3. 09 GeM shows >= 90% F1 (22 correct rows)
4. 10 GeM shows >= 90% F1 (10 correct rows)
5. Results saved to `results/eval_honest_rows.json`
6. `make verify` passes

## DO NOT

- Modify any `.rowgold.json` files (those are honest ground truth)
- Use pipeline output as gold (self-comparison cheat)

## Return

The `eval_honest_rows.py` script + before/after scores + verify output.
