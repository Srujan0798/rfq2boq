# TASK: Add secondary BOQ heuristic for small RFQs — Agent-C2

## 1. GOAL
If no BOQ pages detected, run secondary heuristic: ≥3 quantity-unit pairs within 1000 chars → BOQ.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/preproc/sections.py` — `find_boq_pages()`, `_is_boq_by_table_heuristic()`
- `tests/unit/test_section_classifier.py` — existing tests

Current state:
- `find_boq_pages()` falls back to processing ALL pages if no BOQ detected
- This includes commercial/terms pages, increasing noise
- Small RFQs (5-10 pages) may not have strong BOQ headers

## 3. DELIVERABLES
- [ ] `src/preproc/sections.py` — add `_has_quantity_unit_pairs()` method
- [ ] Modify `find_boq_pages()` to use secondary heuristic before fallback
- [ ] `tests/unit/test_section_classifier.py` — add secondary heuristic tests

## 4. STEPS
1. Read `src/preproc/sections.py`
2. Add method:
   ```python
   def _has_quantity_unit_pairs(self, text: str, min_pairs: int = 3) -> bool:
       """Check if text has at least min_pairs quantity+unit pairs."""
       qty_pattern = re.compile(r"\b\d+(?:,\d+)*(?:\.\d+)?\b")
       unit_pattern = re.compile(
           r"\b(?:sqm|sq\.m|m²|m³|kg|nos|no\.|nr|rm|rmt|ltr|cum|m|mm|cm|"
           r"sqft|cft|ea|hr|day|running\s+metre)\b",
           re.IGNORECASE,
       )
       pairs = 0
       for qty_match in qty_pattern.finditer(text):
           # Check 50-char window after quantity for unit
           window = text[qty_match.end():qty_match.end()+50]
           if unit_pattern.search(window):
               pairs += 1
               if pairs >= min_pairs:
                   return True
       return False
   ```
3. Modify `find_boq_pages()`:
   ```python
   def find_boq_pages(self, pages: list[str]) -> list[int]:
       if not pages:
           return []

       boq_indices = []
       for idx, page_text in enumerate(pages):
           section = self.classify_page(page_text, idx)
           if section == PageSectionType.BOQ:
               boq_indices.append(idx)

       if boq_indices:
           # existing contiguous range logic ...
           return boq_indices

       # Secondary heuristic: quantity-unit pairs
       for idx, page_text in enumerate(pages):
           if self._has_quantity_unit_pairs(page_text):
               boq_indices.append(idx)

       if boq_indices:
           return boq_indices

       # Fallback: all pages
       logger.warning("No BOQ pages detected; falling back to processing all pages")
       return list(range(len(pages)))
   ```
4. Add tests

## 5. VERIFICATION
```bash
$ python3 -m pytest tests/unit/test_section_classifier.py -v
EXPECT: all pass + new tests pass

$ python3 -c "
from src.preproc.sections import SectionClassifier
clf = SectionClassifier()
pages = ['NOTICE INVITING TENDER', '1. Cement 100 kg\n2. Sand 50 kg\n3. Aggregate 30 kg']
print(clf.find_boq_pages(pages))
"
EXPECT: [1]

$ python3 -m pytest tests/unit/ --tb=no
EXPECT: All previously-passing tests still pass
```

## 6. ACCEPTANCE CRITERIA
- Page with "1. Cement 100 kg\n2. Sand 50 kg\n3. Aggregate 30 kg" → detected as BOQ (index 1)
- Page with no quantities → still falls back to all pages (not falsely BOQ)
- Existing BOQ detection still works
- All tests pass
- Coverage ≥ 80%

## 7. CONSTRAINTS
- Don't over-trigger on spec pages (may have density values)
- Require at least 3 pairs to avoid false positives
- Unit pattern must exclude density context (kg/m³) — use word boundary only

## 8. DEPENDENCIES
- Blocked by: C1 (shared file)
- Blocks: None
- Parallel-safe with: B1, B2, B3, F2
- Shared files: `src/preproc/sections.py`

## 9. GOTCHAS
- Spec pages may have many density values — the unit pattern `\bkg\b` without `/m³` is safe
- "1." may be item numbers, not quantities — the qty pattern matches them, but we need units nearby
- Some BOQ pages may have only 2 items — min_pairs=3 may miss them. Consider min_pairs=2 if too strict
- Test with real RFQ pages to calibrate min_pairs
