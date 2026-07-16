# TASK: P8T2 — Gold Expansion (finish 09/10, collect + annotate +20) — Agent-Data

**Phase:** 8 | **Priority:** P0 (data volume is the #1 lever) | **Effort:** 1–2 days (+ owner review)

## 1. GOAL
Grow the real gold corpus from 8 final docs to **≥28**, by (a) finishing the 09/10 GeM drafts and (b) collecting + hand-annotating **20 more real construction-tender documents**, so the NER retrain (P8T5) finally has enough data.

## 2. CONTEXT
`docs/wave_status.md` §9 names data volume as the gap to production. Current: 8 final gold (01–08) + 2 drafts (09, 10). Review queue: `data/real_rfqs/gold/REVIEW_QUEUE.md`. Schema: entity-span gold (tokens, ner_tags, entities, relations, metadata) — see `data/real_rfqs/gold/swa_02_isro_vssc.json`. Entities/relations: `config/constants.py` (8 entities, BIOES).

Read first: `REVIEW_QUEUE.md`, `data/real_rfqs/gold/swa_01_*.json` (shape), `config/constants.py`, `scripts/` annotation helpers.

## 3. DELIVERABLES
- [ ] 09 & 10 GeM drafts reviewed → `swa_09*.json`, `swa_10*.json` (`metadata.status: complete`, `annotator: human_curated`). Use the sample-edit strategy for 09 (922 spans).
- [ ] **20 new real tender docs** in `data/real_rfqs/raw/` (Indian gov/private; insulation/civil/MEP; English; PDFs or BOQ XLSX). Diverse clients/formats. Record provenance in `data/real_rfqs/manifest.json`.
- [ ] 20 new hand-annotated gold files (BIOES entity spans + relations), each `human_curated`, ≥5 MATERIAL spans, validated against the schema.
- [ ] Updated `data/real_rfqs/manifest.json` and a short `data/real_rfqs/gold/CORPUS_SUMMARY.md` (counts per entity type, per doc).
- [ ] `scripts/validate_gold.py` passes on all (now ≥28) gold files.

## 4. STEPS
1. Finish 09/10 from `REVIEW_QUEUE.md` (drop generic/junk spans, keep real items, Hindi excluded).
2. Source 20 real tenders (eProcurement / GeM / CPWD / state PWD / private enquiries). Prefer ones with countable BOQ line items.
3. Pre-draft with the existing draft tool (recall-biased), then **hand-correct** — the human is the authority. Do NOT ship auto-draft as gold.
4. Validate all; update manifest + summary.

## 5. VERIFICATION
```bash
ls data/real_rfqs/gold/swa_*.json data/real_rfqs/gold/*.json | grep -v DRAFT | wc -l
EXPECT: >= 28 (no _DRAFT remaining for 09/10)

python3 scripts/validate_gold.py
EXPECT: all gold files validate; each >=5 MATERIAL spans

python3 - <<'PY'
import json,glob
tot=0
for f in glob.glob("data/real_rfqs/gold/swa_*.json"):
    d=json.load(open(f)); tot+=len(d.get("entities",[]))
print("total gold entities:", tot)
PY
EXPECT: materially higher than before (target 2000+ entities)
```

## 6. ACCEPTANCE CRITERIA
- [ ] ≥28 final gold docs, all `human_curated`/validated, 09/10 no longer draft.
- [ ] 20 new raw docs with provenance recorded; diverse formats.
- [ ] Corpus summary committed; `validate_gold.py` green.

## 7. CONSTRAINTS
- Do NOT fabricate spans not present in the source. Do NOT mark auto-drafts as `complete` — only human review converts draft→final.
- English content only for spans; exclude Hindi/CID glyphs.
- No synthetic data (project purged it deliberately — `attic/synthetic_corpus_archived/`).

## 8. DEPENDENCIES
- **Blocked by:** P8T0. **Feeds:** P8T5 (retrain), P8T1 (more enquiries to eval).
- **Parallel-safe with:** P8T3, P8T6, P8T7.

## 9. GOTCHAS
- GeM PDFs are bilingual; `(cid:)` are Hindi glyph noise — skip those spans.
- Respect document licensing/source terms when collecting; record where each came from.
- Keep gold token offsets consistent with `ner_tags` (loaders accept `ner_tags` and `labels`).
