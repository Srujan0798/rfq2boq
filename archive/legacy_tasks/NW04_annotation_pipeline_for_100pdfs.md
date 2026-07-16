# NW-04 — Annotation pipeline, ready BEFORE the 100 PDFs arrive (P1, parallel-safe)

You are working on RFQ2BOQ at /Users/srujansai/Desktop/rfq2boq, branch `phase8-clean-slate`.

## 1. GOAL
SWA is collecting ~100 real tender PDFs (Sales/Jineth/Softnil — per the 2026-06-11 meeting). Human-annotated gold from those is THE fix for the core problem (NER trained on regex-auto-generated text → real F1 ~0.43; see `docs/CORE_UNDERSTANDING.md`). Build the intake → pre-annotate → human-review → BIOES-export loop NOW so day one of data arrival is productive.

## 2. CONTEXT (read first)
- `docs/CORE_UNDERSTANDING.md` — why this is the lever
- `docs/ANNOTATION_GUIDELINES.md` — entity/BIOES rules (insulation-first)
- `scripts/annotate_rfq.py` — existing annotation CLI (check its real state)
- `src/nlp/patterns/gem_catalog.py` + `dictionary.py` — use as pre-annotation suggesters
- `config/constants.py` — 8 entities, 6 relations, BIOES labels (LOCKED)

## 3. DELIVERABLES
- `scripts/intake_tender.py` — drop a PDF/XLSX into `data/incoming/`, it: dedups by SHA, records provenance (source, date, client) in `data/real_rfqs/INTAKE_MANIFEST.csv`, runs the pipeline to produce a DRAFT annotation (`status: draft-needs-review`, never auto-marked human_verified).
- `scripts/review_annotation.py` — terminal review loop: shows each draft span in context, owner accepts/edits/rejects; writes `status: human_verified` ONLY on explicit accept; logs reviewer + timestamp.
- `scripts/convert_to_bioes.py` — verified path from reviewed gold → train/val/test BIOES files with an enforced held-out list (the 10 SWA NEVER enter train/val — assert it in code, not by filename convention alone).
- Tests for all three (happy path + the "draft can't be promoted without review" guard).
- `docs/ANNOTATION_WORKFLOW.md` — 1 page: how Srujan (or a helper) processes one document in <20 min.

## 4. VERIFICATION (run, paste real output)
```bash
# Use one attic reference file as a dry-run input (do NOT touch swa_enquiries):
cp "attic/data_purged_2026_06_11/additional_real/rfq_road_RFQ9740_050.pdf" data/incoming/ 2>/dev/null || echo "pick any attic PDF"
python3 scripts/intake_tender.py data/incoming/
python3 -m pytest tests/unit/test_intake*.py tests/unit/test_annotation*.py -q
python3 scripts/convert_to_bioes.py --dry-run   # must print held-out assertion line
make verify
```

## 5. ACCEPTANCE CRITERIA
- End-to-end dry run works on 1 attic PDF: intake → draft → (simulated) review → BIOES export.
- Drafts are visibly labeled non-human-verified; promotion requires the review script.
- Held-out enforcement is a hard assert (`raise` if any swa_* doc appears in train/val).
- `make verify` passes; nothing under `data/real_rfqs/swa_enquiries/` or `gold/` modified.

## 6. FORBIDDEN
Auto-stamping human_verified. Training anything in this task. Touching the 10 SWA files or their gold.
