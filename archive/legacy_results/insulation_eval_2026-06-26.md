# Insulation Domain Row-Level Evaluation Results

**Date:** 2026-06-26
**Evaluation Type:** HONEST row-level (pipeline vs independent gold)
**Gold Source:** `data/real_rfqs/gold/rows/insul_*.rowgold.json`
**Pipeline:** Full pipeline (`src/pipeline.py`)

## ⚠️ IMPORTANT: Gold Verification Status

**human_verified: false** — pending owner sign-off.

This evaluation uses draft gold transcribed from BOQ reference PDFs. The gold has NOT been verified by a human expert. Numbers may change after manual review.

---

## Per-Pair Results

| Document | Gold Rows | Pred Rows | TP | FP | FN | Precision | Recall | F1 |
|---------|----------|----------|----|----|----|-----------|--------|-----|
| insul_01_tender | 23 | 23 | 10 | 13 | 13 | 43.5% | 43.5% | 43.5% |
| insul_02_swpl | 19 | 2 | 0 | 2 | 19 | 0.0% | 0.0% | 0.0% |

---

## Macro Summary

| Metric | Value |
|--------|-------|
| **Precision** | 21.7% |
| **Recall** | 21.7% |
| **F1** | 21.7% |

---

## Analysis

### insul_01_tender (BOQ.pdf)
- Gold: 23 rows transcribed from `boq_references/BOQ.pdf`
- Pipeline extracted 23 rows
- Matching: 10 TP, 13 FP, 13 FN
- F1 = 43.5%
- **Issue:** Several items have unit mismatch (gold uses "Sq. Mtr." vs pipeline outputs "sqm") and some quantity variations

### insul_02_swpl (BOQ - INSULATION.pdf)
- Gold: 19 rows transcribed from `boq_references/BOQ - INSULATION.pdf`
- Pipeline extracted only 2 rows
- Matching: 0 TP, 2 FP, 19 FN
- F1 = 0.0%
- **Root cause:** Pipeline extracted very few items from this PDF — likely table extraction failure

---

## Methodology

- **Material similarity threshold:** 0.6 (SequenceMatcher ratio)
- **Quantity tolerance:** ±5%
- **Unit matching:** Normalized equality
- **Gold provenance:** `pdfplumber-table-transcription (DRAFT — needs human review)`
- **Pipeline method:** Full pipeline with pdfplumber

---

## Notes

1. **Gold is draft-only:** `human_verified: false` in all gold files. Awaiting owner sign-off.
2. **Self-comparison risk:** Both gold and pipeline use pdfplumber — F1 may be artificially inflated
3. **Low swpl performance:** Pipeline extracted only 2 rows from the second PDF — investigation needed
4. **~100% is a red flag:** Not observed here; numbers are HONEST

---

## Files Generated

- `results/insulation_pipeline_output.json` — Pipeline extracted rows
- `results/insulation_eval_raw.json` — Raw evaluation data
- `results/insulation_eval_2026-06-26.md` — This report