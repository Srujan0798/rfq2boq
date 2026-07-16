# TASK: Fix 09 GeM Bid Pipeline Hang — Agent-G1

## 1. GOAL
Fix the pipeline hang on `09_gem_bid_7439924/GeM-Bidding-9218026.pdf` (bilingual Hindi/English GeM bid) so it completes within 5 minutes and extracts BOQ items without crashing.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/pipeline.py` — understand `Pipeline.run()` entry point and how it routes PDF vs XLSX
- `src/ingest/pdf_extractor.py` — see how PDFs are opened, how `pdfplumber` is used, timeout handling
- `src/preproc/sections.py` — `SectionClassifier.find_boq_pages()` may be scanning all pages of the 09 GeM PDF (which is large + bilingual)
- `src/nlp/pipeline.py` — `_init_ner()` loads the NER model; 09 GeM may be triggering XLM-Roberta download/loading which hangs
- `tests/e2e/test_all_enquiries.py` — the e2e test that hangs on 09

Current state:
- 09 GeM PDF is a bilingual (Hindi + English) Government e-Marketplace bid document
- Pipeline hangs indefinitely (>15min) when processing it
- 10 GeM (similar bilingual PDF) completes in ~10min with 54 items — so the issue is specific to 09's content/size
- The hang likely occurs in either: (a) pdfplumber page extraction on bilingual text, (b) XLM-Roberta model loading for Hindi, or (c) section classifier scanning too many pages
- All other 8 enquiries process successfully

## 3. DELIVERABLES
Create or modify EXACTLY these files:
- [ ] `src/ingest/pdf_extractor.py` — add `max_pages` parameter and timeout guard around pdfplumber extraction
- [ ] `src/preproc/sections.py` — add early-exit in `find_boq_pages()` when page count exceeds threshold; skip non-BOQ pages faster
- [ ] `src/nlp/pipeline.py` — add timeout/model caching to prevent repeated XLM-Roberta loads; add fallback to skip NER if model load hangs
- [ ] `tests/e2e/test_all_enquiries.py` — add a shorter timeout test for 09 (max 300s instead of no limit)
- [ ] `tests/unit/test_pdf_extractor_timeout.py` — new test: verify pdfplumber timeout and max_pages work

## 4. STEPS
1. Read context files (Section 2)
2. Reproduce the hang: `python3 -c "from src.pipeline import Pipeline; p = Pipeline(); r = p.run('data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf')"` — confirm it hangs
3. Add `max_pages: int = 50` parameter to pdf extraction path in `src/ingest/pdf_extractor.py`
4. Add `timeout_seconds: int = 60` per-page guard using `signal` or `threading.Timer` around pdfplumber page text extraction
5. In `src/preproc/sections.py`, add `max_pages_to_scan: int = 30` to `find_boq_pages()` — stop scanning after 30 pages if no BOQ found
6. In `src/nlp/pipeline.py`, cache the NER model instance (class-level or module-level) so it's loaded once; add `model_load_timeout: int = 120`
7. If XLM-Roberta fails to load within timeout, fallback to English-only BERT model (already available at `models/rfq2boq-ner-final/`)
8. Add tests
9. Run verification (Section 5)

## 5. VERIFICATION
Run these commands. Each must produce the expected output:

```bash
# Test 09 GeM completes within 5 minutes
$ timeout 300 python3 -c "from src.pipeline import Pipeline; p = Pipeline(); r = p.run('data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf'); print('items:', len(r.boq_items))"
EXPECT: completes without error, prints item count >= 0

# Test max_pages limits extraction
$ python3 -m pytest tests/unit/test_pdf_extractor_timeout.py -v
EXPECT: >= 3 passed, 0 failed

# No regressions on other enquiries
$ python3 -m pytest tests/e2e/test_all_enquiries.py -k "01 or 04 or 05" -v --tb=short
EXPECT: 9 passed (3 tests x 3 enquiries)

# Lint
$ python3 -m ruff check src/ingest/pdf_extractor.py src/preproc/sections.py src/nlp/pipeline.py
EXPECT: All checks passed!
```

## 6. ACCEPTANCE CRITERIA
- [ ] 09 GeM completes within 300 seconds (5 minutes)
- [ ] 09 GeM returns `boq_items` (can be 0, but must not hang)
- [ ] All other 9 enquiries still work (no regressions)
- [ ] New tests pass
- [ ] No ruff errors
- [ ] No mypy errors

## 7. CONSTRAINTS
- All imports use `src.` prefix
- Python 3.11+ syntax, type hints required
- DO NOT modify: `config/constants.py`, existing passing tests
- DO NOT add new dependencies (use signal/threading from stdlib)
- Keep changes minimal — this is a robustness fix, not a rewrite

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** G2 (improve 09/10 extraction quality), P8T8 (final handover)
- **Parallel-safe with:** G2, G3, G4
- **Shared files:** `src/pipeline.py` (touched by many tasks — coordinate)

## 9. GOTCHAS
- `signal.SIGALRM` is NOT available on Windows; use `threading.Timer` for cross-platform timeout
- pdfplumber can hang on pages with complex embedded fonts or bilingual text — the timeout must wrap the `.extract_text()` call
- XLM-Roberta is large (~1GB download) — if it's not cached, first load is slow; but it should be cached after first use
- The 09 GeM PDF may have 50+ pages — `max_pages=50` is reasonable for BOQ extraction (BOQs are usually in first 30 pages)
- Do NOT break the existing `pdfplumber` fallback path for other PDFs
