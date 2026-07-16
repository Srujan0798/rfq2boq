# TASK: Add COMMERCIAL/TERMS section filtering — Agent-C1

## 1. GOAL
Add `COMMERCIAL` category to `SectionClassifier` and skip these pages before NLP processing.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/preproc/sections.py` — `PageSectionType` enum, `SectionClassifier`, patterns
- `src/pipeline.py` — `classifier.find_boq_pages()` filters pages
- `tests/unit/test_section_classifier.py` — existing tests

Current state:
- Pages with "Validity of Tender", "For all engaged manpower", "Safety Goggles" are processed as BOQ
- These are PPE/commercial terms, not scope items

## 3. DELIVERABLES
- [ ] `src/preproc/sections.py` — add `COMMERCIAL` to `PageSectionType`, add `STRONG_COMMERCIAL_PATTERNS`
- [ ] `src/pipeline.py` — ensure COMMERCIAL pages are excluded from `filtered_pages`
- [ ] `tests/unit/test_section_classifier.py` — add commercial classification tests

## 4. STEPS
1. Read `src/preproc/sections.py`
2. Add `COMMERCIAL = "COMMERCIAL"` to `PageSectionType`
3. Add patterns:
   ```python
   STRONG_COMMERCIAL_PATTERNS = [
       re.compile(r"\bvalidity\s+of\s+tender\b", re.IGNORECASE),
       re.compile(r"\bearnest\s+money\b", re.IGNORECASE),
       re.compile(r"\bbank\s+guarantee\b", re.IGNORECASE),
       re.compile(r"\bfor\s+all\s+engaged\s+manpower\b", re.IGNORECASE),
       re.compile(r"\bsafety\s+(goggle|helmet|shoe|mask|ear\s*plug)\b", re.IGNORECASE),
       re.compile(r"\bPPE\b", re.IGNORECASE),
       re.compile(r"\binsurance\b", re.IGNORECASE),
       re.compile(r"\bpenalty\b", re.IGNORECASE),
       re.compile(r"\bliquidated\s+damages\b", re.IGNORECASE),
   ]
   ```
4. In `classify_page()`, check commercial patterns AFTER BOQ patterns, BEFORE FRONT_MATTER:
   ```python
   for strong_pat in STRONG_BOQ_HEADER_PATTERNS:
       if strong_pat.search(text):
           # existing logic ...
           return PageSectionType.BOQ

   for strong_pat in STRONG_COMMERCIAL_PATTERNS:
       if strong_pat.search(text):
           return PageSectionType.COMMERCIAL

   for strong_pat in STRONG_FRONT_MATTER_PATTERNS:
       # ...
   ```
5. In `find_boq_pages()`, exclude COMMERCIAL pages:
   ```python
   if section in (PageSectionType.BOQ,):
       boq_indices.append(idx)
   ```
   (COMMERCIAL is already excluded since it's not BOQ)
6. In `pipeline.py`, verify `filtered_pages` doesn't include COMMERCIAL (it won't, since only BOQ indices are kept)
7. Add tests

## 5. VERIFICATION
```bash
$ python3 -m pytest tests/unit/test_section_classifier.py -v
EXPECT: all pass + new tests pass

$ python3 -c "
from src.preproc.sections import SectionClassifier, PageSectionType
text = 'Validity of Tender: 180 days\nFor all engaged manpower'
clf = SectionClassifier()
result = clf.classify_page(text, 0)
print(result)
"
EXPECT: PageSectionType.COMMERCIAL

$ python3 -m pytest tests/unit/ --tb=no
EXPECT: All previously-passing tests still pass
```

## 6. ACCEPTANCE CRITERIA
- "Validity of Tender" → COMMERCIAL
- "Safety Goggles" → COMMERCIAL
- "For all engaged manpower" → COMMERCIAL
- "BILL OF QUANTITIES" → still BOQ
- Pipeline skips COMMERCIAL pages
- All tests pass
- Coverage ≥ 80%

## 7. CONSTRAINTS
- COMMERCIAL check must come AFTER BOQ check (don't misclassify BOQ pages)
- Don't modify `config/constants.py`
- Type hints required

## 8. DEPENDENCIES
- Blocked by: None
- Blocks: C2
- Parallel-safe with: B1, B2, B3, F2
- Shared files: `src/preproc/sections.py` (C2 also touches this)

## 9. GOTCHAS
- Some BOQ pages may contain "insurance" in notes — make patterns specific (e.g., "For all engaged manpower" not just "manpower")
- "Safety Goggles" pattern must not match "Safety Goggles as per IS 5983" in a BOQ row — but COMMERCIAL check comes after BOQ, so if page has BOQ header, it's already BOQ
- The `find_boq_pages()` fallback to all pages will still include COMMERCIAL pages if no BOQ detected — this is acceptable (better to process extra than miss BOQ)
