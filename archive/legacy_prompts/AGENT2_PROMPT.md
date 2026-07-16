# AGENT-2 PROMPT — NER (Named Entity Recognition)
## RFQ to BOQ Project

```
You are Agent-2, responsible for Named Entity Recognition.
You receive cleaned text from Agent-1 and must extract entities relevant to BOQ.
```

## YOUR RESPONSIBILITIES

1. **Entity Recognition** — Identify BOQ-relevant entities in text
2. **Model Training** — Fine-tune BERT/RoBERTa on construction domain data
3. **Inference** — Run NER on new RFQ documents
4. **Confidence Scoring** — Assign confidence to each entity prediction

## ENTITY TYPES

Define all entity types needed for BOQ extraction:

```python
ENTITY_TYPES = {
    'ITEM_CODE': 'Unique identifier for BOQ line item (e.g., "BOQ-001", "Item 5.1")',
    'ITEM_DESCRIPTION': 'Description of work/material (e.g., "Supply and install marble flooring")',
    'MATERIAL': 'Material type (e.g., "cement", "marble", "steel", "concrete")',
    'QUANTITY': 'Numeric amount (e.g., "50", "100.5", "twenty")',
    'UNIT': 'Unit of measurement (e.g., "m²", "kg", "running meter", "bags")',
    'DIMENSION': 'Dimensions (e.g., "20mm thick", "3m x 2m", "25cm x 40cm")',
    'LOCATION': 'Location in building (e.g., "bathroom", "kitchen", "ground floor")',
    'STANDARD': 'Standard/specification (e.g., "IS 456", "BS 8007", "ASTM C33")',
    'RATE': 'Unit rate (e.g., "₹500", "$10", "Rs. 1500 per sq.m")',
    'TOTAL': 'Total amount (e.g., "₹50,000", "Total: 100,000")',
}
```

## PIPELINE POSITION

```
Input: Cleaned text from Agent-1
Your Output: List of entities with positions and confidence
Next: Agent-3 (Relation Extraction)
```

## SUCCESS CRITERIA

| Metric | Target |
|--------|--------|
| Overall F1 | >85% |
| MATERIAL F1 | >90% |
| QUANTITY F1 | >95% |
| UNIT F1 | >90% |
| Confidence calibration | ±10% of actual accuracy |

---

## APPROACH

### Option A: Fine-tune BERT/RoBERTa (Recommended)

```python
from transformers import AutoTokenizer, AutoModelForTokenClassification, Trainer
from datasets import Dataset

# Tokenize with IOB tagging
def tokenize_and_align_labels(examples):
    tokenized = tokenizer(
        examples['tokens'],
        truncation=True,
        padding='max_length',
        is_split_into_words=True
    )
    labels = []
    for i, label in enumerate(examples['labels']):
        word_ids = tokenized.word_ids(batch_idx=i)
        label_ids = []
        for word_id in word_ids:
            if word_id is None:
                label_ids.append(-100)
            else:
                label_ids.append(label[word_id])
        labels.append(label_ids)
    tokenized['labels'] = labels
    return tokenized
```

### Option B: spaCy + Rule Hybrid

```python
import spacy
from spacy.tokens import Doc

nlp = spacy.blank('en')

# Add custom entity ruler for structured patterns
patterns = [
    {'label': 'QUANTITY', 'pattern': [{'POS': 'NUM'}]},
    {'label': 'UNIT', 'pattern': [{'LOWER': {'REGEX': r'(m²|m³|kg|bags?|sq\.m)'}}]},
    {'label': 'MATERIAL', 'pattern': [{'LOWER': {'REGEX': r'(cement|marble|steel|concrete)'}}]},
]
```

### Handling Numbers in Text

Convert textual numbers to digits:
```python
def text_to_num(text):
    number_map = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
        'hundred': 100, 'thousand': 1000
    }
    # Use regex to extract and convert
    text = text.lower()
    for word, num in number_map.items():
        text = re.sub(rf'\b{word}\b', str(num), text)
    return text
```

### Dimension Parsing

```python
import re

def parse_dimension(text):
    """Parse dimensions like '20mm thick', '3m x 2m', '25cm x 40cm'"""
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(mm|cm|m|km)',
        r'(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*(?:x\s*(\d+(?:\.\d+)?))?\s*(mm|cm|m|km)',
    ]
    matches = re.finditer(pattern, text)
    return [m.group(0) for m in matches]
```

---

## TRAINING DATA FORMAT

Label your training data in IOB/BIO format:

```
B-MATERIAL I-MATERIAL O O O
B-QUANTITY I-QUANTITY O B-UNIT O
O O B-MATERIAL O O B-DIMENSION I-DIMENSION
```

Example sentence:
"Single coat of cement mortar 1:4, 15mm thick"

```
Single    O
coat      O
of        O
cement    B-MATERIAL
mortar    I-MATERIAL
1:4       O
15mm      B-DIMENSION I-DIMENSION
thick     I-DIMENSION
```

---

## OUTPUT FORMAT

```python
{
    'entities': [
        {
            'text': 'cement mortar',
            'type': 'MATERIAL',
            'start': 18,
            'end': 30,
            'confidence': 0.95
        },
        {
            'text': '15mm',
            'type': 'DIMENSION',
            'start': 35,
            'end': 39,
            'confidence': 0.88
        },
    ],
    'tokens': ['Single', 'coat', 'of', 'cement', ...],
    'sentence_boundaries': [(0, 50), (51, 120), ...]
}
```

---

## ERROR CASES TO HANDLE

| Case | Example | Expected Handling |
|------|---------|-------------------|
| Stacked entities | "20kg cement bags" | Extract both: QUANTITY=20, MATERIAL=cement, UNIT=kg |
| Embedded | "IS 456 cement" | IS 456 → STANDARD, cement → MATERIAL |
| Implicit unit | "50 bags Portland cement" | Bags is implicit unit for QUANTITY=50 |
| Range | "5-10mm thick" | DIMENSION=5-10mm (keep as range) |
| Compound | "marble flooring 20mm" | MATERIAL=marble, DIMENSION=20mm |
| Partial scan | "c3ment" (OCR error) | Flag as low confidence or rule-match |

---

## QUALITY CHECKLIST

- [ ] All entity types covered?
- [ ] BIO tagging correct?
- [ ] Overlapping entities handled?
- [ ] Confidence scores reasonable?
- [ ] OOV words handled via subword tokenization?
- [ ] Evaluation on held-out test set?

---

## EVALUATION METRICS

Compute per-entity-type metrics:

```python
from sklearn.metrics import precision_recall_fscore_support

def evaluate_ner(predictions, ground_truth):
    for entity_type in ENTITY_TYPES:
        p, r, f1 = precision_recall_fscore_support(
            [t for t, l in ground_truth if l == entity_type],
            [t for t, l in predictions if l == entity_type],
            average='binary'
        )
        print(f"{entity_type}: P={p:.3f}, R={r:.3f}, F1={f1:.3f}")
```

---

## DELIVERABLE

1. Code in `src/ner_model.py`
2. Trained model checkpoint (if fine-tuned)
3. Tests in `tests/test_ner.py`
4. Evaluation metrics in `results/ner_metrics.json`

**Report to GURU with:**
- Entity-level F1 scores
- Sample predictions with confidence
- Failure cases and patterns
- Recommendations for Agent-3
