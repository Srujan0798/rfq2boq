# NW-07 — Ingest SWA's real GeM product catalog as authoritative R2 reference (P0)

You are working on RFQ2BOQ at /Users/srujansai/Desktop/rfq2boq, branch `phase8-clean-slate`.

## 1. GOAL
Replace/extend the hand-built GeM gazetteer with SWA's actual submitted GeM product list (19 products, `data/real_rfqs/swa_gem_catalog.xlsx`). This is the R2 requirement from the SWA 2026-06-11 meeting — GeM catalog = authoritative NER reference.

## 2. CONTEXT (read first)
- `data/real_rfqs/swa_gem_catalog.xlsx` — SWA's real published GeM product list (19 rows, columns: PRODUCT NAME PUBLISHED, PRODUCT ID). Data starts at row 6 (rows 1-5 are blank).
- `src/nlp/patterns/gem_catalog.py` — current hand-built gazetteer (60+ products, 132 material keys)
- `docs/SWA_REQUIREMENTS_2026-06-11.md` R2 section — the requirement
- `config/constants.py` — MATERIAL entity definition

## 3. STEPS
1. Parse `data/real_rfqs/swa_gem_catalog.xlsx` — extract all PRODUCT NAME PUBLISHED entries (deduplicated). The 19 products are:
   - THERMO ACOUSTIC INSULATION, ACCOUSTIC INSOUND BARRIER, Acoustical insulation,
     Insound Acoustical insulation, FOAM TAPE, FOAM GC TAPE, Foam Tape, Aluminum Tape,
     Ceramic Fibre Blanket Insulation, Thermal Insulation Board, Aluminum Foil Scrim Kraft Tape,
     Aluminum Foil Insulation Tape, Preformed Fibrous Pipe Sections For Thermal Insulation-IS: 9842

2. Add a `SWA_GEM_PUBLISHED` dict to `src/nlp/patterns/gem_catalog.py` with:
   - Canonical name (title-cased, normalized)
   - All spelling variants present in the XLSX (case variants, abbreviations)
   - GeM product ID(s) as metadata (store as comments or a parallel dict)

3. Wire `SWA_GEM_PUBLISHED` into the existing `GEM_CATALOG` / `MATERIAL_PATTERNS` so these product names get recognized as MATERIAL entities with HIGH confidence (above regular patterns).

4. Add a validation function `validate_gem_extraction(material_text: str) -> bool` that returns True if the extracted material matches any SWA published product (fuzzy, threshold 0.85). Use this in `src/pipeline.py` for GeM tenders (enquiries 09 and 10) to flag non-catalog materials.

5. Add a provenance note at top of gem_catalog.py: "SWA_GEM_PUBLISHED loaded from data/real_rfqs/swa_gem_catalog.xlsx (SWA's actual submitted GeM portal products, 2026-06-18, authoritative for R2)".

6. Write tests: every product name in SWA_GEM_PUBLISHED must be recognized as MATERIAL by the NLP pipeline.

## 4. VERIFICATION (run, paste real output)
```bash
python3 -c "
from src.nlp.patterns.gem_catalog import SWA_GEM_PUBLISHED, validate_gem_extraction
print('Products:', len(SWA_GEM_PUBLISHED))
tests = ['THERMO ACOUSTIC INSULATION', 'Aluminum Tape', 'Ceramic Fibre Blanket Insulation',
         'Preformed Fibrous Pipe Sections For Thermal Insulation-IS: 9842']
for t in tests:
    print(t, '->', validate_gem_extraction(t))
"
python3 scripts/eval_honest_rows.py   # 09 and 10 must stay at 100%
make verify
```

## 5. ACCEPTANCE CRITERIA
- `len(SWA_GEM_PUBLISHED) >= 13` (unique product names after dedup)
- All 4 test cases above return True from validate_gem_extraction
- Enquiries 09 and 10 still F1=100% after the change
- `make verify` passes; zero gold edits

## 6. FORBIDDEN
Modifying gold files. Hardcoding enquiry numbers. Removing existing GEM_CATALOG entries.
