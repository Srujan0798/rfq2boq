# TASK P3_01: Structure-first PDF extraction — multi-range routing + section precision (R4) — Agent-P3-1

## 1. GOAL
Complete the mentor-endorsed structure-first method: parse the document outline, identify ALL BOQ-bearing sections/annexures (not just the single best), route extraction only there — cutting noise and runtime on 50–100+ page tenders while never missing a BOQ range.

## 2. CONTEXT
Files to read FIRST (in order):
- `docs/SWA_REQUIREMENTS_2026-06-11.md` — R4 verbatim ("maybe one, maybe multiple, maybe annexures")
- `src/preproc/document_structure.py` — existing PyMuPDF outline scan with Schedule/Annexure/Appendix boosting (single-range today)
- `src/preproc/sections.py` — `find_boq_pages`/`analyse_page` (the page-level BOQ signal)
- `src/pipeline.py` — where structure routing feeds extraction
- P1_04's corpus-run status — per-doc durations (identifies the slow OCR-heavy PDFs this should speed up)

Current state:
- GSECL's 62-page tender resolves to pages 60–69 correctly; but (a) only ONE range is returned, (b) a 29MB PDF produced 1281 candidate sections (precision problem), (c) the slow GeM PDFs (P0_03 tiered their tests as `slow`) burn time OCRing pages structure-routing should skip.

## 3. DELIVERABLES
- [ ] `src/preproc/document_structure.py` — `find_boq_ranges(doc) -> list[PageRange]` (replaces the single-range API): every range scored, overlapping ranges merged, annexure references followed (a section saying "as per Annexure-B" pulls Annexure-B's range in)
- [ ] Candidate-section precision: scoring gate documented in the docstring (features: heading keywords, table density on the page, qty/unit token density) with a threshold that reduces the 1281-candidate case to <50 without losing any TRUE range in the evaluation set below
- [ ] `src/pipeline.py` — consumes all ranges; per-range extraction merged with range provenance on each row (`source_pages`)
- [ ] Fallback contract: if NO range scores above threshold → full-document extraction + `structure_fallback:true` flag (R1: never let routing lose data)
- [ ] `tests/unit/test_document_structure.py` — ≥8 tests incl. multi-range merge, annexure follow, fallback trigger
- [ ] `results/structure_eval/STRUCTURE_EVAL.md` — evaluation table over every TRAIN/DEV PDF ≥10 pages: doc, pages, ranges found, pages routed vs total, rows extracted before/after, duration before/after, verdict (rows must be ≥ before; time should drop)

## 4. STEPS
1. Read context. Build the evaluation set list: TRAIN/DEV PDFs ≥10 pages (from manifest + P1_04 durations). NOT test docs — except the sacred-10 fidelity check runs as usual at the end (frozen check, not development data).
2. Implement multi-range + scoring; iterate ONLY against the TRAIN/DEV evaluation set.
3. Wire pipeline consumption + fallback; add row `source_pages` provenance.
4. Tests; full evaluation table; sacred-10 fidelity check; commit (separate commits: structure engine / pipeline wiring / eval artifacts).

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 -m pytest tests/unit/test_document_structure.py -v          # EXPECT: 8+ passed
python3 scripts/run_corpus.py --split train --type boq_bearing       # EXPECT: all ok, durations improved on large PDFs
python3 scripts/audit_fidelity_per_doc.py --all                      # EXPECT: sacred-10 verdicts unchanged, no doc loses rows
python3 -m pytest tests/unit tests/integration -q && make lint && make typecheck
```

## 6. ACCEPTANCE CRITERIA
- [ ] Zero rows lost on ANY corpus doc vs the P1_04 baseline (routing may only add or speed up — R1)
- [ ] Multi-range: at least one real doc demonstrably extracts from ≥2 ranges (name it in the report)
- [ ] 29MB pathological case: candidates <50, runtime reported before/after
- [ ] Fallback proven by test AND by at least one real doc in the eval table
- [ ] Eval table complete and honest (regressions listed, not hidden)

## 7. CONSTRAINTS
- Rule 8: routing heuristics tuned on TRAIN/DEV only
- No new model dependencies (LayoutLMv3 is P3_02's decision, not yours); PyMuPDF + existing stack only
- Frozen files untouched
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P1_04 (baseline numbers), P1_02 (auditor as the regression instrument)
- **Blocks:** P3_02 (shares `src/pipeline.py`)
- **Parallel-safe with:** P2_03, P3_03
- **Shared files:** `src/pipeline.py`, `src/preproc/*`

## 9. GOTCHAS
- Many Indian tender PDFs have NO embedded outline/bookmarks — structure must come from font-size/weight heuristics on rendered text (the existing fast-scan does this; keep it the primary path).
- Scanned (image-only) PDFs: structure scan sees no text → that's a legitimate fallback trigger, not a bug; OCR-first-then-structure is allowed for these but cap it (OCR only until N candidate pages found).
- "Schedule of Quantities" vs "Schedule of Rates": both are headings containing "Schedule"; SOR sections are PRICED (out of scope) — rows from an SOR-only range would violate the unpriced-BOQ scope; treat SOR headings as negative signal, and add a test.
- Page numbers in outlines are 1-based in most viewers, 0-based in PyMuPDF — one off-by-one here silently loses a page of rows (R1); test the boundary explicitly.
