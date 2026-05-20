# Onboarding Guide

## 15-Minute Getting Started

### 1. Setup (5 min)

```bash
# Clone and install
git clone https://github.com/your-org/rfq2boq.git
cd rfq2boq
pip install -e ".[dev]"

# Run quick test
python3 -c "from src.nlp.pipeline import NLPPipeline; print('OK')"
```

### 2. Try the API (5 min)

```bash
# Start API
PYTHONPATH=. uvicorn src.api.main:app --port 8000 &

# Test health
curl http://localhost:8000/api/health

# Try extraction
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"text":"Supply M25 concrete 450 cum at ground floor"}'
```

### 3. Process a PDF (5 min)

```bash
# Place a PDF in data/samples/
cp my_rfq.pdf data/samples/

# Run extraction via CLI
PYTHONPATH=. python3 scripts/demo.py data/samples/my_rfq.pdf

# View results
ls results/
```

## Architecture in 1 Diagram

```
                    ┌─────────────┐
                    │  RFQ PDF    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  PDFLoader  │
                    │  (pdfplumber│
                    │   + OCR)    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌───▼────┐ ┌────▼─────┐
       │  Layout     │ │ NLP    │ │ Ontology │
       │  Analyzer  │ │Pipeline│ │ Loader   │
       └──────┬──────┘ │        │ └────┬─────┘
              │        └────┬───┘      │
              │             │          │
              │        ┌────▼──────────▼──┐
              │        │   BERT-BiLSTM-CRF │
              │        │   NER Model       │
              │        └────┬─────────────┘
              │             │
              │        ┌────▼──────────────┐
              │        │  BOQ Row Builder  │
              │        │  + Rules + Ontology│
              │        └────┬─────────────┘
              │             │
       ┌──────▼──────┐      │
       │  Table      │      │
       │  Extractor  │      │
       └─────────────┘      │
                            │
                     ┌──────▼──────┐
                     │  Excel/JSON │
                     │  Export     │
                     └─────────────┘
```

## Key Files to Read First (in order)

1. **`src/pipeline.py`** — Top-level `Pipeline` class wiring ingest → NLP → domain → export. Start here to understand the flow end-to-end.

2. **`src/nlp/pipeline.py`** — `NLPPipeline` class. Shows how entities flow through NER → patterns → conflict resolution → relation extraction.

3. **`src/ontology/loader.py`** — `ConstructionOntology` class. Shows how materials, standards, units are loaded and queried.

4. **`src/domain/models.py`** — Pydantic models for `EntitySpan`, `BoqRow`, `ExtractionResult`, `IngestedDoc`.

5. **`config/constants.py`** — Entity types, relation types, section types (from `EntityType`, `RelationType`, `SectionType`).

## How to Add a New Entity Type

1. Add to `config/constants.py`:
```python
class EntityType(str, Enum):
    MATERIAL = "MATERIAL"
    # ... existing
    NEW_ENTITY = "NEW_ENTITY"
```

2. Add BIOES tags to `config/constants.py`:
```python
LABEL2ID = {
    # ... existing
    "B-NEW_ENTITY": N,
    "I-NEW_ENTITY": N+1,
    "E-NEW_ENTITY": N+2,
    "S-NEW_ENTITY": N+3,
}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}
```

3. Add to ontology JSON (e.g., `materials.json` → `new_entity_types.json`):
```json
{"new_entity_types": [{"name": "...", "aliases": ["..."]}]}
```

4. Update `src/nlp/patterns/` and `src/rules/` to handle the new entity.

5. Add unit tests in `tests/unit/`.

## How to Retrain

### 1. Generate synthetic data

```bash
PYTHONPATH=. python3 scripts/generate_synthetic.py --output data/synthetic/
```

### 2. Annotate with BIOES

```bash
PYTHONPATH=. python3 scripts/annotate_data.py \
  --input data/synthetic/train.json \
  --output data/annotations/train.json
```

### 3. Train model

```bash
PYTHONPATH=. python3 scripts/train_simple.py
```

### 4. Evaluate

```bash
PYTHONPATH=. python3 scripts/evaluate_real.py
```

### 5. Deploy

```bash
# Model saved to models/ner-bert-bilstm-crf-v1/model.pt
# Restart API to load new model
docker-compose restart api
```

## How to Debug

### Quick debug (print entities)

```python
from src.nlp.pipeline import NLPPipeline
p = NLPPipeline()
r = p.process("Your RFQ text here")
for e in r.entities:
    print(f"{e.type:12} | {e.text} | conf={e.confidence:.2f}")
```

### Debug NER model

```python
from scripts.train_simple import BERTBiLSTMNER
import torch
model = BERTBiLSTMNER('bert-base-cased', num_labels=33)
model.load_state_dict(torch.load('models/ner-bert-bilstm-crf-v1/model.pt'))
model.eval()
# Now inspect logits
```

### Check ontology loading

```python
from src.ontology import ConstructionOntology
ont = ConstructionOntology()
print(f"Materials: {len(ont._materials)}")
print(f"Standards: {len(ont._standards)}")
# Test lookup
mat = ont.lookup_material("M25 concrete")
print(f"Found: {mat}")
```

### Log analysis

```bash
# Search for errors
grep ERROR logs/app.log | tail -20

# Search for timing
grep "timing" logs/app.log | tail -20

# Search for specific extraction
grep "M25" logs/app.log
```

## File Structure Reference

```
rfq2boq/
├── src/
│   ├── api/main.py          # FastAPI app
│   ├── domain/models.py     # Pydantic models
│   ├── ingest/              # PDF extraction, OCR
│   ├── nlp/
│   │   ├── pipeline.py      # Main NLP pipeline
│   │   ├── ner/             # BERT NER model, trainer
│   │   └── patterns/        # Regex, gazetteer
│   ├── ontology/            # JSON KB + loader
│   └── preproc/             # Normalize, sentence, sections
├── scripts/
│   ├── train_simple.py      # Training script
│   ├── evaluate_real.py    # Real-world evaluation
│   └── demo.py              # Demo CLI
├── tests/
│   ├── unit/               # Unit tests
│   └── golden/             # Golden set tests
├── data/
│   ├── annotations/         # BIOES-annotated data
│   ├── real_rfqs/           # Real RFQ validation data
│   └── ontology/            # JSON KB
├── models/                  # Trained models
└── docs/                    # Documentation
```