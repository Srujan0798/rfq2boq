# RFQ2BOQ — Complete Agent Task Assignments

**Generated:** 2026-06-11
**Current State:** 44.8% macro F1 (honest), 43.8% micro F1
**Goal:** Fix extraction bugs + create honest row-level evaluation + retrain NER

---

## Analysis Summary

### What's Actually Broken

| File | Type | eGold | rGold | Pred | F1 | Real Issue |
|------|------|-------|-------|------|-----|-----------|
| 01 GSECL | PDF | 3 | 3 | 3 | 0.0% | **Entity gold expects short material names**; pipeline outputs full descriptions. Row-level: CORRECT (3/3). |
| 02 ISRO | XLSX | 5 | 7 | 4 | 66.7% | Gold has 2 junk entries ("Structure & civil", "Note..."). 3/4 real materials match. |
| 03 Zydus Matoda | XLSX | 17 | 33 | 33 | 56.0% | False positives: "15MM", "20MM" (dimension text as material). Missing "Option 2/3" (headers, not materials). |
| 04 Adani | PDF | 13 | 45 | 2 | 0.0% | **REAL BUG**: Pipeline extracts dimension headers ("19mm thick - SA/DH-AHU/TFA duct") instead of materials. |
| 05 Zydus Animal | XLSX | 53 | 67 | 48 | 93.1% | Good. Minor FP: one extra item. |
| 06 Avante | PDF | 20 | 31 | 31 | 78.4% | 100% recall but 11 false positives (over-extraction). |
| 07 Grew Solar | PDF | 4 | 9 | 9 | 61.5% | 100% recall but 5 false positives. |
| 08 SAEL | XLSX | 12 | 17 | 14 | 92.3% | Good. 2 minor false positives. |
| 09 GeM | PDF | 102 | 22 | 22 | 0.0% | **Entity gold expects 102 individual words**; pipeline outputs 22 complete BOQ rows. Row-level: CORRECT. |
| 10 GeM | PDF | 52 | 10 | 10 | 0.0% | **Entity gold expects 52 individual words**; pipeline outputs 10 complete BOQ rows. Row-level: CORRECT. |

### Root Cause Categories

1. **Evaluation Mismatch (BIGGEST)**: Entity-level gold expects short material names. Pipeline outputs complete BOQ descriptions. Rowgold files exist and ARE correct. Need row-level evaluation.
2. **04 Adani PDF Bug (CRITICAL)**: Pipeline extracts table headers/dimensions instead of actual material descriptions.
3. **Dimension False Positives (MEDIUM)**: "15MM", "19mm thick" etc. extracted as materials.
4. **Over-extraction (MEDIUM)**: Avante (+11), Grew (+5) produce junk extra items.
5. **Gold Data Junk (LOW)**: ISRO gold has non-material entries.
6. **NER Model (SEPARATE)**: v5 overfits to synthetic data. Needs real-data retraining.

---

## Agent Task 1: Fix 04 Adani PDF Extraction (CRITICAL)

**Priority:** P0 — Without this, PDF extraction is fundamentally broken for some docs
**Estimated Effort:** 4-6 hours
**Agent Type:** Coder with PDF/table extraction expertise

### Problem
04 Adani PDF `BOQ PAGE2adani proj.pdf` produces:
```
Predicted: "19mm thick - SA/DH-AHU/TFA duct"
Predicted: "32mm thick with 7 mill glass cloth..."
```
Expected (from entity gold): "MS chilled water pipe insulation nitrile rubber" (13 times)

The pipeline is extracting **dimension/location headers** from the PDF table, not the actual material descriptions. The real BOQ has rows like:
- Material: "MS chilled water pipe insulation nitrile rubber"
- Location: "SA/DH-AHU/TFA duct"
- Thickness: "19mm"

But the pipeline is treating the thickness/location column as the material.

### Files to Modify
- `src/ingest/table_extractor.py` — How tables are parsed from PDF
- `src/ingest/pdf_extractor.py` — How BOQ pages are identified
- `src/pipeline.py` — How extracted rows are mapped to BoqRow

### Reproduction
```bash
cd /Users/srujansai/Desktop/rfq2boq
python3 -c "
from src.pipeline import Pipeline
p = Pipeline()
r = p.run('data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf')
for row in r.boq_items:
    print(f'{row.material} | {row.quantity} {row.unit}')
"
```

### Acceptance Criteria
- [ ] 04 Adani produces at least 10 distinct material rows
- [ ] Materials are actual insulation materials, not dimension headers
- [ ] Run `python3 scripts/eval_honest.py --enquiry 04_adani` shows F1 > 50%
- [ ] `make verify` still passes

### Context
The Adani PDF has a table with columns like: Thickness | Location | Material | Quantity | Unit. The pipeline may be reading columns in the wrong order, or the table structure is unusual. Look at the raw table extraction output to understand the column layout.

---

## Agent Task 2: Fix Entity Gold + Create Row-Level Evaluation (HIGH)

**Priority:** P1 — Without this, all "0% F1" scores are misleading
**Estimated Effort:** 3-4 hours
**Agent Type:** Coder + data analyst

### Problem
Current `scripts/eval_honest.py` compares pipeline `boq_items[i].material` (full descriptions) against entity gold `MATERIAL` entities (short strings). This causes:
- 01 GSECL: 3/3 correct rows → 0% F1 (full desc vs short name)
- 09 GeM: 22/22 correct rows → 0% F1 (22 complete rows vs 102 individual words)
- 10 GeM: 10/10 correct rows → 0% F1 (10 complete rows vs 52 individual words)

Rowgold files (`data/real_rfqs/gold/rows/*.rowgold.json`) exist and contain complete row data (material, quantity, unit).

### Files to Create/Modify
- Create `scripts/eval_honest_rows.py` — Row-level evaluation
- Modify `data/real_rfqs/gold/swa_01_gsecl_wanakbori_tmd8.json` — Add missing MATERIAL entities for first 2 items
- Modify `data/real_rfqs/gold/swa_02_isro_vssc.json` — Remove non-material junk entries

### Reproduction
```bash
# Current broken eval
python3 scripts/eval_honest.py
# Shows 01_gsecl=0%, 09_gem=0%, 10_gem=0% even though rows are correct
```

### Acceptance Criteria
- [ ] `scripts/eval_honest_rows.py` runs successfully
- [ ] Row-level evaluation shows 01 GSECL ≥ 90% F1 (it's actually correct)
- [ ] Row-level evaluation shows 09 GeM ≥ 90% F1 (22/22 correct)
- [ ] Row-level evaluation shows 10 GeM ≥ 90% F1 (10/10 correct)
- [ ] Entity gold 01 GSECL has 3 MATERIAL entities (currently only 1)
- [ ] Entity gold 02 ISRO has no junk entries ("Structure & civil", "Note..." removed)
- [ ] Both eval scripts save results to `results/`

### Context
The rowgold files are honest and human-verified. Use them as ground truth. For row matching, match on (material similarity ≥ 0.6 AND quantity matches AND unit matches). Quantity matching can be fuzzy (±5% or exact).

---

## Agent Task 3: Fix Dimension False Positives (MEDIUM)

**Priority:** P2 — Reduces over-extraction
**Estimated Effort:** 2-3 hours
**Agent Type:** Coder

### Problem
Pipeline extracts dimension/location text as materials:
- 03 Zydus Matoda: "15MM", "20MM"
- 04 Adani: "19mm thick - SA/DH-AHU/TFA duct"
- 06 Avante: "13 mm thick insulation for supply air ducts in return air path."
- 07 Grew: "ACOUSTIC LINING Supply,Installation..."

These are either:
1. Table header rows ("15MM", "20MM")
2. Dimension + location without actual material name
3. Section headers masquerading as items

### Files to Modify
- `src/pipeline_xlsx.py` — Add stronger header filtering
- `src/ingest/table_extractor.py` — Reject rows that are purely dimensions
- `src/domain/boq_assembler.py` — Post-process filter for dimension-only materials

### Acceptance Criteria
- [ ] 03 Zydus Matoda false positives eliminated ("15MM", "20MM" gone)
- [ ] 06 Avante false positives reduced by at least 50% (from 11 to < 6)
- [ ] 07 Grew false positives reduced by at least 50% (from 5 to < 3)
- [ ] No reduction in true positives (recall must not drop)
- [ ] `make verify` still passes

### Context
Look at `src/pipeline_xlsx.py` around line 400+ where `is_header_row` and filtering logic lives. The `TOTAL_KEYWORD_PATTERN` exists but dimension-only rows slip through.

---

## Agent Task 4: Retrain NER on Real Gold Data (SEPARATE TRACK)

**Priority:** P2 — Long-term quality improvement
**Estimated Effort:** 1-2 days
**Agent Type:** ML engineer / Coder

### Problem
- v5 model: val F1=0.755, sacred 10 F1=0.188 (overfits to synthetic)
- Pattern-based NER currently used in production
- Synthetic data (210 docs) + pseudo-labeled (61 docs) don't generalize
- Only 20 real gold docs exist

### Files
- `scripts/train_lora_ner_v5.py` — Current training script
- `data/annotations_combined/` — Training data
- `models/rfq2boq-ner-lora-v5/` — Current model

### Goal
Train a new model (v6) using ONLY real gold data + minimal augmentation. No synthetic data.

### Steps
1. Check `data/annotations_combined/gold_train.json` — how many real annotated docs?
2. If < 50 docs, report "insufficient data — need more human annotations"
3. If ≥ 20 docs, train v6 with real data only
4. Evaluate v6 on sacred 10 honestly
5. Compare v6 vs pattern-based NER on real PDFs

### Acceptance Criteria
- [ ] v6 training completes without errors
- [ ] v6 sacred 10 F1 > v5 sacred 10 F1 (0.188)
- [ ] v6 MATERIAL F1 > 0.0 (v5 MATERIAL F1 is 0.0)
- [ ] Report saved to `results/v6_eval.json`

### Context
The HANDOFF.md admits: "Synthetic data boosts internal metrics but does NOT generalize to real documents." Don't repeat this mistake. Use only real annotations.

---

## Agent Task 5: End-to-End Validation & HANDOFF Update (FINAL)

**Priority:** P1 — Must run after Tasks 1-3 complete
**Estimated Effort:** 2-3 hours
**Agent Type:** Coder + technical writer

### Goal
Run complete honest evaluation and update HANDOFF.md with real numbers.

### Steps
1. Run `python3 scripts/eval_honest.py` (entity-level)
2. Run `python3 scripts/eval_honest_rows.py` (row-level, from Task 2)
3. Run `make verify`
4. Update `HANDOFF.md`:
   - Replace "100%" claims with actual numbers
   - Document both entity-level and row-level F1
   - Document which files have evaluation mismatch vs real bugs
   - Update "Known Limitations" section honestly
5. Create `results/FINAL_HONEST_REPORT.md` with:
   - Per-file breakdown
   - Root cause analysis
   - What was fixed vs what remains

### Acceptance Criteria
- [ ] HANDOFF.md has no "100%" claims unless verified
- [ ] Row-level and entity-level scores both documented
- [ ] `make verify` passes
- [ ] Git tree is clean

---

## Quick Reference: How to Assign

Copy-paste each task block above into your agent prompt. Add this header:

```
You are working on the RFQ2BOQ project at /Users/srujansai/Desktop/rfq2boq.

[Task block here]

Start by reading the relevant source files. Make changes. Test with the reproduction command.
Return a summary of what you changed and the before/after metrics.
```

## Dependencies

```
Task 1 (04 Adani fix)  ──┐
Task 2 (Row eval)       ──┼──→ Task 5 (Final validation)
Task 3 (False pos)      ──┘
Task 4 (NER retrain) ──→ Independent track
```

Tasks 1, 2, 3, 4 can run in parallel. Task 5 needs 1-3 to complete first.
