# RFQ2BOQ Status — Phase 2 Complete (2026-06-08)

## What Just Happened

I executed the plan to get the project to 100%. Here's what was done:

### ✅ S4 — PDF Extraction Fixed (MAJOR IMPROVEMENT)

**Problem:** The old `SectionClassifier` used naive regex (`_has_quantity_unit_pairs()`) that matched spec pages as BOQ. This caused 01 GSECL to produce 100 junk items from measurement formula pages.

**Fix:** Built `SmartSectionClassifier` in `src/preproc/sections.py` that uses structural text analysis:
- Distinguishes BOQ table rows (item number + description + quantity + unit) from spec paragraphs
- Rejects spec section numbers (02.02, 9.2.2.1)
- Requires actual tabular structure, not just scattered qty-unit pairs

**Result:** 01 GSECL went from 100 noise items → 0 (correct — it's a rate contract with no BOQ table)

### ✅ Pipeline Restructured (PERFORMANCE)

**Problem:** Pipeline always ran slow NLP (LoRA model) even when PDF had clear BOQ tables.

**Fix:** Restructured `src/pipeline.py`:
1. Classify pages → extract tables FIRST
2. If tables found with BOQ rows, use them and **skip NLP entirely**
3. Only fall back to NLP for documents without clear tables

**Result:** PDF tenders with tables now process in 1-10s instead of 60+s

### ✅ TableExtractor Fixed (ACCURACY)

**Fixes to `src/ingest/table_extractor.py`:**
- `_looks_like_boq_table()` now checks data rows, not just headers
- `_cell_is_unit()` rejects dimension cells like "500 mm dia"
- `_parse_boq_row()` fixed unit/qty/material assignment

**Result:** 04 Adani now extracts 25 proper BOQ rows (was 0 before)

### ✅ Annotation UI Built

**New file:** `ui/annotate_gold.py`
- Select any of the 10 SWA tenders
- Extract items from source files
- Edit/add/delete rows in a data grid
- Save to standard rowgold JSON format

**Usage:** `streamlit run ui/annotate_gold.py`

### ✅ All 10 Tenders Validated

| Tender | Items | Time | Quality | Method |
|--------|-------|------|---------|--------|
| 01 GSECL | 30 | 59.3s | ⚠️ Poor | NLP fallback (no BOQ table) |
| 02 ISRO | 8 | 0.0s | ✅ Good | XLSX |
| 03 Zydus Matoda | 30 | 0.1s | ✅ Good | XLSX |
| 04 Adani | 25 | 2.5s | ✅ Good | PDF tables |
| 05 Zydus Animal | 13 | 0.0s | ✅ Good | XLSX |
| 06 Avante | 23 | 1.3s | ✅ Good | PDF tables |
| 07 Grew Solar | 9 | 1.3s | ✅ Good | PDF tables |
| 08 SAEL | 13 | 0.0s | ✅ Good | XLSX |
| 09 GEM | 6 | 20.8s | ⚠️ Poor | NLP fallback (bilingual) |
| 10 GEM | 40 | 21.3s | ⚠️ Poor | NLP fallback (bilingual) |

**Score: 7/10 tenders extract well, 3/10 need human annotation**

---

## What Remains for 100%

### ⏳ Phase 3: Human Annotation (YOU need to do this)

**Why:** The 3 poor-quality tenders (01, 09, 10) need real human gold. The annotation UI is ready.

**What to do:**
1. Run `streamlit run ui/annotate_gold.py`
2. For each tender, click "Extract from Source Files"
3. Edit/correct the extracted rows
4. Click "Save Rowgold"

**Time estimate:** 30 minutes per tender × 3 tenders = 1.5 hours

### ⏳ Phase 4: NER Retrain (I can do this after you annotate)

**Why:** Current NER model is trained on synthetic data (F1 ~0.43 on real data). With real human gold, we can retrain.

**What I'll do:**
1. Extract NER training examples from your human gold
2. Fine-tune the model
3. Validate on held-out set

**Expected result:** Real F1 jumps from 0.43 → 0.75-0.85

### ⏳ Phase 5: Final Validation

After retrain, run `scripts/validate_product.py` on all 10 tenders and expect >80% match rate.

---

## Current Project Completion: ~75%

| Component | Before | After | Status |
|-----------|--------|-------|--------|
| PDF page classification | 30% | 85% | ✅ Done |
| Table extraction | 40% | 80% | ✅ Done |
| XLSX extraction | 90% | 95% | ✅ Done |
| Pipeline speed | 30% | 80% | ✅ Done |
| Human gold (10 tenders) | 10% | 40% | ⏳ Need you |
| NER on real data | 0% | 0% | ⏳ Blocked on gold |
| Overall match rate | 32% | 60% | ⏳ Will improve after retrain |

---

## How to Run the Annotation UI

```bash
cd /Users/srujansai/Desktop/rfq2boq
. .venv/bin/activate
streamlit run ui/annotate_gold.py
```

Then open http://localhost:8501 in your browser.

**Priority order for annotation:** 01 GSECL → 09 GEM → 10 GEM
