# TASK P5_01: Export + UI — flags visible, fidelity demonstrable, demo-ready — Agent-P5-1

## 1. GOAL
Make the product surface worthy of the pipeline behind it: Excel/JSON exports that carry every flag and provenance detail, and the Streamlit UI Srujan demos to SWA — upload a real tender, see the BOQ, see exactly what was flagged for review and why (R1 made visible).

## 2. CONTEXT
Files to read FIRST (in order):
- `src/export/excel_generator.py` + JSON/CSV exporters — current state (incl. the `list[str]` join fix from P1_04)
- `src/domain/flags.py` (P3_04) — the typed flag system to surface
- `ui/` — the Streamlit app; `docs/ui_guide.md`, `docs/excel_format.md` — current documented behavior (update both)
- `schema/` — the flag-carrying schema (P3_04's version)
- `docs/SWA_REQUIREMENTS_2026-06-11.md` R1 — "flag, never drop" is a UI promise too

Current state:
- Excel export: functional but flag-blind; descriptions may truncate for display (any truncation of DATA is an R1 bug — display wrapping is fine, data loss is not; audit this).
- UI: real-tender upload only (S2 purge); no flag panel, no fidelity view, no per-row provenance (source page/sheet).

## 3. DELIVERABLES
- [ ] Excel export: BOQ sheet (item, description FULL, qty, unit canonical + original, location/grade/standard/dimension, parent_context, confidence) + severity coloring on flagged rows + a second "Review" sheet listing every flag (severity, stage, message, row ref) + a "Provenance" sheet (source file, sha256, extraction date, pipeline version/commit, source pages per row where available)
- [ ] JSON export: schema-complete incl. flags + provenance (probably done by P3_04 — verify + test)
- [ ] UI: upload → progress → results view with (a) BOQ table, flagged rows visually distinct, (b) flag review panel grouped by severity, (c) document-type banner when a non-BOQ doc is detected (compliance checklist etc. → "0 line items, document classified as X", NOT an empty error), (d) download buttons (xlsx/json), (e) footer: model version + pipeline commit
- [ ] `tests/unit/test_excel_export.py` — ≥8 tests (full description survives, flags land on Review sheet, list-fields joined, empty-doc export, unicode)
- [ ] `tests/integration/test_ui_smoke.py` — Streamlit AppTest-based smoke: upload fixture → rendered rows + flags (`streamlit.testing.v1.AppTest`, no browser automation)
- [ ] `docs/ui_guide.md` + `docs/excel_format.md` rewritten to match reality (exact sheet/column specs mandatory)

## 4. STEPS
1. Read context; audit both exporters for ANY data truncation/omission (report table: field → preserved fully? → fix).
2. Excel work (openpyxl styling minimal + professional; severity = 3 shades, no rainbow).
3. UI work (keep the existing app's structure; add, don't rewrite; every pipeline call goes through the same entry the CLI uses — no UI-only code paths that could diverge).
4. Tests; run the UI manually on 2 real docs (one clean BOQ, one compliance checklist) — text-dump the result in the report.
5. Docs; commit (export / ui / docs separate).

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 -m pytest tests/unit/test_excel_export.py tests/integration/test_ui_smoke.py -v   # EXPECT: 10+ passed
# export a sacred doc; reopen with openpyxl; assert: row count matches audit 'captured', longest description char-for-char equal, Review sheet exists
python3 scripts/audit_fidelity_per_doc.py --all     # EXPECT: unchanged (export must not touch extraction)
make run-ui &  # manual check per §4.4, then kill
python3 -m pytest tests/unit tests/integration -q && make lint && make typecheck
```

## 6. ACCEPTANCE CRITERIA
- [ ] Zero data truncation anywhere in exports (audit table proves it)
- [ ] Every flag visible in both Excel Review sheet and UI panel
- [ ] Non-BOQ upload shows the classified-document banner, not an error/empty table
- [ ] UI runs the identical pipeline path as CLI (one entry point, greppable)
- [ ] Docs match implementation exactly

## 7. CONSTRAINTS
- No Rate/Amount/cost columns ANYWHERE (S1 — check templates you touch)
- No sample/demo data added to the UI (S2) — fixtures live in tests/, drawn from real corpus docs
- No new UI frameworks; Streamlit as-is
- Frozen files untouched; standing constraints `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P3_04 (flags), P1_02 (audit artifacts referenced in Provenance sheet)
- **Blocks:** P5_03 (demo assets), P5_04
- **Parallel-safe with:** P4_01, P4_02
- **Shared files:** `src/export/*`, `ui/*`

## 9. GOTCHAS
- openpyxl cell limit is 32,767 chars — a full tender description fits, but guard + flag rather than crash if some pathological doc exceeds it.
- Streamlit reruns the script top-to-bottom per interaction — pipeline results must be cached (`st.session_state` keyed by file hash) or a 60s extraction reruns on every widget click.
- `AppTest` can't exercise real file-upload widgets fully — inject via session_state in the smoke test; that's accepted practice.
- Conditional formatting survives LibreOffice/Excel differently — use fill styles, not CF rules, for severity coloring (SWA may open in either).
- The GeM validation flags (P2_01) are the demo's money shot on GeM docs — make sure they render with the catalog-mismatch text.
