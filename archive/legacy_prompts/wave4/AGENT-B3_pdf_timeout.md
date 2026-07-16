# TASK: Add timeout to PDF table extraction — Agent-B3

## 1. GOAL
Add 30-second timeout to `TableExtractor.extract()`; fall back to text-only NLP if timeout hits. Also add `max_pages` limit.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/ingest/table_extractor.py` — `extract()` method
- `src/pipeline.py` — calls `self.table_extractor.extract()`
- `tests/unit/test_table_extractor.py` — existing tests

Current state:
- Avante Kirloskar `Insulation Boq_132.pdf` hangs for 2+ minutes in `page.extract_tables()`
- No timeout means batch processing blocks indefinitely

## 3. DELIVERABLES
- [ ] `src/ingest/table_extractor.py` — add `timeout_sec` and `max_pages` parameters to `extract()`
- [ ] `src/pipeline.py` — handle empty result from timeout gracefully
- [ ] `tests/unit/test_table_extractor.py` — mock slow extraction

## 4. STEPS
1. Read `src/ingest/table_extractor.py`
2. Modify `extract()` signature:
   ```python
   def extract(self, pdf_path: str | Path, timeout_sec: float = 30.0, max_pages: int | None = None) -> list[ExtractedTable]:
   ```
3. Implement timeout using `concurrent.futures.ThreadPoolExecutor`:
   ```python
   from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

   def _extract_with_timeout(pdf_path, max_pages):
       tables = []
       with pdfplumber.open(str(pdf_path)) as pdf:
           pages_to_process = pdf.pages[:max_pages] if max_pages else pdf.pages
           for page_num, page in enumerate(pages_to_process, start=1):
               raw_tables = page.extract_tables() or []
               # ... existing logic ...
       return tables

   with ThreadPoolExecutor(max_workers=1) as executor:
       future = executor.submit(_extract_with_timeout, pdf_path, max_pages)
       try:
           return future.result(timeout=timeout_sec)
       except FutureTimeoutError:
           logger.warning("Table extraction timed out after %s seconds", timeout_sec)
           return []
   ```
4. In `src/pipeline.py`, if `table_boq_rows` is empty after extraction, fall through to NLP assembly (already happens, just verify)
5. Add test with mock that sleeps >timeout

## 5. VERIFICATION
```bash
$ python3 -m pytest tests/unit/test_table_extractor.py -v
EXPECT: all pass + new timeout test passes

$ python3 -c "from src.ingest.table_extractor import TableExtractor; t=TableExtractor(); print(t.extract('nonexistent.pdf', max_pages=5, timeout_sec=1.0))"
EXPECT: [] (no crash)

$ python3 -m pytest tests/unit/ --tb=no
EXPECT: All previously-passing tests still pass
```

## 6. ACCEPTANCE CRITERIA
- Slow PDF returns `[]` within 35 seconds (30s timeout + overhead)
- Pipeline falls back to NLP, doesn't crash
- max_pages=20 limits processing to first 20 pages
- All tests pass
- Coverage ≥ 80%

## 7. CONSTRAINTS
- Don't use `multiprocessing` (Python 3.14 issues)
- Use `concurrent.futures.ThreadPoolExecutor` (cross-platform)
- Don't modify `config/constants.py`
- Type hints required

## 8. DEPENDENCIES
- Blocked by: None
- Blocks: None
- Parallel-safe with: B1, B2, C1, C2, F2
- Shared files: `src/ingest/table_extractor.py` (B1, B2 also touch this)

## 9. GOTCHAS
- `ThreadPoolExecutor` may leave threads running after timeout — use `future.cancel()` if possible
- pdfplumber may hold file handles — the `with pdfplumber.open()` context manager should handle this
- On macOS, ThreadPoolExecutor timeout works reliably; test on your platform
- `max_pages` should be applied BEFORE timeout starts (limit work, not just time)
