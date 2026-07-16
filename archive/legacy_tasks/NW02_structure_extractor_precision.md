# NW-02 — Structure extractor precision + camelot decision (P0)

You are working on RFQ2BOQ at /Users/srujansai/Desktop/rfq2boq, branch `phase8-clean-slate`.

## 1. GOAL
Cut the structure extractor's false positives (1281 "sections" detected in one 29MB PDF) without losing the real BOQ headings, and settle the camelot-py question. This implements the SWA mentor's structure-first requirement properly.

## 2. CONTEXT (read first)
- `src/preproc/document_structure.py` — DocumentStructureExtractor (PyMuPDF fast scan + pdfplumber fallback)
- `tests/unit/test_document_structure.py` — 15 existing tests
- `src/pipeline.py` — how the page range feeds extraction (GeM check runs FIRST — keep that order)
- Known-good behavior to preserve: 01 GSECL → "SCHEDULE-B" page 61 top-ranked (confidence 0.60), range (60, 69); GeM 09/10 unaffected (16–40s)

## 3. STEPS
1. Reproduce the noise: run the extractor on the largest PDF in `data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/` and print section count + top 10 by confidence.
2. Tighten heading detection: require heading-like signals (font-size delta OR bold OR ALL-CAPS short line OR Schedule/Annexure/Appendix/Bill/BOQ keyword) instead of bare section-number regex; drop candidates inside table regions.
3. Keep the high-confidence keyword boost (Schedule/Annexure → 0.6) exactly as is.
4. Add 5+ unit tests for the false-positive cases you found.
5. camelot-py: eval logs show "camelot-py not installed, falling back to pdfplumber" on every PDF. Either (a) add it to pyproject + verify it improves at least one of 04/06/07 extractions, or (b) remove the dead camelot code path + log line. Pick based on a real A/B on those 3 PDFs and show the outputs.

## 4. VERIFICATION (run, paste real output)
```bash
python3 -m pytest tests/unit/test_document_structure.py -q
python3 - <<'PY'
from src.pipeline import Pipeline
import time
for f in ["01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf",
          "09_gem_bid_7439924/GeM-Bidding-9218026.pdf",
          "10_gem_bid_7552777/GeM-Bidding-9343469.pdf"]:
    t=time.time(); r=Pipeline().run(f"data/real_rfqs/swa_enquiries/{f}")
    print(f.split('/')[0], len(r.boq_items), f"{time.time()-t:.1f}s")
PY
make verify
```

## 5. ACCEPTANCE CRITERIA
- Section count on the 29MB PDF drops by ≥80% while 01 GSECL still finds page 61 and extracts ≥4 items.
- 09/10 GeM item counts and times unchanged (±10%).
- All 10 SWA files still process without crash (run the loop over all 10 and paste counts).
- `make verify` passes; no gold edits.

## 6. FORBIDDEN
Hard-coding page numbers or filenames. Editing gold. Breaking the GeM-first ordering in pipeline.py.
