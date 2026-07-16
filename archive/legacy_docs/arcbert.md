# ARCBERT Integration Notes

## Model Used: SciBERT (Fallback)

**ARCBERT** (`linjiarui/arcbert-base-cased`) was not available on HuggingFace Hub (returned 401 Unauthorized).

**SciBERT** (`allenai/scibert_scivocab_uncased`) was used as the fallback model.

SciBERT is a BERT model trained on scientific text (Papers with Code corpus), which may provide better generalization for construction/technical documents compared to general-domain BERT.

## Downloaded Model

Location: `models/arcbert-base/`

Files:
- `config.json`
- `pytorch_model.bin` (390MB)
- `vocab.txt`
- `model.safetensors` (also available from HuggingFace)

## Citation

```bibtex
@article{2020scibert,
  author={Iz Beltagy and Kyle Lo and Arman Cohan},
  title={SciBERT: A Pretrained Language Model for Scientific and Technical Text},
  journal={arXiv:1908.08996},
  year={2019}
}
```

## License

Apache 2.0 (same as BERT)

## Usage

```python
from transformers import AutoModel, AutoTokenizer
model = AutoModel.from_pretrained("models/arcbert-base")
tokenizer = AutoTokenizer.from_pretrained("models/arcbert-base")
```

## Fine-tuned Model

Location: `models/arcbert-ner-v1/`

Note: Fine-tuning only completed 1 epoch before timeout. See `results/arcbert_vs_baseline.json` for current metrics.
