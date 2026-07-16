# TASK: P1T5 — Real RFQ Collection — Owner + Agent-1

**Phase:** 1 | **Effort:** 2 days | **Priority:** P0 (closes the long-standing blocker)

## 1. GOAL
Populate `data/real_rfqs/raw/` with ≥50 real Indian construction RFQ PDFs from public government tender portals, plus gold-annotate 20 of them.

## 2. CONTEXT

**Current state:**
- 117 PDFs total: 4 real (CPWD/IREPS/delhi_pwd) + 113 synthetic
- `manifest.csv` built with SHA256, pages, file_size_kb (located at `data/real_rfqs/annotations/manifest.csv`)
- 20 gold annotations: **18 on synthetic PDFs, 2 on real PDFs**. All 20 are complete with entities/relations filled.
- Real F1: 0.506 on 31 documents (from `results/real_world_metrics_v2.json`)
- `data/real_rfqs/annotations/` is git-tracked; `data/real_rfqs/raw/` is gitignored

**Existing real PDFs (4 confirmed):**
- `ireps_2724bb1eff78.pdf` — 12 pages, 30228 chars
- `ireps_bc341034058b.pdf` — 17 pages, 20214 chars
- `cpwd_Guidelines_for_Hassle_Free_Bid_Submission_1778959268.pdf` — 3 pages, 6365 chars
- `delhi_pwd_Tender_1778958751.pdf` — real tender

**Synthetic PDFs (113):** building(26), road(14), bridge(23), electrical(24), plumbing(23), unknown(3)

**Files to read:**
- `data/real_rfqs/annotations/manifest.csv` — built manifest with SHA256 per file
- `data/real_rfqs/annotations/gold_annotations.json` — 20 gold annotations (18 synthetic, 2 real)
- `data/real_rfqs/annotated/*.json` — 7 extracted JSON files
- `docs/HYBRID_PLAN.md`, `docs/WAVE_GOTCHAS.md`

**Public sources (Indian government tender PDFs are public domain under RTI/NDSAP):**
- etenders.gov.in, cpwd.gov.in/tenders, nhai.gov.in, ireps.gov.in, mes.gov.in
- State PWDs: Tamil Nadu, Karnataka, Maharashtra, Gujarat
- GeM portal: gem.gov.in

## 3. DELIVERABLES

- [x] `data/real_rfqs/raw/` — 117 PDFs exist (4 real + 113 synthetic), organized by source
- [x] `data/real_rfqs/annotations/manifest.csv` — SHA256, pages, file_size_kb per file (117 entries)
- [x] `data/real_rfqs/annotations/gold_annotations.json` — 20 complete gold annotations (18 synthetic + 2 real)
- [x] `scripts/scrape_etenders.py` — exists
- [x] `docs/data_collection.md` — exists and updated
- [x] `results/real_world_metrics_v2.json` — F1 0.506 on 31 documents
- [x] `tests/integration/test_real_rfq_corpus.py` — 9 tests passing
- [ ] **Separate synthetic PDFs** into `data/real_rfqs/raw/synthetic_archive/` (keep for training)
- [ ] **Collect 46 more real PDFs** to reach 50 verified-real
- [ ] **Build data/real_rfqs/gold/ directory** with gold-annotated JSON per file

## 4. STEPS

### Phase A — Organize existing data (do first)
1. Create `data/real_rfqs/raw/synthetic_archive/` and move all 113 synthetic PDFs there
2. Keep 4 real PDFs in `data/real_rfqs/raw/` organized by source:
   ```
   data/real_rfqs/raw/
   ├── ireps/
   ├── cpwd/
   ├── delhi_pwd/
   └── synthetic_archive/  (113 PDFs — for training only, NOT for gold)
   ```
3. Update `manifest.csv` to reflect new organization

### Phase B — Collect 46 more real PDFs (Owner + Agent-1)
1. Manual download from portals (Owner):
   - Browse etenders.gov.in, cpwd.gov.in, state PWD portals
   - Download 46+ real RFQ PDFs
   - Organize by source into `data/real_rfqs/raw/{source}/`
2. Update `manifest.csv` with new real PDFs

### Phase C — Build gold/ directory
1. For each of the 50 real PDFs, create `data/real_rfqs/gold/{filename}.json`
2. Schema:
   ```json
   {
     "doc_id": "rfq_001",
     "source_file": "ireps_rfq_001.pdf",
     "tokens": [...],
     "ner_tags": [...],
     "entities": [{"text": "...", "type": "MATERIAL", "start": 0, "end": 10}, ...],
     "relations": [{"head_idx": 0, "tail_idx": 1, "type": "HAS_QUANTITY"}, ...],
     "metadata": {"annotator": "agent-1", "date": "2026-05-19", "status": "complete"}
   }
   ```
3. Use BIOES tagging from `config.constants.BIOES_LABELS`
4. Annotate diverse types: building, road, electrical, plumbing, water-supply

### Phase D — Re-evaluate
1. Run `python3 scripts/evaluate_real.py --gold data/real_rfqs/gold/`
2. Compute span-level F1 per entity
3. Save to `results/real_world_metrics_v2.json`

## 5. VERIFICATION

```bash
# Real PDFs: 50+
$ ls data/real_rfqs/raw/ireps/ data/real_rfqs/raw/cpwd/ data/real_rfqs/raw/*/ | wc -l
EXPECT: ≥50

# Synthetic archived
$ ls data/real_rfqs/raw/synthetic_archive/ | wc -l
EXPECT: 113

# Gold: 30+ annotated
$ ls data/real_rfqs/gold/*.json | wc -l
EXPECT: ≥30

# Manifest updated
$ python3 -c "
import csv
rows = list(csv.DictReader(open('data/real_rfqs/annotations/manifest.csv')))
real = [r for r in rows if r.get('is_real') == 'True']
print(f'{len(rows)} total, {len(real)} real')
"
EXPECT: prints "117 total, 50 real" (after collection)

# Real F1 measured
$ python3 -c "import json; m = json.load(open('results/real_world_metrics_v2.json')); print(f'real F1: {m[\"micro_f1\"]:.3f}')"
EXPECT: prints a number

# Tests pass
$ python3 -m pytest tests/integration/test_real_rfq_corpus.py -v
EXPECT: ≥9 passed

# Lint clean
$ python3 -m ruff check scripts/build_manifest.py scripts/scrape_etenders.py
EXPECT: clean
```

## 6. ACCEPTANCE CRITERIA

- [ ] ≥50 real PDFs (currently 4, need 46 more)
- [ ] Manifest CSV updated with SHA256 per file
- [ ] ≥30 gold-annotated JSON files with actual entity/relation content
- [ ] Real F1 measured on gold set
- [ ] Synthetic PDFs archived (not mixed with real)
- [ ] No copyrighted material (only government tenders)
- [x] `docs/data_collection.md` documents the legal posture

## 7. CONSTRAINTS

- All imports `src.` prefix
- **DO NOT commit PDFs to git** (`data/real_rfqs/raw/` is gitignored)
- **DO commit** `manifest.csv` + `gold/*.json` + `annotations/` files
- Respect robots.txt, 2s minimum delay if scraping
- Sanitize bidder names / contact info — documents may contain personal data

## 8. DEPENDENCIES

- **Blocked by:** None
- **Blocks:** P3T1 (final fine-tuning uses real data)
- **Parallel-safe with:** P1T1, P1T2, P1T3, P1T4

## 9. GOTCHAS

- etenders.gov.in may rate-limit — manual download is realistic fallback
- Many PDFs are scanned — flag in manifest with `is_scanned` column
- Some PDFs are bundled; pick main RFQ scope
- Hindi PDFs welcome (test IndicBERT path from P1T2)
- Exclude >50MB PDFs to avoid storage bloat
- Skip password-protected PDFs
- Real F1 will be lower than synthetic F1 (~99%) — expected, this is the point
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md) § NLP/data

(End of file - 155 lines)
