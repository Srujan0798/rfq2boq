# TASK P3_02: Column-aware PDF table extraction — kill the interleaved-column bug class — Agent-P3-2

## 1. GOAL
Fix the diagnosed multi-column layout problem (07_grew class): when a PDF table has side-by-side columns (description | qty | remarks), plain text extraction interleaves them and corrupts/loses rows. Use positional (bbox-based) extraction so each row is assembled from cells, not from jumbled text lines.

## 2. CONTEXT
Files to read FIRST (in order):
- `tasks/sonnet/LEDGER.md` row "07_grew's 1 remaining dropped row" (2026-07-05) — the exact diagnosed failure: pdfplumber interleaves "Sqm. 500" with adjacent remark-column text ("complies (density will be 180-220 kg/m3)")
- `src/ingest/pdf_extractor.py` + `src/ingest/table_extractor.py` — current extraction (which pdfplumber APIs are used where)
- `src/pipeline.py` — how extracted tables become rows
- P1_04 report — observations it logged about non-sacred PDF quality (your wider test material)

Current state:
- 07_grew extracts 9/9 today ONLY because `0e1cd4e` fixed a section-header false positive; the underlying interleaving remains and WILL corrupt other multi-column docs in the train pool.
- pdfplumber offers `extract_tables()` with explicit strategies and word-level bboxes — currently underused in favor of text-line parsing.
- The literature fallback (LayoutLMv3) is heavy; decision here: exhaust pdfplumber's geometric capabilities first. LayoutLMv3 only if geometric extraction demonstrably fails, and then only as a proposal in your report — NOT an implementation.

## 3. DELIVERABLES
- [ ] `src/ingest/column_detector.py` — `detect_columns(page) -> list[ColumnBand]`: vertical band detection from word x-coordinates (clustering word left-edges + ruling lines when present); works on bordered AND borderless tables
- [ ] `src/ingest/pdf_extractor.py` — row assembly path: when a BOQ-range page has detected columns, build rows cell-by-cell (band × line-y clustering); text-line fallback ONLY when detection confidence is low (and flag `column_fallback:true`)
- [ ] `tests/unit/test_column_detector.py` — ≥8 tests using small synthetic-geometry fixtures (constructed word lists with bboxes — no PDF files needed) covering: 2/3/4-band layouts, merged header cells, wrapped text within a cell, borderless
- [ ] `tests/integration/test_multicolumn_pdfs.py` — 07_grew end-to-end 9/9 WITHOUT the exact-match header workaround being load-bearing (prove: the qty 500 row assembles from its own cells, remark text ends in a remarks field or is dropped from the description)
- [ ] `results/column_eval/COLUMN_EVAL.md` — before/after row-quality table for every TRAIN/DEV PDF with detected multi-column pages: rows count, descriptions clean (no remark bleed — sample 3 rows/doc verbatim), duration

## 4. STEPS
1. Read context; dump 07_grew's page words with bboxes (`page.extract_words()`) to see the real geometry before designing.
2. Implement band detection (start with x-edge histogram clustering; add ruling-line evidence via `page.lines`/`page.rects` when present). Confidence = band separation clarity + line support.
3. Rewire the extractor's BOQ-page path; keep the old path as the low-confidence fallback with its flag.
4. Unit fixtures + tests; integration; corpus-wide before/after eval on TRAIN/DEV PDFs; sacred-10 fidelity check.
5. Commit: detector / extractor rewire / eval artifacts. Report includes verbatim before/after of the 07_grew row and 2 train-pool examples, plus (if applicable) the LayoutLMv3 proposal with the specific docs geometric methods couldn't handle.

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 -m pytest tests/unit/test_column_detector.py tests/integration/test_multicolumn_pdfs.py -v   # EXPECT: 10+ passed
python3 scripts/audit_fidelity_per_doc.py --all      # EXPECT: sacred-10 all PASS, 07_grew 9/9
python3 scripts/run_corpus.py --split train --type boq_bearing   # EXPECT: all ok, no new crashes
python3 -m pytest tests/unit tests/integration -q && make lint && make typecheck
```

## 6. ACCEPTANCE CRITERIA
- [ ] 07_grew's qty-500 row assembles correctly from cell geometry (shown verbatim in report)
- [ ] Zero corpus rows lost vs P3_01-accepted baseline; description cleanliness improved on ≥2 named train docs (before/after text in report)
- [ ] Detector unit-covered ≥85%; every fallback occurrence carries the flag
- [ ] No heavy deps added (no layout models, no cv2 unless already present)
- [ ] Honest failure list: any multi-column page the detector still mangles, named, with geometry notes

## 7. CONSTRAINTS
- Rule 8 (TRAIN/DEV development only), frozen files untouched
- Do not weaken or bypass the `_is_section_header` exact-match fix (`0e1cd4e`) — it stays as defense-in-depth
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P3_01 (shares pipeline.py + its accepted baseline)
- **Blocks:** P3_04
- **Parallel-safe with:** P3_03 (XLSX path — different files), P2_03/P2_04
- **Shared files:** `src/ingest/pdf_extractor.py`, `src/pipeline.py`

## 9. GOTCHAS
- pdfplumber `extract_words()` y-coordinates: `top` grows downward; cluster rows on `top` with tolerance ~3pt, but WRAPPED cell text spans multiple line-y's — assemble a cell first (band + row envelope), THEN join its words, or wrapped descriptions shred into phantom rows (06_avante's item-75 class).
- Numeric columns right-align: their x-left varies, x-RIGHT is stable — cluster numeric bands on right edges.
- Some tenders draw no ruling lines at all (Word-exported PDFs) — the histogram path must carry those alone; that's what the borderless fixtures test.
- A remarks column containing qty-like text ("180-220 kg/m3") is the trap that started this — band assignment must be positional ONLY, never content-based rescue ("looks like a qty, move it left") — content-based rescue is how over-capture bugs are born.
