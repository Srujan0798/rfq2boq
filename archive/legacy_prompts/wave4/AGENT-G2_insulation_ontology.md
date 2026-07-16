# TASK: Build Insulation Domain Ontology — Agent-G2

## 1. GOAL
Create an insulation-specific material ontology that covers the 10 SWA enquiry domains (thermal insulation, acoustic insulation, pipe insulation, duct insulation) so the NER model and BOQ assembler can recognize insulation materials, standards, and units.

## 2. CONTEXT
Files to read FIRST (in order):
- `data/ontology/materials.json` — current material ontology (generic construction: cement, steel, brick, etc.)
- `data/ontology/standards.json` — current standards ontology (IS 456, IS 800, etc.)
- `data/ontology/units.json` — current units ontology
- `data/real_rfqs/swa_enquiries/` — the 10 SWA enquiry files (read their READMEs and XLSX/PDF contents to extract real vocabulary)
- `src/ontology/loader.py` — how ontologies are loaded and queried
- `config/constants.py` — `EntityType` enum (MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE)

Current state:
- Ontology has generic construction materials (cement, concrete, steel, brick, sand, aggregate)
- SWA enquiries are about INSULATION: mineral wool, rock wool, fiberglass, calcium silicate, polyurethane foam, elastomeric foam, ceramic fiber, etc.
- Standards like IS 8183, IS 4671, ASTM C553, BS 3958 are missing
- Units like "running meter", "m²", "m³", "kg", "mm thickness" need insulation-specific aliases
- The NER model cannot recognize what it has never seen — the ontology feeds both the dictionary-based NER and the BOQ assembler validation

## 3. DELIVERABLES
Create or modify EXACTLY these files:
- [ ] `data/ontology/insulation_materials.json` — new file: 50+ insulation materials with categories
- [ ] `data/ontology/insulation_standards.json` — new file: 20+ IS/ASTM/BS standards for insulation
- [ ] `data/ontology/insulation_units.json` — new file: unit aliases specific to insulation (running meter, SQM, CUM, etc.)
- [ ] `src/ontology/loader.py` — modify `ConstructionOntology` to load insulation ontologies alongside base ontologies
- [ ] `tests/unit/test_ontology_loader.py` — add tests for insulation ontology loading and lookup

## 4. STEPS
1. Read all 10 SWA enquiry XLSX files (02, 03, 05, 08) to extract the actual material names used by SWA
2. Read the PDFs (01, 04, 06, 07, 09, 10) to find material mentions in the text
3. Research common Indian insulation standards (IS 8183, IS 4671, IS 9842, IS 11433, etc.)
4. Create `data/ontology/insulation_materials.json` with structure:
   ```json
   {
     "categories": {
       "thermal": ["mineral wool", "rock wool", "fiberglass", ...],
       "acoustic": ["acoustic foam", "mass loaded vinyl", ...],
       "pipe": ["calcium silicate", "polyurethane foam", "elastomeric foam", ...],
       "duct": ["duct liner", "fiberglass duct wrap", ...]
     },
     "materials": [
       {"name": "mineral wool", "aliases": ["mineral fibre", "stone wool"], "category": "thermal", "density_range_kg_m3": [30, 200]}
     ]
   }
   ```
5. Create `data/ontology/insulation_standards.json` with IS/ASTM/BS standards
6. Create `data/ontology/insulation_units.json` with insulation-specific unit aliases
7. Modify `src/ontology/loader.py` to load these files when available
8. Add lookup methods: `lookup_insulation_material(name)`, `lookup_insulation_standard(code)`
9. Add tests
10. Run verification (Section 5)

## 5. VERIFICATION
Run these commands. Each must produce the expected output:

```bash
# Test ontology loads
$ python3 -c "from src.ontology.loader import ConstructionOntology; o = ConstructionOntology(); print('materials:', len(o.insulation_materials)); print('standards:', len(o.insulation_standards))"
EXPECT: materials >= 50, standards >= 20

# Test lookup works
$ python3 -c "from src.ontology.loader import ConstructionOntology; o = ConstructionOntology(); m = o.lookup_insulation_material('mineral wool'); print(m['category'])"
EXPECT: thermal

# Test suite
$ python3 -m pytest tests/unit/test_ontology_loader.py -v
EXPECT: >= 5 new tests pass, 0 failed

# Lint
$ python3 -m ruff check src/ontology/loader.py
EXPECT: All checks passed!
```

## 6. ACCEPTANCE CRITERIA
- [ ] `insulation_materials.json` has >= 50 materials with aliases and categories
- [ ] `insulation_standards.json` has >= 20 standards (IS/ASTM/BS)
- [ ] `insulation_units.json` has >= 15 unit aliases
- [ ] `ConstructionOntology` loads all three files successfully
- [ ] Lookup methods return correct data for known materials
- [ ] All tests pass
- [ ] No ruff errors

## 7. CONSTRAINTS
- All imports use `src.` prefix
- JSON files must be valid (verify with `python3 -m json.tool`)
- Do NOT modify `config/constants.py`
- Do NOT break existing ontology loading
- Keep backward compatibility: existing `lookup_material()` etc. must still work

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** G3 (insulation NER retrain), G4 (BOQ assembler improvements)
- **Parallel-safe with:** G1, G3, G4
- **Shared files:** `src/ontology/loader.py`

## 9. GOTCHAS
- SWA uses British spelling ("fibre" not "fiber") — include both spellings as aliases
- Some materials have multiple names ("PUF" = "polyurethane foam" = "PU foam") — include all aliases
- Indian standards often have year suffixes (IS 8183:2012) — store base code and match with/without year
- "Running meter" is often written as "RMT", "rm", "running m" — include all variants
- Do NOT duplicate existing materials from `materials.json` — insulation materials are NEW
