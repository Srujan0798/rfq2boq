# REPORT: Lane E6 — Insulation batch run

**Date:** 2026-06-22
**Files:** 11 insulation tender PDFs
**Timeout:** 60s per file

## Results Table

| File | Rows | Time (s) | Status |
|------|------|----------|--------|
| TENDER.pdf | 0 | 60 | TIMEOUT |
| TENDER (1) (1).pdf | 0 | 60 | TIMEOUT |
| Tender (2).pdf | 0 | 60 | TIMEOUT |
| Tender (3).pdf | 0 | 60 | TIMEOUT |
| Tender (4) (1).pdf | 0 | 60 | TIMEOUT |
| Tender (5).pdf | 0 | 60 | TIMEOUT |
| TENDER - INSULATION.pdf | 0 | 60 | TIMEOUT |
| TENDER SPECIFICATION- CHW PIPE INSULATION.pdf | 5 | 23.17 | OK |
| TENDER SPECIFICATION-ACCOUSTIC INSULATION.pdf | 2 | 13.92 | OK |
| SWPL-PER-HVAC-RFQ-02 (Thermal & Acoustic Insulation).pdf | 1 | 33.52 | OK |
| Copy of Insulation Enquiry - SAEL.pdf | 13 | 50.97 | OK |

**Total:** 21 rows across 11 files in 541.58s

## Top 3 Files by Row Count

1. **Copy of Insulation Enquiry - SAEL.pdf**: 13 rows — best demo candidate
2. **TENDER SPECIFICATION- CHW PIPE INSULATION.pdf**: 5 rows
3. **TENDER SPECIFICATION-ACCOUSTIC INSULATION.pdf**: 2 rows

## Files That Timed Out

- TENDER.pdf
- TENDER (1) (1).pdf
- Tender (2).pdf
- Tender (3).pdf
- Tender (4) (1).pdf
- Tender (5).pdf
- TENDER - INSULATION.pdf

## Honest Note

**Row count ≠ quality.** These are pipeline output, not gold annotation. The 7 timed-out files likely contain valid BOQ data but the pipeline hangs on OCR or NLP stages. Demo-ready candidates are the 4 files that completed successfully.

## Demo Candidates (Ready)

| File | Rows |
|------|------|
| Copy of Insulation Enquiry - SAEL.pdf | 13 |
| TENDER SPECIFICATION- CHW PIPE INSULATION.pdf | 5 |
| TENDER SPECIFICATION-ACCOUSTIC INSULATION.pdf | 2 |
| SWPL-PER-HVAC-RFQ-02 (Thermal & Acoustic Insulation).pdf | 1 |

## Next Steps

1. Investigate timeout cause for 7 files (likely OCR or NLP model loading)
2. Add more generous timeout for next run
3. Annotate gold for top files to enable honest eval