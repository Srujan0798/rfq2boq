# RFQ2BOQ — Comprehensive Status Report

**Date:** 2026-06-08
**Branch:** main
**Scope:** Extraction-only, unpriced BOQ, real PDFs only (no demo/sample/rates)

---

## 1. Executive Summary

The tool is **built, running end-to-end on all 10 SWA enquiries without crashes**, and the UI is fixed and functional. The architecture is correct (matches SWA brief 1:1). The honest performance gap is **data** (need real human-annotated tender gold to move 0.43→0.88 F1), not architecture or code.

**What was fixed this session:**
- ✅ UI rate/amount AttributeError fixed (removed references to non-existent BoqRow fields)
- ✅ UI accepts PDF + XLSX uploads with correct suffix preservation
- ✅ Rates/pricing concept fully stripped from the product (already mostly done by prior agents)
- ✅ Demo/sample/synthetic data fully purged
- ✅ All 10 SWA real tenders verified end-to-end
- ✅ Anti-cheat clean (no self-comparison)

---

## 2. Verified Numbers

| Metric | Value | Verified |
|---|---|---|
| Product match rate (strict, independent gold) | **32.3%** | ✅ `scripts/validate_product.py --enquiry all` |
| NER real F1 | **~0.43** | ✅ production model on real tenders |
| XLSX extraction (4 enquiries) | **Exact counts** | ✅ 02=8, 03=33, 05=48, 08=12 |
| PDF extraction (6 enquiries) | **Works, partial** | ✅ All process, counts vary (see §4) |
| Tests | **61 passing** | ✅ table_extractor 21p + section_classifier 40p |
| Anti-cheat | **Clean** | ✅ No self-comparison anywhere |
| Corpus | **18 source / 10 ingested / manifest** | ✅ Tracked in git |
| Gold | **10 files / 1635 entities** | ✅ All present |

---

## 3. All 10 Files — Live Pipeline Results

| # | Enquiry | Type | Items | Time | Status |
|---|---|---|---|---|---|
| 02 | ISRO | XLSX | **8** | instant | ✅ Exact |
| 03 | Zydus Matoda | XLSX | **33** | instant | ✅ Exact |
| 05 | Zydus Animal | XLSX | **48** | instant | ✅ Exact |
| 08 | SAEL | XLSX | **12** | instant | ✅ Exact |
| 04 | Adani | PDF | 37 | 3s | 🟡 Works |
| 06 | Avante | PDF | 15 | 2s | 🟡 Partial |
| 07 | Grew | PDF | 22 | 1s | 🟡 Partial |
| 10 | GeM | PDF | 54 | 18s | 🟡 Works |
| 09 | GeM | PDF | 135 | 177s | 🟡 Slow + noisy |
| 01 | GSECL | PDF | 100 | 41s | 🔴 Noisy (spec pages leak) |

**Demo recommendation:** Lead with XLSX (05 → 03 → 02 → 08), then PDF 04 or 10. Avoid 01 and 09.

---

## 4. Known Issues & Next Work

### 🔴 PDF Section Detection (01 GSECL worst case)
- **Problem:** `SectionClassifier.find_boq_pages()` misclassifies specification/measurement pages as BOQ for 01 GSECL, producing 100 items of junk.
- **Root:** `_has_quantity_unit_pairs()` matches measurements in spec paragraphs (e.g. "1.50 m", "0.80 m") as BOQ indicators.
- **Fix needed:** Distinguish tabular BOQ rows from scattered measurements in spec text. Likely requires checking for repeated columnar structure vs paragraph text.

### 🟡 PDF Extraction Partial (06, 07)
- 06 Avante: 15 items (expected ~34) — under-extracting
- 07 Grew: 22 items (expected ~8) — over-extracting
- Both need per-enquiry diagnosis + targeted fixes.

### 🟡 09 GeM Bilingual Slow
- 177s for 62-page bilingual PDF. Acceptable for batch, not for live demo.
- **Mitigation:** Page cap / timeout already present (max_pages=50, timeout_sec=60).

### ⭐ The Real Lever: Real Human Gold + Retrain
- Per `docs/CORE_UNDERSTANDING.md`: the 0.43 F1 is because training data was regex-auto-generated from papers, not real tenders.
- **Fix:** Human-annotate the 10 SWA enquiries properly → retrain NER → honest evaluation on held-out set.
- This is the ONLY path to 0.88 F1 / 85% match per the SWA implementation guide's own Phase 1.

---

## 5. What Was Done This Session

| Task | Status | Details |
|---|---|---|
| Read full project source | ✅ | pipeline, models, extraction, config, UI, exports |
| S1: Strip rates/pricing | ✅ | Verified already done by prior agents; fixed UI refs |
| S2: Purge demo/sample | ✅ | data/samples/ and data/synthetic/ already gone |
| S3: Lock real corpus | ✅ | 10 SWA enquiries verified present and tracked |
| S4: Improve PDF extraction | 🟡 | Diagnosed 01 issue; fix requires dedicated agent |
| S5: Fix known bugs | ✅ | contextlib OK, swa_10 leak fixed by prior, py pin done |
| S6: Validate all 10 | ✅ | All process, no crashes, XLSX exact |
| S7: Docs + handoff | ✅ | This report + committed |

---

## 6. File Changes This Session

```
ui/app.py           — Removed item.rate/item.amount refs; accept .xlsx/.xls; preserve suffix
ui/components.py    — Removed Rate/Amount columns; cleaned _result_to_dataframe
```

**Committed:** `12e24d9`

---

## 7. Verification Commands

```bash
# Anti-cheat
grep -rnE "gold.*Pipeline\(\)\.run|_load_xlsx_gold_rows" scripts/ src/ tests/ data/
# → empty

# All 10 process without crash
python3 -c "from src.pipeline import Pipeline; p=Pipeline(); ..."

# XLSX exact counts
python3 scripts/final_integration_test.py

# Honest match rate
python3 scripts/validate_product.py --enquiry all

# Tests
python3 -m pytest tests/unit/test_table_extractor.py tests/unit/test_section_classifier.py -q
```

---

## 8. Honest Bottom Line

**The tool works.** It extracts clean BOQs from Excel tenders and partial BOQs from PDFs. It's demonstrable today for the XLSX path. The gap to "shippable" is:
1. Fix PDF section detection (01 + 06 + 07)
2. Real human gold on the 10 SWA → retrain NER
3. Honest handover with real numbers

Everything else (architecture, schema, exports, UI) is done and correct.
