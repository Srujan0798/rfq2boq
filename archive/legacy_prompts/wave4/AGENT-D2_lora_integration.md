# TASK: Integrate LoRA NER adapter into pipeline — Agent-D2

## 1. GOAL
Wire LoRA adapter into `NLPPipeline` so it loads when `model_dir` points to LoRA checkpoint.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/nlp/pipeline.py` — `NLPPipeline._init_ner()`
- `src/nlp/ner/lazy_model.py` — lazy model loading
- `src/nlp/ner/lora_adapter.py` — from D1
- `tests/unit/test_pipeline.py` — existing tests

Current state:
- `_init_ner()` loads full model from `models/rfq2boq-ner-final/` or `ner-bert-bilstm-crf-v1/`
- No support for adapter-based models

## 3. DELIVERABLES
- [ ] `src/nlp/pipeline.py` — detect LoRA checkpoint and load adapter
- [ ] `src/nlp/ner/lazy_model.py` — support LoRA loading
- [ ] `tests/unit/test_pipeline.py` — test LoRA path

## 4. STEPS
1. Read context files
2. In `src/nlp/ner/lazy_model.py`, add:
   ```python
   def get_lora_model(base_model_path: str, adapter_path: str):
       from peft import PeftModel
       base = AutoModelForTokenClassification.from_pretrained(base_model_path)
       model = PeftModel.from_pretrained(base, adapter_path)
       return model
   ```
3. In `NLPPipeline._init_ner()`:
   ```python
   def _init_ner(self, model_dir: str | None) -> None:
       # ... existing logic ...

       # Check if model_dir contains LoRA adapter
       if model_dir and (Path(model_dir) / "adapter_config.json").exists():
           self._load_lora_ner(base_model_dir, model_dir)
           return

       # ... existing full model loading ...

   def _load_lora_ner(self, base_path: str, adapter_path: str) -> None:
       try:
           from src.nlp.ner.lazy_model import get_lora_model
           self.ner = get_lora_model(base_path, adapter_path)
       except Exception:
           self.ner = None
   ```
4. Add env var `RFQ2BOQ_LORA_MODEL` support in `config/settings.py` (if not already)
5. Add tests

## 5. VERIFICATION
```bash
$ python3 -m pytest tests/unit/test_pipeline.py -v
EXPECT: all pass + new LoRA test passes

$ python3 -c "
from src.nlp.pipeline import NLPPipeline
p = NLPPipeline(model_dir='models/rfq2boq-ner-lora-v1')
print(p.ner is not None)
"
EXPECT: True (if LoRA checkpoint exists)

$ python3 -m pytest tests/unit/ --tb=no
EXPECT: All previously-passing tests still pass
```

## 6. ACCEPTANCE CRITERIA
- LoRA checkpoint loads successfully
- Pipeline inference works end-to-end
- Fallback to base model if LoRA missing or peft not installed
- All tests pass
- Coverage ≥ 80%

## 7. CONSTRAINTS
- Don't break existing model loading
- Handle missing `peft` gracefully (fallback to base)
- Type hints required

## 8. DEPENDENCIES
- Blocked by: D1
- Blocks: None
- Parallel-safe with: E1, F1, F2, F3, F4

## 9. GOTCHAS
- `adapter_config.json` schema may vary across peft versions
- Base model path must be correct (the original `rfq2boq-ner-final/`)
- If peft is not installed, import will fail — catch ImportError and fallback
- Test with actual checkpoint before merging
