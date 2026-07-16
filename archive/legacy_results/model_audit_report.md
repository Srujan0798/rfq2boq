# Model Audit Report

**Date:** 2026-07-04  
**Auditor:** opencode-go/mimo-v2.5  
**Scope:** All subdirectories under `models/` (excluding `quarantine/`)

---

## Summary

All 7 model directories under `models/` are unsafe for production use. **None qualify as SAFE.** The classifications are:

| Count | Classification |
|-------|---------------|
| 2 | CONTAMINATED |
| 3 | BROKEN |
| 2 | UNKNOWN |
| 0 | SAFE |

Two models (`rfq2boq-ner-lora-cli`, `rfq2boq-ner-lora-real`) already have partial entries in `models/quarantine/` from earlier cleanup attempts.

---

## Classification Table

| Model Directory | Classification | Best Eval F1 | Training Status | Reason |
|---|---|---|---|---|
| `rfq2boq-ner-lora-cli` | **CONTAMINATED** | 9.36% | Crashed (step 23/345) | Trained on leaked test data (`data/annotations/cli_training/`, now deleted for TEST-set leakage). PID 88948. Only 1 epoch of 15 completed. |
| `rfq2boq-ner-lora-real` | **BROKEN** | 7.68% → 0.0% | Completed 5 epochs | PID 6877 dead. Eval F1 collapsed from 7.68% (epoch 2) to 0.0% (epochs 4-5). Only ~39 short docs after split → severe overfitting. |
| `rfq2boq-ner-lora-swa10` | **BROKEN** | 0.0% | Completed 3 epochs | Only 3 training steps. Eval F1: 0.0% at every evaluation. Never learned anything. Unknown training data. |
| `rfq2boq-ner-lora-v2` | **UNKNOWN** | 4.26% | Completed 20 epochs | Un-audited provenance. Base model references non-existent `models/rfq2boq-ner-real-only-v2/final_model`. No documented training data source. |
| `rfq2boq-ner-lora-v3` | **UNKNOWN** | 14.75% | Completed 10 epochs | Un-audited provenance. No documented training data source or README provenance. |
| `rfq2boq-ner-lora-v4` | **BROKEN** | N/A | Empty output | `final_model/` directory is empty — no adapter weights, no checkpoint files. Training never produced usable output. |
| `rfq2boq-ner-lora-v5` | **CONTAMINATED** | 64.68% (synthetic) | Completed 7/20 epochs | Trained on pseudo-labeled (silver) data. 64.68% on contaminated eval set, but only 18.8% on real held-out docs. Violates anti-cheat rule: machine labels never enter training. |

---

## Detailed Evidence per Model

### 1. rfq2boq-ner-lora-cli — CONTAMINATED

- **Base model:** bert-base-cased (PEFT 0.19.1, LoRA r=32, alpha=64)
- **Checkpoints:** checkpoint-23 (only checkpoint)
- **Training:** Crashed at step 23/345 (epoch 1 of 15 planned). `should_training_stop: false` in trainer state — the job was killed, not completed.
- **Best eval:** F1=9.36%, precision=7.1%, recall=13.7% (single eval at epoch 1)
- **Contamination:** PID 88948 copied data into `data/annotations/cli_training/` which was later deleted for TEST-set leakage (per `kleenhand.md` §3.1, `FINAL_HONEST_REPORT.md` §6).
- **Verdict:** Contaminated by test data leakage AND broken by early crash. Double failure.

### 2. rfq2boq-ner-lora-real — BROKEN

- **Base model:** bert-base-cased (PEFT 0.19.1)
- **Checkpoints:** checkpoint-46, checkpoint-115
- **Training:** 5 epochs, 115 steps. Completed but collapsed.
- **Eval progression:** 2.6% → 7.68% (best, epoch 2) → 1.4% → 0.0% → 0.0%
- **Root cause:** Only ~39 short documents after train/val split (per `kleenhand.md` §3.4). Model overfits to background tokens.
- **Verdict:** Training ran to completion but produced a collapsed model. Not usable.

### 3. rfq2boq-ner-lora-swa10 — BROKEN

- **Base model:** bert-base-cased (PEFT 0.19.1)
- **Checkpoints:** checkpoint-1, checkpoint-3
- **Training:** 3 steps (3 epochs on very small data). max_steps=3.
- **Eval:** F1=0.0% at every evaluation (epochs 1, 2, 3). All entity types at 0.
- **Verdict:** Never learned anything. Completely broken.

### 4. rfq2boq-ner-lora-v2 — UNKNOWN

- **Base model:** `models/rfq2boq-ner-real-only-v2/final_model` (PEFT 0.13.0, LoRA r=16, alpha=32)
- **Checkpoints:** checkpoint-1, checkpoint-20
- **Training:** 20 epochs, 20 steps. Completed.
- **Eval:** Best F1=4.26% (epoch 12), mostly QUANTITY-only predictions. MATERIAL, STANDARD, UNIT, DIMENSION, GRADE all at 0.
- **Provenance:** The base model path `models/rfq2boq-ner-real-only-v2/final_model` does not exist in the current `models/` directory. Unknown what data was used for training.
- **Verdict:** Treat as contaminated until proven otherwise.

### 5. rfq2boq-ner-lora-v3 — UNKNOWN

- **Base model:** bert-base-cased (PEFT 0.19.1)
- **Checkpoints:** checkpoint-9, checkpoint-10
- **Training:** 10 epochs, 10 steps. Completed.
- **Eval:** Best F1=14.75% (epoch 10). Only QUANTITY entity detected (F1=36.7%). All other entities at 0.
- **Provenance:** No documented training data source. README is generic template.
- **Verdict:** Treat as contaminated until proven otherwise.

### 6. rfq2boq-ner-lora-v4 — BROKEN

- **Directory structure:** `models/rfq2boq-ner-lora-v4/final_model/` — empty directory
- **No adapter files, no checkpoint files, no config files.**
- **Verdict:** Training never produced output. Empty and unusable.

### 7. rfq2boq-ner-lora-v5 — CONTAMINATED

- **Base model:** bert-base-cased (PEFT 0.13.0)
- **Checkpoints:** checkpoint-96, checkpoint-112
- **Training:** 7 of 20 epochs completed (112/320 steps). `should_training_stop: false` — job was interrupted.
- **Best eval:** F1=64.68% at epoch 7 (checkpoint-112). Good per-entity scores: STANDARD=95.1%, UNIT=94.0%, QUANTITY=43.2%, DIMENSION=61.3%, GRADE=48.8%.
- **However:** This eval is on the contaminated synthetic validation set. Per `AGENTS.md`, real-doc F1 is only 18.8% — a 46-point gap confirming massive overfitting to pseudo-labels.
- **Training data:** Pseudo-labeled/silver data. Violates anti-cheat rule #6: "Machine labels (silver/pseudo/auto) never enter training."
- **Verdict:** Contaminated. The high synthetic eval score is misleading.

---

## Quarantine Plan

The quarantine script (`scripts/quarantine_contaminated_models.py`) will move the following directories to `models/quarantine/` when run with `--execute`:

| Directory | Action |
|---|---|
| `rfq2boq-ner-lora-swa10` | MOVE |
| `rfq2boq-ner-lora-v2` | MOVE |
| `rfq2boq-ner-lora-v3` | MOVE |
| `rfq2boq-ner-lora-v4` | MOVE |
| `rfq2boq-ner-lora-v5` | MOVE |
| `rfq2boq-ner-lora-cli` | SKIP (already partially quarantined) |
| `rfq2boq-ner-lora-real` | SKIP (already partially quarantined) |

A `MANIFEST.json` will be created in `models/quarantine/` recording the original path, classification, reason, and timestamp for each moved directory.

---

## Recommendation

1. Run `python3 scripts/quarantine_contaminated_models.py --execute` with owner approval.
2. For `rfq2boq-ner-lora-cli` and `rfq2boq-ner-lora-real`, decide whether to consolidate their partial quarantine entries or delete them outright.
3. After quarantine, `models/` should contain only `quarantine/` (holding all contaminated/broken/unknown models).
4. A clean retrain on human-verified non-TEST labels (per Gate 3) should produce the first SAFE checkpoint.

---

*This report was generated by the model audit agent. Evidence sources: `kleenhand.md`, `deliverables/FINAL_HONEST_REPORT.md`, `AGENTS.md`, trainer_state.json files, adapter_config.json files.*
