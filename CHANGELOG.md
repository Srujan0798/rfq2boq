# Changelog

All notable changes to RFQ2BOQ are documented here.

## [0.1.0] - 2024-05-16 - Initial Release

### Added

- **BERT-BiLSTM-CRF NER Model** — Trained on 300 synthetic RFQ documents
  - 8 entity types: MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE
  - BIOES tagging scheme
  - Test F1: 99.56% (synthetic), 33.73% (real-world - needs retraining)

- **Complete Pipeline** — End-to-end RFQ to BOQ extraction
  - PDF ingestion with OCR fallback for scanned documents
  - NLP pipeline with entity recognition and relation extraction
  - BOQ row builder with rule-based validation
  - Excel and JSON export

- **Construction Ontology** — 251 materials, 81 standards, 65 units, 60 locations
  - Indian standards focus (IS codes: IS 456, IS 1786, IS 2062, etc.)
  - Alias-based fuzzy matching
  - Validation against domain knowledge

- **Production Infrastructure** — API, CLI, UI
  - FastAPI REST API with rate limiting and health checks
  - Streamlit web interface
  - CLI for batch processing

- **Evaluation Framework** — Synthetic + Real-world
  - `scripts/train_simple.py` — CPU training
  - `scripts/evaluate_real.py` — Real-world evaluation
  - `scripts/validate_annotations.py` — BIOES consistency check

- **Documentation** — Full project documentation
  - Technical report with methodology
  - API reference
  - Operations runbook
  - Onboarding guide for new developers

### Known Limitations

- **Synthetic training gap**: Real RFQ F1 is 33.73% vs 99.56% on synthetic test set
- **English only**: No Hindi/regional language support
- **Indian focus**: Optimized for IS codes, limited ASTM/BS/EN coverage
- **Table extraction**: Complex layouts may fail

### Future Roadmap

- [ ] Real RFQ annotation + retraining (P0)
- [ ] Multi-page PDF batch processing (P1)
- [ ] Hindi/regional language support (P2)
- [ ] International standards coverage (P3)
- [ ] Cloud deployment (P4)

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