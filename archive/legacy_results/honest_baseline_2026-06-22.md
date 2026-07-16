# Honest Baseline Report — 2026-06-22

> Lane A (Anti-cheat) baseline. Published by `derive_independent_row_gold.py` + `eval_honest.py`.

---

## Entity-level evaluation (eval_honest.py)

**Independent gold:** Manually annotated entities in `data/real_rfqs/gold/swa_*.json`.  
**Prediction source:** `Pipeline()` — independent of gold creation.

| Enquiry | Type | Gold | Pred | P | R | F1 |
|---------|------|------|------|---|---|----|
| 01_gsecl | pdf | 3 | 3 | 0.0% | 0.0% | **0.0%** |
| 02_isro | xlsx | 3 | 4 | 75.0% | 100.0% | **85.7%** |
| 03_zydus_matoda | xlsx | 17 | 16 | 87.5% | 82.4% | **84.8%** |
| 04_adani | pdf | 13 | 2 | 0.0% | 0.0% | **0.0%** |
| 05_zydus_animal | xlsx | 53 | 48 | 97.9% | 88.7% | **93.1%** |
| 06_avante | pdf | 20 | 31 | 19.4% | 30.0% | **23.5%** |
| 07_grew | pdf | 4 | 9 | 44.4% | 100.0% | **61.5%** |
| 08_sael | xlsx | 12 | 14 | 85.7% | 100.0% | **92.3%** |
| 09_gem | pdf | 102 | 22 | 0.0% | 0.0% | **0.0%** |
| 10_gem | pdf | 52 | 10 | 0.0% | 0.0% | **0.0%** |

**Macro P/R/F1: 41.0% / 50.1% / 44.1%** (matches AGENTS.md §1)  
**Micro P/R/F1: 54.1% / 30.8% / 39.3%**

### Breakdown
- XLSX F1 (macro): **89.0%** (4 files) — production-ready
- PDF F1 (macro): **14.2%** (6 files) — needs real annotated training data

---

## Row-level evaluation (eval_honest_rows.json) — SELF-COMPARISON DETECTED

**PROBLEM:** `eval_honest_rows.py` uses `Pipeline()` to produce predictions, then compares against
row gold that was ALSO derived from pipeline-like extraction (pdfplumber). For 4 of 6 PDF enquiries,
the gold method is `pdfplumber-table-transcription` — the SAME library used by the pipeline.

This produces a self-comparison artifact: **100.0% F1 on all 10 enquiries** in `results/eval_honest_rows.json`.

### Gold provenance

| Enquiry | Gold method | Independent? |
|---------|------------|-------------|
| 01_gsecl | pdfplumber-table-transcription | **NO** — same library as Pipeline |
| 02_isro | independent-xlsx-transcription | YES — direct XLSX cell read |
| 03_zydus_matoda | direct-xlsx-hand-transcription | YES — manual XLSX transcription |
| 04_adani | pdfplumber-table-transcription | **NO** — same library as Pipeline |
| 05_zydus_animal | independent-xlsx-transcription | YES — direct XLSX cell read |
| 06_avante | pdfplumber-table-transcription | **NO** — same library as Pipeline |
| 07_grew | pdfplumber-table-transcription | **NO** — same library as Pipeline |
| 08_sael | independent-xlsx-transcription | YES — direct XLSX cell read |
| 09_gem | pdfplumber-position-aware-transcription | **NO** — pdfplumber-derived |
| 10_gem | pdfplumber-gem-per-item-transcription | **NO** — pdfplumber-derived |

### Honest row-level verdict

| Type | Enquiries | Honest F1 | Notes |
|------|-----------|-----------|-------|
| XLSX | 02, 03, 05, 08 | **~89.0%** (entity proxy) | Gold IS independent. Pipeline reads XLSX cells → matches. |
| PDF | 01, 04, 06, 07, 09, 10 | **~14.2%** (entity proxy) | Gold is NOT independent (pdfplumber-derived). Pipeline matches its own extraction method. |
| ALL | 10 | **CLAIMED 100% = SELF-COMPARISON** | The 100% claim in `eval_honest_rows.json` is an artifact. |

**Bottom line:** Row-level 100% is NOT trustworthy. Use entity-level 44.1% macro F1 as the honest baseline.

---

## XLSX gold drift (build_row_gold.py vs human-verified)

Running `build_row_gold.py` against source XLSX files produces different gold vs the
human-verified versions in `data/real_rfqs/gold/rows/`:

| Enquiry | Old (human-verified) | Regenerated | Drift |
|---------|---------------------|-------------|-------|
| 02_isro_vssc | 5 entries | 4 entries | "Structure & civil" (qty=0) was removed by source script |
| 03_zydus_matoda_osd | 33 entries | 33 entries | Same count, minor unit normalization diff |
| 05_zydus_animal | 20 entries | 48 entries | Old gold had manual curation (section prefix item numbers, zero-qty filtering) |
| 08_sael | 17 entries | 14 entries | Old gold included section headers/spec paragraphs later removed |

**Conclusion:** Human-verified gold should be kept, but provenance must be tracked.
Regenerated gold resets `human_verified: false`.

---

## Anti-cheat test status

- `tests/unit/test_anti_cheat.py`: 6 tests — all pass
- `tests/integration/test_self_attack.py`: 14 tests — all pass
- `make verify` step 3-4: Greps for "100% COMPLETE" claims + gold modification checks

### Enhancements needed:
1. [ ] Detect gold provenances matching pipeline method (pdfplumber-table-transcription)
2. [ ] Reject eval scripts that compare Pipeline output to same-library-derived gold
3. [ ] Add gold provenance check to `make verify`
4. [ ] Check that `human_verified` is not set to true on non-verified gold

---

## Summary

| Metric | Honest value | Previously claimed | Status |
|--------|-------------|-------------------|--------|
| Entity F1 (macro) | **44.1%** | 44.1% | ✓ Honest, unchanged |
| Row F1 (XLSX) | **~89%** (proxy) | 100% | ✗ Self-comparison |
| Row F1 (PDF) | **~14%** (proxy) | 100% | ✗ Self-comparison |
