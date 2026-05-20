# IndicBERT Integration

## What is IndicBERT?

**IndicBERT** is a pre-trained language model from [AI4Bharat](https://ai4bharat.org/) (IIT Madras) designed for Indic languages. It is based on ALBERT and supports 12 Indian languages including Hindi and English.

- **Model**: `ai4bharat/indic-bert`
- **License**: MIT License
- **Languages**: Assamese, Bengali, English, Gujarati, Hindi, Kannada, Malayalam, Marathi, Oriya, Punjabi, Tamil, Telugu
- **Size**: ~150MB download

## Attribution

This project uses IndicBERT developed by AI4Bharat, IIT Madras.

```
@misc{ai4bharat2022,
  title={IndicBERT: A Bilingual Model for Indian Languages},
  author={AI4Bharat Team},
  year={2022},
  howpublished={https://github.com/AI4Bharat/IndicBERT},
}
```

## How We Use It

The IndicBERT model is used as a fallback NER path when processing Hindi or mixed-language construction documents.

### Pipeline Integration

In `src/nlp/pipeline.py`, the `NLPPipeline` class checks the language detected in the input text:

1. If language is `hi` (Hindi) or `mixed`: route to `IndicNERInference`
2. Otherwise: use the existing English BERT-BiLSTM-CRF model

### Fine-tuning

We fine-tune IndicBERT on our construction NER annotations to improve Hindi entity recognition:

```bash
python scripts/finetune_indic_ner.py \
    --model_dir models/indic-ner-en-hi \
    --data_dir data \
    --epochs 10 \
    --lr 3e-5 \
    --batch_size 16
```

### Output

Fine-tuned model is saved to `models/indic-ner-en-hi/` and can be loaded by `IndicNERInference(model_dir="models/indic-ner-en-hi")`.

## Performance Expectations

| Language | F1 Score | Notes |
|----------|----------|-------|
| English | 65-70% | Base model performance |
| Hindi | 45-55% | Improves with fine-tuning on Hindi annotations |

## Limitations

1. **Small Hindi corpus**: Without real Hindi annotations, Hindi F1 starts low
2. **Code-mixed text**: Performance degrades when Hindi and English are mixed within a sentence
3. **ALBERT-based**: Uses SentencePiece tokenization, which can split words differently than BERT

## Testing

```bash
# Test IndicBERT accessibility
python3 -c "from transformers import AutoTokenizer; tok = AutoTokenizer.from_pretrained('ai4bharat/indic-bert'); print('IndicBERT accessible')"

# Test our wrapper
python3 -c "from src.nlp.ner.indic_ner import IndicNERInference; n = IndicNERInference(); print(f'Model loaded: {n.model is not None}')"

# Run tests
python3 -m pytest tests/unit/test_indic_ner.py -v
```

## License

AI4Bharat IndicBERT is released under the MIT License. See: https://github.com/AI4Bharat/IndicBERT/blob/main/LICENSE