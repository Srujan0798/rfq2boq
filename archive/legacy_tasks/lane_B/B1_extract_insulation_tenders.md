# TASK: Lane B — Extract insulation tenders + draft row-gold — Agent-B (STRONGEST MODEL)

**Worktree:** `/Users/srujansai/Desktop/rfq2boq-laneB`
**Branch:** `phase8-laneB`
**Model:** STRONGEST available (gold quality is the entire training data lever)

---

## 1. GOAL
Extract text + tables from the 11 real insulation tender PDFs and produce DRAFT row-gold for the 2 best RFQ↔BOQ pairs — the first new training-domain gold since the SWA enquiries. Srujan will human-verify before anything is called "gold."

## 2. CONTEXT
Files to read FIRST:
- `docs/CORE_UNDERSTANDING.md` — the real problem: NER trained on regex, not real tenders
- `docs/SWA_REQUIREMENTS_2026-06-11.md` — R1 (100% fidelity), R3 (100-PDF loop)
- `docs/ANNOTATION_GUIDELINES.md` — how gold is structured
- `data/real_rfqs/gold/rows/01_gsecl_wanakbori_tmd8.rowgold.json` — gold format reference
- `data/real_rfqs/raw/insulation_hvac/README.md` — what's in the new corpus
- `tasks/NW04_annotation_pipeline_for_100pdfs.md` — annotation loop spec
- `config/constants.py` — 8 entities (READ ONLY)
- `src/pipeline.py` — the pipeline entry point
- `scripts/eval_honest_rows.py` — how gold is consumed

Current state:
- 11 real tender PDFs in `data/real_rfqs/raw/insulation_hvac/`
- 9 real BOQ PDFs in `data/real_rfqs/raw/insulation_hvac/boq_references/`
- ZERO gold or extraction for insulation domain yet
- Pipeline extracts XLSX well (89% F1) but PDF NER is weak (14%)

Best annotation pairs (RFQ input ↔ expected BOQ output):
1. `TENDER.pdf` ↔ `boq_references/BOQ.pdf`
2. `SWPL-PER-HVAC-RFQ-02 (Thermal & Acoustic Insulation).pdf` ↔ `boq_references/BOQ - INSULATION.pdf`

## 3. DELIVERABLES
- [ ] `data/real_rfqs/extracted/insulation_hvac/` — one `.txt` file per tender PDF (raw extracted text)
- [ ] `data/real_rfqs/extracted/insulation_hvac/tables/` — one `.json` file per tender PDF (extracted tables)
- [ ] `data/real_rfqs/gold/rows/insul_01_tender.rowgold.json` — DRAFT row-gold from `TENDER.pdf` ↔ `BOQ.pdf`
- [ ] `data/real_rfqs/gold/rows/insul_02_swpl.rowgold.json` — DRAFT row-gold from `SWPL...pdf` ↔ `BOQ - INSULATION.pdf`
- [ ] `scripts/extract_insulation_corpus.py` — reusable extraction script
- [ ] `data/real_rfqs/extracted/insulation_hvac/manifest.json` — provenance for each file

## 4. STEPS
1. Activate the 3.12 venv: `source /Users/srujansai/Desktop/rfq2boq-laneB/.venv-lora/bin/activate`
2. Write `scripts/extract_insulation_corpus.py`:
   - Input: all PDFs under `data/real_rfqs/raw/insulation_hvac/` (not boq_references/)
   - Use pdfplumber for text, camelot-py for tables (fallback pdfplumber if camelot fails)
   - Output: `data/real_rfqs/extracted/insulation_hvac/<stem>.txt` + `<stem>_tables.json`
   - Log: `manifest.json` with file, page count, table count, extraction method per PDF
3. Run it: `python3 scripts/extract_insulation_corpus.py`
4. **Draft row-gold from `BOQ.pdf`** (the expected output side):
   - Open `data/real_rfqs/raw/insulation_hvac/boq_references/BOQ.pdf` with pdfplumber
   - Extract every BOQ row: fields = `material` (description), `quantity` (numeric), `unit`
   - Write to `data/real_rfqs/gold/rows/insul_01_tender.rowgold.json` as list of dicts
   - Set `"human_verified": false` and `"source": "BOQ.pdf"` on every entry
   - IMPORTANT: gold comes from the BOQ PDF (expected output), NOT from running the pipeline on TENDER.pdf
5. Repeat step 4 for `BOQ - INSULATION.pdf` → `insul_02_swpl.rowgold.json`
6. Write a quick sanity check:
   ```bash
   python3 -c "
   import json
   g = json.load(open('data/real_rfqs/gold/rows/insul_01_tender.rowgold.json'))
   assert all('material' in r and 'quantity' in r and 'unit' in r for r in g)
   assert all(r.get('human_verified') == False for r in g)
   print(f'insul_01: {len(g)} rows, human_verified=False — OK')
   "
   ```
7. Commit:
   ```
   git add data/real_rfqs/extracted/ data/real_rfqs/gold/rows/insul_0*.rowgold.json scripts/extract_insulation_corpus.py
   git commit -m "feat(data): extract insulation corpus + draft row-gold for 2 pairs (B1)"
   ```

## 5. VERIFICATION
```bash
cd /Users/srujansai/Desktop/rfq2boq-laneB
python3 -c "
import json, pathlib
# Check extractions exist
txts = list(pathlib.Path('data/real_rfqs/extracted/insulation_hvac').glob('*.txt'))
print(f'{len(txts)} text extractions')
assert len(txts) >= 10

# Check draft gold
for f in ['insul_01_tender', 'insul_02_swpl']:
    g = json.load(open(f'data/real_rfqs/gold/rows/{f}.rowgold.json'))
    assert len(g) > 0, f'{f} empty!'
    assert all(r.get(\"human_verified\") == False for r in g), f'{f} must be human_verified=false'
    print(f'{f}: {len(g)} rows OK')
"
python3 -m ruff check src/ scripts/ --quiet
```

## 6. ACCEPTANCE CRITERIA
- [ ] 10+ text extractions created (all 11 tender PDFs attempted)
- [ ] `manifest.json` records provenance for every file
- [ ] `insul_01_tender.rowgold.json` has > 0 rows, `human_verified: false`
- [ ] `insul_02_swpl.rowgold.json` has > 0 rows, `human_verified: false`
- [ ] Gold comes from BOQ PDFs (expected output), NEVER from running pipeline on tenders
- [ ] Lint clean

## 7. CONSTRAINTS
- **ANTI-CHEAT (hardest rule):** Row-gold MUST come from the BOQ reference PDFs, not from pipeline output. Never run the pipeline on `TENDER.pdf` and use that as gold. This is the self-comparison cheat.
- `human_verified: false` on ALL draft gold — Srujan reviews before it becomes "true"
- No schema changes (`config/constants.py` is READ ONLY)
- Imports: `src.` prefix only
- Python 3.12 via `.venv-lora`
- No new branches

## 8. DEPENDENCIES
- Blocked by: nothing (laneB starts from clean base)
- Parallel-safe with: laneA, laneC, laneD, laneE (disjoint file paths)
- Blocks: B2 (annotation loop needs this extracted text), NER retraining

## 9. GOTCHAS
- Some insulation PDFs (`Tender (2).pdf`, `Tender (4).pdf`) are compliance sheets ("Noted/Comply") — they will extract very little; log in manifest, don't fail
- BOQ tables in these PDFs may have merged cells — use pdfplumber's `extract_table()` per page, not just text
- Quantity cells may say "LS" (lump sum) or "R/O" — keep them as-is with `quantity: 0.0, unit: "LS"` and flag `"rate_only": true`
- The `.venv` is Python 3.14 — broken. Use `.venv-lora` (3.12)

---

## REPORT FORMAT (paste back to Srujan)
```
## REPORT: Lane B1 — Insulation extraction + draft gold

Deliverables:
- path — created/modified

Verification:
- PDFs extracted: N/11
- insul_01 rows: N
- insul_02 rows: N
- human_verified: false on all
- ruff: clean

Blockers: none / list
Deviations: none / list
```
