# NW-09 — Intake and run pipeline on 2 new SWA tenders (P0)

You are working on RFQ2BOQ at /Users/srujansai/Desktop/rfq2boq, branch `phase8-clean-slate`.

## 1. GOAL
Two new SWA RFQ files arrived (2026-06-18). Run the extraction pipeline on both, record results honestly, and identify any pipeline gaps. Do NOT create gold files — that requires human review.

## 2. NEW FILES (in data/incoming/)

### File A: `40_vssc_acoustic_boq.xlsx`
- Client: VSSC (Indian Space Research)
- Type: Acoustic insulation BOQ
- Known structure: 5 BOQ items (Wall & Underdeck Acoustic Insulation SQM 1300, Outdoor Noise Barrier SQM 350, Noise Diffractor RMT 55, Acoustic Louvers SQM 150, plus Structure & civil with no qty)
- Note: merged-cell pattern — description row below the item number row

### File B: `R3_zydus_matoda_osd.xlsx`
- Client: Zydus Pharma SEZ, Matoda (revision R3 of OSD Facility enquiry)
- Type: Thermal insulation for HVAC ducts (Sheets: BOQ, COMPLIANCE)
- Known structure: ~11 numbered line items, but some qty cells contain Excel formulas (=6*15, =4*15) not evaluated values
- Note: pipeline must use `data_only=True` in openpyxl to read formula results, not formula strings

## 3. STEPS
1. Run the pipeline on File A:
   ```python
   from src.pipeline import Pipeline
   r = Pipeline().run('data/incoming/40_vssc_acoustic_boq.xlsx')
   print(len(r.boq_items))
   for i in r.boq_items: print(i.material[:60], '|', i.quantity, i.unit)
   ```
   Expected: ~4-5 items extracted. If 0: debug the XLSX path.

2. Run the pipeline on File B:
   ```python
   r = Pipeline().run('data/incoming/R3_zydus_matoda_osd.xlsx')
   print(len(r.boq_items))
   for i in r.boq_items: print(i.material[:60], '|', i.quantity, i.unit)
   ```
   Expected: ~11 items. If formula cells show as 0 or None: fix `src/pipeline_xlsx.py` to open with `data_only=True`.

3. For any pipeline failure: diagnose and fix generically (not file-specific). Common XLSX issues:
   - Formula cells not evaluated → use `data_only=True`
   - Merged cells → iterate merged ranges
   - Qty in wrong column → column-detection logic

4. Write results to `results/new_tenders_2026-06-18.json`:
   ```json
   {
     "40_vssc_acoustic": {"extracted": N, "items": [...]},
     "R3_zydus_matoda": {"extracted": N, "items": [...], "formula_cells_found": true/false}
   }
   ```

5. Run the full eval to confirm no regression:
   ```bash
   python3 scripts/eval_honest_rows.py
   ```

## 4. VERIFICATION (run, paste real output)
```bash
python3 -c "import json; d=json.load(open('results/new_tenders_2026-06-18.json')); [print(k, d[k]['extracted'], 'items') for k in d]"
python3 scripts/eval_honest_rows.py | tail -10
make verify
```

## 5. ACCEPTANCE CRITERIA
- File A: ≥4 items extracted with correct materials and units
- File B: ≥8 items extracted including formula-evaluated quantities (not formula strings)
- Full 10-enquiry eval unchanged (no regression)
- `make verify` passes; zero gold edits

## 6. FORBIDDEN
Creating or editing gold files. Adding file-specific branches. Claiming 100% without independent gold to compare against.
