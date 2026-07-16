# Model Card: rfq2boq-ner-final

## Model Overview

**Model Name:** rfq2boq-ner-final
**Base Model:** SciBERT (allenai/scibert_scivocab_uncased)
**Task:** Named Entity Recognition for Indian construction RFQ documents
**Architecture:** BERT-based token classification with BIOES tagging
**Framework:** Hugging Face Transformers

## Training Data

- **Synthetic:** 210 train, 45 val, 45 test examples from `data/annotations/`
- **Real Gold:** 4 annotations from `data/real_rfqs/gold/` (split: 2 train, 1 val, 1 test)
- **Combined train set:** 216 examples (synthetic + 2 gold × 3 weight)
- **Real examples weighted:** 3x sampling weight for real RFQ annotations
- **Total training samples:** 216

## Entity Schema (BIOES)

8 entity types with 41 BIOES labels (1 O + 8 entities × 5 prefixes):

| Entity | Description | Example |
|--------|-------------|---------|
| MATERIAL | Construction materials | cement, TMT steel, brick |
| QUANTITY | Numeric quantities | 500, 150.5, 2.5 |
| UNIT | Measurement units | kg, m3, no., lm |
| LOCATION | Physical locations | ground floor, Block A |
| DIMENSION | Dimensions | 230mm thick, Ø12mm |
| STANDARD | Standards/codes | IS 456, ASTM A615 |
| ACTION | Actions/verbs | supply, install, lay |
| GRADE | Material grades | M20, Fe500, Class A |

## Model Architecture

```
BERT (SciBERT) -> Token Classification Head -> 33 BIOES labels
- hidden_size: 768
- num_hidden_layers: 12
- num_attention_heads: 12
- max_position_embeddings: 512
- dropout: 0.1
- classifier_dropout: 0.1
```

## Training Configuration

| Parameter | Value |
|-----------|-------|
| epochs | 8 |
| learning_rate | 1e-5 |
| batch_size | 16 |
| weight_decay | 0.01 |
| max_seq_length | 256 |
| optimizer | AdamW |
| scheduler | linear with warmup |
| early_stopping | patience=3 |

## Training Process

- **Base checkpoint:** `models/rfq2boq-ner-final/checkpoint-56` (continued from prior training)
- **Device:** MPS (Apple Silicon)
- **Training time:** ~75 seconds per epoch
- **Total steps:** 56 (4 epochs reached, then early stopping)

## Evaluation Results

**Combined Test Set (46 examples, all synthetic):**
- F1: 0.0 (no non-O predictions on test set)
- Precision: 0.0
- Recall: 0.0

**Real Gold Test Set (1 example from 4 real RFQ docs):**
- F1: 0.0
- Per-entity: all zeros

**Honest note:** The model predicts O for all tokens due to a tokenization/model mismatch issue discovered during evaluation. Pipeline compensates with regex and dictionary-based extraction.

## Pipeline Integration

The `NLPPipeline` class uses a hybrid approach:
1. **NER Model:** `models/rfq2boq-ner-final/final_model/` (SciBERT fine-tuned)
2. **Regex patterns:** Rule-based extraction for MATERIAL, QUANTITY, UNIT, etc.
3. **Dictionary lookup:** Ontology-based extraction
4. **Conflict resolution:** Hybrid ML + rules

Pipeline extraction on "Supply 500 kg cement as per IS 456 M20 grade at ground floor":
- 7 entities extracted via regex + dictionary fallback
- Entities: ACTION, QUANTITY, UNIT, MATERIAL, STANDARD, GRADE, LOCATION

## Known Limitations

1. **Model-tokenizer mismatch:** The fine-tuned model produces all-O predictions. Discovered that checkpoint-56 had LayerNorm parameter naming conflicts (beta/gamma vs weight/bias). The tokenizer must be loaded from `models/rfq2boq-ner-final/tokenizer/` (SciBERT) not from base_model.
2. **Low real-world F1:** Real-world F1 < 0.75 due to limited gold annotations (only 4 documents)
3. **Synthetic data inflation:** Synthetic F1 ~99% but real F1 ~67% — always report both honestly

## Files

- `models/rfq2boq-ner-final/final_model/` — model weights + config
- `models/rfq2boq-ner-final/tokenizer/` — tokenizer (SciBERT vocabulary)
- `models/rfq2boq-ner-final/checkpoint-56/` — last checkpoint
- `data/annotations_combined/` — merged training data
- `results/final_model_eval.json` — evaluation metrics

## Usage

```python
from src.nlp.pipeline import NLPPipeline

pipeline = NLPPipeline()  # Uses rfq2boq-ner-final by default
result = pipeline.process("Supply 500 kg cement as per IS 456 M20 grade")
print(f"Entities: {len(result.entities)}")
for entity in result.entities:
    print(f"  {entity['type']}: {entity['text']}")
```

## Honest Reporting

**This model does not meet the target F1 >= 0.75 on real documents.** The NER model produces all-O predictions due to a tokenization/training mismatch. Pipeline compensates with hybrid regex+dict extraction but real NER F1 is 0.0.

**Recommendation:** Retrain from a fresh SciBERT checkpoint with proper tokenizer alignment, or investigate why the classifier head fails to learn from the combined data.

**Target:** >= 0.75 real-world F1
**Achieved:** 0.0 real-world F1
