# TASK: P1T3 — ARCBERT Integration — Agent-2

**Phase:** 1 | **Effort:** 2–3 days | **Priority:** P1

## 1. GOAL
Replace our planned ConstructionBERT pretraining (A3) with the already-published ARCBERT model from Tsinghua (Lin et al., 2022) — saves us from building a 50k-document corpus and 3 epochs of MLM pretraining.

## 2. CONTEXT
Read first:
- `src/nlp/ner/bert_ner.py` — current `bert-base-cased` based model
- `models/ner-bert-bilstm-crf-v1/` — current trained checkpoint
- [docs/HYBRID_PLAN.md](../../../docs/HYBRID_PLAN.md)
- [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)

ARCBERT references:
- Paper: https://www.sciencedirect.com/science/article/abs/pii/S0166361522001300
- Author page (download links): https://linjiarui.net/en/portfolio/2022-04-02-ARCBERT-largescale-dataset-and-pretrained-model-for-AEC-domain
- Citation: Lin et al., "Pretrained domain-specific language model for natural language processing tasks in the AEC domain", Automation in Construction, 2022.

Current state: our model is trained from `bert-base-cased`. ARCBERT is BERT-base-uncased pre-trained on 1.6B+ tokens of AEC text. Expected lift on construction NER: +3–8% F1.

## 3. DELIVERABLES
- [ ] `models/arcbert-base/` — downloaded checkpoint (config + weights + tokenizer)
- [ ] `scripts/download_arcbert.py` — automation script (with fallback to SciBERT)
- [ ] `src/nlp/ner/arcbert_ner.py` — NER head on top of ARCBERT
- [ ] `scripts/finetune_arcbert_ner.py` — fine-tune on our BIOES annotations
- [ ] `models/arcbert-ner-v1/` — fine-tuned model + metrics.json
- [ ] `results/arcbert_vs_baseline.json` — F1 comparison
- [ ] `tests/unit/test_arcbert.py` — ≥5 tests
- [ ] `docs/arcbert.md` — license/citation + usage notes
- [ ] If ARCBERT NOT downloadable: `docs/arcbert_unavailable.md` documenting the block, with SciBERT fallback executed instead

## 4. STEPS
1. Read context files.
2. **Acquire model** — `python3 scripts/download_arcbert.py`:
   - Primary: try linjiarui.net author page, GitHub if linked
   - Secondary: try HuggingFace Hub for `linjiarui/arcbert` or similar
   - Fallback if both fail: download `allenai/scibert_scivocab_uncased` (closest free domain LM) and document the substitution in `docs/arcbert_unavailable.md`
   - Save to `models/arcbert-base/` regardless of source (so downstream code is source-agnostic)
3. Implement `src/nlp/ner/arcbert_ner.py`:
   ```python
   class ARCBERTNER:
       def __init__(self, base_model_dir="models/arcbert-base", num_labels=NUM_LABELS): ...
       # Uses same BERT-BiLSTM-CRF head as our existing model, just different encoder
   ```
4. Fine-tune script `scripts/finetune_arcbert_ner.py`:
   - Load `models/arcbert-base/` as encoder
   - Add BiLSTM(2×256) + CRF head
   - Train on `data/annotations/` for 10 epochs, lr=2e-5, batch=16 (MPS)
   - Save to `models/arcbert-ner-v1/` with metrics.json
5. Comparison evaluation `scripts/compare_arcbert.py`:
   - Eval `models/ner-bert-bilstm-crf-v1` (current baseline)
   - Eval `models/arcbert-ner-v1` (new)
   - Both on same test set
   - Write `results/arcbert_vs_baseline.json`
6. Tests cover: model loads, prediction shape correct, fine-tune script runs on tiny dataset.
7. `docs/arcbert.md`: cite the paper, document license terms (academic use unless otherwise stated), explain how to update the model.

## 5. VERIFICATION
```bash
# Model files present
$ ls models/arcbert-base/config.json models/arcbert-base/pytorch_model.bin
EXPECT: both exist (or .safetensors instead of .bin)

# Fine-tuned model trained
$ ls models/arcbert-ner-v1/metrics.json
EXPECT: exists
$ python3 -c "import json; m = json.load(open('models/arcbert-ner-v1/metrics.json')); assert m['test_f1'] > 0.5"
EXPECT: no AssertionError

# Comparison written
$ python3 -c "import json; d = json.load(open('results/arcbert_vs_baseline.json')); print('baseline:', d['baseline_f1'], 'arcbert:', d['arcbert_f1'])"
EXPECT: two floats; arcbert_f1 should be ≥ baseline_f1 (otherwise document why)

# Smoke test
$ python3 -c "from src.nlp.ner.arcbert_ner import ARCBERTNER; n = ARCBERTNER(); print('loaded')"
EXPECT: prints "loaded"

# Tests
$ python3 -m pytest tests/unit/test_arcbert.py -v
EXPECT: ≥5 passed
```

## 6. ACCEPTANCE CRITERIA
- [ ] `models/arcbert-base/` exists (ARCBERT proper OR documented SciBERT fallback)
- [ ] Fine-tuned NER on top, saved to `models/arcbert-ner-v1/`
- [ ] F1 measured + compared against baseline
- [ ] If ARCBERT used: F1 should improve or stay flat (document the delta honestly)
- [ ] If SciBERT used as fallback: F1 may be lower than custom; acceptable
- [ ] License attribution in `docs/arcbert.md` (or `docs/arcbert_unavailable.md`)
- [ ] Coverage of new code ≥ 80%

## 7. CONSTRAINTS
- All imports `src.` prefix
- DO NOT delete `models/ner-bert-bilstm-crf-v1/` — keep both available
- Add ARCBERT-NER to pipeline as optional path, NOT default (until P3T1 promotes it)
- DO NOT publicly share ARCBERT weights — only redistribute under original license
- BIOES tagging (same as English path)

## 8. DEPENDENCIES
- **Blocked by:** None (can be parallel with P1T1, P1T2, P1T4, P1T5)
- **Blocks:** P3T1 (final fine-tuning uses ARCBERT base)
- **Parallel-safe with:** All other P1 tasks

## 9. GOTCHAS
- ARCBERT may be on a Chinese university server — download may be slow/blocked. Fallback to SciBERT is documented and acceptable.
- ARCBERT was published on `bert-base-uncased` — ours used `bert-base-cased`. Tokenizer differences require re-tokenizing the annotations.
- If using SciBERT: tokenizer is `allenai/scibert_scivocab_uncased` with custom vocab — must use that exact tokenizer.
- MPS memory: batch 16 ok for `bert-base` size (~110M params).
- Expect 1–3 hour training run on MPS.
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md) § ML/training.
