# NW-05 — One canonical unit/quantity normalizer everywhere (P1)

You are working on RFQ2BOQ at /Users/srujansai/Desktop/rfq2boq, branch `phase8-clean-slate`.

## 1. GOAL
Unit/qty normalization is duplicated across the pipeline, the XLSX path, the evaluators, and validators — drift between copies is exactly what produces fake-looking mismatches (e.g., 03 Zydus 33/33 rows scoring 0%). Consolidate to ONE normalizer; everything imports it.

## 2. CONTEXT (read first)
- `src/rules/units.py` — should become the single source (`CANONICAL_UNITS` from `config/constants.py`)
- Find every other normalization table/function: `grep -rn "sqm\|rmt\|cum\|normalize_unit\|canonical_unit" src/ scripts/ | grep -v test` and list ALL hits in your REPORT before changing anything
- Known aliases that must map identically: `Sq meter/Sq. Mtr./SQM/sqm`, `RMT/Rmt/rmt/rm`, `cu.m/m³/cum`, `no./nos/Nos./NOS`, `Kg/kg/KG`, `ltr/L`
- `scripts/eval_honest_rows.py`, `scripts/validate_product.py`, `src/pipeline_xlsx.py`, `src/domain/boq_assembler.py`

## 3. STEPS
1. Inventory every normalizer copy (paste the list).
2. Extend `src/rules/units.py` to cover the union of all alias tables + quantity coercion helper (`to_float_qty`: handles "1,200", "270.00", int/float/str).
3. Replace each local copy with imports of the shared functions. Delete the dead copies.
4. Add a table-driven test: every alias above → its canonical form, identical via every public entry point.

## 4. VERIFICATION (run, paste real output)
```bash
python3 -m pytest tests/unit/test_units*.py tests/unit/test_pipeline_xlsx.py -q
python3 scripts/eval_honest_rows.py     # numbers may legitimately move — report before/after
make verify
```

## 5. ACCEPTANCE CRITERIA
- `grep -rn "def normalize_unit\|UNIT_ALIASES\s*=" src/ scripts/ | grep -v rules/units | grep -v test` → empty (one definition site).
- All 10 SWA files still process; per-file item counts unchanged (paste loop output).
- Eval before/after table in REPORT with a 3-sentence explanation of any movement.
- `make verify` passes; zero gold edits.

## 6. FORBIDDEN
Editing gold. "Normalizing" gold files on disk. Adding enquiry-specific alias hacks.
