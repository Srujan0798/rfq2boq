# Column-Aware PDF Extraction Eval (P3_02)

> **Task:** P3_02 column-aware PDF table extraction — kill the
> interleaved-column bug class (07_grew class). Each row assembled
> cell-by-cell from detected column bands, not from jumbled text
> lines.
>
> **Author:** Agent-P3-2 (this task) on `phase9-final`.
>
> **Source spec:** `tasks/phase9/P3_02_column_aware_extraction.md`
>
> **Goal:** every BOQ row is reconstructed from its cell geometry.
> Material cell text NEVER bleeds across the qty/unit/remarks bands.

---

## 1. Method

1. **Detector:** `src/ingest/column_detector.py` exposes
   `detect_columns(page) -> ColumnDetectorResult`. Two complementary
   inputs are fused:
   - **Ruling-line evidence** (rects with high vertical extent +
     small horizontal extent → column dividers; rects with high
     horizontal extent + small vertical extent → row separators).
   - **Word x-edge histogram** (gap-based 1-D clustering of word
     x0 + x1 positions; merged into bands). Used when no ruling
     lines are present (the §9 gotcha — Word-exported PDFs).
2. **Row assembly:** `assemble_cell_based_rows(page, bands)`
   clusters words into row envelopes by y-center proximity
   (tolerance 6pt). Each word is assigned to the band whose
   y_center is closest (center-based, not range-based, to avoid
   boundary words being claimed by two adjacent envelopes).
   Wrapped cells are joined to a single row when their visual
   lines share unit/qty text (the 07_grew ACOUSTIC LINING case).
3. **Merge logic:** `merge_wrapped_rows` does:
   - **Trailing continuation merge** — same-data-row pattern
     (identical unit+qty) folds wrapped material into a single
     row without duplicating the structural cells.
   - **Leading context merge** — only the IMMEDIATE previous
     non-anchor row is considered, AND only if that row is a
     "compact" single-line section header (y-range ≤ 8pt). Multi-
     line spec paragraphs (y-range 20-50pt) are NOT pulled in —
     they belong to the section as a whole, not to the first
     data row.
4. **Confidence:** in [0, 1] = 0.5 × word_coverage + 0.5 × ruling_strength
   + 0.15 fused bonus if both signals are present.
5. **Pipeline integration:** `src/ingest/pdf_extractor.py` adds
   `extract_column_aware_tables()` and
   `extract_column_aware_diagnostics()` methods.
   `src/ingest/table_extractor.py` adds
   `TableExtractor.extract_column_aware()` (extraction_method =
   `"column_aware"`).

   The existing pipeline (`src/pipeline.py`) does NOT yet wire the
   column-aware path as the first attempt; it still uses the
   pdfplumber path that produced the P3_01-accepted 9/9 baseline
   via the `_is_section_header` exact-match fix at `0e1cd4e`. The
   column-aware path is exposed for evaluation and future pipeline
   integration. Wiring it as the first-attempt path is a one-line
   change in `src/pipeline.py` and is left as the natural follow-up
   to P3_02 (the spec's §3 "row assembly path" + §5 confidence-gated
   text-line fallback).

---

## 2. Pre-P3_02 baseline snapshot of 07_grew (sacred row 5 — "ACOUSTIC LINING")

The diagnosed failure (per `tasks/sonnet/LEDGER.md` 2026-07-05 row
"07_grew's 1 remaining dropped row"): pdfplumber interleaves
"Sqm. 500" with adjacent remark-column text ("complies (density
will be 180-220 kg/m3)"). The current code happens to produce
9/9 because the `_is_section_header` exact-match fix (`0e1cd4e`)
strips the bleed, but the underlying interleaving remains and will
corrupt similar multi-column docs in the train pool.

Verbatim current text of the "ACOUSTIC LINING" row's material cell
(from `Pipeline().run()` BEFORE P3_02 code landed):

```
ACOUSTIC LINING Supply,InstallationandTestingofAccousticliningwith10mmthickClass
```

Notes:
- The "ACOUSTIC LINING" prefix is the section header from
  `pending_header` (table_extractor.py map_to_boq_rows), prepended
  because pdfplumber split this row out of the previous section's
  table.
- The right-hand band (REMARKS, x=475–557) has "complies (density
  will be 180-220 kg/m3)" which does NOT appear in the material
  text (the split tables saved us) but is on the same y-line as
  the qty and could leak into other documents.
- 9/9 row count is preserved by the section-header defense
  (`0e1cd4e`) — but the cell assignment is positional luck, not
  engineered.

---

## 3. Post-P3_02 verbatim of 07_grew row 5 (the qty-500 row)

After P3_02 lands, the column-aware assembly produces (from
`extract_column_aware_tables`):

```
row 5 (row 4 in 0-indexed)
  bands    : ITEM (x=50-76)  MATERIAL (x=76-375)  UNIT (x=375-400)  QTY (x=400-428)  REMARKS (x=475-557)
  item_no  : (none — section header row, recognised by short text + numeric column empty)
  material : ACOUSTIC LINING Supply,InstallationandTestingofAccousticliningwith10mmthickClass1ratingOpenCellnitrilerubberinsulationmaterialwithdensityof140to 180 kg /m³along with manufacturer recommended adhesive.
  unit     : Sqm.
  qty      : 500
  remarks  : complies (density will be 180-220 kg/m3)
```

Crucial property: the qty=500 cell was assembled from its own
(band QTY, y≈252), the remark text "complies (density will be
180-220 kg/m3)" is a sibling cell in band REMARKS, and the
material text spans the wrapped y=249–256 envelope without the
remark characters leaking in.

The assertion in `tests/integration/test_multicolumn_pdfs.py`
proves this:

```python
def test_seven_grow_qty_500_row_assembles_from_cells() -> None:
    ...
    assert "Supply,InstallationandTestingof" in material
    assert "ACOUSTIC LINING" in material
    assert "complies" not in material
    assert "180-220" not in material
    assert qty == "500"  # in its own cell
    assert unit == "Sqm."  # in its own cell
```

---

## 4. Before/after on 07_grew (the canonical P3_02 case)

| metric | before P3_02 (existing pdfplumber path) | after P3_02 (column-aware path) |
|---|---|---|
| row count (data rows in 07_grew gold) | 9 ✓ | 9 ✓ (column-aware returns 11: 9 data + 2 R/O sections 6/7) |
| ACOUSTIC LINING row 5 material | "ACOUSTIC LINING Supply,InstallationandTestingof..." (with "ACOUSTIC LINING" prepended as section header via pending_header) | "ACOUSTIC LINING Supply,InstallationandTestingof...withdensityof140to 180 kg /m³along with manufacturer recommended adhesive." (full wrapped description merged cell-by-cell) |
| remark text in material cell | none (saved by section-header defense) | none (cell-by-cell; remark correctly placed in REMARKS band) |
| unit cell duplication | n/a | none (`Sqm.` appears once, not `Sqm. Sqm.`) |
| qty cell duplication | n/a | none (`500` appears once, not `500 500`) |
| wrap shred (06_avante item-75 class) | n/a | prevented: same-data-row merge folds wrapped material into a single row |
| bottom-line fidelity | 9/9 (0 dropped) | 9/9 (0 dropped) |

The 07_grew case is the SUCCESS of P3_02: the column-aware path
preserves the 9/9 baseline AND correctly assigns the
interleaved remark text to its own band instead of letting it
bleed into the material cell.

---

## 5. Before/after on 04_adani (a TRAIN-pool multi-column doc)

| metric | before P3_02 (existing pdfplumber path) | after P3_02 (column-aware path) |
|---|---|---|
| row count | – (file is currently outside the P3_01-accepted baseline) | 6 rows assembled from the column-aware path on page 1 of `BOQ PAGE2adani proj.pdf` |
| band detection | – | 35 narrow bands detected (borderless page → word-edge histogram only) |
| description cleanliness | – | the first assembled row's material is "duct, Armaflex, fixing specifications. Density insulation shall be Kg/m³." — clean of any cross-column bleed |

The 04_adani case is the FAILURE of P3_02: the borderless adani
page produces 35 narrow bands (the detector's
`_merge_close_bands` with `min_band_width=6` is too lenient for
pages where pdfplumber's word extraction puts every character on
its own visual line). The cell assignment is noisy; the column-
aware path on this page is not yet a clean improvement. The
existing pdfplumber path is still preferred for this doc.

---

## 6. Failure / honesty list

The detector and merger may still mangle pages that:

* **Borderless pages with no ruling lines AND <4 words per band.**
  The 04_adani BOQ page falls into this class — the word-edge
  histogram produces 35 narrow bands (mostly 1-word clusters at
  variable x positions). The detector's `_merge_close_bands`
  should absorb more aggressively; the current `min_band_width=6`
  is too lenient for these pages. Output still assembles 6 anchor
  rows, but the band → cell assignment is noisy.

* **Right-aligned numeric columns that drift by >10pt.** The
  detector clusters on x0 + x1; if the right edge is unstable,
  multiple narrow clusters form. Same fix as above (tighter merge).

* **Rotated text (90° headers, landscape tables).** Not in scope
  for P3_02; would require a separate detector.

* **Pages with overlapping envelopes (wrapping material that
  crosses the unit/qty y-line).** The same-data-row merge handles
  the 07_grew ACOUSTIC LINING case (identical unit+qty), but a
  more sophisticated detector would also handle same-material,
  no-unit rows. Out of scope for P3_02.

---

## 7. Unit-test coverage (`tests/unit/test_column_detector.py`)

22 tests, 100% pass:

1. 2-band layout (item | description) — word-histogram path
2. 3-band layout (item | material | qty) — no ruling lines
3. 4-band layout (item | material | unit | qty) — no ruling lines
4. 5-band layout with ruling lines (07_grew class)
5. Borderless 5-band layout
6. Wrapped-text within a cell does NOT shred into phantom rows
7. filter_empty_bands drops zero-word slivers (page margins)
8. _merge_close_bands absorbs sub-min-width slivers
9. _cluster_xs merges positions with small gaps
10. _cluster_xs within-gap merge
11. Ruling-line evidence: tall thin rects are dividers
12. Ruling-line evidence: short wide rects are row separators
13. cluster_words_into_rows respects y_tolerance
14. Leading context merge: compact section header is pulled in
15. Leading context merge: tall spec paragraph is NOT pulled in
16. _detect_band_roles assigns correct roles
17. Confidence: ruled page is reliable; empty page is not
18. Edge case: degenerate page geometry (zero dimensions)
19. Edge case: no words returns empty
20. assemble_cell_based_rows: each word assigned to ONE band only
21. Integration: detect_columns on a 07_grew-shape page produces ≥5 bands

---

## 8. Integration-test coverage (`tests/integration/test_multicolumn_pdfs.py`)

6 tests, 100% pass on the real 07_grew PDF:

1. The detector finds ≥5 column bands on 07_grew
2. The 9 data rows (gold row count) are extracted
3. The famous "qty 500" row assembles from its own cells (no remark bleed)
4. The earlier rows (11.1, 11.2, 11.3, 11.4) have clean material (no remarks)
5. The 8.x rows (CHW Pipings) are extracted with their sq.mtr unit
6. The diagnostics dump reports the band count correctly

---

## 9. Run instructions

```bash
cd /Users/srujansai/rfq2boq-phase9
PYTHONPATH=/Users/srujansai/rfq2boq-phase9 python3.12 scripts/eval_column_aware.py --split all --type boq_bearing --limit 5
```

Writes per-doc results to `results/column_eval/per_doc/<doc_id>.json`
and a summary to `results/column_eval/summary.json`.

```bash
PYTHONPATH=/Users/srujansai/rfq2boq-phase9 python3.12 -m pytest tests/unit/test_column_detector.py tests/integration/test_multicolumn_pdfs.py -v
```

Runs all 28 P3_02 tests (22 unit + 6 integration).
