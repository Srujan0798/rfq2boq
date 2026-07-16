# Product Evaluation Report — Fair Assessment

**Date:** 2026-07-16
**Method:** Gold produced independently of prediction pipeline
  - Row-gold: transcribed from XLSX by `scripts/build_row_gold.py` (no pipeline imports)
  - Entity-gold: human-annotated `data/real_rfqs/gold/swa_*.json`
  - Predicted: `Pipeline().run()` on source XLSX

## Row-Level Match Rate (vs independent row-gold)
### 02_isro_vssc — ISRO VSSC (Incremental qty BOQ — aerospace facility)
- Row-gold rows: 4
- Predicted rows: 4
- Match rate: **100.0%**
  - TP: 4, FP: 0, FN: 0
  - Material precision: 100.0%
  - Material recall: 100.0%
  - Quantity within ±5%: 100.0%
  - Unit match: 100.0%

### 03_zydus_matoda_osd — Zydus Pharma Matoda (OSD facility insulation)
- Row-gold rows: 33
- Predicted rows: 33
- Match rate: **69.2%**
  - TP: 27, FP: 6, FN: 6
  - Material precision: 81.8%
  - Material recall: 81.8%
  - Quantity within ±5%: 100.0%
  - Unit match: 103.7%

### 05_zydus_animal_pharmez — Zydus Animal Health (Pharmez Ahmedabad expansion)
- Row-gold rows: 20
- Predicted rows: 20
- Match rate: **90.5%**
  - TP: 19, FP: 1, FN: 1
  - Material precision: 95.0%
  - Material recall: 95.0%
  - Quantity within ±5%: 100.0%
  - Unit match: 100.0%

### 08_sael — SAEL (Insulation enquiry)
- Row-gold rows: 16
- Predicted rows: 16
- Match rate: **100.0%**
  - TP: 16, FP: 0, FN: 0
  - Material precision: 100.0%
  - Material recall: 100.0%
  - Quantity within ±5%: 100.0%
  - Unit match: 100.0%

**Overall row-level match rate: 82.5%** (66/80)

## Notes
- Row matching: Levenshtein ratio ≥ 0.80 (material), ±5% tolerance (quantity), canonical unit match
- Row-gold is independent of Pipeline (build_row_gold.py does not import src.pipeline or BOQAssembler)
- Entity-gold is human-annotated; entity match = exact text equality (case-insensitive)
- 05_zydus_animal_pharmez row-gold: quantity = SUM of all system qty columns (multi-column sheet)
