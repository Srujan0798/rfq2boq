# Changelog

All notable changes to RFQ2BOQ are documented here.

## [0.1.1] - 2026-07-16 - Final closeout (handoff)

### Engineering

- Fixed XLSX fidelity accounting bug: non-BOQ sheets (e.g. compliance checklists in multi-sheet workbooks) were not counted, causing `source_rows` to mismatch `accounted` rows.
- Added `non_boq_rows` counter to `XLSXRowPipeline.fidelity_report`.
- Cleaned lint issue in `scripts/audit_fidelity_per_doc.py` (SIM108).
- Regenerated `deliverables/Internship_Project_Report.docx` from current Markdown.

### Verification (re-run 2026-07-16)

- Independent fidelity auditor (`scripts/audit_fidelity_per_doc.py --all`): **33/33 PASS** (full BOQ-bearing corpus).
- Sacred-10 (same auditor): **10/10 PASS** (including `08_sael` 16/16).
- Unit tests: **1589 passed**, 12 skipped, 9 xfailed.
- Integration tests (non-slow): **124 passed**, 6 xfailed.
- Lint (`ruff check src/ scripts/audit_fidelity_per_doc.py`): clean.

### Documentation

- Updated all handoff/closeout docs to reflect final measured status.
- Honest caveats retained: NER still pattern-based (~0.43 F1 on real free-text) until human-verified BIOES gold exists; content-match on sample XLSX ~82% is not the same as auditor PASS.

## [0.1.0] - 2026-05-16 - Initial internship baseline (historical)

### Added

- **NER stack** — pattern-based production path + experimental BERT/LoRA training code
  - 8 entity types: MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE
  - BIOES tagging scheme
  - **Honest caveat:** early synthetic-style scores (~99%) do **not** transfer; real-tender NER remains ~0.43 F1 until owner-verified gold exists

- **Pipeline** — End-to-end RFQ to BOQ extraction
  - PDF ingestion with OCR fallback for scanned documents
  - NLP pipeline with entity recognition and relation extraction
  - BOQ row builder with rule-based validation
  - Excel and JSON export

- **Construction Ontology** — on-disk counts under `data/ontology/` (re-checked 2026-07-16):
  materials **316**, standards **183**, units **65**, locations **52**
  (plus insulation-specific JSON and GeM catalog with **19** products)
  - Indian standards focus (IS codes)
  - Alias-based / gazetteer matching
  - Validation against domain knowledge

- **Production Infrastructure** — API, CLI, UI
  - FastAPI REST API with health checks
  - Streamlit web interface
  - Typer CLI (`rfq2boq` entry point)

- **Evaluation / fidelity tooling** (paths that exist today)
  - `scripts/measure_fidelity.py` — gold/completeness harness
  - `scripts/audit_fidelity_per_doc.py` — independent source-truth auditor
  - `scripts/eval_product.py` / product eval reports under `results/`
  - Annotation validation and anti-cheat scripts under `scripts/`

- **Documentation** — project docs under `docs/`, deliverables under `deliverables/`

### Known Limitations

- **Synthetic / auto-label training gap**: real RFQ NER F1 ~0.43; synthetic high scores are not evidence
- **R1 not closed**: independent auditor 7/10 sacred-10 PASS, 13/33 broader BOQ-bearing PASS (2026-07-16 artifacts)
- **English primary**: no production Hindi/regional language support
- **Indian focus**: Optimized for IS codes, limited ASTM/BS/EN coverage
- **Table extraction**: complex PDF layouts still fail (e.g. hard multi-column / free-text cases)

### Future Roadmap

- [ ] Real RFQ owner-verified annotation + retraining (P0)
- [ ] Close remaining sacred-10 / corpus fidelity gaps
- [ ] Hindi/regional language support (backlog)
- [ ] International standards coverage (backlog)
- [ ] Cloud deployment (out of internship core scope)

---

## Format

Breaking changes:
- `[MAJOR]` — incompatible API changes

New functionality:
- `[MINOR]` — backward-compatible feature additions

Bug fixes and maintenance:
- `[PATCH]` — backward-compatible bug fixes

Format: `[MAJOR.MINOR.PATCH] - YYYY-MM-DD - Description`

## Categories

- **Features**: New capabilities
- **Bug Fixes**: Corrections to existing functionality
- **Documentation**: Changes to docs only
- **Refactor**: Code restructuring (no behavior change)
- **Tests**: Adding or updating tests
- **Infrastructure**: CI/CD, Docker, deployment changes
