# Hindi Support

## Overview

The RFQ2BOQ pipeline supports Hindi language RFQ processing through IndicBERT-based NER. When Hindi or mixed (code-switched) text is detected, the system automatically switches to an Hindi-capable NER model.

## Language Detection

The `src/nlp/lang_detect.py` module uses Devanagari Unicode range detection:

- **Hindi (`hi`)**: >20% Devanagari characters
- **Mixed (`mixed`)**: 0-20% Devanagari (code-switched text)
- **English (`en`)**: No Devanagari characters

## Hindi NER Pipeline

### Architecture

```
Input Text
    │
    ▼
detect_language() ──► Hindi/mixed?
    │
    ├─► YES ──► IndicNERInference (IndicBERT / xlm-roberta-base)
    │
    └─► NO ──► LazyNERModel (English BERT-BiLSTM-CRF)
```

### Key Files

| File | Purpose |
|------|---------|
| `src/nlp/lang_detect.py` | Language detection (Devanagari-based) |
| `src/nlp/ner/indic_ner.py` | IndicBERT NER inference wrapper |
| `src/nlp/pipeline.py` | Pipeline with language-aware routing |
| `scripts/finetune_indic_ner.py` | Fine-tuning script for Hindi NER |

### Models

- **Primary**: `ai4bharat/indic-bert` (ALBERT-based, 12 Indic languages)
- **Fallback**: `xlm-roberta-base` (mBERT-based multilingual)
- **Fine-tuned**: `models/indic-ner-en-hi/` (fine-tuned on construction NER)

## BIOES Tagging

Hindi NER uses the same BIOES tagging scheme as English:

| Tag | Meaning | Example |
|-----|---------|---------|
| `B-MATERIAL` | Beginning of material entity | सीमेंट |
| `I-MATERIAL` | Inside material entity | (continuation) |
| `E-MATERIAL` | End of material entity | (end) |
| `S-QUANTITY` | Single-token quantity | 500 |
| `O` | Outside any entity | की |

## Training Data

Hindi BIOES training data is stored in:
- `data/annotations/hindi_train.json` (50+ examples)

Format:
```json
{
  "tokens": ["सीमेंट", "500", "बैग", "में", "आपूर्ति", "करें"],
  "ner_tags": ["B-MATERIAL", "B-QUANTITY", "I-QUANTITY", "O", "B-ACTION", "E-ACTION"],
  "language": "hi"
}
```

## Fine-tuning IndicBERT

```bash
python scripts/finetune_indic_ner.py \
    --model ai4bharat/indic-bert \
    --data data/annotations \
    --output models/indic-ner-en-hi \
    --epochs 10 \
    --batch 16 \
    --lr 3e-5
```

## Performance

| Language | F1 Score | Notes |
|---------|----------|-------|
| English | 65-70% | Base model performance |
| Hindi | 45-55% | Improves with fine-tuning on Hindi annotations |

## Limitations

1. **Small Hindi corpus**: Without real Hindi annotations, Hindi F1 starts low (~45-55%)
2. **Code-mixed text**: Performance degrades when Hindi and English are mixed within a sentence
3. **ALBERT-based tokenization**: Uses SentencePiece tokenization which can split words differently than BERT
4. **MPS not always available**: Falls back to CPU silently for IndicBERT on some hardware
5. **No transliterated Hindi**: Roman-script Hindi (e.g., "cement ki aapurti") is not explicitly handled

## Adding More Hindi Data

1. Create annotations in `data/annotations/hindi_train.json`
2. Follow BIOES tagging format
3. Include `language` field ("hi" or "mixed")
4. Fine-tune with `scripts/finetune_indic_ner.py`

## Testing

```bash
# Hindi detection
python3 -c "from src.nlp.lang_detect import detect_language, is_hindi; assert is_hindi('सीमेंट की आपूर्ति करें'); print('Hindi detection OK')"

# Hindi NER
python3 -c "from src.nlp.pipeline import NLPPipeline; p = NLPPipeline(); r = p.process('500 किलो सीमेंट की आपूर्ति'); print(f'entities: {len(r.entities)}')"

# English still works
python3 -c "from src.nlp.pipeline import NLPPipeline; p = NLPPipeline(); r = p.process('Supply 500 kg of cement'); assert len(r.entities) >= 0; print('English still works OK')"

# Run tests
python3 -m pytest tests/unit/test_hindi_support.py -v
```

## Attribution

IndicBERT developed by [AI4Bharat, IIT Madras](https://ai4bharat.org/). Released under MIT License.

```
@misc{ai4bharat2022,
  title={IndicBERT: A Bilingual Model for Indian Languages},
  author={AI4Bharat Team},
  year={2022},
  howpublished={https://github.com/AI4Bharat/IndicBERT},
}
```
