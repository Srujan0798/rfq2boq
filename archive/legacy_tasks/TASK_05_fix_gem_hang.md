# TASK 5 — Fix 09 GeM PDF Hang (P0)

You are working on the RFQ2BOQ project at /Users/srujansai/Desktop/rfq2boq.

## Problem

09 GeM PDF takes 3.6+ minutes to process. This makes it unusable for live demo. It should complete in under 60 seconds.

Run this:
```bash
cd /Users/srujansai/Desktop/rfq2boq
time python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf'); print(f'Items: {len(r.boq_items)}')"
```

Current: ~200+ seconds
Target: < 60 seconds

## Known Issues

1. The pipeline has a `ThreadPoolExecutor` in table extraction that was already removed in a prior fix (B3)
2. NER model loading takes ~30s (108M params on MPS) — this is expected and OK
3. Table extraction on GeM-style split-quantity PDFs may be slow
4. The pipeline tries to extract tables from ALL pages, not just BOQ pages

## Files to Read and Modify

- `src/ingest/table_extractor.py` — Table extraction timing
- `src/ingest/pdf_extractor.py` — Page extraction, split-quantity handling
- `src/pipeline.py` — Timeout handling, page filtering
- `src/preproc/sections.py` — Section classifier to limit pages

## Reproduction

```bash
cd /Users/srujansai/Desktop/rfq2boq
time python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf'); print(f'Items: {len(r.boq_items)}')"
```

## Acceptance Criteria

1. 09 GeM completes in < 60 seconds
2. Still extracts at least 15 items (currently ~22, don't lose them)
3. 10 GeM also completes in < 60 seconds (same PDF style)
4. Other PDFs are not slowed down
5. `make verify` passes

## Hints

- Add per-PDF timeout with graceful fallback
- Limit table extraction to BOQ pages only (use section classifier)
- GeM PDFs have split-quantity columns — the special handler may be slow
- Consider adding `max_pages=20` or similar for table extraction while keeping text extraction at 100 pages

## DO NOT

- Remove the split-quantity handler entirely (it works, just slow)
- Modify gold files
- Break other PDF extractions

## Return

What you changed + timing before/after + item counts + verify output.
