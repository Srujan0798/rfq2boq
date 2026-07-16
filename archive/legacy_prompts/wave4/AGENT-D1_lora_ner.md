# TASK: Implement LoRA few-shot NER adapter — Agent-D1

## 1. GOAL
Add LoRA-based few-shot NER that fine-tunes the production BERT model on 20-50 gold annotations.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/nlp/ner/bert_ner.py` — BERT-BiLSTM-CRF model
- `src/nlp/ner/lazy_model.py` — lazy model loading
- `src/nlp/ner/trainer.py` — training utilities
- `data/real_rfqs/annotations/gold_annotations.json` — gold data
- `config/constants.py` — BIOES labels, EntityType

Current state:
- Production model: `models/rfq2boq-ner-final/` (synthetic-trained, F1=0.430)
- Real data F1: 0.213 (all-O collapse fixed but still low)
- Gold: ~20 documents, 413 entities
- Full retrain needs 1000+ examples — not feasible

## 3. DELIVERABLES
- [ ] `src/nlp/ner/lora_adapter.py` — LoRA wrapper for BERT-CRF
- [ ] `scripts/train_lora_ner.py` — training script
- [ ] `tests/unit/test_lora_ner.py` — tests
- [ ] Model checkpoint: `models/rfq2boq-ner-lora-v1/`

## 4. STEPS
1. Install peft: `pip install peft`
2. Create `src/nlp/ner/lora_adapter.py`:
   ```python
   from peft import LoraConfig, get_peft_model, TaskType
   from transformers import AutoModelForTokenClassification

   class LoRANERAdapter:
       def __init__(self, base_model_path: str, num_labels: int):
           self.base_model = AutoModelForTokenClassification.from_pretrained(
               base_model_path,
               num_labels=num_labels,
           )
           lora_config = LoraConfig(
               task_type=TaskType.TOKEN_CLS,
               r=16,
               lora_alpha=32,
               lora_dropout=0.1,
               bias="none",
               target_modules=["query", "value"],
           )
           self.model = get_peft_model(self.base_model, lora_config)
           self.model.print_trainable_parameters()

       def save(self, path: str):
           self.model.save_pretrained(path)

       def load(self, path: str):
           from peft import PeftModel
           self.model = PeftModel.from_pretrained(self.base_model, path)
   ```
3. Create `scripts/train_lora_ner.py`:
   - Load gold annotations (BIOES format)
   - Convert to HuggingFace Dataset
   - 80/10/10 split
   - Train with Trainer API, 20 epochs, early stopping
   - Save adapter to `models/rfq2boq-ner-lora-v1/`
4. Add tests

## 5. VERIFICATION
```bash
$ pip install peft
$ python3 scripts/train_lora_ner.py
EXPECT: Trains in <30 min, val F1 > 0.50

$ python3 -m pytest tests/unit/test_lora_ner.py -v
EXPECT: all pass

$ python3 -m pytest tests/unit/ --tb=no
EXPECT: All previously-passing tests still pass
```

## 6. ACCEPTANCE CRITERIA
- LoRA adapter trains in <30 min on MPS
- Val F1 ≥ 0.50 (vs current 0.213)
- MATERIAL F1 ≥ 0.40 (vs current 0.00)
- Adapter size <20 MB
- Base model unchanged
- All tests pass

## 7. CONSTRAINTS
- Python 3.11–3.13 (not 3.14)
- Use `src.` prefix
- BIOES tagging only
- Don't modify base model files in `models/rfq2boq-ner-final/`
- Type hints required

## 8. DEPENDENCIES
- Blocked by: A1 (clean gold needed), E1 (validation aligned)
- Blocks: D2
- Parallel-safe with: F1, F2, F3, F4

## 9. GOTCHAS
- `peft` may not be installed — add to `pyproject.toml` dependencies
- MPS memory limited — use batch_size=4, gradient_accumulation_steps=4
- Gold annotations may be imbalanced (many MATERIAL, few UNIT/DIMENSION) — use class weights or focal loss
- If gold is too noisy, LoRA will overfit — clean gold first (A1)
- `AutoModelForTokenClassification` may need `ignore_mismatched_sizes=True` if num_labels differs
- The base model was trained with a custom head (BiLSTM+CRF) — LoRA may only adapt the BERT encoder, not the CRF head. Test if this is sufficient.
