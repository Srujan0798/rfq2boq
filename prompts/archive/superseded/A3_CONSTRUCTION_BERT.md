# TASK: ConstructionBERT Domain Pretraining — Agent-2

**Wave:** 2 | **Tier:** A | **Priority:** P1

## 1. GOAL
Continue MLM pretraining of BERT on a construction-domain corpus to bridge the vocabulary gap between general English and construction RFQ language. Expected lift: +3-5% F1 on real-world test set.

## 2. CONTEXT
Read first:
- `models/ner-bert-bilstm-crf-v1/` — current model trained from `bert-base-cased`
- `config/constants.py` — entity schema
- `results/real_world_metrics.json` — current real-world F1 (67%)
- [docs/conventions.md](../../docs/conventions.md)

Current state: NER uses vanilla `bert-base-cased`. Construction vocabulary (M20, Fe500, IS 2062, sqm, cum, etc.) is under-represented in pretraining.

## 3. DELIVERABLES
- [ ] `scripts/scrape_construction_corpus.py` — corpus collection script
- [ ] `scripts/prepare_corpus.py` — clean, dedupe (MinHash), sentence-split
- [ ] `scripts/pretrain_construction_bert.py` — MLM continuation training
- [ ] `scripts/finetune_construction_ner.py` — fine-tune NER on top
- [ ] `data/construction_corpus/raw/` — raw scraped docs
- [ ] `data/construction_corpus/processed/corpus.jsonl` — cleaned sentences
- [ ] `models/construction-bert-base/` — pretrained checkpoint
- [ ] `models/construction-ner-bilstm-crf-v1/` — fine-tuned NER
- [ ] `results/domain_pretrain_eval.json` — F1 vs vanilla BERT comparison
- [ ] `MODEL_CARD.md` — for HuggingFace upload
- [ ] `tests/unit/test_construction_bert.py` — at least 4 smoke tests

## 4. STEPS
1. **Collect corpus** (target ≥50k documents, ~500MB raw text):
   - Wikipedia construction articles (use `wikipedia-api`)
   - aboutcivil.org, theconstructor.org (respect robots.txt, 2s delay)
   - Public IS standards text where freely available
   - Scraped tenders from `data/real_rfqs/raw/` if any exist
   - Save to `data/construction_corpus/raw/`
2. **Preprocess**: `python3 scripts/prepare_corpus.py`
   - Strip HTML, deduplicate via MinHash (Jaccard > 0.8)
   - Sentence segmentation
   - Output: `data/construction_corpus/processed/corpus.jsonl` (one sentence per line)
3. **Continue pretraining**: `python3 scripts/pretrain_construction_bert.py --epochs 3 --batch 32 --lr 5e-5 --mlm-prob 0.15`
   - Start from `bert-base-cased`
   - Save to `models/construction-bert-base/`
   - Track perplexity per epoch
4. **Fine-tune NER**: `python3 scripts/finetune_construction_ner.py`
   - Same training data as current model (`data/annotations/`)
   - Use construction-bert-base as encoder
   - Same BERT-BiLSTM-CRF architecture
   - Save to `models/construction-ner-bilstm-crf-v1/`
5. **Evaluate**: compare vanilla-BERT NER vs construction-BERT NER
   - On synthetic test set
   - On real-world test set (`data/real_rfqs/test_gold/`)
   - Save deltas to `results/domain_pretrain_eval.json`
6. **Optional**: Upload to HuggingFace Hub if access available
7. Run verification

## 5. VERIFICATION
```bash
# Corpus exists with sufficient size
$ wc -l data/construction_corpus/processed/corpus.jsonl
EXPECT: ≥50000 (50k sentences)

# Pretrained model saved
$ ls models/construction-bert-base/config.json models/construction-bert-base/pytorch_model.bin
EXPECT: both exist

# Fine-tuned NER saved
$ ls models/construction-ner-bilstm-crf-v1/model.pt
EXPECT: exists

# Eval comparison written
$ python3 -c "import json; d=json.load(open('results/domain_pretrain_eval.json')); print(d['vanilla_bert_f1'], d['construction_bert_f1'])"
EXPECT: two floats; construction_bert_f1 should be ≥ vanilla_bert_f1

# Smoke test
$ python3 -c "from transformers import AutoModel, AutoTokenizer; m = AutoModel.from_pretrained('models/construction-bert-base'); t = AutoTokenizer.from_pretrained('models/construction-bert-base'); out = m(**t('IS 456 cement', return_tensors='pt')); print(out.last_hidden_state.shape)"
EXPECT: torch.Size([1, N, 768])

# Tests
$ python3 -m pytest tests/unit/test_construction_bert.py -v
EXPECT: ≥4 passed
```

## 6. ACCEPTANCE CRITERIA
- [ ] All Section 5 commands succeed
- [ ] `construction_bert_f1` on real-world test ≥ `vanilla_bert_f1` (any positive delta)
- [ ] Perplexity decreased on validation corpus (vs initial bert-base)
- [ ] Coverage of new code ≥ 80%
- [ ] No regression in existing tests
- [ ] `MODEL_CARD.md` includes: training data summary, sizes, license, intended use, limitations

## 7. CONSTRAINTS
- All imports use `src.` prefix
- DO NOT change `config/constants.py`
- DO NOT overwrite `models/ner-bert-bilstm-crf-v1/` — write to a new directory
- Respect site robots.txt for scraping
- License-compatible sources only (no paywalled or copyrighted material in corpus)

## 8. DEPENDENCIES
- **Blocked by:** A0 (test fix)
- **Blocks:** A4 (calibration — should run on best model)
- **Parallel-safe with:** A1, A2, A5, A6, A7
- **Shared files:** `src/nlp/pipeline.py` (if pointing to new default model)

## 9. GOTCHAS
- MPS memory limit (~8GB unified) — batch 32 may OOM. Drop to 16 if needed
- 500MB raw text → ~200M tokens — pretraining 3 epochs may take 4-8 hours on MPS
- If scraping blocked, use `wikipedia-api` Python package (no auth needed)
- Tokenizer must be saved alongside model
- Construction Wikipedia articles often have non-Latin chars (formulas, symbols) — preprocess to strip or normalize
- Real-world F1 baseline is 67% — even 2-3% lift is meaningful
- HuggingFace Hub upload requires `huggingface-cli login` — skip if no account
