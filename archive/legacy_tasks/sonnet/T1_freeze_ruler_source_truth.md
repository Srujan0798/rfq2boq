# T1 — Freeze the ruler: owner-verified source truth · the keystone task

## 1. GOAL
Create one immutable, owner-confirmed source-row count per sacred-10 document, and make every fidelity harness read ONLY from it — because today the "source rows" number changes between runs (01_gsecl: 3→397; 09_gem: 22→157→207), which makes every fidelity % meaningless.

## 2. CONTEXT (read first)
- `results/fidelity_audit_summary.txt` (2026-07-04: the unstable counts)
- `scripts/measure_fidelity.py` and `scripts/fidelity_audit.py` — find where each derives `source_rows` today (gold files, live XLSX counting, pipeline output — all inconsistent)
- Source docs: `data/real_rfqs/` (sacred 10 PDFs/XLSX)
- Cheat history: source counts derived from pipeline output = self-comparison (incident #3). Forbidden.

## 3. DELIVERABLES
- `data/real_rfqs/source_truth.json` — per doc: `{doc_id, source_row_count, unit: "BOQ line items", method: "human count", evidence: "<page/sheet + row range>", counted_by: "machine-draft", owner_confirmed: false}`
- `scripts/draft_source_truth.py` — produces the machine DRAFT counts with page/sheet evidence for the owner to check
- Patched `scripts/measure_fidelity.py` + `scripts/fidelity_audit.py`: source counts read exclusively from `source_truth.json`; hard error if a doc is missing or `owner_confirmed` is false (warn-and-mark, don't silently proceed)
- `results/source_truth_review.md` — side-by-side: doc, machine count, page refs, screenshot-style row excerpts (first 3 / last 3 rows text) so Srujan can confirm each count fast
- Test `tests/unit/test_source_truth.py` — harnesses refuse pipeline-derived source counts; JSON schema validated

## 4. STEPS
1. Read both harnesses; document (in the REPORT) exactly where each gets `source_rows` today and why they disagree.
2. Write `draft_source_truth.py`: for XLSX count data rows in the BOQ sheet (state header/blank/section-row rules explicitly in code comments); for PDFs locate BOQ tables (use `src/preproc/document_structure.py` routing + `pdfplumber` tables) and count line items. Every count carries evidence refs. **The pipeline's extraction output must NOT be the counter.**
3. Generate `source_truth.json` (all `owner_confirmed:false`) + `source_truth_review.md`.
4. Patch both harnesses to read only this file. Add the unit test.
5. Run both harnesses; confirm counts now stable across two consecutive runs.
6. **STOP — owner step:** present `source_truth_review.md` to Srujan. He confirms/corrects each count (especially 01_gsecl: is Schedule-B really ~397 items, or 3? and 09/10 GeM). Flip `owner_confirmed:true` only per his answer, with `confirmed_date`.

## 5. VERIFICATION
```bash
PYTHONPATH=. .venv/bin/python scripts/draft_source_truth.py            # regenerates draft, idempotent
PYTHONPATH=. .venv/bin/python scripts/measure_fidelity.py              # source col == source_truth.json values, both runs identical
.venv/bin/python -m pytest tests/unit/test_source_truth.py -q          # green
make verify                                                             # green
```

## 6. ACCEPTANCE CRITERIA
`source_truth.json` exists for all 10 docs with evidence refs; harnesses read only it; two consecutive harness runs produce identical source counts; review doc ready for owner; after owner pass, all 10 `owner_confirmed:true`.

## 7. CONSTRAINTS
Never derive source counts from pipeline output. Never edit gold files. Rate-only/`Comply`-column rows: count per the documented rule you state in code, and surface the rule in the review doc for the owner to ratify.

## 8. DEPENDENCIES
Blocks: T4a/T4b, T7. Blocked by: T0. Parallel-safe: with T3.

## 9. GOTCHAS
- 01_gsecl Schedule-B spans pages ~60–69 with sub-items — decide and DOCUMENT whether sub-rows count as items; the owner ratifies the rule, not you.
- 09/10 GeM PDFs previously hung extractors — draft counting must have a timeout and may cite the GeM portal item table directly.
- XLSX merged cells and section-header rows inflate naive counts — your counting rules must be explicit and reviewable.
