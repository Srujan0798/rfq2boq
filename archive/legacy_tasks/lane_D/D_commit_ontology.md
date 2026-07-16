# TASK: Lane D — Commit ontology + GeM work, add insulation IS-codes — Agent-D

**Worktree:** `/Users/srujansai/Desktop/rfq2boq-laneD`
**Branch:** `phase8-laneD`
**Model:** MiniMax (or lightest available — this is mechanical work)

---

## 1. GOAL
Commit the already-passing ontology/GeM work and extend it with insulation IS-code standards extracted from spec PDFs, so the NER gazetteer is enriched with real domain terms.

## 2. CONTEXT
Files to read FIRST:
- `data/ontology/insulation_materials.json` — already created (thermal/acoustic materials)
- `data/ontology/insulation_standards.json` — already created (standards)
- `data/ontology/insulation_units.json` — already created (units)
- `src/nlp/patterns/gem_catalog.py` — already updated (GeM gazetteer)
- `src/ontology/loader.py` — already updated (loads insulation ontology)
- `tests/unit/test_gem_catalog.py` — 28 tests pass
- `tests/unit/test_ontology_loader.py` — passing
- `config/constants.py` — READ ONLY. 8 entities, 6 relations, BIOES. Never modify.
- `resources/Specifications/INSULATION TECH SPEC.pdf` — IS-code source
- `resources/Specifications/37. RPMS-ENGG-SPC-HV-019-Thermal insulation.pdf` — standards source

Current state: all changes uncommitted, lint clean, 28 tests pass.

## 3. DELIVERABLES
- [ ] `data/ontology/insulation_standards.json` — add IS-code entries extracted from spec PDFs (IS 8183, IS 9842, IS 11239 etc. if present in the PDFs)
- [ ] `data/ontology/insulation_materials.json` — add any missing materials found in specs
- [ ] `tests/unit/test_ontology_loader.py` — ensure all new entries are covered
- [ ] Git commit with REPORT in commit body

## 4. STEPS
1. Run `cd /Users/srujansai/Desktop/rfq2boq-laneD && python3 -m pytest tests/unit/test_gem_catalog.py tests/unit/test_ontology_loader.py -q` — confirm 28 pass.
2. Use pdfplumber to extract text from `resources/Specifications/INSULATION TECH SPEC.pdf` and `resources/Specifications/37. RPMS-ENGG-SPC-HV-019-Thermal insulation.pdf`. Look for IS/BS/ASTM/ASHRAE standard codes (regex `IS[\s-]\d{3,5}`).
3. Append found codes to `data/ontology/insulation_standards.json` under a `"standards"` key. Include only codes that actually appear in the PDFs — no invented entries.
4. Run `python3 -m ruff check src/ --quiet` — must be clean.
5. Run `python3 -m pytest tests/unit/test_gem_catalog.py tests/unit/test_ontology_loader.py -q` — must still pass.
6. Commit ALL changes (the pre-existing uncommitted diff + new ontology entries):
   ```
   git add src/nlp/patterns/gem_catalog.py src/ontology/loader.py \
     tests/unit/test_gem_catalog.py tests/unit/test_ontology_loader.py \
     data/ontology/insulation_materials.json data/ontology/insulation_standards.json \
     data/ontology/insulation_units.json
   git commit -m "feat(ontology): GeM gazetteer + insulation domain ontology (D1-D2)"
   ```

## 5. VERIFICATION
```bash
cd /Users/srujansai/Desktop/rfq2boq-laneD
python3 -m pytest tests/unit/test_gem_catalog.py tests/unit/test_ontology_loader.py -q
python3 -m ruff check src/ --quiet
git log --oneline -1
python3 -c "from src.ontology.loader import OntologyLoader; o=OntologyLoader(); print(len(o.get_materials()), 'materials loaded')"
```

## 6. ACCEPTANCE CRITERIA
- [ ] 28+ tests pass (no regressions)
- [ ] Lint clean
- [ ] `insulation_standards.json` has at least 3 IS-code entries derived from PDFs
- [ ] All entries traceable to source PDF (add `"source"` field per entry)
- [ ] Commit exists on `phase8-laneD`

## 7. CONSTRAINTS
- Imports: `src.` prefix only
- Schema (`config/constants.py`) READ ONLY — never modify
- No invented standards — only what appears in the PDFs
- Python 3.11–3.13 (venv at `.venv-lora` uses 3.12; use that)
- No new branches

## 8. DEPENDENCIES
- Blocked by: nothing (all prior D work already done)
- Blocks: Srujan merging laneD → phase8-clean-slate

## 9. GOTCHAS
- The `.venv` in the laneD worktree is Python 3.14 — broken. Use `.venv-lora` (3.12): `source /Users/srujansai/Desktop/rfq2boq-laneD/.venv-lora/bin/activate`
- Do NOT edit `config/constants.py` — ontology is additive data, not schema
- pdfplumber may return None for some pages — handle gracefully

---

## REPORT FORMAT (paste back to Srujan on completion)
```
## REPORT: Lane D — Ontology commit

Deliverables:
- path — created/modified

Verification:
- pytest: N passed
- ruff: clean
- standards extracted: N codes from which PDFs
- materials loader: N materials loaded

Blockers: none / list
Deviations: none / list
```
