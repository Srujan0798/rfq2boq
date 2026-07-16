# The 10 SWA Enquiries (held-out TEST anchor — NOT the whole corpus)

**Corrected 2026-07-05 — this file previously claimed these 10 are the whole scope. That was wrong and misled agents into scoping fidelity/training work to only 10 documents.**

These are 10 of the 127 real RFQ documents this project has. They are the **frozen TEST-split anchor** (see `data/real_rfqs/split_test.json` and `data/real_rfqs/corpus_manifest.json`) — never trained on, never mined for gazetteer terms, evaluated once at the end. They are NOT the only documents verification/eval/training should center on.

**The full corpus** (see `data/real_rfqs/corpus_manifest.json`, 127 docs total):
- `data/specifications/Specifications/` — 50 docs (spec1 batch, also in `resources/Specifications.rar`)
- `data/specifications/Specification 2/` — 41 docs (spec2 batch, incl. XLSX BOQs)
- `data/real_rfqs/swa_enquiries/` (this dir) — the 10 sacred/TEST enquiries
- email enquiry bundle folders under `data/specifications/` (Grew Solar/SAEL/AVANTE/Adani/Zydus Animal Health) — these ARE the original source documents this dir's gold was built from

All of the above are real RFQs and are in scope for fidelity fixes, human annotation, and training (TRAIN/DEV split docs) — see `tasks/sonnet/T4b_fidelity_full_corpus.md` and `tasks/sonnet/00_START_HERE.md` §CORPUS.

See docs/PHASE8_UNIFIED_TIMELINE_AND_FLOW.md for historical context (honest metrics, owner verification) — note its "10 files as sacred core" framing predates the full-corpus expansion and should be read as "sacred **TEST** core," not "sacred **only** data."

Demo order (strongest first):
1. 05 Zydus Animal (XLSX, 48 rows, instant, strongest)
2. 03 Zydus Matoda (XLSX, 33 rows, instant, strong)
3. 02 ISRO (XLSX, 8 rows, instant, lead with this)
4. 08 SAEL (XLSX, 12 rows, instant, clean)
5. 04 Adani (PDF, 41 rows, 5s, good)
6. 06 Avante (PDF, 34 rows, 6s, good)
(07, 10, 01 OK/weak; 09 GeM 🔴 pre-run only, do not live drag - 219s + HF download)

Place the actual source files in the subdirs using the exact names from tests/e2e/test_all_enquiries.py or the per-enquiry READMEs.
