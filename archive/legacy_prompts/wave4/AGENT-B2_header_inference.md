# TASK: Infer material from section headers — Agent-B2

## 1. GOAL
When a table row's material is only a dimension (no material keywords), prepend the nearest preceding section header.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/ingest/table_extractor.py` — `_parse_boq_row()` and `TableExtractor` class
- `src/preproc/sections.py` — `extract_sections()` finds section headers
- `tests/unit/test_table_extractor.py` — existing tests

Current state:
- Row material="15 mm thick" with no explicit material name
- Section header above table says "ACOUSTIC LINING"
- Expected: "Acoustic lining 15 mm thick"

## 3. DELIVERABLES
- [ ] `src/ingest/table_extractor.py` — add `_infer_material_from_header()` and wire into `extract()` / `_parse_boq_row()`
- [ ] `tests/unit/test_table_extractor.py` — test header inference

## 4. STEPS
1. Read `src/ingest/table_extractor.py` and `src/preproc/sections.py`
2. In `TableExtractor.__init__()`, add `self._section_headers: dict[int, str] = {}`
3. In `extract()`, before processing tables:
   - For each page, run `extract_sections(page_text)`
   - Store the last non-boilerplate section header per page number
   - Skip headers matching `r"schedule|bill|annexure|nit|notice"`
4. In `_parse_boq_row()`, after extracting `material`:
   - If material matches `r"^\d+\s*mm\s*thick$"` (pure dimension):
     - Look up `self._section_headers.get(table.page_number, "")`
     - If found, prepend: `f"{header} {material}"`
5. Add tests

## 5. VERIFICATION
```bash
$ python3 -m pytest tests/unit/test_table_extractor.py -v
EXPECT: all pass + new test passes

$ python3 -m pytest tests/unit/ --tb=no
EXPECT: All previously-passing tests still pass

$ python3 -m ruff check src/ingest/table_extractor.py
EXPECT: All checks passed!
```

## 6. ACCEPTANCE CRITERIA
- "15 mm thick" with header "ACOUSTIC LINING" → "Acoustic lining 15 mm thick"
- "50 mm thick" with no header → stays "50 mm thick" (no crash)
- "Cement 15 mm thick" → stays "Cement 15 mm thick" (already has material)
- Existing tests pass
- Coverage ≥ 80%

## 7. CONSTRAINTS
- Only prepend if material is PURE dimension (regex match `r"^\d+\s*mm\s*thick$")`
- Don't prepend if material already contains material keywords (cement, steel, etc.)
- Skip boilerplate headers (schedule, bill, annexure)

## 8. DEPENDENCIES
- Blocked by: B1 (merged cell splitting — shared file)
- Blocks: None
- Parallel-safe with: B3, C1, C2, F2
- Shared files: `src/ingest/table_extractor.py`

## 9. GOTCHAS
- Section headers may be multi-line — take first line only
- Headers like "SCHEDULE-B" are not material names — skip via regex
- `extract_sections()` may be slow on large pages — only run once per page
- Some section headers are ALL CAPS — title-case them before prepending
