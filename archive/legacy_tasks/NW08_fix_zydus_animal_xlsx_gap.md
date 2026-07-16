# NW-08 — Fix 05 Zydus Animal Pharmez: XLSX extraction gap (48.7% → target ≥90%) (P0)

You are working on RFQ2BOQ at /Users/srujansai/Desktop/rfq2boq, branch `phase8-clean-slate`.

## 1. GOAL
Enquiry 05 (Zydus Animal Health Pharmez XLSX) scores 48.7% F1 — pipeline extracts 48 rows but gold has 67. Find and fix the 19 missing rows without editing gold.

## 2. CONTEXT (read first)
- `data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/` — contains:
  - `Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx` — main BOQ
  - `Copy of TDS TO BE FILLED BY VENDOR-INSULATION.xlsx` — spec sheet (probably skip)
- `data/real_rfqs/gold/rows/05_zydus_animal_pharmez.rowgold.json` — 67 gold entries, `human_verified=False`
- `src/pipeline_xlsx.py` — XLSX extraction path
- Note: `human_verified=False` means the gold may have errors too. Build a diff table and note any gold entries that look suspicious.

## 3. STEPS
1. Load the XLSX manually with openpyxl/pandas and count all non-empty data rows. Print the first 10 and last 10 rows. Compare to what the pipeline produces.

2. Build honest diff: for each gold entry mark FOUND / MISSING / WRONG-QTY against pipeline output. Paste this table in your REPORT.

3. Find the dominant failure mode:
   - Are rows being skipped due to header-detection logic?
   - Are multi-row merged cells collapsing items?
   - Is the quantity column being misidentified?
   - Are rows with 0 qty or blank description being dropped?

4. Fix the pipeline (NOT the gold) for whatever is genuinely missing.

5. Note in your REPORT any gold entries that appear to be duplicates or errors (given human_verified=False) — do NOT edit gold, just flag them.

## 4. VERIFICATION (run, paste real output)
```bash
python3 -c "
import openpyxl
wb = openpyxl.load_workbook('data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx', read_only=True)
ws = wb.active
rows = [r for r in ws.iter_rows(values_only=True) if any(c for c in r)]
print('Non-empty rows:', len(rows))
for r in rows[:5]: print(r)
"
python3 scripts/eval_honest_rows.py   # report 05 F1 before and after
make verify
```

## 5. ACCEPTANCE CRITERIA
- 05 Zydus Animal F1 ≥ 90% OR a documented per-row explanation for every remaining miss
- No regression on enquiries 01/03/04/06/08/09/10 (must stay 100%)
- Diff table in REPORT covering all 67 gold rows
- `make verify` passes; zero gold edits

## 6. FORBIDDEN
Editing gold. Hardcoding row ranges for this specific file. Dropping gold entries by claiming they are errors (flag only, don't edit).
