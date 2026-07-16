# TASK: P8T4 — PDF Extraction Quality (the real weak link) — Agent-Extract

**Phase:** 8 | **Priority:** P0 | **Effort:** 1–2 days

## 1. GOAL
Materially improve PDF→BOQ extraction (section detection, table extraction, and material↔quantity↔unit pairing), measured honestly against the P8T1 entity-level/row metric — no metric gaming.

## 2. CONTEXT
PDF enquiries extract partially (e.g. 01 GSECL = 5 weak rows; sample "For all engaged manpower" is junk). The pipeline flattens PDF text and runs NER, then proximity-pairs entities; pairing and table structure are lost. Section detector exists at `src/preproc/sections.py`.

Read first: `src/pipeline.py` (PDF path), `src/ingest/` (pdf extractor, OCR, table detection), `src/preproc/sections.py`, `src/domain/boq_assembler.py`, `results/PRODUCT_EVAL.md` (P8T1 baseline).

## 3. DELIVERABLES
- [ ] Improved BOQ-section detection so extraction focuses on the BOQ table, not front matter (GSECL front-matter junk must stop).
- [ ] Table-aware extraction for PDF BOQ tables (e.g. `pdfplumber`/`camelot`) feeding row structure into assembly, with graceful fallback to text+NER when no table is found.
- [ ] Improved material↔quantity↔unit pairing in the PDF assembly path (column/line association, not just token proximity).
- [ ] Before/after numbers on the PDF enquiries using `scripts/eval_product.py` (P8T1), committed to `results/`.
- [ ] Tests: `tests/unit/test_pdf_tables.py`, `tests/integration/test_pdf_extraction_e2e.py` on real PDF enquiries.

## 4. STEPS
1. `systematic-debugging`: run eval on PDF enquiries, categorize failures (wrong section, no table, bad pairing, OCR).
2. `brainstorming` the approach per failure class; pick table extraction lib; design fallback.
3. TDD each improvement; keep the XLSX path untouched.
4. Re-run P8T1 eval; report honest before/after per enquiry.

## 5. VERIFICATION
```bash
python3 scripts/eval_product.py --all 2>&1 | tee /tmp/after.txt
# Compare to the committed baseline; expect PDF entity-level F1 to rise, honestly
diff <(grep -A12 "entity-level" results/PRODUCT_EVAL.baseline.md) <(grep -A12 "entity-level" results/PRODUCT_EVAL.md)
python3 -m pytest tests/unit/test_pdf_tables.py tests/integration/test_pdf_extraction_e2e.py -v
EXPECT: tests pass; measurable, honest improvement; XLSX path unchanged
```

## 6. ACCEPTANCE CRITERIA
- [ ] PDF entity-level F1 improves vs the P8T1 baseline (report the delta; if it doesn't, say so and explain).
- [ ] GSECL no longer extracts front-matter as BOQ items.
- [ ] XLSX path unchanged; tests green; no hardcoded per-file outputs.

## 7. CONSTRAINTS
- Measure ONLY via P8T1's honest eval. Do NOT change matcher thresholds or build gold from the pipeline.
- Keep the XLSX row-preservation path intact.
- `src.` imports, type hints, Python 3.11–3.13.

## 8. DEPENDENCIES
- **Blocked by:** P8T1 (need the honest yardstick). **Benefits from:** P8T3 (clean gold). **Feeds:** P8T8.

## 9. GOTCHAS
- Some PDFs are scanned/CID — table libs may fail; fall back gracefully, never crash.
- 62-page docs: restrict to detected BOQ section for speed; full-text only as fallback.
- A big jump (e.g. to ~90%+) on PDF entity F1 is suspicious — verify it's not leakage from gold.
