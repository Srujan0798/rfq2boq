# TASK: P1T4 — CPWD DSR Rate Library (Real 500+ Items) — Agent-1

**Phase:** 1 | **Effort:** 2 days | **Priority:** P0 (blocks Phase 3 Excel polish)

## 1. GOAL
Replace the current 70-item rate stubs (`data/rates/rates_cpwd.json` etc.) with the actual CPWD DSR 2023 rate library — ≥500 line items, parsed from the official PDF — so the BOQ Excel output uses authoritative government rates.

## 2. CONTEXT
Read first:
- `data/rates/rates_cpwd.json` (14 items), `rates_dsr.json` (20), `rates_msr.json` (22), `rates_average_india.json` (14) — current stubs, total 70 items
- `src/domain/cost_estimator.py` — current cost engine, lookup logic
- `src/ingest/pdf_extractor.py` — `PDFExtractor` class (reuse for parsing DSR PDFs)
- `src/ingest/table_extractor.py` — Camelot table extraction (already integrated)
- [docs/HYBRID_PLAN.md](../../../docs/HYBRID_PLAN.md)
- [docs/SCOPE_GUARD.md](../../../docs/SCOPE_GUARD.md) — drift patterns to refuse
- [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)

CPWD DSR (Delhi Schedule of Rates) is the government-mandated rate book used across Indian construction tenders. Public-domain under RTI/NDSAP.

Sources (try in order):

- Official: https://cpwd.gov.in/Documents/cpwd_publication.aspx (SSL/access issues possible)
- Mirror: https://helptheengineer.com/cpwd-publication/
- Mirror: https://civilenggascent.com/cpwd-sor-schedule-of-rates-2023-pdf-download/
- Mirror (search): scribd.com → "DSR Vol 1 Civil 2023"
- Aggregator (for cross-check): https://nsrcivil.in/cpwd-dsr-2023-corrections/

Current state: cost estimator works but uses 70 stub items. Real BOQ output has "rate estimated" notes everywhere because so few items match.

## 3. DELIVERABLES
- [ ] `data/rates/dsr_2023/raw_pdfs/DSR_Vol_1_Civil_2023.pdf` (gitignored, manual download OK)
- [ ] `data/rates/dsr_2023/raw_pdfs/DSR_Vol_2_2023.pdf` (gitignored, optional Vol 2)
- [ ] `scripts/parse_dsr_pdf.py` — pdfplumber/Camelot extractor for line items
- [ ] `scripts/download_dsr.py` — automation with manual-fallback instructions
- [ ] `data/rates/cpwd_dsr_2023.json` — parsed ≥500 items, committed (small, ~200 KB)
- [ ] `data/rates/cpwd_dsr_2023.csv` — same data as CSV
- [ ] `src/domain/cost_estimator.py` — update to load DSR JSON as primary, fall back to existing stubs
- [ ] `tests/unit/test_dsr_rates.py` — ≥6 tests
- [ ] `docs/rates_dsr.md` — sources, license attribution, refresh process

## 4. STEPS
1. Read context, run existing tests (`make test`) to confirm baseline 353 passing.
2. **Acquire DSR PDFs:** try `python3 scripts/download_dsr.py`. If automation fails (likely — government sites block scrapers), document manual steps:
   - Open `https://helptheengineer.com/cpwd-publication/` in browser
   - Download DSR 2023 Vol 1 (Civil) — typically ~80 MB PDF
   - Save to `data/rates/dsr_2023/raw_pdfs/DSR_Vol_1_Civil_2023.pdf`
   - (Vol 2 is electrical/specialty — optional)
3. **Parse the PDF** with `python3 scripts/parse_dsr_pdf.py`:
   - Use pdfplumber to extract tables page-by-page
   - DSR has consistent table layout: Item Code | Description | Unit | Rate (₹)
   - Walk each chapter (Earthwork, Concrete, Steel, Masonry, Plaster, Flooring, Painting, Plumbing, Electrical, etc.)
   - Output schema:
     ```json
     {
       "version": "DSR 2023",
       "source": "CPWD Delhi Schedule of Rates 2023",
       "region": "delhi",
       "currency": "INR",
       "items": [
         {
           "code": "2.1.1",
           "description": "Earthwork in excavation by mechanical means…",
           "chapter": "2 — Earthwork",
           "unit": "m^3",
           "rate_inr": 245.50,
           "year": 2023
         },
         ... 500+ items ...
       ]
     }
     ```
4. **Update `src/domain/cost_estimator.py`:**
   - On init, load `data/rates/cpwd_dsr_2023.json` if present
   - In `lookup_rate(material, grade, unit, region)`:
     1. Exact match on (material substring in description, unit, region) → return DSR item
     2. Fuzzy match (Levenshtein < 3 on description tokens) → return DSR item with `"match_type": "fuzzy"`
     3. Fall back to existing `rates_cpwd.json` stub
     4. Return None if nothing matches
   - Always include `"source"` in the returned dict so user knows ("DSR 2023" vs "stub" vs None)
5. **CSV exporter:** write a small companion `scripts/dsr_to_csv.py` that converts the JSON.
6. Tests in `tests/unit/test_dsr_rates.py`:
   - Loads JSON, ≥500 items
   - At least 10 common materials match: cement, steel, brick, mortar, concrete, plaster, tile, paint, wood, glass
   - Fuzzy fallback works on misspellings
   - Source attribution always present
   - Estimator returns None for nonsense input gracefully
7. `docs/rates_dsr.md`:
   - Where DSR comes from (NDSAP/RTI public-domain)
   - Refresh schedule (CPWD releases new DSR roughly annually)
   - Correction slips: CPWD publishes errata after release; document this
   - State SOR alternatives (Maharashtra, Karnataka, Tamil Nadu)
8. Run verification.

## 5. VERIFICATION
```bash
# PDFs in place
$ ls data/rates/dsr_2023/raw_pdfs/*.pdf | wc -l
EXPECT: ≥1

# Parsed JSON has ≥500 items
$ python3 -c "import json; d=json.load(open('data/rates/cpwd_dsr_2023.json')); print(len(d['items']))"
EXPECT: ≥500

# Common materials covered
$ python3 -c "
import json
d = json.load(open('data/rates/cpwd_dsr_2023.json'))
descs = ' '.join(i['description'].lower() for i in d['items'])
for mat in ['cement', 'steel', 'brick', 'mortar', 'concrete', 'plaster', 'tile', 'paint', 'wood', 'glass']:
    assert mat in descs, f'{mat} missing'
print('all 10 materials found')
"
EXPECT: prints "all 10 materials found"

# Cost estimator uses DSR
$ python3 -c "
from src.domain.cost_estimator import CostEstimator
c = CostEstimator()
r = c.lookup_rate('cement', 'OPC 43', 'kg', 'delhi')
print(r)
assert r is None or ('source' in r and 'rate' in r)
"
EXPECT: dict with source + rate, OR None — no exception

# Tests
$ python3 -m pytest tests/unit/test_dsr_rates.py -v
EXPECT: ≥6 passed

# Coverage
$ python3 -m pytest tests/unit/test_dsr_rates.py --cov=src.domain.cost_estimator --cov-report=term-missing 2>&1 | grep "TOTAL"
EXPECT: ≥80% on cost_estimator

# Lint
$ python3 -m ruff check scripts/parse_dsr_pdf.py scripts/download_dsr.py src/domain/cost_estimator.py
EXPECT: clean

# No regression
$ python3 -m pytest tests/unit tests/integration tests/golden tests/fuzz --tb=no
EXPECT: 353+ passed
```

## 6. ACCEPTANCE CRITERIA
- [ ] DSR PDF acquired (manual download is acceptable)
- [ ] ≥500 line items parsed
- [ ] CSV export works
- [ ] Cost estimator loads DSR and uses it as primary source
- [ ] Stubs preserved as fallback
- [ ] Coverage ≥ 80% on cost_estimator
- [ ] `docs/rates_dsr.md` documents legal posture + refresh process

## 7. CONSTRAINTS
- All imports `src.` prefix
- DO NOT commit the DSR PDFs themselves to git (too large; `.gitignore` already covers `data/rates/dsr_2023/raw_pdfs/`)
- DO commit the parsed JSON + CSV (small, valuable)
- License attribution required (NDSAP/RTI public domain; cite CPWD)
- DO NOT remove existing stub files — they serve as fallback
- DO NOT add features outside §3 deliverables (no API endpoint, no UI changes)

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** P3T3 (CPWD Excel polish needs real rates)
- **Parallel-safe with:** P1T2, P1T3, P1T5

## 9. GOTCHAS
- DSR PDFs may be 50–200 MB; not git-friendly (already gitignored)
- pdfplumber struggles with merged cells; some chapters may need Camelot fallback
- Rate columns sometimes split across multiple sub-units (per m, per m², per piece) — keep them distinct
- DSR 2023 has correction slips published after release; document this in `docs/rates_dsr.md` but don't bake into JSON yet
- Official CPWD URL often has SSL issues — mirrors are the realistic source
- Indian number format in PDF: ₹1,23,456 (lakhs separator) — parse correctly to 123456 not 12345
- Some items have material + labour breakdown; capture both if present, total rate is enough for our use
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md) § ML/Path

## End-of-task REPORT format

```text
## REPORT: P1T4 CPWD DSR Rate Library

Deliverables:
- data/rates/dsr_2023/raw_pdfs/<file>.pdf  (created)
- scripts/parse_dsr_pdf.py                  (created)
- scripts/download_dsr.py                   (created)
- data/rates/cpwd_dsr_2023.json             (created, N items)
- data/rates/cpwd_dsr_2023.csv              (created)
- src/domain/cost_estimator.py              (modified — DSR primary)
- tests/unit/test_dsr_rates.py              (created, M tests)
- docs/rates_dsr.md                         (created)

Verification:
- pytest tests/unit/test_dsr_rates.py: M passed, 0 failed
- DSR JSON items: N (≥500 target)
- Common materials found: 10/10
- Coverage on cost_estimator: XX%
- Full test suite: 353+ passed
- ruff: clean

Blockers: [none / list]
Deviations: [none / list]
Outside-spec edits: [none / list]
```
