# TASK: Expand unit alias recognition — Agent-F2

## 1. GOAL
Add missing unit aliases: sqft, cft, ea, hr, day, running metre.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/ingest/table_extractor.py` — `unit_keywords` list in `_looks_like_boq_table()` and `_parse_boq_row()`
- `src/nlp/patterns/regex_patterns.py` — `_BOQ_UNITS` regex
- `src/domain/boq_assembler.py` — `_normalize_unit()` method
- `tests/unit/test_table_extractor.py` — existing tests

Current state:
- Missing: sqft, cft, ea, hr, day, running metre
- These appear in real RFQs but are not recognized

## 3. DELIVERABLES
- [ ] `src/ingest/table_extractor.py` — expand `unit_keywords` in both methods
- [ ] `src/nlp/patterns/regex_patterns.py` — expand `_BOQ_UNITS`
- [ ] `src/domain/boq_assembler.py` — add mappings in `_normalize_unit()`
- [ ] `tests/unit/test_table_extractor.py` — unit alias matrix test

## 4. STEPS
1. Read all context files
2. In `table_extractor.py`, expand `unit_keywords`:
   ```python
   unit_keywords = [
       # existing...
       "sqm", "sq.m", "sq. mtr", "mtr", "kg", "nos", "no.", "rm",
       "m³", "cum", "ltr", "m2", "m3", "sq.mtr", "rmt", "lm", "m²",
       "sqmtrs", "sq. mtrs", "sqmtr",
       # NEW:
       "sqft", "sq.ft", "sft", "sq feet", "square feet",
       "cft", "cu.ft", "cu ft",
       "ea", "ea.", "each",
       "hr", "hrs", "hour", "hours",
       "day", "days",
       "running metre", "running meter", "r.mtr",
   ]
   ```
3. In `regex_patterns.py`, expand `_BOQ_UNITS`:
   ```python
   _BOQ_UNITS = re.compile(
       r"\b(sqm|sq\.m|sq\. mtr|mtr|m²|m2|m³|m3|cum|cu\.m|rmt|rm|lm|"
       r"kg|kgs|mt|t|ton|tons|tonne|nos|no\.|no|nr|nr\."
       r"|ltr|liter|litre|l|ml|"
       r"bag|bags|box|boxes|roll|rolls|drum|drums|coil|coils|bundle|bundles|"
       r"pair|pairs|set|sets|sheet|sheets|panel|panels|pce|pcs|piece|pieces|"
       r"sqft|sq\.ft|sft|sq\s+feet|square\s+feet|"
       r"cft|cu\.ft|cu\s+ft|"
       r"ea|ea\.|each|"
       r"hr|hrs|hour|hours|"
       r"day|days|"
       r"running\s+metre|running\s+meter|r\.mtr)\b",
       re.IGNORECASE,
   )
   ```
4. In `boq_assembler.py`, add to `_normalize_unit()`:
   ```python
   unit_map = {
       # existing...
       "sqft": "sqft", "sq.ft": "sqft", "sft": "sqft", "sq feet": "sqft", "square feet": "sqft",
       "cft": "cft", "cu.ft": "cft", "cu ft": "cft",
       "ea": "nos", "ea.": "nos", "each": "nos",
       "hr": "hr", "hrs": "hr", "hour": "hr", "hours": "hr",
       "day": "day", "days": "day",
       "running metre": "m", "running meter": "m", "r.mtr": "m",
   }
   ```
5. Add test with 20+ variants

## 5. VERIFICATION
```bash
$ python3 -m pytest tests/unit/test_table_extractor.py::test_unit_aliases -v
EXPECT: passes

$ python3 -c "
from src.domain.boq_assembler import BOQAssembler
a = BOQAssembler()
print(a._normalize_unit('sqft', 'tile'))
print(a._normalize_unit('ea', 'valve'))
print(a._normalize_unit('hrs', 'labour'))
"
EXPECT: sqft, nos, hr

$ python3 -m pytest tests/unit/ --tb=no
EXPECT: All previously-passing tests still pass
```

## 6. ACCEPTANCE CRITERIA
- All 20+ variants recognized by table extractor
- All variants normalized to canonical form
- sqft → sqft (keep as-is, don't convert to m²)
- cft → cft (keep as-is)
- ea/each → nos
- hr/hrs/hour → hr
- day/days → day
- running metre → m
- No regressions
- Coverage ≥ 80%

## 7. CONSTRAINTS
- Canonical forms: m², m³, nos, kg, m, ltr, sqft, cft, hr, day
- Don't convert sqft→m² or cft→m³ (estimators use original units)
- Type hints required

## 8. DEPENDENCIES
- Blocked by: None
- Blocks: None
- Parallel-safe with: ALL other tasks

## 9. GOTCHAS
- "ft" alone is ambiguous (foot vs fort) — only match as part of sqft/cft
- "ea" could be "each" or abbreviation — safe to map to nos
- "day" may appear in "daywork" — word boundary prevents false match
- "running metre" has space — regex must handle `\s+`
