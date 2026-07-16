# D5 DECISION PACK — 05_zydus_animal_pharmez multi-quantity-column ruling

> **For:** Srujan (owner). **From:** P1_03 agent. **Date:** 2026-07-06.
> **Question:** When a source XLSX has multiple quantity columns per material row
> (one per area/package), what does ONE BOQ line item mean? This is D5, the last
> open business rule on the sacred-10.

---

## 1. The source sheet's actual structure

`Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx`, Sheet1 (78 rows × 15 cols).

**Header (row 1):**
| Col | A | B | C | D | E | F | G | H | I | J | K | L | M | N |
|-----|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | SR. NO. | DESCRIPTION OF WORK | Units | CHW MANIFOLD (POST) | CHW PIPING & INSUL | CHW MANIFOLD (PRE) | CHW PIPING & INSUL | HOT WATER MANIFOLD | HOT WATER PIPING & INSUL | (blank) | LP STEAM MANIFOLD | LP STEAM PIPING & INSUL | TOTAL | Remarks |

So: 8 quantity columns (D–K, skipping blank J), each for a different area/package of the same material line. Column M = TOTAL (sum). Column N = Remarks (thickness spec).

**3 example rows:**

| SR | DESCRIPTION | Units | D (CHW POST) | E (CHW PIPING) | F (CHW PRE) | G (CHW PIPING) | M (TOTAL) | Remarks |
|----|-------------|-------|-------------|----------------|------------|----------------|-----------|---------|
| 1 | 300 mm dia | RMT | (blank) | R.O. | (blank) | (blank) | 0 | 38MM |
| 6 | 100 mm dia (Manifold size typ) | RMT | 0 | R.O. | 12 | 10 | 22 | 32MM |
| 10 | 50 mm dia | RMT | 0 | R.O. | 55 | 25 | 80 | 25MM |

**The pattern:** each material (e.g. "300 mm dia pipe insulation") has ONE line in the sheet, but its quantity is split across 8 area columns. Some cells are R.O. (rate-only), some blank, some numeric. The TOTAL column sums the numeric cells.

## 2. Current behavior

- **Pipeline:** emits one BOQ row per (material × non-empty qty column) = **48 rows**. Each row's `description` = the material text, `quantity` = the cell value, `unit` = RMT, `location` = the column header (area name). This is the "Option B" multi-qty rule from AGENTS.md.
- **Gold (owner-verified):** **20 rows** — one per material line, `quantity` = TOTAL column value, `unit` = RMT. No location breakdown.
- **Fidelity:** FAIL (48 captured vs 20 source → 28 extra / over-capture).

## 3. Candidate rules

### Rule A — One row per material line, qty = TOTAL (sum) → 20 rows
**Output for example rows:**
| SR | description | qty | unit |
|----|-------------|-----|------|
| 1 | 300 mm dia | 0 | RMT |
| 6 | 100 mm dia (Manifold size typ) | 22 | RMT |
| 10 | 50 mm dia | 80 | RMT |

- **Pros:** matches how an estimator reads a BOQ — one line per item, total qty to price. Matches existing gold (20 rows). Simplest output.
- **Cons:** loses the per-area breakdown (which area needs how much). If the contractor needs area-level quantities for procurement logistics, this loses information.
- **Caveat (§9 gotcha):** if the 8 columns carry DIFFERENT units, summing is invalid. In this sheet all columns are RMT, so summing is valid. But a future sheet could have mixed units → needs a flag.

### Rule B — One row per material × qty-column → 48 rows (current pipeline behavior)
**Output for example rows:**
| SR | description | qty | unit | location |
|----|-------------|-----|------|----------|
| 1 | 300 mm dia | R.O. | RMT | CHW PIPING & INSUL |
| 6 | 100 mm dia | 12 | RMT | CHW MANIFOLD (PRE) |
| 6 | 100 mm dia | 10 | RMT | CHW PIPING & INSUL |
| 10 | 50 mm dia | 55 | RMT | CHW MANIFOLD (PRE) |
| 10 | 50 mm dia | 25 | RMT | CHW PIPING & INSUL |
| ... | (one per non-empty cell) | | | |

- **Pros:** preserves full area-level breakdown. No information lost.
- **Cons:** inflates row count (48 vs 20) — an estimator sees the same material repeated. Doesn't match gold. Over-capture per R1 (more rows than the BOQ has line items).
- **This is the current behavior — it produces a fidelity FAIL.**

### Rule C — Parent row (TOTAL) + flagged child breakdown rows → 20 parent + N flagged children
**Output:** 20 parent rows (qty=TOTAL, unit=RMT) + N child rows (qty=cell, location=column header) flagged `low_confidence` / `breakdown`.

- **Pros:** keeps both views. Parent rows match gold (20 PASS); children are flagged for the estimator who wants the breakdown. R1-compliant (nothing dropped, breakdowns flagged).
- **Cons:** more complex output. The "flagged children" need a clear UI/export convention so they don't confuse the estimator.

## 4. Recommendation

**Rule A (one row per material, qty=TOTAL)** — for these reasons:
1. It matches how BOQs are priced: one line per item, total qty, unit rate × total = line amount.
2. It matches the owner-verified gold (20 rows) → sacred-10 goes to 10/10 PASS.
3. The per-area breakdown is procurement logistics, not a pricing BOQ concern — it can live in a separate "quantity breakdown" annex if SWA needs it.
4. **Mixed-unit caveat:** if a future sheet has different units across qty columns, Rule A must NOT sum — it should flag the row instead. I recommend: sum only if all non-empty cells in the qty columns share the row's unit; otherwise emit the parent row with qty=TOTAL and a `mixed_unit_breakdown` flag.

## 5. What the owner rules

**Srujan: write your ruling below (date + chosen rule + any conditions).**

```
RULE A — 2026-07-06 (owner ruling, Srujan)
- one row per material line, quantity = the sheet's own TOTAL column
- If a future sheet has mismatched units across qty columns, do NOT
  sum — emit the parent row with a `mixed_unit_breakdown` flag
  (decision pack §4 variant).
```

## 6. What happens after the ruling

- **If Rule A:** implement qty-column summing in `src/pipeline_xlsx.py` (narrow scope: detect multi-qty-column layout by header, sum into one row per material). Gold stays at 20. Source_truth stays at 20. Sacred-10 → 10/10 PASS. **← owner chose this.**
- **If Rule B (keep current):** gold needs changing to 48 (orchestrator applies, Rule 3). Source_truth changes to 48. Over-capture is the accepted norm for multi-qty sheets.
- **If Rule C:** implement parent+flagged-children emission. Gold stays at 20 (parents match). Children are flagged, not failing. Most complex implementation.

**P1_03 implementation status (2026-07-06, agent):** Rule A implemented in `src/pipeline_xlsx.py`. Narrow scope: when `total_col is not None and len(quantity_cols) >= 2` (multi-qty-column + TOTAL layout, the 05_zydus_animal case), rows with TOTAL ≤ 0 are skipped (counted as `total_rows` for fidelity). Single-qty + TOTAL layouts (R1 flag-never-drop) and the wide_matrix path (no TOTAL) are unchanged. The `mixed_unit_breakdown` flag is set on parent rows whose qty-column headers carry unit tokens not in the row's unit (word-boundary match; for 05_zydus_animal all 8 qty columns share RMT/sq.m, so the flag stays False for every emitted row).

**source_truth.json correction (NOT committed per orchestrator instruction):** the 05_zydus_animal entry's `source_row_count` was changed locally from 48 → 20 to match the Rule A output + the owner-verified gold. This change is left in the working tree (uncommitted) for the orchestrator to re-pin; per the dispatch instructions: *"if the existing 48-row source_truth needs correction, document it but don't commit."*

**In all cases:** the other 9 sacred docs' extraction paths must be byte-identical (the §6 canary: 03_zydus 33/33 must not regress). The regression test (`test_sacred10_fidelity.py`) locks the result.