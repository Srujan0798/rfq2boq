# TASK: Fix 01 GSECL Extraction (2 items from 62-page PDF) — Agent-G5

## 1. GOAL
Fix the pipeline so that `01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf` (62-page PDF) extracts more than 2 BOQ items — target is >= 10 items matching the actual insulation BOQ.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/ingest/pdf_extractor.py` — PDF text extraction
- `src/ingest/table_extractor.py` — table → BOQ row extraction (recently fixed with _is_unit/_is_quantity)
- `src/preproc/sections.py` — section classifier, `find_boq_pages()`
- `src/nlp/pipeline.py` — NER pipeline
- `src/domain/boq_assembler.py` — BOQ assembly
- `data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/` — the actual PDF and any README

Current state:
- 01 GSECL is a 62-page PDF that takes ~107 seconds to process
- Pipeline returns only 2 items: `pipe 1.50 m` and `pipe 2.0 m`
- The actual document contains a full insulation BOQ with many items
- Problem is likely: (a) section classifier misses BOQ pages, (b) table extractor doesn't find tables, (c) NER doesn't recognize insulation vocabulary, or (d) assembler drops valid rows

## 3. DELIVERABLES
Create or modify EXACTLY these files:
- [ ] `src/ingest/pdf_extractor.py` — add debug logging to show which pages are extracted
- [ ] `src/preproc/sections.py` — improve BOQ page detection for large multi-section PDFs
- [ ] `src/ingest/table_extractor.py` — add fallback: if no tables found, use NER on full page text
- [ ] `scripts/debug_01_gsecl.py` — NEW: diagnostic script that shows step-by-step what the pipeline does for 01
- [ ] `tests/unit/test_pdf_extractor.py` — add test for large PDF handling

## 4. STEPS
1. Read context files (Section 2)
2. Run diagnostic:
   ```bash
   python3 -c "
   from src.pipeline import Pipeline
   p = Pipeline()
   result = p.run('data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf')
   print('items:', len(result.boq_items))
   for item in result.boq_items: print(item)
   print('metadata:', result.metadata)
   "
   ```
3. Create `scripts/debug_01_gsecl.py` that:
   - Extracts text from each page and prints page number + first 200 chars
   - Runs section classifier and prints which pages are classified as BOQ
   - Runs table extractor on BOQ pages and prints found tables
   - Runs NER on page text and prints detected entities
   - Runs assembler and prints final rows
4. Analyze output to find where items are being lost
5. Fix the identified issue(s):
   - If section classifier misses BOQ pages: improve `find_boq_pages()` for large PDFs
   - If tables not found: improve table detection or add text-based fallback
   - If NER misses entities: this is G3's domain — document the issue for G3
   - If assembler drops rows: fix assembler logic
6. Run verification (Section 5)

## 5. VERIFICATION
Run these commands. Each must produce the expected output:

```bash
# Debug script runs and produces diagnostic output
$ python3 scripts/debug_01_gsecl.py
EXPECT: shows page-by-page extraction, classification, tables, entities, rows

# Pipeline produces more items
$ python3 -c "
from src.pipeline import Pipeline
p = Pipeline()
result = p.run('data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf')
print('items:', len(result.boq_items))
"
EXPECT: >= 10 items (currently 2)

# No regressions on other PDFs
$ python3 -c "
from src.pipeline import Pipeline
p = Pipeline()
for pdf in ['04_adani', '06_avante_kirloskar_pune', '07_grew_solar_narmadapuram']:
    result = p.run(f'data/real_rfqs/swa_enquiries/{pdf}/')
    print(pdf, len(result.boq_items))
"
EXPECT: similar item counts as before (12, 14, 23)

# Tests pass
$ python3 -m pytest tests/unit/test_pdf_extractor.py -v --tb=short
EXPECT: all tests pass
```

## 6. ACCEPTANCE CRITERIA
- [ ] 01 GSECL produces >= 10 BOQ items (up from 2)
- [ ] Processing time remains under 180 seconds (3 minutes)
- [ ] No regressions on other PDF enquiries
- [ ] Debug script provides clear visibility into extraction pipeline
- [ ] All tests pass
- [ ] No ruff errors

## 7. CONSTRAINTS
- All imports use `src.` prefix
- Do NOT modify `config/constants.py`
- Keep changes minimal and targeted
- If the issue is NER vocabulary (insulation terms not recognized), document it — G3 handles NER retraining

## 8. DEPENDENCIES
- **Blocked by:** None (can run in parallel with G2/G3)
- **Blocks:** P8T8 (final handover)
- **Parallel-safe with:** G1, G2, G3, G4
- **Shared files:** `src/ingest/pdf_extractor.py`, `src/preproc/sections.py`

## 9. GOTCHAS
- 62-page PDFs may have BOQ spread across multiple non-contiguous page ranges
- The PDF may have scanned/image pages — pdfplumber may not extract text from these
- If the PDF is image-based, OCR may be needed — but that's a bigger task; focus on text extraction first
- "Schedule B" or "Bill of Quantities" may appear in headers/footers on every page — don't misclassify all pages as BOQ
- The 2 items currently extracted (`pipe 1.50 m`, `pipe 2.0 m`) suggest the NER is finding SOMETHING but missing the actual insulation materials
