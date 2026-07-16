# TASK: Align validation harness with clean gold — Agent-E1

## 1. GOAL
Update `scripts/validate_real_rfqs.py` to filter gold rows before comparison (remove section headers, specs, totals).

## 2. CONTEXT
Files to read FIRST (in order):
- `scripts/validate_real_rfqs.py` — validation script
- `src/eval/boq_matcher.py` — `match_boq_rows()`
- `data/real_rfqs/gold/swa_*.json` — gold files (read to understand dirty rows)

Current state:
- Gold contains section headers ("ACOUSTIC LINING"), spec paragraphs, total rows
- Pipeline correctly skips these → looks like 0% recall
- Match rate is 2.8% because gold is inflated

## 3. DELIVERABLES
- [ ] `scripts/validate_real_rfqs.py` — add `_is_valid_gold_row()` filter
- [ ] `scripts/clean_gold.py` — standalone audit script
- [ ] Update `docs/wave_status.md` with corrected metrics

## 4. STEPS
1. Read `scripts/validate_real_rfqs.py`
2. Add filter function:
   ```python
   def _is_valid_gold_row(row: dict) -> bool:
       material = row.get("material", "")
       qty = row.get("quantity", 0)
       unit = row.get("unit", "")

       # Must have all three
       if not material or qty <= 0 or not unit:
           return False

       # Not a spec paragraph
       if len(material) > 200:
           return False

       # Not a total/subtotal row
       lower = material.lower()
       if any(kw in lower for kw in ["total", "sub-total", "grand total", "sub total"]):
           return False

       # Not a section header (ALL CAPS short text)
       if material.isupper() and len(material) < 30:
           return False

       # Not a note/remark
       if lower.startswith(("note", "remark", "refer", "see")):
           return False

       return True
   ```
3. Apply filter in `load_ground_truth_from_ingested()`:
   ```python
   rows = [r for r in rows if _is_valid_gold_row(r)]
   ```
4. Create `scripts/clean_gold.py`:
   - Load each gold file
   - Print dirty rows (those that fail filter)
   - Print clean row count vs original
5. Run and report

## 5. VERIFICATION
```bash
$ python3 scripts/clean_gold.py
EXPECT: Shows dirty rows per enquiry, clean counts

$ python3 scripts/validate_real_rfqs.py
EXPECT: Ground truth row counts drop, match rate improves

$ python3 -m pytest tests/unit/ --tb=no
EXPECT: All previously-passing tests still pass
```

## 6. ACCEPTANCE CRITERIA
- Gold row count drops by 30-50% (removing headers/specs)
- Match rate improves to >20% (from 2.8%)
- No crash on any enquiry
- clean_gold.py lists all dirty rows for review
- All tests pass

## 7. CONSTRAINTS
- Don't modify gold files in-place (read-only)
- Filter at load time
- Don't break existing matcher logic

## 8. DEPENDENCIES
- Blocked by: A1 (Srujan cleans gold first — this agent only adds filtering)
- Blocks: None
- Parallel-safe with: D1, D2, F1, F2, F3, F4

## 9. GOTCHAS
- Some real BOQ rows may have long descriptions (>200 chars) — tune threshold if needed
- "TOTAL" may appear in legitimate material names ("Total station") — rare, ignore
- The filter is conservative — it's OK if some borderline rows are kept
- Srujan must manually review dirty rows from clean_gold.py output
