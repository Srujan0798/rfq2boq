# NW-03 — 04 Adani: close the 16-vs-45 row gap honestly (P1)

You are working on RFQ2BOQ at /Users/srujansai/Desktop/rfq2boq, branch `phase8-clean-slate`.

## 1. GOAL
04 Adani currently extracts 16 items; its rowgold has 45 entries. Find out which side is right, row by row, and fix the pipeline (NOT the gold) for whatever is genuinely missing.

## 2. CONTEXT (read first)
- `data/real_rfqs/gold/rows/04_adani.rowgold.json` — 45 entries, human_verified, pdfplumber-table-transcription
- `data/real_rfqs/swa_enquiries/04_adani/` — there are TWO BOQ PDFs (`BOQ PAGEadani proj.pdf` and `BOQ PAGE2adani proj.pdf`) + 2 spec PDFs. First determine which file(s) the 45 gold entries cover — possibly BOTH (the gold may span the two BOQ pages).
- `src/ingest/table_extractor.py` — parent/child tracking added 2026-06-11 (`map_to_boq_rows`)
- NW-01's corrected evaluator (must be merged before this task)

## 3. STEPS
1. Build the honest diff: for each of the 45 gold rows, mark FOUND / MISSING / WRONG-QTY against the pipeline output of the correct file(s). Paste this table in your REPORT.
2. If the gold spans both BOQ PDFs: make the pipeline (or the eval harness) process both files for enquiry 04 the way an estimator would — but generically (multi-file enquiry support), not `if enquiry=="04"`.
3. Fix the dominant extraction failure modes found (truncated materials at 60 chars, duplicate collapse, 0-qty rows, missed child rows).
4. Re-run NW-01's evaluator for 04.

## 4. VERIFICATION (run, paste real output)
```bash
python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf'); print(len(r.boq_items)); [print(f'{row.material[:60]} | {row.quantity} {row.unit}') for row in r.boq_items[:10]]"
python3 scripts/eval_honest_rows.py
make verify
```

## 5. ACCEPTANCE CRITERIA
- The FOUND/MISSING table is in the REPORT (45 rows accounted for).
- ≥30 of 45 gold rows FOUND with qty within ±5% and sane units, OR a documented per-row reason why the remainder are not extractable (e.g., gold transcribed from a spec PDF the pipeline correctly skips).
- No regression on 01/06/07/09/10 item counts (paste the 10-file loop output).
- `make verify` passes; zero gold edits.

## 6. FORBIDDEN
Editing gold to shrink the 45. Filename-specific branches. Counting duplicates as distinct FOUNDs.
