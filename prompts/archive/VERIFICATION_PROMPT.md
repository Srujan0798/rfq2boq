# VERIFICATION PROMPT — Line-by-Line Verification (RFQ2BOQ)
## For AI Orchestrators and Quality Controllers

```
You are the verification engine. You check EVERYTHING.
No code passes without your approval.
No output ships without your stamp.
```

## VERIFICATION WORKFLOW

```
For each component:
1. Read source file completely
2. Check each requirement line-by-line
3. Run tests
4. Report Pass/Fail with specific issues
5. No partial credit — either it works or it doesn't
```

---

## VERIFICATION 1: PDF PROCESSOR (`src/pdf_processor.py`)

### MUST HAVE:
- [ ] `extract_text(pdf_path)` function
- [ ] `extract_tables(pdf_path)` function
- [ ] `ocr_pdf(pdf_path)` function
- [ ] `detect_sections(text)` function
- [ ] `clean_text(text)` function

### CORRECTNESS CHECKS:
- [ ] pdfplumber used for native PDF text extraction
- [ ] pytesseract used for OCR
- [ ] Table extraction returns list of rows
- [ ] Section detection uses keyword/regex matching
- [ ] Text cleaning handles encoding issues

### EDGE CASES:
- [ ] Empty PDF returns empty string, not crash
- [ ] Scanned (image-only) PDF triggers OCR
- [ ] Encrypted PDF reports error gracefully
- [ ] Multi-column layout detection implemented
- [ ] Headers/footers excluded from body text

### PERFORMANCE:
- [ ] <5 seconds per page for text extraction
- [ ] <10 seconds per page for OCR
- [ ] Memory usage reasonable (<2GB for 100-page PDF)

---

## VERIFICATION 2: NER MODEL (`src/ner_model.py`)

### MUST HAVE:
- [ ] Entity types: MATERIAL, QUANTITY, UNIT, DIMENSION, LOCATION, STANDARD
- [ ] `predict_entities(text)` function
- [ ] `train_model(train_data)` function
- [ ] `load_model(path)` function
- [ ] Confidence scores in output

### CORRECTNESS CHECKS:
- [ ] BIO/IOB tagging scheme documented and consistent
- [ ] Tokenization aligns with model (BERT/RoBERTa wordpiece)
- [ ] Entity positions are character offsets
- [ ] Confidence scores in [0, 1] range

### TRAINING:
- [ ] Training data in correct format (tokens + labels)
- [ ] Validation split from training data
- [ ] Metrics computed per entity type
- [ ] Model checkpoint saved

### EVALUATION:
- [ ] Precision, Recall, F1 per entity type
- [ ] Overall micro/macro F1
- [ ] Test set is held-out (not training data)
- [ ] Results reproducible (random seed set)

---

## VERIFICATION 3: RELATION EXTRACTOR (`src/relation_extractor.py`)

### MUST HAVE:
- [ ] Relation types: HAS_QUANTITY, HAS_UNIT, HAS_MATERIAL, HAS_LOCATION, HAS_STANDARD
- [ ] `extract_relations(entities)` function
- [ ] `validate_entry(item)` function
- [ ] `cross_reference_kb(item)` function

### CORRECTNESS CHECKS:
- [ ] Relations extracted based on entity proximity
- [ ] Validation rules catch quantity=0, missing unit, etc.
- [ ] Knowledge base integration works
- [ ] Unresolved ambiguities flagged

### VALIDATION RULES:
- [ ] Quantity must be > 0
- [ ] Unit must be standard type
- [ ] Material-unit consistency checked
- [ ] Standard codes validated against KB

---

## VERIFICATION 4: BOQ GENERATOR (`src/boq_generator.py`)

### MUST HAVE:
- [ ] `map_to_boq(entities, relations)` function
- [ ] `generate_json(boq_entries)` function
- [ ] `generate_excel(boq_entries)` function
- [ ] Unit normalization function

### CORRECTNESS CHECKS:
- [ ] All BOQ fields populated correctly
- [ ] Item codes unique and sequential
- [ ] Total amount = quantity × unit_rate
- [ ] Unit normalization handles all variants

### OUTPUT:
- [ ] JSON schema valid
- [ ] Excel file opens without errors
- [ ] Confidence scores included
- [ ] Validation flags included

---

## VERIFICATION 5: END-TO-END PIPELINE (`experiments/run_pipeline.py`)

### MUST WORK:
```python
# Full pipeline test
rfq_path = 'samples/rfq_sample.pdf'
boq_json = run_pipeline(rfq_path)
boq_xlsx = json_to_excel(boq_json)

assert len(boq_json['items']) > 0
assert os.path.exists(boq_xlsx)
assert all(item['quantity'] for item in boq_json['items'])
```

### INTEGRATION CHECKS:
- [ ] Agent-1 → Agent-2 data flow works
- [ ] Agent-2 → Agent-3 data flow works
- [ ] Agent-3 → Agent-4 data flow works
- [ ] Error in any agent handled gracefully
- [ ] Processing continues after non-critical errors

---

## VERIFICATION 6: TESTS (`tests/`)

### REQUIRED TESTS:

**test_pdf_processor.py:**
- [ ] test_native_pdf_extraction
- [ ] test_scanned_pdf_ocr
- [ ] test_table_extraction
- [ ] test_section_detection
- [ ] test_text_cleaning
- [ ] test_empty_pdf_handling
- [ ] test_encrypted_pdf_error

**test_ner_model.py:**
- [ ] test_entity_prediction
- [ ] test_confidence_scores
- [ ] test_known_entities
- [ ] test_ambiguous_entities
- [ ] test_oov_handling

**test_relation_extractor.py:**
- [ ] test_has_quantity_relation
- [ ] test_has_unit_relation
- [ ] test_validation_catches_errors
- [ ] test_kb_cross_reference

**test_boq_generator.py:**
- [ ] test_json_output_valid
- [ ] test_excel_output_opens
- [ ] test_unit_normalization
- [ ] test_boq_completeness

**test_pipeline.py:**
- [ ] test_end_to_end_pipeline
- [ ] test_error_handling
- [ ] test_performance

---

## VERIFICATION 7: DOCUMENTATION

### MUST HAVE:
- [ ] README.md with setup instructions
- [ ] API documentation for each module
- [ ] Usage examples
- [ ] Known limitations
- [ ] Performance benchmarks

---

## VERIFICATION REPORT FORMAT

```
COMPONENT: [name]
STATUS: [PASS/FAIL]
ISSUES:
  - [Issue 1]
  - [Issue 2]
FIXES REQUIRED:
  - [Fix 1]
  - [Fix 2]
RETEST NEEDED: [Yes/No]
```

---

## FINAL APPROVAL

Only after ALL verifications pass:

```
PROJECT STATUS: READY FOR SUBMISSION

✅ PDF Processing: PASS
✅ NER Model: PASS
✅ Relation Extraction: PASS
✅ BOQ Generation: PASS
✅ Integration: PASS
✅ Tests: PASS
✅ Documentation: PASS

VERDICT: APPROVED
```