# TASK: P1T2 — IndicBERT Integration — Agent-2

**Phase:** 1 | **Effort:** 1 day | **Priority:** P1

## 1. GOAL
Replace our custom bilingual training plan (A6) with the freely available, MIT-licensed IndicBERT from AI4Bharat (IIT Madras). Hindi RFQ understanding becomes plug-and-play.

## 2. CONTEXT
Read first:
- `src/nlp/lang_detect.py` — current language detection
- `src/nlp/pipeline.py` — where the bilingual model would plug in
- `config/constants.py` — entity types
- [docs/HYBRID_PLAN.md](../../../docs/HYBRID_PLAN.md) — why we're swapping
- [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)

IndicBERT references:
- HuggingFace: https://huggingface.co/ai4bharat/indic-bert
- GitHub: https://github.com/AI4Bharat/IndicBERT
- License: MIT
- Supports: Assamese, Bengali, English, Gujarati, Hindi, Kannada, Malayalam, Marathi, Oriya, Punjabi, Tamil, Telugu
- We only use English + Hindi.

Current state: our `lang_detect.py` exists but the bilingual model path (A6) is mostly stubbed. We replace that path with IndicBERT-based NER.

## 3. DELIVERABLES
- [ ] `src/nlp/ner/indic_ner.py` — IndicBERT NER wrapper
- [ ] `scripts/finetune_indic_ner.py` — fine-tune IndicBERT on our annotations (en+hi if any)
- [ ] `src/nlp/pipeline.py` — route Hindi/mixed-language docs to IndicBERT path
- [ ] `tests/unit/test_indic_ner.py` — ≥5 tests
- [ ] `docs/indicbert.md` — usage notes + license attribution
- [ ] `pyproject.toml` — add `huggingface-hub>=0.20` if not already there

## 4. STEPS
1. Read context files.
2. Verify HuggingFace model accessible: `python3 -c "from transformers import AutoTokenizer, AutoModel; tok = AutoTokenizer.from_pretrained('ai4bharat/indic-bert'); m = AutoModel.from_pretrained('ai4bharat/indic-bert'); print(m.config.hidden_size)"`
3. Implement `src/nlp/ner/indic_ner.py`:
   ```python
   class IndicNERInference:
       def __init__(self, model_dir: str | None = None):
           # If model_dir given (fine-tuned), load that; else load base ai4bharat/indic-bert
           ...
       def predict(self, text: str) -> list[EntitySpan]:
           # Tokenize → forward → decode BIOES → return EntitySpans
           ...
   ```
4. Fine-tuning script `scripts/finetune_indic_ner.py`:
   - Base: `ai4bharat/indic-bert`
   - Data: `data/annotations/` (English) + `data/annotations_hi/` (Hindi, if exists; else skip)
   - Output: `models/indic-ner-en-hi/`
   - Hyperparams: lr=3e-5, epochs=10, batch=16 (MPS), use BIOES labels from `config.constants`
   - Log per-language F1
5. Update `src/nlp/pipeline.py`:
   - In `NLPPipeline.__init__`, accept `enable_indic: bool = True`
   - When `enable_indic` and `lang_detect` returns 'hi' or 'mixed': route to `IndicNERInference`
   - Otherwise: existing English BERT-BiLSTM-CRF path
   - Falls back to English path if Indic model not loadable
6. Tests:
   - Test base IndicBERT loads (mark slow, allow skip if no network)
   - Test pipeline routing decision for English / Hindi / mixed text
   - Test graceful fallback when Indic model missing
   - Test `IndicNERInference.predict` returns `list[EntitySpan]` (mock model)
7. `docs/indicbert.md`:
   - What IndicBERT is, who made it, license
   - How we use it (just the path selection)
   - Performance expectations (Hindi F1 starts low, improves with fine-tuning on real Hindi annotations)

## 5. VERIFICATION
```bash
# Model accessible
$ python3 -c "from transformers import AutoTokenizer; tok = AutoTokenizer.from_pretrained('ai4bharat/indic-bert'); print(tok('समस्या परीक्षण', return_tensors='pt')['input_ids'].shape)"
EXPECT: torch.Size([1, N]) (no exception)

# Our wrapper loads
$ python3 -c "from src.nlp.ner.indic_ner import IndicNERInference; n = IndicNERInference(); r = n.predict('Supply 500 kg cement'); assert isinstance(r, list)"
EXPECT: no AssertionError

# Pipeline routes correctly
$ python3 -c "from src.nlp.pipeline import NLPPipeline; p = NLPPipeline(enable_indic=True); r = p.process('500 किलोग्राम सीमेंट आपूर्ति'); assert len(r.entities) >= 0"
EXPECT: no AssertionError

# Tests
$ python3 -m pytest tests/unit/test_indic_ner.py -v
EXPECT: ≥5 passed

# No regression
$ python3 -m pytest tests/unit tests/integration tests/golden --tb=no
EXPECT: same pass count or higher
```

## 6. ACCEPTANCE CRITERIA
- [ ] IndicBERT downloadable + usable from our code
- [ ] Pipeline routes Hindi/mixed text to IndicBERT path
- [ ] English text still uses existing model (no regression)
- [ ] Fallback works when IndicBERT not available (network issues, etc.)
- [ ] Coverage of new code ≥ 80%
- [ ] `docs/indicbert.md` cites MIT license + AI4Bharat attribution

## 7. CONSTRAINTS
- All imports `src.` prefix
- DO NOT remove the existing English BERT-BiLSTM-CRF model — keep both paths
- DO NOT bundle the IndicBERT weights in git — they download on first use
- License attribution required: AI4Bharat, IIT Madras, MIT License
- Use BIOES tagging (same as English path) — do NOT switch to BIO

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** P3T1 (final fine-tune will combine ARCBERT + IndicBERT outputs)
- **Parallel-safe with:** P1T1, P1T3, P1T4, P1T5

## 9. GOTCHAS
- IndicBERT is ALBERT-based, not BERT — uses slightly different tokenizer (SentencePiece)
- MPS-compatible (verified) but downloads ~150MB on first use
- Fine-tuning on small Hindi corpus may hurt English performance; keep models separate
- Don't expose `ai4bharat/indic-bert` HuggingFace identifier in user-facing docs — abstract as "Indic NER model"
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md) § ML/training for MPS device pattern
