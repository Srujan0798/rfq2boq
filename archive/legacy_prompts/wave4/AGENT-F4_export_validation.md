# TASK: Add BoqRow validation before export — Agent-F4

## 1. GOAL
Add `BoqRow.validate()` that ensures consistent types and non-empty required fields. Exporters skip invalid rows.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/domain/models.py` — `BoqRow` Pydantic model
- `src/export/excel_generator.py` — `_write_item_row()`
- `src/export/json_formatter.py` — `format_to_string()`
- `tests/unit/test_models.py` — existing tests (if any)

Current state:
- BoqRow can have empty material, zero quantity, empty unit
- Exporters don't validate — may crash or produce garbage
- quantity field is Decimal but exporters sometimes treat as float

## 3. DELIVERABLES
- [ ] `src/domain/models.py` — add `validate()` method to BoqRow
- [ ] `src/export/excel_generator.py` — skip invalid rows, log warning
- [ ] `src/export/json_formatter.py` — skip invalid rows, log warning
- [ ] `tests/unit/test_models.py` — test validation logic

## 4. STEPS
1. Read context files
2. Add to BoqRow:
   ```python
   def validate(self) -> list[str]:
       """Return list of validation error messages. Empty list = valid."""
       errors = []
       if not self.material or not self.material.strip():
           errors.append("material is empty")
       if self.quantity is None or self.quantity <= 0:
           if not getattr(self, 'rate_only', False):
               errors.append(f"quantity is invalid: {self.quantity}")
       if not self.unit or not self.unit.strip():
           errors.append("unit is empty")
       return errors
   ```
3. In `excel_generator.py` `export()`:
   ```python
   valid_items = []
   for item in boq_items:
       if hasattr(item, 'validate'):
           errs = item.validate()
           if errs:
               logger.warning("Skipping invalid BOQ row %s: %s", getattr(item, 'item_no', '?'), errs)
               continue
       valid_items.append(item)
   boq_dicts = [self._as_dict(it) for it in valid_items]
   ```
4. In `json_formatter.py`, same filtering
5. Add tests

## 5. VERIFICATION
```bash
$ python3 -m pytest tests/unit/test_models.py -v
EXPECT: all pass + new validation tests pass

$ python3 -c "
from src.domain.models import BoqRow
r1 = BoqRow(material='Cement', quantity=100, unit='kg')
print(r1.validate())
r2 = BoqRow(material='', quantity=0, unit='')
print(r2.validate())
"
EXPECT: [] for r1, 3 errors for r2

$ python3 -m pytest tests/unit/ --tb=no
EXPECT: All previously-passing tests still pass
```

## 6. ACCEPTANCE CRITERIA
- Empty material → skipped + logged warning
- Zero quantity (non-rate-only) → skipped + logged
- Empty unit → skipped + logged
- Valid rows → exported normally
- Rate-only rows (quantity=0, rate_only=True) → NOT skipped
- No crashes
- All tests pass
- Coverage ≥ 80%

## 7. CONSTRAINTS
- Don't change BoqRow field types (keep Decimal for quantity)
- Log at WARNING level
- Use `logging` module, not print

## 8. DEPENDENCIES
- Blocked by: F1 (rate_only flag — shared model)
- Blocks: None
- Parallel-safe with: F2, F3, B1, B2, B3, C1, C2

## 9. GOTCHAS
- Some legitimate rows may have quantity=0 (R/O) — check rate_only flag first
- Decimal serialization in JSON needs `str()` wrapper — Pydantic handles this
- `hasattr(item, 'validate')` check for backward compat with plain dicts
- Excel generator may receive dicts instead of BoqRow objects — handle both
