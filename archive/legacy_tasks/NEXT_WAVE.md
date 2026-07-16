# NEXT WAVE — dispatch index (written by Fable orchestrator, 2026-06-11)

**Branch:** `phase8-clean-slate` (the ONLY branch — never create new ones)
**Client requirements (read before any task):** `docs/SWA_REQUIREMENTS_2026-06-11.md` — R1 100% conversion fidelity (flag, never drop), R2 GeM catalog as NER reference, R3 100-PDF dataset incoming, R4 structure-first PDF extraction. Plus the SWA brief: `resources/RFQ to BOQ Scope Extraction using NLP system.pdf`.
**Protocol:** ONE task → agent finishes → Srujan pastes REPORT to Fable → Fable reproduces + `make verify` → commit → next task. No parallel agents on this tree.
**Every task inherits these rules:** no gold-file edits, no matcher-threshold lowering, no `if filename ==` hacks, no handoff rewrites, no new branches, no synthetic data, unpriced BOQ only, imports `src.` only, Python 3.11–3.13 for anything that touches torch. A ~100% score is a red flag — investigate, don't celebrate.

| # | File | Priority | What it fixes | Safe in parallel? |
|---|------|----------|---------------|-------------------|
| NW-01 | `tasks/NW01_fix_row_eval_artifacts.md` | P0 | Row-eval scores 03 Zydus 0% despite 33/33 rows; 04 eval reads the wrong Adani PDF | Run FIRST, alone |
| NW-02 | `tasks/NW02_structure_extractor_precision.md` | P0 | 1281 false-positive sections in large PDFs; camelot-py missing | After NW-01 |
| NW-03 | `tasks/NW03_adani_extraction_quality.md` | P1 | 04 Adani: 16 extracted vs 45 rowgold rows — close the gap honestly | After NW-01 |
| NW-04 | `tasks/NW04_annotation_pipeline_for_100pdfs.md` | P1 | Ready the human-annotation loop BEFORE SWA's 100 PDFs arrive | Parallel-safe (new files only) |
| NW-05 | `tasks/NW05_unified_unit_normalizer.md` | P1 | One canonical unit/qty normalizer shared by pipeline + evaluator | After NW-01 |
| NW-06 | `tasks/NW06_repo_hygiene_and_docs.md` | P2 | Restore real reference PDFs from attic, port phase8 prompts from main-clean, fix doc inaccuracies | Last |

## Owner-only checklist (Srujan — agents cannot do these)
1. **Push the 166 unpushed commits** from a stable network: `git push -u origin phase8-clean-slate` (then set it as default branch on GitHub). Until pushed, one disk failure loses a month of work.
2. **Remote URL embeds a GitHub token** (`git remote -v` shows `x-access-token:gh…@github.com`). Rotate that token and switch to a credential helper.
3. **Gold sign-off (~40 min):** 03 Zydus rowgold (provenance was disputed on 2026-06-08 — re-verify 5 random rows against the XLSX yourself), and 09/10 GeM gold (tooling-transcribed, needs your eyes).
4. **100-PDF dataset:** chase Sales team / Jineth / Softnil archive (from the 2026-06-11 meeting). This is THE lever for NER — nothing else moves real F1.
5. **Python env:** the venv is back on 3.14 (charter pins 3.11–3.13). Rebuild when convenient: `python3.12 -m venv .venv && source .venv/bin/activate && pip install -e .`
