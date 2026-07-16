# Quarantine Manifest — created 2026-07-15 during T2 of P7 triage

Quarantine rule: MOVE, never DELETE. Owner reviews before final disposition.

## logs/
| item | origin | reason |
|---|---|---|
| `train_lora_run4.log` | untracked `logs/` | Stray LoRA training log; regenerable from `scripts/train_lora_ner_v5.py` and friends; not a committed deliverable. |

## results/*.log + *.err (adhoc pytest/int script output)
| item | origin | reason |
|---|---|---|
| `test_all.log` | untracked `results/` | Adhoc pytest stdout capture; regenerable; not a committed artifact. |
| `test_all2.log` | untracked `results/` | Adhoc pytest stdout capture; regenerable. |
| `test_int.log` | untracked `results/` | Adhoc integration test stdout; regenerable. |
| `test_int2.log` | untracked `results/` | Adhoc integration test stdout; regenerable. |
| `test_int3.log` | untracked `results/` | Adhoc integration test stdout; regenerable. |
| `test_int4.log` | untracked `results/` | Adhoc integration test stdout; regenerable. |
| `test_int_sbc.log` | untracked `results/` | Adhoc integration test stdout; regenerable. |
| `test_sacred.log` | untracked `results/` | Adhoc sacred-10 test stdout; regenerable. |
| `test_all.err` | untracked `results/` | Adhoc pytest stderr; regenerable. |
| `test_all2.err` | untracked `results/` | Adhoc pytest stderr; regenerable. |
| `test_int.err` | untracked `results/` | Adhoc integration stderr; regenerable. |
| `test_int2.err` | untracked `results/` | Adhoc integration stderr; regenerable. |
| `test_int3.err` | untracked `results/` | Adhoc integration stderr; regenerable. |
| `test_int4.err` | untracked `results/` | Adhoc integration stderr; regenerable. |
| `test_int_sbc.err` | untracked `results/` | Adhoc integration stderr; regenerable. |
| `test_sacred.err` | untracked `results/` | Adhoc sacred-10 stderr; regenerable. |

## results/annotation_wave1/ (draft scratch)
| item | origin | reason |
|---|---|---|
| `draft_70.log` | untracked `results/annotation_wave1/` | Adhoc script log from draft generation; DRAFT_STATS.md is the tracked deliverable. |

## results/fidelity/ (stray outputs from audits)
| item | origin | reason |
|---|---|---|
| `all_audit.log` | untracked `results/fidelity/` | Redirected stderr/stdout from running fidelity audit across all docs; regenerable via `scripts/audit_fidelity_per_doc.py`. |
| `all_audit.err` | untracked `results/fidelity/` | Redirected stderr from the same run; regenerable. |
| `07_grew_preview.png` | untracked `results/fidelity/` | Adhoc preview image, not referenced by any committed report; regenerable/screenshot. |

## results/corpus_run/ (regenerable run logs)
| item | origin | reason |
|---|---|---|
| `20260706_144944/run.log` | untracked `results/corpus_run/` | Timestamped corpus-run stderr/stdout; status.json is the tracked summary artifact. |
| `20260706_145537/run.log` | untracked `results/corpus_run/` | Same as above. |
| `20260706_155344/run.log` | untracked `results/corpus_run/` | Same as above. |
| `20260706_165901/run.log` | untracked `results/corpus_run/` | Same as above. |
| `20260707_050946/run.log` | untracked `results/corpus_run/` | Same as above. |
| `20260707_050950/run.log` | untracked `results/corpus_run/` | Same as above. |
| `20260707_051057/run.log` | untracked `results/corpus_run/` | Same as above. |

## results/ui_dropin/_scratch/ (temp driver dir)
| item | origin | reason |
|---|---|---|
| `results/ui_dropin/_scratch/` | untracked directory | Temporary UI-corpus drop-in driver scratch dir (PID file, local driver script, shell wrapper, logs); not meant to ship. |

## contamination/ (fabrication artifacts from Incident #13)
| item | origin | reason |
|---|---|---|
| `v1.0.0_TAG_RECORD.md` | local git tag `v1.0.0` at commit `0870b8e` | Tag asserted "All 10 SWA files at 100.0% row F1 — ship it" on a fabricated commit chain (gold edited to match pipeline output, independent gold deleted). Tag removed from `phase9-final`; this record preserves the provenance for owner review. Must not be pushed to replacement `main`. |
