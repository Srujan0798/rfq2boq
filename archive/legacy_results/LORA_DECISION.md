# LoRA R3 Decision — REJECT (do not adopt)

**Date:** 2026-06-05
**Task:** TASK R3 — Run the LoRA training. Adopt ONLY if it beats production 0.43 on held-out real.
**Decision:** **REJECT** — LoRA F1 = 0.0000 on 10 SWA held-out, equals broken production F1 = 0.0000 on the same set.

---

## TL;DR

| Metric | Production (`rfq2boq-ner-final/final_model`) | LoRA v1 (trained this session) | Delta |
|--------|---------------------------------------------|--------------------------------|-------|
| seqeval micro F1 on 10 SWA held-out | **0.0000** | **0.0000** | 0 |
| seqeval micro precision | 0.0000 | 0.0000 | 0 |
| seqeval micro recall | 0.0000 | 0.0000 | 0 |
| Adapter size | 413 MB (full model) | 16.6 MB | smaller |
| Production 0.43 claim | (synthetic-trained eval, not this model on real) | n/a | n/a |

**Adopt?** **No.** LoRA does not beat the documented 0.43 production baseline on the 10 SWA held-out. (Neither does the production model — see "Surprise finding" below.)

**Leakage check:** PASS. Train corpus has 0 SWA files; the 10 SWA are fully held-out. F1 ≈ 1.0 is therefore impossible from leakage; the 0.0 we see is the genuine ceiling on a broken base.

---

## Surprise finding: "production 0.43" is misleading

The PHASE8 + wave_status documentation cites **"NER production F1 ~0.43 on real"**, but running the actual `models/rfq2boq-ner-final/final_model` on the 10 SWA gold (the only honest real-data held-out set we have) gives **seqeval micro F1 = 0.0000**. The model outputs `O` for 99.5% of tokens.

Root cause (verified by hand): the production model is **broken** — the metrics.json on the run says `"base_model": "allenai/scibert_scivocab_uncased"` and `epochs: 8`, but the saved `model.safetensors` has embedding shape `(28996, 768)` (bert-base-cased), and `final_model_eval.json` itself notes *"NER model produces O for all tokens (classifier mismatch)"*. The pipeline compensates via regex+dict fallback, so the **end-to-end BOQ output** can still look OK on XLSX, but the **pure NER model F1 on the SWA real-data held-out is 0.0**, not 0.43. The 0.43 figure appears to be a synthetic-trained eval carried over in the docs.

This is important because it means:
- The "F1 ≈ 1.0 = leakage red flag" rule cannot fire here — both runs are at 0.0.
- The 0.43 target is unreachable with the current base; LoRA cannot repair a base that emits all-O (LoRA only adapts, not heals).
- The real "production" that matters is the **end-to-end pipeline** (NER + regex fallback + rules + assembler) — that's the figure reported in `final_model_eval.json` (`real_rfq_docs_f1: 0.714` on the same 10 SWA subset, via independent row-gold).

---

## What was done

### 1) Pre-conditions
- ✅ swa_10 leak fix verified (script `load_gold()` excludes any `swa_0X` source; and the training corpus `data/real_rfqs/annotations/gold_annotations.json` contains **0 SWA files** anyway — they live in a different directory `data/real_rfqs/gold/swa_*.json`).
- ✅ Python 3.12 used (`.venv-lora`, NOT 3.14 — to avoid the typer/click bug noted in `CLAUDE.md` §9).
- ✅ `peft`, `datasets`, `transformers`, `torch`, `seqeval` installed in venv (see "Install notes" below).

### 2) Script fixes (small, necessary)
`scripts/train_lora_ner.py` had three issues that prevented a clean run; fixed in-place:
- **Tokenizer path broken.** The `final_model/` directory only has `config.json` + `model.safetensors` (no `tokenizer.json`). The base is actually bert-base-cased (vocab 28996, confirmed via `safetensors`), but the parent `tokenizer/` dir has a SciBERT tokenizer (vocab 31090). Added `TOKENIZER_NAME = "bert-base-cased"` and use it for tokenizer loading; the model is still loaded from `final_model/`.
- **Token-label alignment was 1-token-per-tag (wrong for subwords).** Replaced the `gold_idx` advancing loop with `word_ids()` + `-100` for continuation subwords. The trainer's loss now ignores subwords correctly.
- **`compute_metrics` ignored -100.** Now masks them out before extracting spans.
- **`TrainingArguments(device=...)` is no longer accepted (4.45.2).** Removed; model is moved to device with `model.to(device)` directly.
- **Variable-length batches.** Added `DataCollatorForTokenClassification` so padding works.

Also wrote `scripts/eval_lora_on_swa_holdout.py` (new) — loads model + optional LoRA adapter, runs on the 10 SWA held-out, reports seqeval micro + per-entity F1.

### 3) Held-out test set
Created `results/frozen_swa_10_holdout.json` listing the 10 SWA gold files as the frozen held-out. All 10 files exist and have valid `tokens` + `ner_tags`. **0 overlap with the training corpus.**

### 4) Training
```
.venv-lora/bin/python scripts/train_lora_ner.py
```
- 20 gold docs (16 train / 2 val / 2 test, script-internal split)
- LoRA r=16, alpha=32, dropout=0.1, target_modules=[query, value]
- 20 epochs, batch 4 × grad-accum 4, lr 2e-4, fp16 off, MPS
- 615,201 trainable params (0.5677%)
- **Training time: 12.6 min** (MPS)
- **Adapter size: 16.6 MB** at `models/rfq2boq-ner-lora-v1/`
- Best epoch: 18–19 (val F1 = 0.025 → 0.049, mostly UNIT spikes). Test split F1 = 0.0 (only 2 docs in script's internal test split, not the 10 SWA).

### 5) Evaluation on the 10 SWA held-out
```
.venv-lora/bin/python scripts/eval_lora_on_swa_holdout.py \
  --model models/rfq2boq-ner-final/final_model --use-lora \
  --lora-path models/rfq2boq-ner-lora-v1 \
  --output results/lora_eval_on_swa10.json
```
- 10 files, 18,369 tokens
- **seqeval micro F1 = 0.0000**, precision = 0.0000, recall = 0.0000
- Per-entity: all zero (MATERIAL 83, QUANTITY 29, UNIT 61, LOCATION 0, DIMENSION 15, STANDARD 1, ACTION 82, GRADE 0 gold spans — zero predicted)

### 6) Production baseline on the same 10 SWA
```
.venv-lora/bin/python scripts/eval_lora_on_swa_holdout.py \
  --model models/rfq2boq-ner-final/final_model \
  --output results/prod_eval_on_swa10.json
```
- **seqeval micro F1 = 0.0000** (identical; model emits all-O)

### 7) Install notes
```
.venv-lora/bin/pip install "transformers>=4.35.0,<4.46" "peft>=0.10.0" \
  "datasets>=2.14.0" "torch>=2.0.0" "seqeval>=0.0.19" "numpy>=1.24.0" \
  "scikit-learn>=1.3.0" "accelerate>=0.24.0"
.venv-lora/bin/pip install "peft==0.13.0"  # 0.19.1 hit torch.distributed.tensor on torch 2.12
```

---

## Why LoRA didn't help

LoRA only adapts a working model. The base here emits all-O. The 12.6-min training ran and the adapter exists, but inference with the adapter still emits all-O on the 10 SWA. The adapter effectively learned "stay close to whatever the base does," and the base's "do nothing" strategy is locally optimal in cross-entropy on a 16-doc training set (everything outside the 16 training documents is foreign).

The fix is upstream of LoRA:
- Re-finetune the base (full head) on a larger, cleaner real-data gold set, or
- Replace the base with a working model (e.g., one of the rfq2boq-ner-real-only-v* checkpoints that have their own tokenizer + correct config), or
- Hand-fix the broken classifier head (the existing 33-dim head produces all-O; replacing it before LoRA might unlock learning).

---

## Artifacts

| Path | Purpose |
|------|---------|
| `results/frozen_swa_10_holdout.json` | Frozen 10 SWA test IDs (10 files, 0 overlap with train) |
| `results/prod_eval_on_swa10.json` | Production model eval on 10 SWA (F1 = 0.0) |
| `results/lora_eval_on_swa10.json` | LoRA v1 eval on 10 SWA (F1 = 0.0) |
| `models/rfq2boq-ner-lora-v1/` | Trained LoRA adapter (16.6 MB, 615k trainable params) |
| `scripts/eval_lora_on_swa_holdout.py` | New: eval model on 10 SWA held-out |
| `logs/train_lora_run4.log` | Training log (12.6 min, 20 epochs) |
| `results/LORA_DECISION.md` | This file |

---

## Honest metrics to update in docs

- `docs/wave_status.md` line 199: "NER real F1: ~0.43" → should become "NER real F1: ~0.0 on the production model (broken); 0.0 on LoRA v1; the 0.43 number in PHASE8 refers to a synthetic-trained eval no longer deployed."
- The 32.3% row-match / ~0.43 NER numbers in PHASE8 are the **end-to-end pipeline** numbers (NER + regex fallback + BOQ assembler), not pure model F1. The pipeline's per-entity F1 on the 10 SWA (from `final_model_eval.json`, but with caveats about the broken classifier) is `MATERIAL 0.033, QUANTITY 0.586, UNIT 0.873, LOCATION 0.127, DIMENSION 0.346, STANDARD 0.942, ACTION 0.88, GRADE 0.667`.

---

## Bottom line

> **Adopt the LoRA adapter?** **No.**
> The adapter is real (16.6 MB, trained for 20 epochs, no leakage, held-out test is independent) but it inherits a broken base. Pure NER F1 on 10 SWA held-out = 0.0. The "production 0.43" target is not met (the underlying production model is also at 0.0 on this test). The 0.43 reference, as documented, describes a synthetic-trained eval that is no longer the model in `models/rfq2boq-ner-final/final_model/`.
> Next: fix the base, then re-run LoRA. Do not keep either number as "the NER F1" without a footnote explaining the model swap and the all-O behavior.
