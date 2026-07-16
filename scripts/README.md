# scripts/ — RFQ2BOQ

## Frozen eval scripts (DO NOT MODIFY)

These are locked by `config/FROZEN_HASHES.sha256`. Any change is a task failure.

| Script | Purpose |
|--------|---------|
| `measure_fidelity.py` | Corpus-wide fidelity measurement |
| `fidelity_audit.py` | Per-document fidelity audit (independence gate) |
| `eval_honest_rows.py` | Row-level eval against row gold |
| `eval_ner.py` | Entity-level NER eval |
| `check_gold_provenance.py` | Gold file provenance verification |
| `check_eval_hacks.py` | Detects eval tampering patterns |
| `check_split_leakage.py` | Ensures no TEST data in train paths |
| `check_frozen_hashes.py` | Verifies sha256 of frozen files |

## Active scripts (referenced by tasks/phase9/)

| Script | Purpose | Referenced by |
|--------|---------|---------------|
| `audit_fidelity_per_doc.py` | Per-doc fidelity audit artifacts | P1_02, P1_03, P3_01–P3_04 |
| `run_corpus.py` | Batch runner for full corpus | P1_04, P3_01–P3_04 |
| `annotation_factory.py` | Pre-annotate → human-review loop | P2_02, P2_03, P2_04 |
| `validate_annotations.py` | BIOES validation | P2_02, P2_03, P2_04 |
| `check_gold_provenance.py` | Gold stamp verification | P0_02, P0_03, P2_04 |
| `draft_source_truth.py` | Auto source-row counter | P1_01 |
| `draft_source_truth_extras.py` | Extended source-row counter | P1_01 |
| `corpus_sweep.py` | Repo-wide document sweep | P1_00 |
| `intake_rfq.py` | Standing intake command | P1_00, P5_04 |
| `ingest_gem_catalog.py` | GeM XLSX → JSON converter | P2_01 |
| `gen_regression_expectations.py` | Regression expectations regen | P5_02 |
| `train_lora_ner_real_only.py` | NER training (real gold only) | P4_01 |

## One-off / legacy scripts (safe to ignore)

Everything else in this directory. These are historical utilities from earlier waves. They are kept for reference but not actively maintained. Do not archive — scripts are lower priority than docs/tasks/results clutter.
