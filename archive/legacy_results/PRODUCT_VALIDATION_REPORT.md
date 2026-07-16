# Product Validation Report

**Date:** 2026-06-09
**Validation method:** Pipeline().run() on XLSX source → BOQRow list vs gold BOQ
**Matcher:** Levenshtein ratio ≥ 0.80 (material), ±5% tolerance (quantity), canonical unit match

## Overall Summary
| Metric | Value |
|---|---|
| Gold BOQ rows (total) | 17 |
| Predicted rows (total) | 14 |
| True positives | 14 |
| False positives | 0 |
| False negatives | 3 |
| **Overall match rate** | **82.4%** |

## 08_sael — SAEL
**Insulation enquiry**

- Gold BOQ rows: 17
- Predicted BOQ rows: 14
- Matched correctly (TP): 14
- Wrong material (>20% Lev): 0
- Wrong quantity (>5% off): 0
- Missed entirely (FN): 3
- **Match rate: 82.4%**
- Material precision: 100.0%
- Material recall: 82.4%

**Verdict: **SHIP IT****

### Per-row details (first 10)
| # | Gold Material | Predicted Material | Score | Qty Diff | Unit | Match? |
|---|---|---|---|---|---|---|
| 1 | THERMAL INSULATION | — | 0.55 | 100% | no | ✗ |
| 2 | Supply, Installation of Insulation mater... | — | 0.49 | 100% | no | ✗ |
| 3 | 50 mm thick  for Clean Room SA Duct - MA... | 50 mm thick  for Clean Room SA Duct - MA... | 1.00 | 0% | yes | ✓ |
| 4 | 32 mm thick  for Clean Room SA Duct - Fo... | 32 mm thick  for Clean Room SA Duct - Fo... | 1.00 | 0% | yes | ✓ |
| 5 | 25 mm thick  for Clean Room SA Duct - Fo... | 25 mm thick  for Clean Room SA Duct - Fo... | 1.00 | 0% | yes | ✓ |
| 6 | 19 mm thick for Comfort SA Duct | 19 mm thick for Comfort SA Duct | 1.00 | 0% | yes | ✓ |
| 7 | 13 mm thick for Comfort RA Duct | 13 mm thick for Comfort RA Duct | 1.00 | 0% | yes | ✓ |
| 8 | Supply, Installation of Insulation mater... | Supply, Installation of Insulation mater... | 1.00 | 0% | yes | ✓ |
| 9 | Supply & Installation of underdeck insul... | Supply & Installation of underdeck insul... | 1.00 | 0% | yes | ✓ |
| 10 | S.I.T.C. of Thermal insulation of CHW Pi... | — | 0.01 | 100% | no | ✗ |

## Method Notes
- **Material match:** Levenshtein ratio ≥ 0.80 after stripping stopwords
- **Quantity match:** |pred - gold| / gold ≤ 5% (estimator round-off allowed)
- **Unit match:** canonicalized via _normalize_unit() (sqm/SQM/sqm. → sqm)
- **Row is TP** if all three match. FP if predicted with no gold match. FN if gold with no predicted match.
- Rate/Amount columns ignored (derived, not entity-level facts)
- Section headers / sub-totals / Total rows excluded from both sides
- Match rate < 50%: flagged NOT shippable yet (no soft language)
