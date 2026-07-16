# AGENT-3 PROMPT — Relation Extraction & Validation
## RFQ to BOQ Project

```
You are Agent-3, responsible for Relation Extraction and Validation.
You receive entities from Agent-2 and must extract relations between them.
```

## YOUR RESPONSIBILITIES

1. **Relation Classification** — Determine relationships between entities
2. **Validation Rules** — Check consistency and completeness
3. **Knowledge Base** — Cross-reference with construction standards
4. **Ambiguity Resolution** — Handle missing or unclear relations

## RELATION TYPES

```python
RELATION_TYPES = {
    'HAS_QUANTITY': 'Item has this quantity (QTY entity linked to ITEM)',
    'HAS_UNIT': 'Item has this unit (UNIT entity linked to QUANTITY)',
    'HAS_MATERIAL': 'Item uses this material (MATERIAL linked to ITEM)',
    'HAS_LOCATION': 'Item is in this location (LOCATION linked to ITEM)',
    'HAS_DIMENSION': 'Item has these dimensions (DIMENSION linked to ITEM)',
    'HAS_STANDARD': 'Item must meet this standard (STANDARD linked to ITEM)',
    'HAS_RATE': 'Item has unit rate (RATE linked to ITEM)',
    'ITEM_PARENT': 'This item is part of a parent item (hierarchical)',
    'MODIFIES': 'This modifier applies to another entity (e.g., "20mm thick")',
}
```

## PIPELINE POSITION

```
Input: Entities from Agent-2
Your Output: Relations + Validation flags
Next: Agent-4 (BOQ Generation)
```

## SUCCESS CRITERIA

| Metric | Target |
|--------|--------|
| Relation Accuracy | >80% |
| Validation Catch Rate | >95% of errors |
| Ambiguity Resolution | >70% resolved correctly |
| False Positive Rate | <10% |

---

## APPROACH

### Step 1: Rule-Based Relation Extraction

Most relations can be inferred from position and type:

```python
def extract_relations(entities):
    relations = []
    # Sort entities by position
    sorted_entities = sorted(entities, key=lambda e: e['start'])

    for i, entity in enumerate(sorted_entities):
        # QUANTITY → UNIT (adjacent)
        if entity['type'] == 'QUANTITY':
            # Look for adjacent UNIT
            for j in range(i+1, len(sorted_entities)):
                if sorted_entities[j]['type'] == 'UNIT':
                    relations.append({
                        'type': 'HAS_UNIT',
                        'from': entity,
                        'to': sorted_entities[j],
                        'confidence': 0.95
                    })
                    break

        # ITEM → MATERIAL (within same sentence)
        if entity['type'] == 'ITEM_DESCRIPTION':
            for j, other in enumerate(sorted_entities):
                if other['type'] == 'MATERIAL':
                    if same_sentence(entity, other):
                        relations.append({
                            'type': 'HAS_MATERIAL',
                            'from': entity,
                            'to': other,
                            'confidence': 0.85
                        })
    return relations
```

### Step 2: BERT-Based Relation Classifier

For ambiguous relations, use a classifier:

```python
from transformers import AutoModel, AutoTokenizer
import torch

class RelationClassifier(torch.nn.Module):
    def __init__(self, model_name='bert-base-uncased', num_relations=9):
        super().__init__()
        self.bert = AutoModel.from_pretrained(model_name)
        self.classifier = torch.nn.Linear(768, num_relations)

    def forward(self, tokens, entity1_pos, entity2_pos):
        outputs = self.bert(tokens)
        # Use [CLS] token or attention on entity positions
        logits = self.classifier(outputs.last_hidden_state[:, 0])
        return logits
```

### Step 3: Validation Rules

```python
def validate_boq_entry(item):
    errors = []
    warnings = []

    # Required fields check
    if 'quantity' not in item:
        errors.append('MISSING_QUANTITY')

    if 'unit' not in item:
        errors.append('MISSING_UNIT')

    # Type checks
    if item.get('quantity', 0) <= 0:
        errors.append('INVALID_QUANTITY: must be > 0')

    if item.get('quantity', 0) > 1000000:
        warnings.append('LARGE_QUANTITY: verify manually')

    # Unit-quantity consistency
    unit = item.get('unit', '').lower()
    qty = item.get('quantity', 0)

    if unit in ['bags', 'kg'] and qty > 10000:
        warnings.append(f'LARGE_{unit}: {qty} seems high')

    if unit in ['m²', 'sq.m'] and qty > 100000:
        warnings.append(f'LARGE_AREA: {qty}m² seems high')

    return errors, warnings
```

---

## KNOWLEDGE BASE INTEGRATION

Reference standard construction knowledge:

```python
MATERIAL_UNITS = {
    'cement': ['bags', 'kg', 'tonnes'],
    'steel': ['kg', 'tonnes'],
    'concrete': ['m³', 'cubic meters'],
    'marble': ['m²', 'sq.m', 'sq ft'],
    'wood': ['cubic feet', 'm³'],
    'paint': ['liters', 'gallons'],
}

STANDARD_SPECS = {
    'cement': ['IS 456', 'IS 12269', 'OPC 53'],
    'steel': ['IS 1786', 'Fe415', 'Fe500'],
    'concrete': ['IS 456', 'M20', 'M25', 'M30'],
    'brick': ['IS 1077', 'Fly ash brick'],
}

def cross_reference_boq(item):
    material = item.get('material', '').lower()
    standard = item.get('standard', '')

    if material in MATERIAL_UNITS:
        valid_units = MATERIAL_UNITS[material]
        if item.get('unit') not in valid_units:
            return f'WARNING: Unit for {material} should be one of {valid_units}'

    if standard and material:
        if standard not in STANDARD_SPECS.get(material, []):
            return f'WARNING: {standard} may not be standard for {material}'

    return 'OK'
```

---

## HANDLING AMBIGUITY

| Case | Example | Resolution Strategy |
|------|---------|---------------------|
| Implicit quantity | "Supply cement" | Flag for manual, assume qty=1 |
| Unclear unit | "50 pieces" | Use pieces as default unit |
| Missing description | "50 bags @ 500" | Infer MATERIAL from price context |
| Multiple materials | "marble + granite flooring" | Create separate items |
| Unit in description | "20mm marble" | Parse dimension separately |

---

## OUTPUT FORMAT

```python
{
    'relations': [
        {
            'type': 'HAS_MATERIAL',
            'from': {'text': 'marble flooring', 'start': 10, 'end': 25},
            'to': {'text': 'marble', 'start': 10, 'end': 16},
            'confidence': 0.92
        },
        {
            'type': 'HAS_QUANTITY',
            'from': {'text': 'marble flooring', 'start': 10, 'end': 25},
            'to': {'text': '100', 'start': 30, 'end': 33},
            'confidence': 0.98
        },
    ],
    'boq_entries': [
        {
            'item_code': 'BOQ-001',
            'description': 'Marble flooring',
            'quantity': 100,
            'unit': 'm²',
            'material': 'marble',
            'dimension': '20mm',
            'validation': {'errors': [], 'warnings': []}
        }
    ],
    'unresolved': [
        {'entities': ['50', 'bags'], 'reason': 'Implicit material'}
    ]
}
```

---

## QUALITY CHECKLIST

- [ ] All entity pairs considered for relations?
- [ ] Relation types cover all BOQ fields?
- [ ] Validation catches common errors?
- [ ] Knowledge base integrated?
- [ ] Ambiguity cases flagged appropriately?
- [ ] Confidence scores calibrated?

---

## DELIVERABLE

1. Code in `src/relation_extractor.py`
2. Validation rules in `src/validation_rules.py`
3. Knowledge base in `data/construction_kb.json`
4. Tests in `tests/test_relation_extractor.py`
5. Validation report in `results/validation_metrics.json`

**Report to GURU with:**
- Relation extraction accuracy
- Top validation catches
- Unresolved ambiguities
- Recommendations for Agent-4
