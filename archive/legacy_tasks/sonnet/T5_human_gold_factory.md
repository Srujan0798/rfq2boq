# T5 — Human-gold factory: ≥1,000 verified sentences + ≥30 row-gold docs · owner-gated

## 1. GOAL
Convert the full corpus into genuinely human-verified training data — the ONLY thing that honestly moves real NER F1 (the source literature's own Phase 1: 1,000+ sentences, 50+ real docs). Machine drafts; **Srujan verifies**; nothing trains without his stamp.

## 2. CONTEXT (read first)
- `docs/CORE_UNDERSTANDING.md` §3 — the original sin: auto-generated labels. Never again.
- Existing tooling: `scripts/annotate_rfq.py`, `scripts/preannotate_swa_enquiries.py`, `scripts/review_annotation.py`, `scripts/validate_annotations.py`, `scripts/convert_to_bioes.py` (has held-out asserts), `scripts/gold_spotcheck_report.py`
- Raw material: 429 silver sentence drafts (`data/annotations/real_specs_silver.json`) + `data/annotations/cli_drafts/` (uncommitted agent output — audit first) — ALL drafts, none verified
- `docs/ANNOTATION_GUIDELINES.md`, `docs/ANNOTATION_WORKFLOW.md`
- Split from T3: annotate TRAIN and DEV docs. NEVER TEST.

## 3. DELIVERABLES
- One unified review loop: `scripts/review_batch.py` — renders batches of ~50 sentences (or 1 doc's rows) side-by-side with source text; owner approves/corrects/rejects each; approved records get `human_verified:true, reviewer:"srujan", review_date`
- `data/annotations/verified/` — the verified BIOES sentence store (schema: `tokens`, `ner_tags`, `source_doc_sha`, `human_verified`, `reviewer`, `review_date`)
- `data/real_rfqs/gold/rows/` extended — row gold per TRAIN/DEV BOQ doc with page/cell provenance
- `results/annotation_progress.md` — running count: verified sentences / row-gold docs / per-entity distribution (MATERIAL count explicitly)
- Review batches queued in priority order for the owner

## 4. STEPS
1. Audit `data/annotations/cli_drafts/` + `cli_training/`: what generated them, are they draft-only? If anything is marked verified without a reviewer, strip trust (coordinate with T2). Commit or discard per audit.
2. Build/finish `review_batch.py` on top of `review_annotation.py`. Requirements: shows source snippet, entity spans highlighted per BIOES, one-key approve/correct/reject, writes provenance. The owner should sustain ~100+ sentences per sitting.
3. Queue priority: (a) TRAIN BOQ-bearing docs' row gold; (b) MATERIAL-rich sentences (MATERIAL F1 = 0.00 held-out — the single weakest entity; bias selection so ≥40% of queued sentences contain MATERIAL spans); (c) DIMENSION/STANDARD-rich spec sentences; (d) breadth across clients.
4. **Owner loop (repeating):** hand Srujan a batch → he verifies → you validate (`validate_annotations.py`), update progress doc, queue next. Target ≥1,000 sentences + ≥30 row-gold docs; do not stop the loop at the minimum if he keeps going.
5. Every batch: `check_gold_provenance.py` + `test_no_test_split_leakage` green before storing.
6. Ledger + REPORT per batch.

## 5. VERIFICATION
```bash
.venv/bin/python -c "import json,glob;n=sum(1 for f in glob.glob('data/annotations/verified/*.json') for r in json.load(open(f)) if r.get('human_verified') and r.get('reviewer')=='srujan');print('verified sentences:',n)"
PYTHONPATH=. .venv/bin/python scripts/validate_annotations.py           # green
PYTHONPATH=. .venv/bin/python scripts/check_gold_provenance.py          # green
.venv/bin/python -m pytest tests/unit/test_no_test_split_leakage.py -q  # green
```

## 6. ACCEPTANCE CRITERIA
≥1,000 verified sentences (≥40% containing MATERIAL) + ≥30 verified row-gold docs, all reviewer-stamped; zero TEST-doc content; progress doc current. **Closable only by owner sign-off.**

## 7. CONSTRAINTS
You NEVER stamp `human_verified:true`. You never "fix" a rejected draft by re-submitting it unchanged. BIOES only, schema from `config.constants`. English primary.

## 8. DEPENDENCIES
Blocks: T6. Blocked by: T2, T3. Parallel-safe: with T4a/T4b (different files).

## 9. GOTCHAS
- Silver drafts came from the gazetteer — they systematically MISS entities the gazetteer doesn't know. Instruct the owner (in the batch UI) to ADD missed spans, not only approve/reject, or the verified data inherits the gazetteer's blind spots and training becomes circular anyway.
- Sentence tokenization must match the trainer's tokenizer expectations (whitespace pre-tokenized `tokens` list, BIOES `ner_tags` aligned 1:1).
- `data/annotations/*.json` legacy files use `ner_tags` OR `labels` keys — the verified store uses `ner_tags` only.
