# Corpus Filter Report — Honest Assessment

**Date:** 2026-06-09
**Scanned:** 68 real PDFs (>1KB) from `data/real_rfqs/additional_real/`

## Critical Finding

| Category | Count |
|---|---|
| **Insulation-domain** | **0** |
| HVAC/mechanical adjacent | 10 |
| Other construction (civil, electrical, road, bridge) | 58 |
| Empty placeholders (<1KB) | 100 |

**The `additional_real/` corpus contains ZERO insulation-domain tenders.**

## What We Actually Have

### HVAC Adjacent (10 files)
All 10 are **plumbing RFQs** that mention pumps, valves, pipes — mechanical adjacent but NOT insulation-specific:
- `rfq_plumbing_RFQ1499_048.pdf` through `rfq_plumbing_RFQ7857_013.pdf`
- Keywords found: "pump", "valve", "pipe" — no insulation materials

### Other Construction (58 files)
- **Building RFQs** (15): cement, steel, bricks, tiles, plaster
- **Road RFQs** (6): macadam, bitumen, concrete
- **Bridge RFQs** (11): pre-stressed steel, concrete decks
- **Electrical RFQs** (9): cables, switches, DB boxes, fans
- **Government docs** (17): CPWD guidelines, EPI volumes, NHAI, IREPS, Delhi PWD, Odisha PWD

### Empty Placeholders (100 files)
Exactly 302-byte empty PDFs with no content. Likely download failures or placeholders.

## Honest Conclusion

**Phase 1 insulation-domain filtering FAILS.** There are no insulation tenders in the corpus.

The original plan assumed 168 files with insulation content. Reality:
- 100 files are empty
- 58 files are general construction (not insulation)
- 10 files are plumbing/HVAC (not insulation)
- **0 files are insulation-domain**

## Adjusted Strategy

Since insulation data does not exist in `additional_real/`, we have two options:

### Option A: Source Insulation Data (Recommended)
- Obtain real insulation RFQs from SWA's actual business
- Thermal insulation, acoustic insulation, HVAC duct insulation, pipe insulation tenders
- Target: 80-100 insulation-domain documents for annotation

### Option B: Train on General Construction
- Use the 58 real construction RFQs + existing 20 gold annotations
- Train a general construction NER model (not insulation-specific)
- Accept lower domain precision on insulation materials

**Decision needed from owner:** Which path?
