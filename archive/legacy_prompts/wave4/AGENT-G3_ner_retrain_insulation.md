# TASK: Retrain NER on Insulation Domain Data — Agent-G3

## 1. GOAL
Retrain the NER model (or train a LoRA adapter) on insulation-domain data so that F1 on real insulation tenders exceeds 0.50 (current: 0.213 on real, 0.43 production).

## 2. CONTEXT
Files to read FIRST (in order):
- `src/nlp/ner/lora_adapter.py` — existing LoRA adapter class (ready for training integration)
- `src/nlp/pipeline.py` — `_init_ner()` and `_load_lora_ner()` methods
- `scripts/train_lora_ner.py` — current stub (loads data but no training loop)
- `config/constants.py` — BIOES labels, entity types
- `data/annotations/` — existing BIOES-tagged training data
- `data/real_rfqs/swa_enquiries/` — the 10 SWA files (held-out validation set, DO NOT train on)
- `docs/ANNOTATION_GUIDELINES.md` — how to annotate correctly

Current state:
- Production model (`models/rfq2boq-ner-final/`) achieves ~0.43 F1 on real data, ~0.99 on synthetic
- The model was trained on generic construction (cement, concrete, steel) — not insulation
- LoRA adapter class exists but training script is a stub
- 10 SWA enquiries are STRICTLY held-out — train on other real gold only (~12 files from ireps, cpwd, etc.)
- Real gold needs cleaning (section headers/specs counted as MATERIAL)

## 3. DELIVERABLES
Create or modify EXACTLY these files:
- [ ] `scripts/train_lora_ner.py` — COMPLETE the training loop with HF Trainer, BIOES, 80/10/10 split, adapter save
- [ ] `scripts/prepare_insulation_training_data.py` — NEW: extract insulation-domain sentences from real RFQs and create BIOES annotations
- [ ] `src/nlp/ner/lora_adapter.py` — add `train()` method if not present; ensure `save()` works correctly
- [ ] `models/rfq2boq-ner-insulation-v1/` — trained LoRA adapter checkpoint (created by training script)
- [ ] `tests/unit/test_lora_ner.py` — tests for LoRA training, prediction, save/load

## 4. STEPS
1. Read context files (Section 2)
2. Audit existing real gold annotations in `data/annotations/` and `data/real_rfqs/`:
   - Find all insulation-related sentences
   - Clean annotations (remove section headers as MATERIAL, keep only actual BOQ items)
3. Use `scripts/clean_gold.py` (already exists) to clean dirty annotations
4. Create `scripts/prepare_insulation_training_data.py`:
   - Load all real RFQ annotations EXCEPT the 10 SWA enquiries
   - Filter for insulation-domain sentences (contain words like "insulation", "wool", "foam", "calcium silicate")
   - Output BIOES-format JSON ready for training
5. Complete `scripts/train_lora_ner.py`:
   - Load base model: `models/rfq2boq-ner-final/` or `bert-base-uncased`
   - Load prepared insulation training data
   - Split 80% train / 10% val / 10% test
   - Use `peft` LoRA config: r=16, lora_alpha=32, target_modules=["query", "key", "value"]
   - Train with HF Trainer: 3-5 epochs, batch_size=16, learning_rate=2e-4
   - Evaluate per-entity F1
   - Save adapter to `models/rfq2boq-ner-insulation-v1/`
6. Update `src/nlp/pipeline.py` to use insulation adapter when available
7. Add tests
8. Run verification (Section 5)

## 5. VERIFICATION
Run these commands. Each must produce the expected output:

```bash
# Training script runs without error
$ python3 scripts/train_lora_ner.py --data_dir data/annotations --output_dir models/rfq2boq-ner-insulation-v1 --epochs 3
EXPECT: completes, saves adapter to models/rfq2boq-ner-insulation-v1/

# Adapter loads and predicts
$ python3 -c "
from src.nlp.ner.lora_adapter import LoRANERAdapter
adapter = LoRANERAdapter.load('models/rfq2boq-ner-final', 'models/rfq2boq-ner-insulation-v1')
entities = adapter.predict('Supply and install 50mm thick mineral wool insulation for 150mm dia pipe as per IS 8183')
print('entities:', len(entities))
for e in entities: print(e)
"
EXPECT: >= 3 entities detected (MATERIAL: mineral wool, DIMENSION: 50mm, STANDARD: IS 8183)

# Tests pass
$ python3 -m pytest tests/unit/test_lora_ner.py -v
EXPECT: >= 5 passed, 0 failed

# No regressions
$ python3 -m pytest tests/unit/test_pipeline.py -v --tb=short
EXPECT: all existing tests pass
```

## 6. ACCEPTANCE CRITERIA
- [ ] Training script completes successfully
- [ ] LoRA adapter saved to `models/rfq2boq-ner-insulation-v1/`
- [ ] Adapter loads and predicts insulation entities correctly
- [ ] Per-entity F1 on held-out test set >= 0.50 (target: beat 0.43 production)
- [ ] MATERIAL recall specifically >= 0.60 (currently worst performing entity)
- [ ] All tests pass
- [ ] No ruff errors

## 7. CONSTRAINTS
- All imports use `src.` prefix
- BIOES tagging only
- Entity types from `config.constants.EntityType`
- Python 3.11+ syntax, type hints required
- DO NOT train on the 10 SWA enquiries — they are held-out validation
- DO NOT modify `config/constants.py`
- MPS device available, CUDA is not
- If `peft` or `datasets` not installed, install them in the venv (`.venv/`) not system-wide

## 8. DEPENDENCIES
- **Blocked by:** G2 (insulation ontology — provides vocabulary for data prep)
- **Blocks:** G4 (BOQ assembler improvements), P8T5 (full NER retrain)
- **Parallel-safe with:** G1
- **Shared files:** `src/nlp/pipeline.py`, `models/` directory

## 9. GOTCHAS
- The 10 SWA enquiries MUST NOT be in training data — verify by checking file paths
- `scripts/train_lora_ner.py` is currently a stub — you need to write the FULL training loop
- Base model may be large — MPS has 16GB shared memory, watch for OOM
- BIOES format: labels like `B-MATERIAL`, `I-MATERIAL`, `E-MATERIAL`, `S-UNIT`, etc.
- If `peft` is not installed: `pip install peft` inside `.venv`
- Real gold may have inconsistent quality — use `scripts/clean_gold.py` first
- Training on MPS may be slower than CPU for small batches — test both
