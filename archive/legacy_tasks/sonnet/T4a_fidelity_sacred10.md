# T4a — 100% capture-or-flag on the sacred 10 (pattern path, no ML)

## 1. GOAL
Every sacred-10 document reaches per-doc PASS — `captured + flagged == source_truth AND dropped == 0 AND over_capture == 0` — by fixing extraction honestly, worst document first.

## 2. CONTEXT (read first)
- `data/real_rfqs/source_truth.json` (T1 — owner-confirmed counts; if not confirmed yet, STOP and wait)
- Current per-doc state (2026-07-04): 01_gsecl 1% · 10_gem 12% · 09_gem 14% · 07_grew 43% · 06_avante 72% · 04_adani 83% · 05 over-captures (48 vs 20) · 02/03/08 pass
- `src/preproc/document_structure.py` (structure-first routing, R4), `src/ingest/table_extractor.py`, `src/pipeline_xlsx.py`, `src/pipeline.py`
- R1: flag-never-drop. A row you can't parse becomes a FLAGGED row with raw text, not a missing row.

## 3. DELIVERABLES
- Extraction fixes in `src/` (each with a unit test in `tests/`)
- Configurable multi-qty rule in `src/pipeline_xlsx.py`: `RFQ2BOQ_MULTIQTY_MODE = n_rows (default) | single_row` via `config.settings` — fixes 05 over-capture together with dedupe
- `results/fidelity_after_T4a.md` — the per-doc table, two consecutive identical runs
- Updated `scripts/measure_fidelity.py` if flag-counting needs wiring (never the PASS definition)

## 4. STEPS — one doc at a time, commit per doc
1. **01_gsecl (1%):** multi-page Schedule-B (~pages 60–69). Structure-first must return the FULL page range; table extractor must stitch multi-page tables (repeated headers, continuation rows). Sub-item counting follows the owner-ratified rule from T1.
2. **09/10_gem (14%/12%):** GeM portal PDFs. Implement multi-range BOQ sections (R4 says "maybe multiple, maybe annexures") + section false-positive filter (known: 1281 candidate sections on one 29MB PDF). Add a per-file timeout (these docs previously hung). Catalog `gem_id` anchors validate item rows.
3. **07_grew (43%), 06_avante (72%), 04_adani (83%):** diff extracted vs source_truth row-by-row; classify each miss (wrong table picked / dropped row / merged cell / header misread); fix by class, not by doc.
4. **05_zydus_animal (over-capture):** multi-qty columns → `n_rows` mode with dedupe on (description, location, qty-column); verify 48→exact source count against the XLSX itself.
5. After each fix: run BOTH harnesses; append the per-doc number to the ledger; `make verify`; commit.
6. Final: two consecutive full runs, identical output → `results/fidelity_after_T4a.md`.

## 5. VERIFICATION
```bash
PYTHONPATH=. .venv/bin/python scripts/measure_fidelity.py      # all 10 PASS
PYTHONPATH=. .venv/bin/python scripts/fidelity_audit.py --all  # matches
.venv/bin/python -m pytest tests/ -q                            # green
make verify                                                     # green
```

## 6. ACCEPTANCE CRITERIA
All 10 per-doc PASS against owner-confirmed source truth (or a documented per-doc blocker the owner explicitly accepts); zero dropped; zero over-capture; every fix has a test; numbers stable across two runs.

## 7. CONSTRAINTS
No gold edits, no source_truth edits, no per-file thresholds, no filename logic. If a target seems impossible, the answer is a REPORT explaining why with evidence — not a relaxed rule.

## 8. DEPENDENCIES
Blocks: T4b, T7. Blocked by: T1 (owner-confirmed), T0. Parallel-safe: no (touches core extraction).

## 9. GOTCHAS
- 09/10 GeM hang history: timeouts + page-range routing BEFORE parsing, not after.
- Fixing 01's multi-page stitching may change 04/06 numbers — re-run ALL docs after every fix, not just the one you touched.
- "Comply"-column BOQs (compliance sheets) have qty AND unit swapped column order in some docs (seen: Unit=600.00, Qty=M2) — header inference must use content type, not position.
