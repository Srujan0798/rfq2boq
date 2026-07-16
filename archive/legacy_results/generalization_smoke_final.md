# Generalization Smoke Report

**Date:** 2026-06-08
**Purpose:** Honest run on files the pipeline was never tuned or given gold for.
**Rule:** These files are *not* the 10 SWA sacred. Improvements must help here before claiming progress.

## Summary

- Files run: 2
- Total items across all: 6
- Files with errors: 0

## Per-file

### rfq_bridge_RFQ1904_047.pdf
- Items: 6
- Time: 1.9s
- Bad rows (empty material or invalid qty): 0
- Sample rows:
  - 1. orcement steel | 15000.0 kg
  - 1. 0 concrete for | 300.0 m³
  - 1. tressed steel s | 5000.0 kg
  - 1. ck anchor 25m | 200.0 nos
  - 1. astomeric bear | 13478.0 nos

### cpwd_Guidelines_for_Hassle_Free_Bid_Submission_1778959268.pdf
- Items: 0
- Time: 139.5s
- Bad rows (empty material or invalid qty): 0
- Sample rows:

## Notes for next steps
- If a file produces 0 or very few usable rows: investigate page classification, table detection (pdfplumber fallback), or NER recall on that vocabulary.
- Never add special cases for particular filenames. Fix the general layers.
- After owner 09/10 sign-off + retrain, re-run this smoke on a fresh batch of additional_real to measure real improvement on unseen.
