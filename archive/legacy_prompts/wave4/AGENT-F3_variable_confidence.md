# TASK: Implement variable confidence scores for table rows — Agent-F3

## 1. GOAL
Replace hardcoded confidence=0.85 with variable scores based on row quality.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/ingest/table_extractor.py` — `_parse_boq_row()`
- `src/pipeline.py` — table rows get `confidence=0.85`
- `tests/unit/test_table_extractor.py` — existing tests

Current state:
- All table rows get `confidence=0.85` regardless of quality
- Factors that should affect confidence:
  - Item number present (+0.10)
  - Unit detected via regex (+0.10)
  - Quantity parsed successfully (+0.10)
  - Fallback parsing used (-0.10)
  - Zero quantity (-0.10)

## 3. DELIVERABLES
- [ ] `src/ingest/table_extractor.py` — return `confidence` from `_parse_boq_row()`
- [ ] `src/pipeline.py` — use row confidence instead of hardcoded 0.85
- [ ] `tests/unit/test_table_extractor.py` — test confidence scoring

## 4. STEPS
1. Read context files
2. Modify `_parse_boq_row()` to compute and return confidence:
   ```python
   # After parsing row...
   confidence = 0.70  # base

   # +0.10 if item number detected
   if item_number_detected:
       confidence += 0.10

   # +0.10 if unit matched via regex (not fallback)
   if unit_matched_via_regex:
       confidence += 0.10

   # +0.10 if quantity parsed successfully (>0)
   if qty_val > 0:
       confidence += 0.10

   # -0.10 if fallback parsing used
   if fallback_used:
       confidence -= 0.10

   # -0.10 if zero quantity
   if qty_val == 0:
       confidence -= 0.10

   confidence = max(0.50, min(0.95, confidence))

   return {
       # ... existing fields ...
       "confidence": confidence,
   }
   ```
3. In `pipeline.py`:
   ```python
   new_item = BoqRow(
       # ...
       confidence=row_data.get("confidence", 0.70),
   )
   ```
4. Add tests

## 5. VERIFICATION
```bash
$ python3 -m pytest tests/unit/test_table_extractor.py -v
EXPECT: all pass + new confidence tests pass

$ python3 -c "
from src.ingest.table_extractor import TableExtractor, ExtractedTable
t = TableExtractor()
table = ExtractedTable(rows=[], page_number=1)
# Structured row
row1 = ['1.', 'Cement', '100', 'kg']
print(t._parse_boq_row(row1, table)['confidence'])
# Fallback row
row2 = ['Cement', '100 kg']
print(t._parse_boq_row(row2, table)['confidence'])
"
EXPECT: ~0.90 for structured, ~0.60 for fallback

$ python3 -m pytest tests/unit/ --tb=no
EXPECT: All previously-passing tests still pass
```

## 6. ACCEPTANCE CRITERIA
- Structured row (item no + unit + qty) → confidence ≥ 0.90
- Fallback row → confidence ≤ 0.70
- Zero quantity row → confidence ≤ 0.60
- Confidence capped at 0.95, floored at 0.50
- All existing tests pass
- Coverage ≥ 80%

## 7. CONSTRAINTS
- Confidence must be float 0.0–1.0
- Don't break Excel export (uses confidence for color coding: <0.5 red, <0.85 orange)
- Type hints required

## 8. DEPENDENCIES
- Blocked by: B1 (shared file — row structure changes)
- Blocks: None
- Parallel-safe with: F1, F2, F4, C1, C2

## 9. GOTCHAS
- Excel color coding: <0.5 = red, <0.85 = orange, ≥0.85 = black
- Ensure most good rows land at ≥0.85 (black) so export looks professional
- Fallback rows at 0.60–0.70 will show orange — correct, they need review
- The `unit_matched_via_regex` flag needs to be tracked during parsing
