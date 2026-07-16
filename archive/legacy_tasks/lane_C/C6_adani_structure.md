# TASK: Lane C — Fix Adani PDF extraction (structure-first on real PDF) — Agent-C

**Worktree:** `/Users/srujansai/Desktop/rfq2boq-laneC`
**Branch:** `phase8-laneC`
**Model:** Strong coding (OpenCode paid)

---

## 1. GOAL
Apply the structure-first extractor (C1) to the Adani PDF (enquiry 04) — currently extracts only 12 rows vs 45 in gold — and close the gap honestly using section routing.

## 2. CONTEXT
Files to read FIRST:
- `src/preproc/document_structure.py` — structure extractor (already improved in C1)
- `src/ingest/table_extractor.py` — table extraction with timeout (improved in C4)
- `data/real_rfqs/swa_enquiries/04_adani/` — list files here
- `tasks/NW03_adani_extraction_quality.md` — original task spec for Adani
- `results/honest_baseline_2026-06-22.md` — current honest baseline
- `data/real_rfqs/gold/rows/04_adani.rowgold.json` — gold: 45 rows expected
- `config/constants.py` — READ ONLY

Current state:
- Structure extractor improved (C1) but not yet applied to Adani
- Adani extracts 12 rows, gold expects 45 — gap is 33 rows
- Root cause (per NW03): Adani is a large multi-section PDF; rows are spread across sub-section BOQ tables that the flat extractor misses

## 3. DELIVERABLES
- [ ] `src/ingest/pdf_extractor.py` or `src/preproc/document_structure.py` — route Adani-style multi-section PDFs through the structure extractor to find all BOQ sub-sections before table extraction
- [ ] `tests/integration/test_adani_structure.py` — verify extracted row count improves (>20 rows minimum; document honest number)
- [ ] Updated honest number in the test (do not hardcode 45 if you don't reach it)

## 4. STEPS
1. Activate: `source /Users/srujansai/Desktop/rfq2boq-laneC/.venv-lora/bin/activate`
2. Identify the Adani PDF path:
   ```bash
   ls data/real_rfqs/swa_enquiries/04_adani/
   ```
3. Run structure extractor on Adani PDF to see what sections are found:
   ```python
   from src.preproc.document_structure import extract_document_structure
   sections = extract_document_structure('data/real_rfqs/swa_enquiries/04_adani/<filename>.pdf')
   print([(s['title'], s['page']) for s in sections])
   ```
4. Identify pages that contain BOQ content (look for section titles containing "BOQ", "Schedule", "Bill of Quantities", "Items").
5. Modify the PDF extraction pipeline to: (a) extract structure first, (b) identify BOQ-relevant page ranges, (c) run table extractor only on those pages.
6. Run and report honest row count:
   ```python
   from src.pipeline import Pipeline
   p = Pipeline()
   r = p.process_file('data/real_rfqs/swa_enquiries/04_adani/<filename>.pdf')
   print(f'Adani rows: {len(r.rows)}')
   ```
7. Write integration test with the **actual honest** count (not hardcoded 45):
   ```python
   def test_adani_structure_extraction():
       from src.pipeline import Pipeline
       p = Pipeline()
       r = p.process_file('data/real_rfqs/swa_enquiries/04_adani/<filename>.pdf')
       # Document honest improvement — must be better than the old 12
       assert len(r.rows) > 20, f"Expected >20 rows, got {len(r.rows)}"
   ```
8. `python3 -m ruff check src/ --quiet` — clean
9. `python3 -m pytest tests/integration/test_adani_structure.py -q` — pass
10. Commit:
    ```
    git commit -m "feat(ingest): structure-first routing improves Adani PDF extraction (C6)"
    ```

## 5. VERIFICATION
```bash
cd /Users/srujansai/Desktop/rfq2boq-laneC
source .venv-lora/bin/activate
python3 -m pytest tests/integration/test_adani_structure.py -v
python3 -m ruff check src/ --quiet
python3 -c "
from src.pipeline import Pipeline
p = Pipeline()
r = p.process_file('data/real_rfqs/swa_enquiries/04_adani/<filename>.pdf')
print(f'Adani: {len(r.rows)} rows (gold: 45, old: 12)')
"
```

## 6. ACCEPTANCE CRITERIA
- [ ] Adani extracts >20 rows (honest improvement over 12)
- [ ] Test records the honest achieved count, not the gold target
- [ ] No `if filename == '04_adani'` hacks — solution must be general
- [ ] Lint clean, test passes
- [ ] No regressions on existing tests

## 7. CONSTRAINTS
- No filename-specific hacks (`if enquiry == '04_adani': ...` is a cheat)
- Solution must generalize to other multi-section PDFs (the insulation tenders are also multi-section)
- Report the honest count, even if it's 25 not 45
- Python 3.12 via `.venv-lora`

## 8. DEPENDENCIES
- Needs C1 (already done in prior commit)
- Parallel-safe with B, D, E
- Blocks: nothing (standalone improvement)

## 9. GOTCHAS
- Adani PDF may be scanned — OCR fallback may be needed
- Some "BOQ" sections may contain only spec descriptions, not actual quantities — filter by presence of numeric cells
- Do not raise the gold file to match your output (gold is locked)

---

## REPORT FORMAT
```
## REPORT: Lane C6 — Adani structure-first

Deliverables:
- path — created/modified

Verification:
- Adani rows before: 12
- Adani rows after: N (honest)
- pytest: N passed
- ruff: clean

Blockers: none / list
Deviations: none / list
```
