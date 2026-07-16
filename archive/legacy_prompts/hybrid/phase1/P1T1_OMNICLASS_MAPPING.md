# TASK: P1T1 — OmniClass Mapping — Agent-1

**Phase:** 1 | **Effort:** 2 hours | **Priority:** P0 (smallest, do first)

## 1. GOAL
Create a bidirectional mapping between our 8 RFQ2BOQ entity types and the OmniClass classification system used by every major BIM tool, so our outputs become standards-interoperable without code changes.

## 2. CONTEXT
Read first:
- `config/constants.py` — our 8 entity types
- `data/ontology/materials.json` — our materials list (sample)
- `data/ontology/standards.json` — our standards list (sample)
- [docs/HYBRID_PLAN.md](../../../docs/HYBRID_PLAN.md) — why we're doing this
- [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md) — project-wide gotchas
- OmniClass reference: https://www.csiresources.org/standards/omniclass

OmniClass relevant tables:
- Table 22 (Work Results) — our ACTION entities
- Table 23 (Products) — our MATERIAL entities
- Table 23 also covers GRADE through product specifications
- Table 41 (Materials properties) — our STANDARD entities
- Table 49 (Properties) — for DIMENSION
- Table 13 (Spaces by function) — our LOCATION entities
- Units in OmniClass use standard SI references

## 3. DELIVERABLES
- [ ] `data/ontology/omniclass_map.json` — mapping file (see §4 for schema)
- [ ] `src/ontology/omniclass.py` — small loader class
- [ ] `tests/unit/test_omniclass_map.py` — ≥6 tests
- [ ] `docs/omniclass_mapping.md` — human-readable map explanation

## 4. STEPS
1. Read context files.
2. Create `data/ontology/omniclass_map.json` with this exact shape:
   ```json
   {
     "version": "1.0",
     "source": "OmniClass 2019 + RFQ2BOQ 1.0",
     "entity_to_omniclass": {
       "MATERIAL": {"table": "23", "name": "Products", "default_code": "23-13"},
       "QUANTITY": {"table": null, "note": "Plain numeric value, no OmniClass equivalent"},
       "UNIT": {"table": null, "note": "Standard SI unit symbol"},
       "LOCATION": {"table": "13", "name": "Spaces by Function", "default_code": "13-11"},
       "DIMENSION": {"table": "49", "name": "Properties", "default_code": "49-21"},
       "STANDARD": {"table": "41", "name": "Materials and Methods", "default_code": "41-31"},
       "ACTION": {"table": "22", "name": "Work Results", "default_code": "22-00"},
       "GRADE": {"table": "23", "name": "Products (specification)", "default_code": "23-13-25"}
     },
     "material_specifics": {
       "cement": "23-13-21-13",
       "concrete": "23-13-21-19",
       "steel_reinforcement": "23-13-25-11",
       "structural_steel": "23-13-25-15",
       "brick": "23-13-23-11",
       "mortar": "23-13-21-23",
       "plaster": "23-13-29-11",
       "tile": "23-15-23-11"
     },
     "action_specifics": {
       "supply": "22-01",
       "install": "22-03",
       "lay": "22-03-21",
       "fix": "22-03-31",
       "construct": "22-03"
     }
   }
   ```
3. Create `src/ontology/omniclass.py`:
   ```python
   class OmniClassMapper:
       def __init__(self, path="data/ontology/omniclass_map.json"): ...
       def map_entity(self, entity_type: str, text: str | None = None) -> dict: ...
       def reverse_lookup(self, omniclass_code: str) -> str: ...  # OmniClass → our type
   ```
4. Add unit tests covering: every entity type maps to something (or explicit None); reverse lookup works; unknown codes return None gracefully.
5. Write `docs/omniclass_mapping.md` explaining the mapping in plain English.
6. Run verification.

## 5. VERIFICATION
```bash
$ python3 -c "import json; m=json.load(open('data/ontology/omniclass_map.json')); assert 'entity_to_omniclass' in m; assert len(m['entity_to_omniclass']) == 8"
EXPECT: no AssertionError

$ python3 -c "from src.ontology.omniclass import OmniClassMapper; m = OmniClassMapper(); assert m.map_entity('MATERIAL', 'cement')['code'].startswith('23-')"
EXPECT: no AssertionError

$ python3 -m pytest tests/unit/test_omniclass_map.py -v
EXPECT: ≥6 passed

$ test -f docs/omniclass_mapping.md
EXPECT: exit 0
```

## 6. ACCEPTANCE CRITERIA
- [ ] All 8 entity types present in `entity_to_omniclass`
- [ ] At least 8 material_specifics entries
- [ ] At least 5 action_specifics entries
- [ ] `OmniClassMapper.map_entity` returns a dict with `table`, `code`, `name` keys
- [ ] Reverse lookup works for at least 3 sample codes
- [ ] Coverage of `src/ontology/omniclass.py` ≥ 80%

## 7. CONSTRAINTS
- All imports use `src.` prefix
- DO NOT change existing `data/ontology/*.json` files
- DO NOT introduce rdflib or owlready2 dependencies — keep it simple JSON
- OmniClass codes can be partial (table-section), no need to be most specific level

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** Future IFC export improvements (already covered by `src/export/adapters/ifc_export.py`)
- **Parallel-safe with:** P1T2, P1T3, P1T4, P1T5

## 9. GOTCHAS
- OmniClass uses dashes in codes (e.g., `23-13-21-13`), keep them as strings, never split into numbers
- Some entities (QUANTITY, UNIT) genuinely have no OmniClass equivalent; that's fine — return `null` with a note
- Do NOT invent codes that don't exist in OmniClass; use partial codes if you can't find specifics
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md) § Architecture for path conventions
