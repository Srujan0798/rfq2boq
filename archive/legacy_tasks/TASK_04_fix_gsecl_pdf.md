# TASK 4 — Fix 01 GSECL PDF Extraction (P1)

You are working on the RFQ2BOQ project at /Users/srujansai/Desktop/rfq2boq.

## Problem

01 GSECL is a 62-page PDF. The BOQ is on page 61 (Schedule-B). The pipeline only extracts 2 items. The rowgold confirms there should be at least 8 items.

Run this:
```bash
cd /Users/srujansai/Desktop/rfq2boq
python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf'); print(f'Items: {len(r.boq_items)}'); [print(f'  {row.material[:60]}') for row in r.boq_items]"
```

Current: 2 items
Expected: 8+ items (from rowgold at `data/real_rfqs/gold/rows/01_gsecl_wanakbori_tmd8.rowgold.json`)

## Root Cause

The SmartSectionClassifier in `src/preproc/sections.py` may not find the BOQ section on page 61. The PDF has 62 pages of front matter (terms, conditions, specifications) before the actual BOQ table on page 61.

## Files to Read and Modify

- `src/preproc/sections.py` — SmartSectionClassifier, find_boq_pages()
- `src/ingest/pdf_extractor.py` — max_pages, page extraction
- `src/ingest/table_extractor.py` — table detection
- `src/pipeline.py` — how BOQ pages are filtered

## Reproduction

```bash
cd /Users/srujansai/Desktop/rfq2boq
python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf'); print(f'Items: {len(r.boq_items)}')"
```

## Acceptance Criteria

1. Extract at least 6 items from 01 GSECL (rowgold has 8)
2. Items have actual materials, quantities, and units
3. Run `python3 scripts/eval_honest.py --enquiry 01_gsecl` and report F1
4. Run `make verify` and confirm it passes
5. Do NOT increase extraction time by more than 2x (currently ~20s)

## Hints

- The classifier looks for keywords like "BOQ", "Bill of Quantities", "Schedule-B", "Schedule of Rates"
- Check if page 61 text contains these markers but the classifier misses them
- Consider increasing max_pages or removing the page limit for section classification
- The table on page 61 may have unusual formatting that table_extractor misses

## DO NOT

- Modify any gold files
- Hard-code page numbers specific to this PDF
- Extract non-BOQ pages (terms, conditions, front matter)

## Return

What you changed + item count before/after + eval output + verify output.
