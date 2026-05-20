> **SUPERSEDED** — This file's code signatures are useful implementation guidance, but architectural decisions have been overridden by `plan/` frozen specs. See `docs/merge_decisions.md`. Key remaps: `src/nlp/` → `code/models/` + `code/patterns/`, BIO → BIOES, plain BERT → BERT-BiLSTM-CRF, entity names updated to plan/'s 8 types, relation names to UPPER_SNAKE.

# AGENT-2: ML / AI / NLP Specialist

## Role
You are responsible for the **NLP extraction engine** — the brain of the system. You build the BERT NER model, spaCy pattern matchers, relation extractor, and the unified NLP pipeline. Your output quality directly determines BOQ accuracy.

## Timeline: Weeks 3–4
## Depends On: AGENT-1 (needs annotated data + ontology + ingestion pipeline)

---

## Your Files & Ownership

```
src/nlp/
├── __init__.py
├── ner/
│   ├── __init__.py
│   ├── bert_ner.py           # BERT NER model definition + loading
│   ├── trainer.py            # Fine-tuning pipeline
│   ├── inference.py          # Batch/single NER inference
│   └── dataset.py            # Custom NER dataset (BIO format)
├── patterns/
│   ├── __init__.py
│   ├── entity_ruler.py       # spaCy EntityRuler configuration
│   ├── regex_patterns.py     # Regex for measurements, standards, quantities
│   └── dictionary.py         # Dictionary-based material/standard lookup
├── relations/
│   ├── __init__.py
│   ├── extractor.py          # Relation extraction engine
│   └── rules.py              # Domain-specific relation rules
└── pipeline.py               # Unified NLP pipeline (orchestrates everything)

scripts/
├── train_ner.py              # Training script (CLI entry point)
└── evaluate.py               # Evaluation script with metrics

notebooks/
├── 01_data_exploration.ipynb # Explore annotated data distribution
├── 02_ner_training.ipynb     # Interactive training + analysis
└── 03_evaluation.ipynb       # Detailed evaluation + error analysis
```

---

## What You Receive from AGENT-1

1. **Training data**: `data/annotated/train.json`, `val.json`, `test.json`
   - BIO-tagged tokens with entity labels
   - Relation triples per sentence
2. **Knowledge base**: `data/ontology/materials.json`, `standards.json`, `units.json`, `locations.json`
3. **Constants**: `config/constants.py` — `ENTITY_LABELS`, `BIO_LABELS`, `RELATION_TYPES`
4. **Ingestion pipeline**: `src/ingestion/` — produces clean text from PDFs

---

## Week 3 Tasks: NER Models + Pattern Matching

### Task 2.1: NER Dataset Class
**Create `src/nlp/ner/dataset.py`**

- Load BIO-tagged data from AGENT-1's annotated JSON files
- Tokenize with BERT tokenizer (handle subword alignment — BIO tags must align to subword tokens)
- Return PyTorch Dataset compatible with HuggingFace Trainer

```python
class NERDataset(torch.utils.data.Dataset):
    def __init__(self, data_path: str, tokenizer, max_length: int = 512):
        """Load BIO-tagged data, tokenize, align labels."""

    def __getitem__(self, idx) -> dict:
        """Return input_ids, attention_mask, labels."""

    @staticmethod
    def align_labels(tokens, labels, tokenizer):
        """Align BIO labels to BERT subword tokens."""
```

**Critical**: Subword alignment is the #1 source of bugs in token classification. When BERT splits "galvanized" into ["gal", "##van", "##ized"], only the first subtoken gets the B-/I- label; the rest get -100 (ignored in loss).

### Task 2.2: BERT NER Model
**Create `src/nlp/ner/bert_ner.py`**

- Wrap HuggingFace `AutoModelForTokenClassification`
- Base model: `bert-base-uncased` (or `distilbert-base-uncased` for speed)
- Number of labels = len(BIO_LABELS) from constants
- Support loading from pretrained checkpoint

```python
class ConstructionNER:
    def __init__(self, model_name: str = "bert-base-uncased", num_labels: int = None):
        """Initialize BERT for token classification."""

    def load(self, checkpoint_path: str):
        """Load fine-tuned model from disk."""

    def predict(self, text: str) -> list[Entity]:
        """Run NER inference on text, return Entity objects."""

    def predict_batch(self, texts: list[str]) -> list[list[Entity]]:
        """Batch NER inference."""
```

### Task 2.3: Training Pipeline
**Create `src/nlp/ner/trainer.py`**

- Use HuggingFace `Trainer` with `TrainingArguments`
- Training config:
  - Learning rate: 2e-5
  - Batch size: 16
  - Epochs: 5–10
  - Weight decay: 0.01
  - Evaluation strategy: per epoch
  - Save best model by F1
- Compute metrics: precision, recall, F1 (entity-level using `seqeval`)
- Save model + tokenizer to `config.MODEL_DIR`

```python
class NERTrainer:
    def __init__(self, model, train_dataset, val_dataset, output_dir: str):
        """Set up HuggingFace Trainer."""

    def train(self) -> TrainResult:
        """Fine-tune model, return metrics."""

    def evaluate(self, test_dataset) -> EvalResult:
        """Evaluate on test set, return per-entity metrics."""

    @staticmethod
    def compute_metrics(pred) -> dict:
        """Compute seqeval precision/recall/F1."""
```

### Task 2.4: NER Inference Module
**Create `src/nlp/ner/inference.py`**

- Load trained model once, reuse for all predictions
- Convert model output (BIO tags) back to Entity objects with spans
- Merge consecutive B-/I- tags into single entities
- Add confidence scores from softmax probabilities

```python
class NERInference:
    def __init__(self, model_dir: str):
        """Load trained model + tokenizer."""

    def extract_entities(self, text: str) -> list[Entity]:
        """Extract entities with spans and confidence."""

    def _bio_to_entities(self, tokens, tags, scores) -> list[Entity]:
        """Convert BIO tag sequence to Entity objects."""
```

### Task 2.5: Train the NER Model
**Create `scripts/train_ner.py`**

- CLI script that loads data, initializes model, runs training
- Log training metrics to console
- Save best model checkpoint
- Print final evaluation metrics

**Run training** and verify:
- F1 > 0.85 on test set (overall)
- Per-entity F1:
  - MATERIAL > 0.80
  - STANDARD > 0.90 (pattern-heavy, should be high)
  - QUANTITY > 0.90
  - UNIT > 0.95
  - LOCATION > 0.75
  - THICKNESS > 0.85
  - SPECIFICATION > 0.80
  - WORK_TYPE > 0.80

If F1 is below target: check annotation quality, add more training data, try longer training.

### Task 2.6: spaCy EntityRuler Patterns
**Create `src/nlp/patterns/entity_ruler.py`**

Build spaCy EntityRuler with patterns for structured/predictable entities:

```python
class ConstructionEntityRuler:
    def __init__(self, ontology_dir: str):
        """Load ontology and build spaCy patterns."""

    def build_patterns(self) -> list[dict]:
        """Generate spaCy pattern dicts from ontology."""

    def create_ruler(self, nlp) -> EntityRuler:
        """Add ruler to spaCy pipeline."""
```

Patterns to build:
- **STANDARD**: `IS \d{3,5}`, `ASTM [A-Z]\d+`, `BS EN \d+`, etc.
- **UNIT**: Match all aliases from units.json
- **QUANTITY**: `\d+(\.\d+)?` followed by a known unit
- **THICKNESS**: `\d+mm`, `\d+ mm thick`, `gauge \d+`
- **MATERIAL**: Match all material names + aliases from materials.json
- **SPECIFICATION**: `Grade \d+`, `M\d+`, `Fe \d+`

### Task 2.7: Regex Pattern Matcher
**Create `src/nlp/patterns/regex_patterns.py`**

Regex patterns for highly structured entities:

```python
PATTERNS = {
    "STANDARD": [
        r"IS\s*\d{3,5}",
        r"ASTM\s*[A-Z]\d+",
        r"BS\s*EN\s*\d+",
        r"DIN\s*\d+",
    ],
    "THICKNESS": [
        r"\d+(\.\d+)?\s*mm(\s*thick)?",
        r"gauge\s*\d+",
        r"\d+(\.\d+)?\s*inch(es)?",
    ],
    "QUANTITY": [
        r"\d+(\.\d+)?\s*(sqm|cum|rmt|kg|nos|m|meters?|litres?)",
    ],
}
```

### Task 2.8: Dictionary Lookup
**Create `src/nlp/patterns/dictionary.py`**

- Load ontology JSONs
- Build Aho-Corasick or simple trie for fast multi-pattern matching
- Return matches with entity type + confidence (1.0 for exact match, 0.8 for alias match)

---

## Week 4 Tasks: Relations + Unified Pipeline

### Task 2.9: Relation Rules
**Create `src/nlp/relations/rules.py`**

Define rules for linking entities into relations:

```python
RELATION_RULES = [
    {
        "type": "material_has_thickness",
        "head": "MATERIAL",
        "tail": "THICKNESS",
        "max_distance": 50,  # characters between entities
        "same_sentence": True,
    },
    {
        "type": "material_at_location",
        "head": "MATERIAL",
        "tail": "LOCATION",
        "max_distance": 100,
        "same_sentence": True,  # or same paragraph
    },
    {
        "type": "material_meets_standard",
        "head": "MATERIAL",
        "tail": "STANDARD",
        "max_distance": 80,
        "keywords": ["as per", "conforming to", "in accordance with", "complying with"],
    },
    {
        "type": "material_has_quantity",
        "head": "MATERIAL",
        "tail": "QUANTITY",
        "max_distance": 60,
        "same_sentence": True,
    },
    {
        "type": "material_has_spec",
        "head": "MATERIAL",
        "tail": "SPECIFICATION",
        "max_distance": 40,
        "same_sentence": True,
    },
    {
        "type": "work_uses_material",
        "head": "WORK_TYPE",
        "tail": "MATERIAL",
        "max_distance": 80,
        "same_sentence": True,
    },
]
```

### Task 2.10: Relation Extractor
**Create `src/nlp/relations/extractor.py`**

- Take entity list + original text
- Apply relation rules: proximity + sentence boundary + keyword matching
- Score each relation by distance and rule confidence
- Handle ambiguity: if multiple materials could link to one thickness, pick closest

```python
class RelationExtractor:
    def __init__(self, rules: list[dict]):
        """Initialize with relation rules."""

    def extract(self, entities: list[Entity], text: str, sentences: list[Sentence]) -> list[Relation]:
        """Extract relations between entities using rules."""

    def _check_rule(self, head: Entity, tail: Entity, rule: dict, text: str) -> float | None:
        """Check if a head-tail pair satisfies a rule. Return confidence or None."""
```

### Task 2.11: Unified NLP Pipeline
**Create `src/nlp/pipeline.py`**

This is the **master orchestrator** of all NLP components:

```python
class NLPPipeline:
    def __init__(self, model_dir: str, ontology_dir: str):
        """Load BERT NER, spaCy patterns, relation extractor."""

    def process(self, text: str, sections: list[DocumentSection] = None) -> ExtractionResult:
        """Full NLP extraction pipeline."""
        # 1. Run BERT NER on free-text sections → entities
        # 2. Run spaCy EntityRuler on all text → more entities
        # 3. Run regex patterns → more entities
        # 4. Merge + deduplicate entities (prefer higher confidence)
        # 5. Run relation extraction on merged entities
        # 6. Return ExtractionResult (entities + relations)

    def _merge_entities(self, bert_entities, pattern_entities, regex_entities) -> list[Entity]:
        """Merge entities from all sources, deduplicate overlaps."""
        # If two entities overlap in span:
        #   - Same label → keep higher confidence
        #   - Different labels → keep both if non-overlapping, else higher confidence

    def _route_by_section(self, sections: list[DocumentSection]):
        """Route free-text sections to BERT, structured to patterns."""
```

**Entity merge logic is critical**: When BERT and patterns both find an entity at the same span, you must resolve conflicts intelligently. Rules:
1. If same span + same label → keep higher confidence, note both sources
2. If same span + different label → flag for review, keep BERT (usually more contextual)
3. If overlapping but not identical spans → keep the longer span if it makes semantic sense

### Task 2.12: Evaluation Script
**Create `scripts/evaluate.py`**

- Load test data from AGENT-1
- Run NLP pipeline on test sentences
- Compute:
  - Per-entity precision, recall, F1
  - Overall micro/macro F1
  - Relation extraction accuracy (if ground truth relations available)
  - Confusion matrix per entity type
- Print formatted report
- Save metrics to `data/evaluation_results.json`

---

## Unit Tests You Must Write

```
tests/unit/
├── test_bert_ner.py          # Test model loading, prediction, entity extraction
├── test_patterns.py          # Test EntityRuler, regex, dictionary matching
├── test_relations.py         # Test relation rules, extraction, edge cases
└── test_pipeline.py          # Test unified pipeline, entity merging
```

Test scenarios:
- Simple sentence with one material + one standard → correct entities + relation
- Complex sentence with multiple materials → all extracted, correct relations
- Table row with material, qty, unit → pattern matcher handles correctly
- Overlapping entities from BERT and patterns → merge resolves correctly
- Sentence with no entities → empty result, no errors
- Very long text → no memory issues, reasonable time

---

## Dependencies You Need

```
torch>=2.0
transformers>=4.35
datasets>=2.14
seqeval>=1.2
spacy>=3.7
accelerate>=0.24      # For training
```

Download spaCy model: `python -m spacy download en_core_web_sm`

---

## Target Metrics

| Metric | Target | Action if Below |
|--------|--------|-----------------|
| Overall F1 | > 0.85 | Check annotations, add data, more epochs |
| MATERIAL F1 | > 0.80 | Add more material variations to training |
| STANDARD F1 | > 0.90 | Patterns should catch most — check regex |
| QUANTITY F1 | > 0.90 | Pattern-heavy — check regex coverage |
| UNIT F1 | > 0.95 | Dictionary match — check completeness |
| LOCATION F1 | > 0.75 | Hardest entity — may need more context |
| Relation accuracy | > 0.75 | Tune distance thresholds, add keywords |

---

## Definition of Done

- [ ] BERT NER model fine-tuned and saved to `MODEL_DIR`
- [ ] Overall test F1 > 0.85
- [ ] spaCy EntityRuler handles all standard/unit/measurement patterns
- [ ] Regex patterns cover Indian, American, British, European standards
- [ ] Dictionary lookup matches all materials + aliases from ontology
- [ ] Relation extractor links entities with > 0.75 accuracy
- [ ] Unified pipeline orchestrates BERT + patterns + relations
- [ ] Entity merge logic resolves conflicts correctly
- [ ] All unit tests pass
- [ ] Evaluation script produces clean metrics report
- [ ] Notebooks document training curves and error analysis

---

## Handoff to AGENT-3

When you're done, AGENT-3 needs:
1. `src/nlp/pipeline.py` — the `NLPPipeline` class with a `process(text) -> ExtractionResult` method
2. Trained model saved in `MODEL_DIR`
3. `data/evaluation_results.json` — metrics for documentation
4. The `ExtractionResult` contains `entities: list[Entity]` and `relations: list[Relation]`

AGENT-3 will consume your `ExtractionResult` to assemble BOQ line items.
