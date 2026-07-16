# TASK 1 — Fix 04 Adani PDF Extraction (P0)

You are working on the RFQ2BOQ project at /Users/srujansai/Desktop/rfq2boq.

## Problem

04 Adani PDF extracts dimension headers instead of actual material names.

Run this command:
```bash
cd /Users/srujansai/Desktop/rfq2boq
python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf'); [print(f'{row.material} | {row.quantity} {row.unit}') for row in r.boq_items]"
```

Current output:
```
19mm thick - SA/DH-AHU/TFA duct | 0.0 no.
32mm thick with 7 mill glass cloth... | 0.0 no.
```

These are DIMENSION HEADERS, not materials. The actual BOQ has materials like "MS chilled water pipe insulation nitrile rubber" (13 rows).

Expected output:
```
MS chilled water pipe insulation nitrile rubber | 100.0 Rmt
MS chilled water pipe insulation nitrile rubber | 200.0 Rmt
... (13 total rows)
```

## Files to Read and Modify

- `src/ingest/table_extractor.py` — How tables are parsed from PDF
- `src/ingest/pdf_extractor.py` — How pages are identified and extracted
- `src/pipeline.py` — How rows are mapped to BoqRow

## Reproduction

```bash
cd /Users/srujansai/Desktop/rfq2boq
python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf'); [print(f'{row.material} | {row.quantity} {row.unit}') for row in r.boq_items]"
```

## Acceptance Criteria

1. At least 10 distinct material rows extracted
2. Materials are actual insulation materials, not dimension/location text
3. Each row has quantity > 0 and a valid unit
4. Run `python3 scripts/eval_honest.py --enquiry 04_adani` and report F1
5. Run `make verify` and confirm it passes

## DO NOT

- Modify any gold files in `data/real_rfqs/gold/`
- Claim 100% without showing the actual eval output
- Modify any test files unless necessary

## Return

What you changed + the eval output + verify output.
