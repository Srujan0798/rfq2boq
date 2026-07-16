# TASK: A8 Real RFQ PDF Collection — FINAL BLOCKER

**Wave:** 2 | **Tier:** A | **Priority:** **P0** (last open blocker)

## 1. GOAL

Collect 50 real construction RFQ/tender PDFs for model evaluation. This is the single most impactful improvement for real-world F1.

## 2. CONTEXT

Files to read first:
- `data/real_rfqs/raw/` — existing directory with 4 real PDFs already present:
  - `cpwd_Guidelines_for_Hassle_Free_Bid_Submission_1778959268.pdf`
  - `delhi_pwd_Tender_1778958751.pdf`
  - `ireps_2724bb1eff78.pdf`
  - `ireps_bc341034058b.pdf`
- `data/real_rfqs/extracted/` — 55 extracted JSON files from these PDFs
- `scripts/annotate_helper.py` — annotation tool
- `docs/wave_status.md` — current metrics showing real-world F1 at 67.05% (target 75%)

Current state: 4 real PDFs exist in `data/real_rfqs/raw/`. The task is to annotate them and collect more.

## 3. DELIVERABLES

Exact paths:
1. `data/real_rfqs/raw/` — 50 PDFs minimum
2. `data/real_rfqs/annotated/` — annotations for at least 20 PDFs
3. `data/real_rfqs/metadata.csv` — CSV with: filename, source, date, page_count, has_tables, language

## 4. STEPS

1. **Collect PDFs from public sources:**
   - CPWD (Central Public Works Department) tender documents
   - MES (Military Engineering Services) tenders
   - State PWD websites (e.g., Gujarat, Maharashtra, Karnataka)
   - GeM (Government e-Marketplace) RFQs
   - NPQL (National Portal for Tenders) — tender documents
   - CPWD tender site: https://cpwd.gov.in/tenders
   - Search for "RFQ tender PDF" in public domain

2. **Organize by source:**
   ```
   data/real_rfqs/raw/
   ├── cpwd/          # CPWD tenders
   ├── mes/           # Military Engineering Services
   ├── state_pwd/     # State PWD documents
   └── gem/           # GeM RFQs
   ```

3. **Create `data/real_rfqs/metadata.csv`:**
   ```csv
   filename,source,date,pages,has_tables,language,annotations
   rfq_001.pdf,cpwd,2024-01-15,5,true,en,rfq_001.json
   ```

4. **Annotate at least 20 PDFs:**
   - Use `scripts/annotate_helper.py` to semi-automate
   - Focus on PDFs with: clear material lists, quantities, units
   - Annotate all 8 entity types: MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE
   - Annotate relations: HAS_QUANTITY, HAS_UNIT, AT_LOCATION, OF_GRADE, COMPLIES_WITH, HAS_DIMENSION

5. **Split into train/val/test:**
   - 35 for training, 10 for validation, 5 for testing
   - Store in `data/real_rfqs/split/`

## 5. VERIFICATION

```bash
# Count PDFs
ls data/real_rfqs/raw/**/*.pdf 2>/dev/null | wc -l  # should be >= 50

# Count annotated
ls data/real_rfqs/annotated/*.json 2>/dev/null | wc -l  # should be >= 20

# Check metadata
python3 -c "import csv; rows = list(csv.DictReader(open('data/real_rfqs/metadata.csv'))); print(f'{len(rows)} PDFs, {sum(1 for r in rows if r.get(\"annotations\"))} annotated')"

# Verify annotations format
python3 -c "import json; ann = json.load(open('data/real_rfqs/annotated/rfq_001.json')); print(f'{len(ann[\"entities\"])} entities, {len(ann[\"relations\"])} relations')"
```

## 6. ACCEPTANCE CRITERIA

- [ ] ≥50 real RFQ PDFs in `data/real_rfqs/raw/`
- [ ] ≥20 PDFs with annotations in `data/real_rfqs/annotated/`
- [ ] `metadata.csv` exists with all required columns
- [ ] Annotations use BIOES tagging for entities
- [ ] Annotations include relations for at least 10 PDFs
- [ ] Split: 35 train, 10 val, 5 test
- [ ] All PDFs are publicly available government tender documents (no copyright issues)
- [ ] Mix of: building, road, water supply, electrical tenders

## 7. CONSTRAINTS

- PDFs must be publicly available (government tender documents)
- NO copyright infringement — only use public domain documents
- Annotations must follow BIOES tagging scheme from `config/constants.py`
- Entity types must match `EntityType` enum exactly
- Hindi PDFs welcome (for multilingual testing)

## 8. DEPENDENCIES

- Blocks: All downstream evaluation — real-world F1 can only improve with real data
- Blocked by: None (this is the final open item)

## 9. GOTCHAS

- CPWD and state PWD sites often require registration — use anonymous access where possible
- PDFs from different states may have different formats — document the format variations
- Some PDFs may be scanned images (OCR needed) — note in metadata
- Tabular data in PDFs is harder to extract — prioritize PDFs with clear lists
- Budget: the more diverse the source, the better the model generalizes
