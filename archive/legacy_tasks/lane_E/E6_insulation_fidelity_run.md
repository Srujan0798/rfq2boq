# TASK: Lane E — Run all 11 insulation tenders end-to-end, fidelity report — Agent-E

**Worktree:** `/Users/srujansai/Desktop/rfq2boq-laneE`
**Branch:** `phase8-laneE`
**Model:** Strong coding (OpenCode paid / Xiaomi)

---

## 1. GOAL
Run the pipeline on all 11 insulation tender PDFs, collect fidelity reports, and identify which tenders are ready to demo vs which need more work — honest numbers, zero data drops flagged.

## 2. CONTEXT
Files to read FIRST:
- `src/pipeline.py` — main pipeline entry point
- `src/domain/boq_assembler.py` — fidelity_report property (added in E2)
- `data/real_rfqs/raw/insulation_hvac/README.md` — what each PDF is
- `results/honest_baseline_2026-06-22.md` — existing honest baseline
- `config/constants.py` — READ ONLY

Insulation tenders (in `data/real_rfqs/raw/insulation_hvac/`):
```
TENDER.pdf, TENDER (1) (1).pdf, Tender (2).pdf, Tender (3).pdf,
Tender (4) (1).pdf, Tender (5).pdf, TENDER - INSULATION.pdf,
TENDER SPECIFICATION- CHW PIPE INSULATION.pdf,
TENDER SPECIFICATION-ACCOUSTIC INSULATION.pdf,
SWPL-PER-HVAC-RFQ-02 (Thermal & Acoustic Insulation).pdf,
Copy of Insulation Enquiry - SAEL.pdf
```

## 3. DELIVERABLES
- [ ] `scripts/run_insulation_batch.py` — batch runner script
- [ ] `results/insulation_batch_run_2026-06-22.json` — per-file output: rows extracted, time, fidelity_report, errors
- [ ] `results/insulation_batch_run_2026-06-22.md` — human-readable table summary
- [ ] `tests/integration/test_insulation_batch_no_crash.py` — asserts pipeline does not crash on any of the 11 files (rows may be 0; crash is not allowed)

## 4. STEPS
1. Activate: `source /Users/srujansai/Desktop/rfq2boq-laneE/.venv-lora/bin/activate`
2. Write `scripts/run_insulation_batch.py`:
   ```python
   import json, time, pathlib
   from src.pipeline import Pipeline

   TENDER_DIR = pathlib.Path("data/real_rfqs/raw/insulation_hvac")
   results = []
   p = Pipeline()
   for pdf in sorted(TENDER_DIR.glob("*.pdf")):
       t0 = time.time()
       try:
           r = p.process_file(str(pdf))
           rows = len(r.rows) if hasattr(r, 'rows') else 0
           fidelity = r.fidelity_report if hasattr(r, 'fidelity_report') else {}
           error = None
       except Exception as e:
           rows, fidelity, error = 0, {}, str(e)
       results.append({
           "file": pdf.name, "rows": rows,
           "time_sec": round(time.time()-t0, 2),
           "fidelity": fidelity, "error": error
       })
       print(f"{pdf.name}: {rows} rows, {round(time.time()-t0,2)}s, error={error}")

   with open("results/insulation_batch_run_2026-06-22.json", "w") as f:
       json.dump(results, f, indent=2)
   print(f"\nTotal: {sum(r['rows'] for r in results)} rows across {len(results)} files")
   ```
3. Run it: `python3 scripts/run_insulation_batch.py` (may take 5–15 min for 11 PDFs)
4. Write `results/insulation_batch_run_2026-06-22.md` summarizing:
   - Table: file | rows | time | status (OK/ERROR/ZERO)
   - Top 3 files by row count → these are the demo candidates
   - Any files that errored → list them
   - Honest note: rows ≠ correct rows (no gold yet; this is quantity, not quality)
5. Write `tests/integration/test_insulation_batch_no_crash.py`:
   ```python
   import pytest, pathlib
   from src.pipeline import Pipeline

   TENDER_DIR = pathlib.Path("data/real_rfqs/raw/insulation_hvac")
   PDFS = sorted(TENDER_DIR.glob("*.pdf"))

   @pytest.mark.parametrize("pdf", PDFS, ids=[p.name for p in PDFS])
   def test_pipeline_no_crash(pdf):
       p = Pipeline()
       result = p.process_file(str(pdf))
       # rows may be 0 — compliance PDFs are legitimately empty
       # but pipeline must not raise
       assert result is not None
   ```
6. `python3 -m pytest tests/integration/test_insulation_batch_no_crash.py -q --tb=short`
7. `python3 -m ruff check src/ scripts/ --quiet`
8. Commit:
   ```
   git commit -m "eval: insulation batch run — fidelity + no-crash test (E6)"
   ```

## 5. VERIFICATION
```bash
cd /Users/srujansai/Desktop/rfq2boq-laneE
source .venv-lora/bin/activate
python3 -m pytest tests/integration/test_insulation_batch_no_crash.py -q
cat results/insulation_batch_run_2026-06-22.md
python3 -m ruff check src/ scripts/ --quiet
```

## 6. ACCEPTANCE CRITERIA
- [ ] All 11 PDFs attempted (no skips)
- [ ] Zero pipeline crashes (0 errors in JSON; legitimate empty results are OK)
- [ ] `results/insulation_batch_run_2026-06-22.md` table produced with honest row counts
- [ ] No-crash test passes for all 11 files
- [ ] Honest note in report: "row count ≠ quality; gold annotation pending"
- [ ] Lint clean

## 7. CONSTRAINTS
- Do NOT use extracted row counts as gold — they are pipeline output
- Do NOT report 100% on any quality metric — we have no insulation gold yet
- Timeout: if any PDF takes >120s, record timeout in results and move on
- Python 3.12 via `.venv-lora`

## 8. DEPENDENCIES
- Blocked by: nothing
- Parallel-safe with B, C, D, A
- Enables: once Lane B produces draft gold, E7 can run honest eval on insulation domain

## 9. GOTCHAS
- `Tender (2).pdf` and `Tender (4).pdf` are compliance sheets — pipeline will return 0 rows. That's correct, not a bug.
- `TENDER.pdf` is the best candidate for real BOQ rows
- Some PDFs may trigger OCR (slow) — the timeout added in C4 should handle this
- Use `.venv-lora` (3.12), NOT `.venv` (3.14)

---

## REPORT FORMAT
```
## REPORT: Lane E6 — Insulation batch run

Deliverables:
- results/insulation_batch_run_2026-06-22.json — created
- results/insulation_batch_run_2026-06-22.md — created
- tests/integration/test_insulation_batch_no_crash.py — created

Verification:
- 11/11 PDFs attempted
- Crashes: 0
- Top 3 files by rows: [file: N rows, ...]
- pytest: N passed
- ruff: clean

Blockers: none / list
```
