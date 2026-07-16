# TASK 3 — Fix Dimension False Positives (P2)

You are working on the RFQ2BOQ project at /Users/srujansai/Desktop/rfq2boq.

## Problem

The pipeline extracts dimension text and section headers as materials. These are NOT materials:

**03 Zydus Matoda (XLSX):**
- "15MM" — this is a column header/dimension, not a material
- "20MM" — same

**06 Avante (PDF):**
- "13 mm thick insulation for supply air ducts in return air path." — dimension+location, not a material
- "19 mm thick insulation for return air ducts." — same
- (11 false positives total)

**07 Grew Solar (PDF):**
- "ACOUSTIC LINING Supply,Installation..." — section header, not a material
- "75 mm thick Insulation on 1200NB to 1000NB" — dimension header
- (5 false positives total)

## Files to Read and Modify

- `src/pipeline_xlsx.py` — XLSX extraction (around line 400+, `is_header_row` logic)
- `src/domain/boq_assembler.py` — Post-process filtering
- `src/ingest/table_extractor.py` — PDF table filtering

## Reproduction

```bash
cd /Users/srujansai/Desktop/rfq2boq

# 03 Zydus Matoda
python3 -c "from src.pipeline_xlsx import XLSXRowPipeline; xp=XLSXRowPipeline(); items=xp.run('data/real_rfqs/swa_enquiries/03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx'); [print(row.material) for row in items if 'MM' in row.material or 'mm' in row.material]"

# 06 Avante
python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Boq_132.pdf'); [print(row.material[:60]) for row in r.boq_items]"

# 07 Grew
python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf'); [print(row.material[:60]) for row in r.boq_items]"
```

## Acceptance Criteria

1. 03 Zydus Matoda: No "15MM", "20MM", or pure-dimension rows in output
2. 06 Avante: False positives reduced from 11 to < 6
3. 07 Grew Solar: False positives reduced from 5 to < 3
4. True positives must NOT decrease (recall stays same or improves)
5. Run `python3 scripts/eval_honest.py` and show the improvement
6. `make verify` passes

## Hints

- Reject rows where material is purely a dimension (matches patterns like "15MM", "20 mm thick", "13 mm thick" with no actual material noun)
- Reject rows that are section headers (all-caps, no quantity, or quantity=0 with no rate_only flag)
- In XLSX pipeline, strengthen `is_header_row()` to catch dimension-only cells

## DO NOT

- Modify any gold files
- Reduce recall (don't remove real materials)

## Return

What you changed + before/after false positive counts + verify output.
