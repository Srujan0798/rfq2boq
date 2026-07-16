# TASK: Hindi Multilingual Support (English + Hindi ONLY) — Agent-1

**Wave:** 2 | **Tier:** A | **Priority:** P1

## 1. GOAL
Add Hindi-language support for Indian regional construction tenders. **Only English and Hindi** — no other languages. Many Indian RFQs mix Devanagari Hindi with English (technical terms, codes); the model must handle both.

## 2. CONTEXT
Read first:
- `data/annotations/train.json` — current English annotation format
- `config/constants.py` — entity/relation/label schemas (language-agnostic)
- `src/ontology/loader.py` — current English-only ontology
- `ui/app.py` — current Streamlit UI (English-only)
- [docs/conventions.md](../../../docs/conventions.md)

Current state: All training data, ontology, and UI are English-only. The model uses `bert-base-cased` (English-only).

## 3. DELIVERABLES
- [ ] `scripts/generate_synthetic_hindi.py` — generate 150 Hindi RFQ docs
- [ ] `data/synthetic_hi/` — generated Hindi PDFs + JSON
- [ ] `scripts/annotate_hindi.py` — BIOES-annotate Hindi docs
- [ ] `data/annotations_hi/train.json`, `val.json`, `test.json`
- [ ] `scripts/train_bilingual.py` — bilingual NER training
- [ ] `models/bilingual-ner-en-hi/` — trained model + metrics.json
- [ ] `src/nlp/lang_detect.py` — language detection (English / Hindi / mixed)
- [ ] `src/ontology/bilingual.py` — bilingual ontology overlay (Hindi translations for top 100 materials/standards/units/locations)
- [ ] `src/nlp/pipeline.py` — accepts/detects language, routes appropriately
- [ ] `ui/app.py` — language selector (English / Hindi)
- [ ] `ui/locales/en.json`, `ui/locales/hi.json` — UI strings
- [ ] `results/bilingual_metrics.json` — per-language F1
- [ ] `tests/unit/test_hindi_support.py` — minimum 8 tests

## 4. STEPS
1. Generate Hindi templates:
   - Translate top 50 English RFQ templates to Hindi using `Helsinki-NLP/opus-mt-en-hi` (local, no API cost)
   - Mix Devanagari + romanized Hindi (real-world tenders do this)
   - Keep technical codes/standards in English (IS 456, M20 grade) — bilingual reality
   - Generate 150 PDFs to `data/synthetic_hi/`
2. Annotate with BIOES:
   - Same 8 entity types (MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE)
   - Entity TEXT in Hindi; entity TYPES still English (MATERIAL, etc.)
   - Output to `data/annotations_hi/`
3. Implement language detector:
   - Count Devanagari Unicode chars (`ऀ-ॿ`)
   - If >20% → Hindi
   - If 5–20% → mixed (bilingual)
   - Else → English
4. Train bilingual model:
   - Base: `xlm-roberta-base` (not `bert-base-cased`)
   - Combined dataset: `data/annotations/` + `data/annotations_hi/`
   - Equal sampling
   - Save to `models/bilingual-ner-en-hi/`
   - Track per-language F1 separately
5. Bilingual ontology overlay:
   - Add Hindi translations for top 100 materials, standards, units, locations
   - Example: "cement" → "सीमेंट", "ground floor" → "भूतल", "kg" → "किलोग्राम"
   - Lookup supports either language
6. Pipeline integration:
   - Detect language on input
   - For English-only: use existing `bert-base-cased` model (faster)
   - For Hindi or mixed: use `xlm-roberta-base` bilingual model
   - Configurable via env var `RFQ2BOQ_FORCE_BILINGUAL`
7. UI:
   - Sidebar language toggle
   - Translate all UI strings via JSON locale files
8. Verification

## 5. VERIFICATION
```bash
# Hindi data generated
$ ls data/synthetic_hi/*.pdf | wc -l
EXPECT: ≥150

# Hindi annotations
$ python3 -c "import json; d = json.load(open('data/annotations_hi/train.json')); assert len(d) > 50; assert any('ऀ' <= c <= 'ॿ' for ex in d for tok in ex['tokens'] for c in tok)"
EXPECT: no AssertionError

# Language detection
$ python3 -c "from src.nlp.lang_detect import detect_language; assert detect_language('Supply cement') == 'en'; assert detect_language('सीमेंट की आपूर्ति') == 'hi'; assert detect_language('Supply सीमेंट 500 kg') == 'mixed'"
EXPECT: no AssertionError

# Bilingual model trained
$ ls models/bilingual-ner-en-hi/metrics.json models/bilingual-ner-en-hi/model.pt
EXPECT: both exist

# Per-language F1
$ python3 -c "import json; m = json.load(open('results/bilingual_metrics.json')); assert m['english_f1'] > 0.5 and m['hindi_f1'] > 0.3"
EXPECT: no AssertionError

# Pipeline routes correctly
$ python3 -c "from src.nlp.pipeline import NLPPipeline; p = NLPPipeline(); r_hi = p.process('500 किलोग्राम सीमेंट IS 456 के अनुसार'); assert len(r_hi.entities) > 0"
EXPECT: no AssertionError

# Ontology lookups bilingual
$ python3 -c "from src.ontology.bilingual import BilingualOntology; o = BilingualOntology(); assert o.lookup_material('cement') is not None; assert o.lookup_material('सीमेंट') is not None"
EXPECT: no AssertionError

# Tests
$ python3 -m pytest tests/unit/test_hindi_support.py -v
EXPECT: ≥8 passed

# No regression
$ python3 -m pytest tests/ --tb=no
EXPECT: same pass count or higher
```

## 6. ACCEPTANCE CRITERIA
- [ ] All Section 5 commands succeed
- [ ] Hindi F1 ≥ 0.35 (lower bar — first iteration on translated synthetic)
- [ ] English F1 does NOT regress more than 2% on bilingual model
- [ ] Mixed-language documents extract entities from both languages
- [ ] UI fully usable in Hindi (every visible string translated)
- [ ] Coverage of new code ≥ 80%

## 7. CONSTRAINTS
- **ONLY English + Hindi.** No Tamil, Marathi, Bengali, or other languages.
- All imports use `src.` prefix
- DO NOT translate entity TYPE names — they stay English (MATERIAL, QUANTITY, etc.)
- DO NOT replace the existing `bert-base-cased` model — add bilingual as additional model
- Forbidden: machine-translation API calls in production code paths (use offline models)
- DO NOT touch `config/constants.py`

## 8. DEPENDENCIES
- **Blocked by:** A0 (test fix)
- **Blocks:** None
- **Parallel-safe with:** A1, A2, A3, A4, A5, A7
- **Shared files:** `src/nlp/pipeline.py` (also A1, A3, A4, A5) — coordinate merge order

## 9. GOTCHAS
- Real Indian RFQs mix Hindi + English heavily — pure-Devanagari documents are rare. The bilingual model is the main use case
- `xlm-roberta-base` is multilingual; it handles 100+ languages — we deliberately train on only en+hi
- Hindi tokenization differs from English — `xlm-roberta-base` tokenizer handles it correctly
- Devanagari char range: `ऀ-ॿ` (standard Hindi)
- BIOES tags themselves stay English (`B-MATERIAL`, `S-QUANTITY`) — entity types are universal
- Helsinki-NLP/opus-mt-en-hi quality is decent but not perfect — manually review 10 generated docs before mass generation
- 150 Hindi docs is a starting point; real Hindi tender corpus would need 1000+
- UI: use `streamlit-i18n` or load JSON locale files manually; both work
