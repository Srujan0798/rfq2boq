# TASK: Add rate-only (R/O) flag to BoqRow — Agent-F1

## 1. GOAL
Detect R/O (Rate Only) rows and flag them so downstream cost estimation can skip.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/domain/models.py` — `BoqRow` Pydantic model
- `src/ingest/table_extractor.py` — `_parse_boq_row()`
- `src/pipeline_xlsx.py` — XLSX row processing
- `src/export/excel_generator.py` — Excel output
- `tests/unit/test_table_extractor.py` — existing tests

Current state:
- BoqRow has no rate_only flag
- R/O rows appear with quantity=0, confusing cost estimation

## 3. DELIVERABLES
- [ ] `src/domain/models.py` — add `rate_only: bool = False` to BoqRow
- [ ] `src/ingest/table_extractor.py` — detect R/O in quantity cell
- [ ] `src/pipeline_xlsx.py` — detect R/O in XLSX rows
- [ ] `src/export/excel_generator.py` — add "R/O" note in Notes column
- [ ] `tests/unit/test_table_extractor.py` — test R/O detection
- [ ] `tests/unit/test_models.py` — test BoqRow serialization with flag

## 4. STEPS
1. Read all context files
2. Add to BoqRow:
   ```python
   rate_only: bool = False
   ```
3. In `table_extractor.py` `_parse_boq_row()`:
   ```python
   RO_PATTERN = re.compile(r"\bR[/\s]?O\b|rate\s+only", re.IGNORECASE)
   if RO_PATTERN.search(quantity):
       rate_only = True
       qty_val = 0.0
   ```
4. In `pipeline_xlsx.py` `_find_best_quantity()`:
   ```python
   if RO_PATTERN.search(str(raw)):
       return Decimal("0")  # signal rate-only
   ```
   (Need to also set rate_only flag in the BoqRow creation)
5. In `excel_generator.py` `_write_item_row()`:
   ```python
   if item.get("rate_only"):
       note = "R/O — Rate Only"
   ```
6. Add tests

## 5. VERIFICATION
```bash
$ python3 -m pytest tests/unit/test_table_extractor.py tests/unit/test_models.py -v
EXPECT: all pass + new tests pass

$ python3 -c "from src.domain.models import BoqRow; r=BoqRow(material='Test', rate_only=True); print(r.rate_only)"
EXPECT: True

$ python3 -m pytest tests/unit/ --tb=no
EXPECT: All previously-passing tests still pass
```

## 6. ACCEPTANCE CRITERIA
- "R/O" in qty column → rate_only=True
- "Rate Only" → rate_only=True
- Normal quantity → rate_only=False
- Excel export shows "R/O" note for flagged rows
- JSON export includes rate_only field
- All tests pass
- Coverage ≥ 80%

## 7. CONSTRAINTS
- Default False for backward compatibility
- Don't break existing BoqRow serialization (Pydantic handles new fields)
- Type hints required

## 8. DEPENDENCIES
- Blocked by: None
- Blocks: None
- Parallel-safe with: F2, F3, F4, B1, B2, B3, C1, C2

## 9. GOTCHAS
- "RO" could be "Romania" or "Round Off" — check context (in qty column = safe)
- Some XLSX files may have "R/O" in a separate column, not quantity — check all text cells
- Pydantic v2 may require `model_config = {"extra": "allow"}` if deserializing old data — test
