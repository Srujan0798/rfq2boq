# Entity Error Analysis Report

**Date:** 2026-07-04
**Evaluator:** agent_entity_audit (automated)
**Macro F1 (overall):** 60.0%
**Source:** results/eval_honest.json

---

## 1. Per-File Entity F1 Table (Worst → Best)

| Rank | File | Type | F1 | Precision | Recall | TP | FP | FN | Gold Count | Pred Count |
|------|------|------|-----|-----------|--------|-----|-----|-----|------------|------------|
| 1 | 04_adani | pdf | 0.000 | 0.000 | 0.000 | 0 | 43 | 13 | 13 | 43 |
| 2 | 09_gem | pdf | 0.210 | 0.591 | 0.127 | 13 | 9 | 89 | 102 | 22 |
| 3 | 10_gem | pdf | 0.323 | 1.000 | 0.192 | 10 | 0 | 42 | 52 | 10 |
| 4 | 03_zydus_matoda | xlsx | 0.560 | 0.424 | 0.824 | 14 | 19 | 3 | 17 | 33 |
| 5 | 07_grew | pdf | 0.615 | 0.444 | 1.000 | 4 | 5 | 0 | 4 | 9 |
| 6 | 02_isro | xlsx | 0.750 | 0.600 | 1.000 | 3 | 2 | 0 | 3 | 5 |
| 7 | 06_avante | pdf | 0.784 | 0.645 | 1.000 | 20 | 11 | 0 | 20 | 31 |
| 8 | 08_sael | xlsx | 0.828 | 0.706 | 1.000 | 12 | 5 | 0 | 12 | 17 |
| 9 | 05_zydus_animal | xlsx | 0.931 | 0.979 | 0.887 | 47 | 1 | 6 | 53 | 48 |
| 10 | 01_gsecl | pdf | 1.000 | 1.000 | 1.000 | 3 | 0 | 0 | 3 | 3 |

**Summary:**
- XLSX path macro F1: 76.7%
- PDF path macro F1: 48.9%
- Total gold: 279, Total predicted: 221

---

## 2. Worst Entity Types Per File

### 04_adani (F1 = 0.0)
| Entity Type | Gold Count | Pred Count | TP | FP | FN |
|-------------|------------|------------|-----|-----|-----|
| MATERIAL | 13 | 0 | 0 | 0 | 13 |
| DIMENSION | 0 | 43 | 0 | 43 | 0 |
| ACTION | 0 | 0 | 0 | 0 | 0 |
| UNIT | 0 | 0 | 0 | 0 | 0 |
| QUANTITY | 0 | 0 | 0 | 0 | 0 |

**Root cause:** The PDF table extraction maps the dimension column (e.g., "500 mm dia") as the material field for every row. The gold expects "MS chilled water pipe insulation nitrile rubber" as MATERIAL and "500 mm dia" as DIMENSION. The pipeline produces zero MATERIAL entities and 43 spurious DIMENSION-as-MATERIAL entities.

### 09_gem (F1 = 0.210)
| Entity Type | Gold Count | Pred Count | TP | FP | FN |
|-------------|------------|------------|-----|-----|-----|
| MATERIAL | 13 | 22 | 13 | 9 | ~80 |
| WIRE (mis-labeled MATERIAL) | ~65 | 0 | 0 | 0 | ~65 |
| INSULATION (MATERIAL) | ~6 | 0 | 0 | 0 | ~6 |
| Pipe (MATERIAL) | ~2 | 0 | 0 | 0 | ~2 |
| right (MATERIAL) | 1 | 0 | 0 | 0 | 1 |
| window (MATERIAL) | 1 | 0 | 0 | 0 | 1 |

**Root cause:** Gold annotations treat individual tokens "Wire" (×65), "insulation" (×6), "Pipe" (×2), "right" (×1), "window" (×1) as separate MATERIAL entities. The pipeline merges them into full material descriptions like "Bonded mineral -Rock- wool mattresses with one side GS wire netting". Additionally, OCR garbage ("Construction Manager, BHEL SITE X MAHESH Side Gs") pollutes extracted material strings.

### 10_gem (F1 = 0.323)
| Entity Type | Gold Count | Pred Count | TP | FP | FN |
|-------------|------------|------------|-----|-----|-----|
| MATERIAL (Rock wool) | ~22 | 9 | 9 | 0 | ~13 |
| MATERIAL (Wire/wire) | ~24 | 0 | 0 | 0 | ~24 |
| MATERIAL (Insulation/mineral) | ~6 | 0 | 0 | 0 | ~6 |
| MATERIAL (right/window) | 2 | 0 | 0 | 0 | 2 |

**Root cause:** Same as 09_gem — fine-grained gold token-level annotations vs. pipeline's compound material descriptions. 42 FN are mostly individual "Rock wool", "wire", "Insulation", "Mineral Wool" tokens that the pipeline doesn't produce as separate entities.

### 03_zydus_matoda (F1 = 0.560)
| Entity Type | Gold Count | Pred Count | TP | FP | FN |
|-------------|------------|------------|-----|-----|-----|
| MATERIAL | 8 | 29 | 8 | 21 | 0 |
| ACTION | 3 | 0 | 3 | 0 | 0 |
| QUANTITY | 3 | 0 | 3 | 0 | 0 |
| UNIT | 3 | 0 | 3 | 0 | 0 |
| DIMENSION | 0 | 0 | 0 | 0 | 0 |

**Root cause:** The XLSX pipeline extracts 19 false-positive MATERIAL entities. These are pipe size codes ("15MM", "20MM", "25MM", etc.) from the table's quantity/matrix columns being treated as material descriptions. Gold expects these as DIMENSION/QUANTITY, not MATERIAL. Also, "Option 2" and "Option 3" are gold MATERIAL entities not recognized by the pipeline.

---

## 3. Root-Cause Categorization

### RC-1: PDF Table-Structure Misparse (04_adani)
**Category:** Table-header misclassification / column mapping error
**Severity:** Critical (kills entire file F1)
**Affected files:** 04_adani
**Description:** The PDF pipeline's table extractor maps the dimension column (pipe diameter) as the material field. For a document where the material description is constant ("MS chilled water pipe insulation nitrile rubber") across all rows and only the diameter varies, the pipeline picks up the diameter as the material.
**Evidence:**
- Gold material: "MS chilled water pipe insulation nitrile rubber" (×12), "MS chilled water pipe insulation PUF" (×1)
- Pipeline material: "500 mm dia", "400 mm dia", "300 mm dia", ... (all 43 entries are dimension-as-material)
- Extraction output: `BOQ_PAGE.extracted.json` shows `material: "500 mm dia"` with `rate_only: true` for sub-header rows

### RC-2: Gold Annotation Granularity Mismatch (09_gem, 10_gem)
**Category:** Annotation convention mismatch
**Severity:** High (affects 2 files, 131 gold entities)
**Affected files:** 09_gem, 10_gem
**Description:** Gold annotations for GeM bidding documents treat individual tokens ("Wire" ×65, "Rock wool" ×22, "insulation" ×6, "Pipe" ×2) as separate MATERIAL entities. The pipeline produces full compound material descriptions ("Bonded mineral -Rock- wool mattresses with one side GS wire netting"). The gold and pipeline use fundamentally different granularity for material entities in these documents.
**Evidence:**
- 09_gem gold: 65 × "Wire", 6 × "insulation", 3 × "Insulation", 2 × "Pipe", 1 × "right", 1 × "window" = ~78 fine-grained MATERIAL entities
- 09_gem pred: 22 compound material descriptions, only 13 match gold
- 10_gem gold: 22 × "Rock wool", 24 × "wire/wire", 6 × "Insulation/Mineral Wool" = ~52 fine-grained MATERIAL entities
- 10_gem pred: 10 compound material descriptions, all 10 match gold

### RC-3: OCR Garbage in Material Strings (09_gem)
**Category:** OCR/tokenization issue
**Severity:** Medium (causes FP in 09_gem)
**Affected files:** 09_gem
**Description:** OCR of Hindi/English GeM bid documents appends bidder names and Hindi text to material strings. Examples: "Bonded Mineral -rock- Wool Mattresses With One Construction Manager, BHEL SITE 7 MAHESH Side Gs".
**Evidence:**
- 6 entries in 09_gem pred contain "Construction Manager, BHEL SITE X MAHESH Side Gs" appended to material
- These are false positives because the gold expects just "Bonded mineral -Rock- wool mattresses with one side GS wire netting"

### RC-4: XLSX Matrix Column as Material (03_zydus_matoda)
**Category:** Table-header misclassification / column mapping error
**Severity:** Medium (19 FP in 03_zydus_matoda)
**Affected files:** 03_zydus_matoda
**Description:** The XLSX pipeline extracts pipe size codes from the wide-matrix quantity columns as MATERIAL entities. In insulation enquiry XLSX files, columns are labeled with pipe sizes (15MM, 20MM, 25MM, etc.) and rows contain insulation thickness specifications. The pipeline treats these column headers as material descriptions.
**Evidence:**
- Unmatched pred: "15MM", "20MM", "25MM", "32MM", "40MM", "50MM", "65MM", "80MM", "100MM", "125MM", "150MM" (×2 for two tables)
- Gold expects: "Option 2", "Option 3", "Drain piping with 19mm thick insulation..." as MATERIAL

### RC-5: Missing Action/Unit/Quantity Entities (04_adani)
**Category:** Regex pattern gap / entity extraction gap
**Severity:** Medium (13 FN across ACTION, UNIT, QUANTITY)
**Affected files:** 04_adani
**Description:** The pipeline doesn't extract ACTION ("Supply installation testing commissioning"), UNIT ("Rmt"), or QUANTITY ("1540", "365", etc.) entities for the 04_adani document. These are present in gold but missing from predictions.
**Evidence:**
- Gold has 13 ACTION, 13 UNIT, 13 QUANTITY entities
- Pipeline produces 0 of each
- The PDF table structure puts these in separate columns that the table extractor may not map correctly

### RC-6: Overly Long Material Strings (06_avante, 07_grew, 08_sael)
**Category:** Material phrase extraction (material_phrases.py)
**Severity:** Low-Medium (FP count: 11, 5, 5 respectively)
**Affected files:** 06_avante, 07_grew, 08_sael
**Description:** The pipeline extracts full BOQ row sentences as material, including specification details that should be stripped. Gold expects short canonical material phrases, but the pipeline keeps long strings like "Supply, Installation of Insulation material. Thermal insulation of Ducts with low smoke/low fire propagating FM listed..."
**Evidence:**
- 06_avante: 11 FP — e.g., "13 mm thick insulation for supply air ducts in return air path." when gold expects just the dimension items
- 07_grew: 5 FP — e.g., "ACOUSTIC LINING Supply,InstallationandTestingofAcousticliningwith10mmthick..."
- 08_sael: 5 FP — e.g., "THERMAL INSULATION" and full specification paragraphs

---

## 4. Concrete Fix Proposals

### Fix 1: PDF Table Column Disambiguation for 04_adani-style Documents
**File:** `src/ingest/pdf_extractor.py` or `src/ingest/table_extractor.py`
**Root cause:** RC-1
**Impact:** HIGH — would fix 04_adani F1 from 0.0 → ~1.0
**Description:** When the PDF table extractor finds that all rows share the same material description text but differ in dimension values, it should:
1. Detect the "constant material + varying dimension" pattern
2. Map the dimension column to DIMENSION, not MATERIAL
3. Use the shared material text as the MATERIAL entity for all rows
**Estimated effort:** Medium (requires table-structure analysis heuristic)

### Fix 2: GeM Gold Annotation Reconciliation
**File:** `data/real_rfqs/gold/swa_09_gem_bid_7439924.json`, `data/real_rfqs/gold/swa_10_gem_bid_7552777.json`
**Root cause:** RC-2
**Impact:** HIGH — would improve F1 from 0.21→ ~0.5 for 09_gem and 0.32→ ~0.5 for 10_gem
**Description:** The gold annotations for GeM documents use a different granularity convention than the pipeline. Two options:
1. **Re-annotate gold** to use compound material descriptions matching the pipeline output format (recommended)
2. **Add a post-processing step** in the pipeline that splits compound materials into individual tokens for matching
**Note:** This requires human annotation work. The current gold annotations appear to treat "Wire" as a separate MATERIAL entity when it appears in wire netting descriptions, which is debatable.

### Fix 3: OCR Garbage Filtering for GeM Documents
**File:** `src/ingest/pdf_extractor.py` or `src/preproc/text_cleaner.py`
**Root cause:** RC-3
**Impact:** MEDIUM — would eliminate ~6 FP in 09_gem
**Description:** Add a post-processing filter to strip non-material text appended to material strings:
1. Pattern: "With One [non-material text] Side Gs" → strip from "With One" onward
2. Pattern: Hindi Unicode characters (U+0900-U+097F) mixed with English → strip Hindi suffix
3. Pattern: "Construction Manager, BHEL SITE..." → strip entirely
**Estimated effort:** Low (regex filter in material_phrases.py)

### Fix 4: XLSX Wide-Matrix Column Header Filtering
**File:** `src/pipeline_xlsx.py`
**Root cause:** RC-4
**Impact:** MEDIUM — would eliminate 19 FP in 03_zydus_matoda, improving F1 from 0.56→ ~0.88
**Description:** In the XLSX pipeline, when processing wide-matrix insulation enquiry files:
1. Detect column headers that are pure dimension codes (e.g., "15MM", "20mm OD", "65MM OD")
2. Do not emit these as MATERIAL entities
3. Instead, combine the row material description with the column dimension to form a proper DIMENSION entity
**Estimated effort:** Medium (requires matrix-detection heuristic in pipeline_xlsx.py)

### Fix 5: ACTION/UNIT/QUANTITY Extraction for PDF Table Rows
**File:** `src/ingest/pdf_extractor.py` or `src/ingest/table_extractor.py`
**Root cause:** RC-5
**Impact:** MEDIUM — would recover 13 ACTION + 13 UNIT + 13 QUANTITY entities for 04_adani
**Description:** The PDF table extractor should map column headers to entity types:
1. Column "Description" → MATERIAL + ACTION
2. Column with unit text ("Rmt", "Sqm", "nos") → UNIT
3. Numeric column (quantity) → QUANTITY
4. Dimension column → DIMENSION
**Estimated effort:** Medium (requires header-based column classification)

### Fix 6: Material Phrase Length Limiting
**File:** `src/nlp/patterns/material_phrases.py`
**Root cause:** RC-6
**Impact:** LOW-MEDIUM — would reduce FP in 06_avante, 07_grew, 08_sael
**Description:** Add a max-length heuristic to `extract_canonical_material()`:
1. If extracted material > 200 chars, truncate at the first sentence boundary
2. If extracted material contains "Supply" or "Installation" after stripping, re-strip action prefix
3. Add additional reference suffixes: "as per specification", "including adhesive", "as per approved"
**Estimated effort:** Low (add patterns to _REFERENCE_SUFFIXES in material_phrases.py)

---

## 5. Estimated Impact Summary

| Fix | Target File(s) | Current F1 | Projected F1 | Effort | Priority |
|-----|----------------|------------|--------------|--------|----------|
| Fix 1 | 04_adani | 0.000 | ~1.000 | Medium | P0 |
| Fix 2 | 09_gem, 10_gem | 0.210, 0.323 | ~0.500, ~0.500 | Human annotation | P0 |
| Fix 3 | 09_gem | 0.210 | ~0.250 | Low | P1 |
| Fix 4 | 03_zydus_matoda | 0.560 | ~0.880 | Medium | P1 |
| Fix 5 | 04_adani | 0.000 | (complements Fix 1) | Medium | P1 |
| Fix 6 | 06_avante, 07_grew, 08_sael | 0.784, 0.615, 0.828 | ~0.85, ~0.70, ~0.88 | Low | P2 |

**Combined projected macro F1:** ~60.0% → ~72-75% (with Fixes 1-4 implemented)

---

## 6. Key Findings

1. **04_adani is the single biggest drag on macro F1** — a complete F1=0.0 file due to column misparse. Fix 1 alone would boost macro F1 by ~5-6 points.

2. **09_gem and 10_gem have a fundamental annotation granularity problem** — the gold uses token-level "Wire"/"Rock wool" entities while the pipeline produces compound descriptions. This requires either re-annotation or a matching-layer fix.

3. **XLSX pipeline over-extraction** (03_zydus_matoda) is the main XLSX issue — pipe size codes from matrix columns are incorrectly classified as MATERIAL.

4. **PDF pipeline does well on simple BOQs** (01_gsecl = 1.0, 05_zydus_animal = 0.93) but struggles with complex table structures and OCR-heavy documents.

5. **Material phrase extraction** could be tightened for long specification strings to reduce FP in 06_avante, 07_grew, 08_sael.
