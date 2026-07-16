# TASK P2_01: Ingest SWA's GeM catalog verbatim as the authoritative NER reference (R2) — Agent-P2-1

## 1. GOAL
Make the client-provided GeM product catalog the single authoritative closed-vocabulary reference for material extraction on GeM tenders: ingested verbatim with provenance, wired into dictionary lookup, and used to VALIDATE GeM extractions (a non-catalog material on a GeM tender = flagged red).

## 2. CONTEXT
Files to read FIRST (in order):
- `docs/SWA_REQUIREMENTS_2026-06-11.md` — R2 verbatim
- `data/real_rfqs/swa_gem_catalog.xlsx` + `data/real_rfqs/swa_gem_catalog_full.json` — the delivered catalog (VERIFY provenance first: check `data/real_rfqs/INTAKE_MANIFEST.csv` and git history for who/when these arrived; if provenance is unclear, note it and ask orchestrator before treating as authoritative)
- `resources/PUBLISH PRODUCT.xlsx` — likely the ORIGINAL SWA-provided catalog export (compare with the above)
- `src/nlp/patterns/gem_catalog.py` — the current hand-built 60+ product gazetteer this replaces/extends
- `src/nlp/patterns/` dictionary-lookup wiring (find where `DictionaryLookup` consumes the gazetteer)

Current state:
- A hand-built gazetteer (~132 material keys) is integrated. The real catalog files exist in the repo but their ingestion was done in untrusted sessions — treat current `gem_catalog.py` content as unverified and REGENERATE from the source files.
- The 2 sacred GeM docs (09, 10) are TEST split; the corpus has more GeM-portal docs in the train pool (check manifest for `gem` in names).

## 3. DELIVERABLES
- [ ] `data/ontology/gem_catalog.json` — the ingested catalog: every product row from the source XLSX verbatim (name, category, any spec columns present), plus `_provenance` block (source file, sha256, ingest date, row count)
- [ ] `scripts/ingest_gem_catalog.py` — deterministic converter XLSX → JSON (re-runnable, byte-stable output; sorts by source row order)
- [ ] `src/nlp/patterns/gem_catalog.py` — regenerated: loads from `data/ontology/gem_catalog.json` (no more hard-coded lists); exposes `get_gem_materials() -> dict[str, GemProduct]` and `is_gem_material(text: str) -> bool` (exact + normalized matching: case, whitespace, common OCR artifacts)
- [ ] `src/rules/gem_validation.py` — `validate_gem_extraction(doc_is_gem: bool, materials: list[str]) -> list[GemFlag]`: non-catalog material on a GeM doc → flag (never drop — R1); wire into the pipeline's rule stage for GeM docs
- [ ] `tests/unit/test_gem_catalog.py` — ≥6 tests: load, exact match, normalized match, negative match, validation flags, provenance block present
- [ ] `tests/integration/test_gem_pipeline.py` — pipeline on ONE train-pool GeM doc: extracted materials validated, flags surface in output

## 4. STEPS
1. Provenance check (see §2) — report findings either way.
2. Compare `PUBLISH PRODUCT.xlsx` vs `swa_gem_catalog.xlsx` vs `swa_gem_catalog_full.json`: same product set? Report the diff; ingest from the most-original SWA source (likely `PUBLISH PRODUCT.xlsx` in sacred `resources/` — READ it, never modify anything under `resources/`).
3. Write the ingest script; generate `data/ontology/gem_catalog.json`.
4. Regenerate the gazetteer module; wire validation into the rules stage (GeM-doc detection: manifest `source_batch`/filename markers + document text markers like "GeM Bid" — document your detection rule).
5. Tests; run the integration doc; commit.

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 scripts/ingest_gem_catalog.py && python3 scripts/ingest_gem_catalog.py   # run twice
git status --short data/ontology/gem_catalog.json      # EXPECT: no diff after 2nd run (deterministic)
python3 -c "from src.nlp.patterns.gem_catalog import get_gem_materials; m=get_gem_materials(); print(len(m)); assert len(m) >= 60"
python3 -m pytest tests/unit/test_gem_catalog.py tests/integration/test_gem_pipeline.py -v   # EXPECT: 7+ passed
python3 scripts/audit_fidelity_per_doc.py --all        # EXPECT: sacred-10 unchanged (09/10 are GeM — flags may ADD, rows must not move)
make lint && make typecheck && python3 -m pytest tests/unit tests/integration -q
```

## 6. ACCEPTANCE CRITERIA
- [ ] Catalog JSON is verbatim from the SWA source (spot-check 5 random rows against the XLSX in the report) with full provenance block
- [ ] Zero hard-coded product strings remain in `gem_catalog.py`
- [ ] GeM validation flags, never drops; flags carry reason + the non-matching text
- [ ] Sacred-10 row counts unchanged; TEST docs not used to TUNE anything (09/10 appear only in the frozen fidelity check, not in your development loop — develop against train-pool GeM docs)
- [ ] Ingest re-runnable + deterministic

## 7. CONSTRAINTS
- `resources/` is read-only, SACRED
- Rule 8: do not mine TEST docs (09, 10, or any of the 42) for terms, patterns, or thresholds
- No paraphrase/fuzzy expansion of catalog terms (the entire POINT of R2 is exact standardized vocabulary; normalization is limited to case/whitespace/OCR-artifact cleanup, each covered by a test)
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P0_03
- **Blocks:** P2_03 (drafts use the catalog for MATERIAL pre-annotation), P4_01 (gazetteer features)
- **Parallel-safe with:** P1_02, P1_04
- **Shared files:** `src/nlp/patterns/gem_catalog.py`

## 9. GOTCHAS
- OCR artifacts observed in GeM materials (a rogue-commit topic in the chaos repo — do NOT trust that code; implement cleanly): typical artifacts are doubled spaces, `0/O` swaps, trailing form-feed chars.
- `swa_gem_catalog_full.json` may itself be a prior agent's conversion — that's why you regenerate from XLSX rather than trusting it.
- Catalog product names can be long (>100 chars with specs embedded) — the gazetteer matcher must handle multi-word phrase matching efficiently (existing `DictionaryLookup` phrase mechanics; don't build a new matcher).
- GeM-doc detection must not false-positive on non-GeM docs that merely mention "GeM" in boilerplate — require ≥2 signals (filename/manifest + document header text).
