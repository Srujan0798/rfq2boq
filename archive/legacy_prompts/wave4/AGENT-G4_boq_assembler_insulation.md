# TASK: Improve BOQ Assembler for Insulation Domain — Agent-G4

## 1. GOAL
Improve the BOQ assembler to correctly group insulation-specific entities (material + thickness/diameter + unit + location) into proper BOQ rows, raising the row-level match rate from ~32% to >= 60% on the 4 XLSX enquiries.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/domain/boq_assembler.py` — current BOQ assembly logic
- `src/domain/models.py` — `BoqRow` dataclass and validation
- `src/ingest/table_extractor.py` — table → BOQ row extraction (recently fixed)
- `data/real_rfqs/swa_enquiries/` — the 10 SWA enquiries (XLSX files have ground truth)
- `scripts/eval_product.py` — row-level evaluation script
- `src/ontology/loader.py` — ontology lookups (will be enhanced by G2)

Current state:
- Row-level match on 4 XLSX enquiries: 02=36.4%, 03=5.1%, 05=43.8%, 08=70.6% (average ~32.3%)
- The assembler groups entities by proximity but doesn't understand insulation semantics
- Example: "50mm thick mineral wool insulation for 150mm dia pipe" should produce:
  - material: "mineral wool insulation"
  - dimension: "50mm thick"
  - dimension: "150mm dia"
  - location: "pipe"
- Currently these may be split into separate rows or miss the thickness entirely
- Table extractor now works (B1/B2/B3 fixes) but assembler doesn't leverage the improved data

## 3. DELIVERABLES
Create or modify EXACTLY these files:
- [ ] `src/domain/boq_assembler.py` — add insulation-aware grouping logic
- [ ] `src/domain/models.py` — add `thickness_mm`, `diameter_mm`, `insulation_type` fields to `BoqRow` if useful
- [ ] `src/rules/insulation_rules.py` — NEW: insulation-specific rules for entity grouping and validation
- [ ] `tests/unit/test_boq_assembler.py` — add insulation-specific test cases
- [ ] `scripts/eval_product.py` — ensure it reports per-enquiry match rates correctly

## 4. STEPS
1. Read context files (Section 2)
2. Run current evaluation to establish baseline:
   ```bash
   python3 scripts/eval_product.py --gold data/real_rfqs/swa_enquiries/ --predicted results/
   ```
3. Analyze the 4 XLSX ground truth files to understand the expected row structure:
   - What fields does each row have? (item_no, description, quantity, unit, rate, amount)
   - How are dimensions represented? ("50mm thick", "150mm dia", "25mm thick")
   - How are locations represented? ("pipe", "duct", "tank", "equipment")
4. Implement insulation-aware grouping in `src/domain/boq_assembler.py`:
   - When MATERIAL contains "insulation", look for nearby DIMENSION entities
   - Group by: material + thickness + diameter + location
   - If multiple dimensions found, create separate rows (e.g., "50mm" and "25mm" are different items)
5. Create `src/rules/insulation_rules.py` with:
   - `extract_thickness_mm(text: str) -> int | None` — parse "50mm thick", "25 mm", etc.
   - `extract_diameter_mm(text: str) -> int | None` — parse "150mm dia", "100 mm diameter", etc.
   - `infer_insulation_type(material: str) -> str` — "thermal", "acoustic", "pipe", "duct"
   - `validate_insulation_row(row: BoqRow) -> list[str]` — check thickness + diameter + unit consistency
6. Update `BoqRow` in `src/domain/models.py` if needed
7. Add tests with real examples from SWA enquiries
8. Run verification (Section 5)

## 5. VERIFICATION
Run these commands. Each must produce the expected output:

```bash
# Baseline evaluation
$ python3 scripts/eval_product.py --gold data/real_rfqs/swa_enquiries/ --predicted results/
EXPECT: reports current baseline (should be ~32%)

# Test insulation rules
$ python3 -m pytest tests/unit/test_boq_assembler.py -v -k "insulation"
EXPECT: >= 5 new insulation tests pass, 0 failed

# Test thickness extraction
$ python3 -c "
from src.rules.insulation_rules import extract_thickness_mm
print(extract_thickness_mm('50mm thick mineral wool'))
print(extract_thickness_mm('25 mm thick'))
"
EXPECT: 50, 25

# Full assembler test
$ python3 -c "
from src.domain.boq_assembler import BOQAssembler
from src.domain.models import Entity, EntityType
entities = [
    Entity(text='mineral wool', type=EntityType.MATERIAL, start=0, end=10),
    Entity(text='50mm', type=EntityType.DIMENSION, start=11, end=15),
    Entity(text='150mm dia pipe', type=EntityType.LOCATION, start=20, end=34),
    Entity(text='100', type=EntityType.QUANTITY, start=35, end=38),
    Entity(text='m2', type=EntityType.UNIT, start=39, end=41),
]
asm = BOQAssembler()
rows = asm.assemble(entities)
print('rows:', len(rows))
for r in rows: print(r.material, r.dimensions, r.quantity, r.unit)
"
EXPECT: 1 row with material='mineral wool', dimensions=['50mm'], quantity=100, unit='m2'

# No regressions
$ python3 -m pytest tests/unit/test_boq_assembler.py -v --tb=short
EXPECT: all existing tests pass
```

## 6. ACCEPTANCE CRITERIA
- [ ] Row-level match rate on 4 XLSX enquiries >= 60% (up from ~32%)
  - 02 ISRO: >= 60%
  - 03 Zydus Matoda: >= 50%
  - 05 Zydus Animal: >= 60%
  - 08 SAEL: >= 80%
- [ ] Insulation-specific entity grouping works correctly
- [ ] Thickness and diameter extraction works for common patterns
- [ ] All tests pass
- [ ] No ruff errors
- [ ] No mypy errors

## 7. CONSTRAINTS
- All imports use `src.` prefix
- Entity types from `config.constants.EntityType`
- Do NOT modify `config/constants.py`
- Do NOT break existing BOQ assembly for non-insulation materials
- Keep backward compatibility

## 8. DEPENDENCIES
- **Blocked by:** G2 (insulation ontology — provides material/standard lookups)
- **Blocks:** P8T8 (final handover)
- **Parallel-safe with:** G1
- **Shared files:** `src/domain/boq_assembler.py`, `src/domain/models.py`

## 9. GOTCHAS
- "50mm thick" and "50 mm thick" are the same — handle both spacing patterns
- "150mm dia" and "150 mm diameter" and "150mm Ø" are the same — normalize
- Some rows have TWO dimensions (thickness + diameter) — don't drop either
- "Running meter" (RMT) is a common insulation unit — ensure it's recognized
- The 03 Zydus Matoda has the lowest match rate (5.1%) — focus extra attention there
- Don't overfit to the 4 XLSX files — the rules should generalize to new insulation tenders
