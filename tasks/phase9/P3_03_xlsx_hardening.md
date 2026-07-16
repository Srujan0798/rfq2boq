# TASK P3_03: XLSX path hardening — table-type detection, hierarchy, wrapped rows — Agent-P3-3

## 1. GOAL
Make the XLSX extraction path robust across the whole corpus's spreadsheet diversity: correctly classify non-BOQ tables (compliance checklists, make-lists), handle hierarchical item numbering with parent inheritance, and survive multi-line/merged-cell layouts — without disturbing the sacred-10 guarantees.

## 2. CONTEXT
Files to read FIRST (in order):
- `src/pipeline_xlsx.py` + `src/ingest/table_extractor.py` — the path you're hardening; find `_is_boq_data_row`, `_is_pure_dimension` (the incident-#8 conditional guard — NEVER weaken), `_is_section_header` (exact-match), and the checklist detector IF P1_04 re-implemented it
- `tasks/sonnet/LEDGER.md` rows: "live upload test" (Gopin compliance checklist), 06_avante diagnosis (multi-line-wrap + parent-inheritance), 08_sael (numbered-clause outline)
- P1_04's report — XLSX quality observations across the corpus
- `results/fidelity/` — current per-doc state
- Branch `w3-tip-untriaged` commit `cc61c7a` (multi-sheet workbook processing) — reference diff; re-verify before adopting anything from it

Current state:
- Compliance checklists (`Sl.No | Details | Specification | Bidder Reply`) fooled the row heuristic into fake rows with 0.9–1.0 confidence (fixed once in a lost context; P1_04 may have restored — verify).
- Hierarchical numbering (11 → 11.1 → 11.1.1) works for capture but children don't inherit parent context (a child row "25mm thick" means nothing without its parent's material) — BOQ assembly needs the hierarchy.
- Make-lists and approved-vendor tables in non_training docs still risk false extraction if a user uploads one (R1: correct answer is 0 rows + a document-type flag, not invented rows).

## 3. DELIVERABLES
- [ ] `src/ingest/table_classifier.py` — `classify_table(header_row, sample_rows) -> TableType` (`BOQ | COMPLIANCE_CHECKLIST | MAKE_LIST | VENDOR_LIST | GENERIC_SPEC | UNKNOWN`), rule-based on header shape + column content signatures; docstring documents each signature with a real corpus example
- [ ] `src/pipeline_xlsx.py` — consumes classification: only `BOQ` (and `UNKNOWN` with flag) tables enter row extraction; others produce a typed document-level flag
- [ ] Hierarchy: item-number parser (`11.1.1` → parents) + `parent_context` field on child rows (parent's description chain, for BOQ assembly + export display); NO row merging (children stay rows — R1)
- [ ] Multi-line-wrap handling: merged-cell and wrapped-description assembly on the XLSX path (06_avante item-75 class), with the qty+unit+item# guard pattern from `f3affab` respected
- [ ] `tests/unit/test_table_classifier.py` — ≥10 tests: each type classified from real header shapes (copy them from corpus docs), UNKNOWN default, header-case/spacing tolerance
- [ ] `tests/unit/test_xlsx_hierarchy.py` — ≥6 tests: parsing, inheritance chain, sibling ordering, malformed numbering tolerance
- [ ] Updated `results/fidelity/` after re-run

## 4. STEPS
1. Read context; inventory ALL distinct header shapes in the corpus (script over the boq_bearing + a sample of others; paste the shape census in the report — it justifies the signatures).
2. Build classifier from the census; wire into pipeline; verify the Gopin doc yields 0 rows + checklist flag.
3. Implement hierarchy + parent_context; verify on 08_sael (its 17 rows keep numbering; children get parent chains).
4. Multi-line-wrap assembly; verify 06_avante stays 31/31 and its two once-dropped rows carry clean descriptions.
5. Sacred-10 + corpus re-run; tests; commit in 3 commits (classifier / hierarchy / wrap).

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 -m pytest tests/unit/test_table_classifier.py tests/unit/test_xlsx_hierarchy.py -v   # EXPECT: 16+ passed
# Gopin compliance doc through the pipeline: EXPECT rows==0 and flags contain COMPLIANCE_CHECKLIST
python3 scripts/audit_fidelity_per_doc.py --all        # EXPECT: all sacred verdicts unchanged (03: 33/33 canary!)
python3 scripts/run_corpus.py --split all --type all   # EXPECT: all docs ok
python3 -m pytest tests/unit tests/integration -q && make lint && make typecheck
```

## 6. ACCEPTANCE CRITERIA
- [ ] Header-shape census in report; every classifier signature traceable to real docs
- [ ] Gopin-class docs: 0 rows + typed flag (R1-honest zero, proven)
- [ ] 03_zydus 33/33, 06_avante 31/31, 08_sael 17/17 unchanged — the three canaries
- [ ] Child rows carry parent_context; no rows merged away
- [ ] Zero corpus regressions vs P3_01/P3_02-accepted baselines

## 7. CONSTRAINTS
- The conditional `_is_pure_dimension` guard and `_is_section_header` exact-match are LOAD-BEARING (fought over 5+ times, re-poisoned in the chaos repo's fake wave5) — extend around them, never through them
- If P1_03's D5 implementation touched `pipeline_xlsx.py`, rebase on it — check `git log -- src/pipeline_xlsx.py` first; conflicts go to the orchestrator, not resolved by guess
- Frozen files untouched; Rule 8
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P1_03 (implementation half — shared file), P1_04
- **Blocks:** P3_04
- **Parallel-safe with:** P3_01, P3_02 (PDF path), P2_03/P2_04
- **Shared files:** `src/pipeline_xlsx.py`, `src/ingest/table_extractor.py`

## 9. GOTCHAS
- XLSX header rows are not always row 1 — logos/title blocks occupy top rows; the classifier gets the DETECTED header row (existing header-detection logic finds it; reuse, don't duplicate).
- openpyxl merged cells: only the anchor cell holds the value; `cell.value is None` on the rest — resolve via `sheet.merged_cells.ranges` before classification or wrap assembly.
- Numbered-clause outlines (08_sael) look like hierarchy AND are real BOQ rows — hierarchy parsing must not reclassify the table type.
- Some corpus XLSX have MULTIPLE sheets with different table types in one workbook — classify per-sheet-per-table, not per-file (this is what `cc61c7a` attempted; verify its approach independently).
