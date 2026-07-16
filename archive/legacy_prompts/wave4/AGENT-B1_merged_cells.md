# TASK: Split merged multi-line table cells — Agent-B1

## 1. GOAL
When a table description cell contains `\n` and multiple dimension patterns, split into separate BOQ rows.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/ingest/table_extractor.py` — `_parse_boq_row()` parses individual rows; `map_to_boq_rows()` collects results
- `tests/unit/test_table_extractor.py` — existing tests

Current state:
- pdfplumber produces rows like `['2.1', '500 mm dia\n400 mm dia', 'Rmt.', '1044']`
- Current behavior: material="500 mm dia\n400 mm dia" (one row)
- Expected: two rows with material="500 mm dia" and "400 mm dia", same qty=1044, unit="Rmt."

## 3. DELIVERABLES
- [ ] `src/ingest/table_extractor.py` — modify `_parse_boq_row()` to detect and split merged cells; modify `map_to_boq_rows()` to handle list returns
- [ ] `tests/unit/test_table_extractor.py` — add `test_merged_cell_splitting`

## 4. STEPS
1. Read `src/ingest/table_extractor.py`
2. In `_parse_boq_row()`, after extracting `material`:
   - If `\n` in material:
     - Split by `\n`
     - Check if any split part matches `r"\d+\s*mm\s*(dia|diameter)"`
     - If ≥2 dimension-like parts found, return LIST of row dicts instead of one dict
   - Otherwise return single dict (or None) as before
3. In `map_to_boq_rows()`, handle `_parse_boq_row` returning either `dict | None` or `list[dict]`:
   ```python
   boq_row = self._parse_boq_row(row, table)
   if boq_row is None:
       continue
   if isinstance(boq_row, list):
       boq_rows.extend(boq_row)
   else:
       boq_rows.append(boq_row)
   ```
4. Add test: `['2.1', '500 mm dia\n400 mm dia', 'Rmt.', '1044']` → 2 rows

## 5. VERIFICATION
```bash
# Test the new code
$ python3 -m pytest tests/unit/test_table_extractor.py -v
EXPECT: all pass + new test passes

# No regressions
$ python3 -m pytest tests/unit/ --tb=no
EXPECT: All previously-passing tests still pass

# Lint
$ python3 -m ruff check src/ingest/table_extractor.py
EXPECT: All checks passed!
```

## 6. ACCEPTANCE CRITERIA
- Merged cell with 2 dimension parts → 2 rows
- Merged cell with 3 dimension parts → 3 rows
- Non-merged cell → 1 row (no regression)
- All existing tests pass
- Coverage of new code ≥ 80%

## 7. CONSTRAINTS
- All imports use `src.` prefix
- Type hints required on new code
- Python 3.11+ syntax
- DO NOT modify: `config/constants.py`, `config/settings.py`, existing passing tests
- DO NOT add backwards-compat shims or dead code

## 8. DEPENDENCIES
- Blocked by: None
- Blocks: B2 (header inference)
- Parallel-safe with: B3, C1, C2, F2
- Shared files: `src/ingest/table_extractor.py` (B3 also touches this — coordinate)

## 9. GOTCHAS
- Some `\n` in material is legitimate (wrapped text) — only split if dimension pattern matches
- Quantity should be SAME for all split rows (not divided)
- `map_to_boq_rows()` currently expects `_parse_boq_row` to return `dict | None` — changing to `dict | list[dict] | None` affects type signature
- The `_parse_boq_row` return type annotation must be updated: `dict[str, Any] | list[dict[str, Any]] | None`
