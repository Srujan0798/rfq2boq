# T4b — 100% capture-or-flag across the WHOLE corpus

## 1. GOAL
Extend the T4a bar from 10 docs to every BOQ-bearing document in the full ~105-doc corpus: frozen source truth per doc, per-doc PASS, zero silent drops.

## 2. CONTEXT
- `data/real_rfqs/corpus_manifest.json` (T3) — the `boq_bearing` docs are your worklist (expect ~40–60)
- `scripts/draft_source_truth.py` (T1) — reuse for batch drafting
- TEST-split docs (T3): fidelity may RUN on them (it's capture-counting, not tuning) but NO extraction-code changes may be justified by TEST-doc results — fix classes of bugs found on TRAIN/DEV docs only.

## 3. DELIVERABLES
- `source_truth.json` extended to every BOQ-bearing corpus doc (machine drafts + batched owner confirmation via `results/source_truth_review_corpus.md`)
- Extraction fixes for TRAIN/DEV failures (each with tests)
- `results/fidelity_full_corpus.md` — per-doc table, whole corpus, two identical consecutive runs
- Extended `scripts/measure_fidelity.py` doc registry: reads the corpus manifest, not a hardcoded 10-doc map

## 4. STEPS
1. Generalize the fidelity harness to iterate the manifest's `boq_bearing` docs.
2. Batch-draft source truth for all of them; produce the owner review doc in batches of ~15 (STOP for owner confirmation per batch — proceed batch-by-batch, don't block the whole task on one sitting).
3. Run the sweep on confirmed batches; classify failures (same classes as T4a); fix on TRAIN/DEV evidence; re-run.
4. Spec-only docs: assert the pipeline correctly yields 0 BOQ rows WITHOUT crashing (the structure-first router must classify them spec-only — 7 already proven; extend to all).
5. Ledger + REPORT per batch.

## 5. VERIFICATION
```bash
PYTHONPATH=. .venv/bin/python scripts/measure_fidelity.py --corpus   # per-doc PASS on all confirmed boq_bearing docs
.venv/bin/python -m pytest tests/ -q && make verify                   # green
```

## 6. ACCEPTANCE CRITERIA
Every owner-confirmed BOQ-bearing doc: per-doc PASS or owner-accepted documented blocker; spec-only docs: 0 rows, 0 crashes; results stable across two runs.

## 7. CONSTRAINTS
Same as T4a. Additionally: no extraction change may cite a TEST doc as its justification.

## 8. DEPENDENCIES
Blocks: T7. Blocked by: T3, T4a. Parallel-safe: with T5 (different files).

## 9. GOTCHAS
- Spec-2 XLSX BOQs (`BOQ - Insulation.xlsx`, `Insulation Medical.xlsx`, `Insulation ARFF.xlsx`, `Insulation.xlsx`) exercise the multi-qty rule differently than Zydus — verify mode behavior on each.
- Compliance-sheet PDFs ("BOQ compliance", "Specification compliance") are BOQ-bearing but have vendor-fill columns — capture the item rows, flag the fill-ins.
- Very large PDFs (Adani Pune 6.6MB, DC-90 4.5MB, Tender Specs 4.5MB) need the per-file timeout from T4a.
