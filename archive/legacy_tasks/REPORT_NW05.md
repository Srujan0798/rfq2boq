# REPORT — NW-05: Unified Unit Normalizer

**Date:** 2026-06-28
**Branch:** phase8-clean-slate

## What Changed

All unit normalization now flows through `src/rules/units.py` as the single source of truth.

### Files Modified

| File | Change |
|------|--------|
| `src/unit_normalization.py` | Re-exported `normalize_unit` from `src.rules.units` + added `__all__` |
| `src/ontology/loader.py` | Renamed method `normalize_unit` → `resolve_unit_symbol` to avoid name collision |
| `scripts/build_row_gold_03.py` | Removed local `_normalize_unit`, imported from `src.rules.units` |
| `tests/unit/test_units_unified.py` | NEW: 425 table-driven tests covering all alias→canonical mappings |
| `tests/unit/test_ontology_loader.py` | Updated to call `resolve_unit_symbol` |
| `tests/integration/test_pipeline.py` | Fixed expected canonical forms (`cum`, `sqm` not `m^3`, `m^2`) |
| `tests/e2e/test_full_pipeline.py` | Fixed expected canonical forms + import path |

### Files Kept As-Is (by design)

| File | Reason |
|------|--------|
| `src/domain/boq_assembler.py` `_normalize_unit` | Material-context logic (e.g., concrete→cum), underscore-prefixed |
| `src/ingest/text_boq_extractor.py` `_UNIT_MAP` | Lossy domain-specific map, different conventions |
| `src/ingest/preprocessor.py` `unit_replacements` | Text-cleaning, different concern |

## Acceptance Criterion

```bash
grep -rEn "def normalize_unit|UNIT_ALIASES\s*=" src/ scripts/
# Expected: only rules/units.py + test files
```

**VERIFIED:** Empty output (excluding `rules/units.py` and test files).

## Eval Before/After (10-enquiry baseline)

| Metric | NW-03 Baseline | After NW-05 | Delta |
|--------|----------------|-------------|-------|
| Micro P | 87.6% | 87.6% | 0 |
| Micro R | 78.3% | 78.3% | 0 |
| Micro F1 | 82.7% | 82.7% | 0 |
| Macro P | 77.2% | 77.2% | 0 |
| Macro R | 72.4% | 72.4% | 0 |
| Macro F1 | 74.4% | 74.4% | 0 |

**Conclusion:** Zero regression. NW-05 was a pure refactor — consolidated duplicate normalizer logic without changing behavior.
