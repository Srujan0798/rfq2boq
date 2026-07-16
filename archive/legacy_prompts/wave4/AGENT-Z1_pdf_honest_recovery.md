# TASK: PDF Real-World Honest Recovery — Agent-Z1

## 1. GOAL
Close the gap between XLSX extraction (production-ready, ~89% F1) and PDF extraction (broken on real docs, ~14% F1) **without** any caching, result-storing, demo-shortcut, or pretrained-data cheating — so the same engine that scores X on `data/real_rfqs/swa_enquiries/` also scores X on a brand-new RFQ the owner has never seen.

## 2. CONTEXT

Files to read FIRST (in this order, do not skip):

- `AGENTS.md` — full conventions, entity/relation types, BIODS, settings
- `docs/wave_status.md` — what is honestly done vs pending
- `docs/SCOPE_GUARD.md` — refuse drift
- `results/eval_honest.json` — current per-doc F1 (the ground truth of where we are)
- `results/NER_REAL_REPORT.md` — confirms BERT v5 overfits synthetic, real F1 ≈ 0.188
- `results/PRODUCT_VALIDATION_REPORT.md` — the owner-validated number
- `src/pipeline.py` — main PDF extraction pipeline
- `src/pipeline_xlsx.py` — XLSX pipeline (the one that works)
- `src/nlp/ner/lazy_model.py` — BERT inference path
- `src/nlp/ner/inference.py` — batch NER inference
- `src/nlp/patterns/` — the **production** regex + gazetteer NER (this is what to improve, not BERT)
- `src/nlp/pipeline.py` — NER orchestration
- `src/eval/` — matchers that compute F1
- `scripts/eval_honest.py`, `scripts/eval_honest_rows.py` — the honest evaluators (do not modify)
- `tests/unit/test_anti_cheat.py` — anti-cheat regression tests (must keep green)
- `data/real_rfqs/swa_enquiries/` — the 10 SWA files; the only real validation set
- `data/real_rfqs/gold/` — human-annotated gold

Current state of the area being modified:
- XLSX path: 89.0% entity F1, 0.85–0.93 per-file. Production-ready.
- PDF path: 14.2% entity F1. Gold is short material phrases (e.g. "MS chilled water pipe insulation nitrile rubber"); pipeline returns full sentence descriptions. The matcher cannot pair them, so 0.0 F1 on 04_adani and 01_gsecl even though the engine "found" the items.
- BERT v5: val F1=0.755 on synthetic, 0.188 on real. **Do NOT re-train BERT as a fix.** The data is the problem (only ~1636 entities of human gold across 10 files, mostly pre-cleaned). Re-training on the same data will re-overfit.
- Production NER is the pattern engine (`src/nlp/patterns/` + `src/nlp/pipeline.py`). That is what to fix.
- `src/llm/client.py:71-96` has a Redis cache for LLM calls. It is gated behind a feature flag. Confirm it is **disabled** for honest eval and not silently short-circuiting PDF extraction.

## 3. DELIVERABLES

Create or modify EXACTLY these files:

- [ ] `results/diagnosis_pdf.md` — root-cause writeup of why PDF F1 is 14%
- [ ] `src/nlp/patterns/material_phrases.py` (or equivalent) — extract short canonical material phrases from long sentence-level pipeline output, not the other way around
- [ ] `src/eval/matchers.py` — make the entity matcher tolerant to the "gold is short phrase, pred is full sentence" asymmetry (do NOT make it looser than 0.6 token-overlap; that would be cheating)
- [ ] `scripts/eval_honest_v2.py` — wraps `eval_honest.py` logic with the new matcher and writes `results/eval_honest_v2.json`
- [ ] `tests/unit/test_pdf_honest_recovery.py` — ≥ 6 unit tests for the new phrase extractor and matcher
- [ ] `tests/integration/test_held_out_fresh_rfq.py` — runs the pipeline on a NEW RFQ the SWA set has never seen (use any file in `data/real_rfqs/raw/` or `data/real_rfqs/reference_real/` that is NOT in `swa_enquiries/`), asserts it produces output without crashing, and asserts the output is NOT byte-identical to any prior run output for a different file (proves no caching)
- [ ] `docs/wave_status.md` — append a "Z1 results" section with new per-file F1
- [ ] `results/eval_honest_v2.json` — the new numbers, with a `held_out` field for the fresh file

Do NOT modify:
- `scripts/eval_honest.py` (the canonical honest eval is frozen)
- `tests/unit/test_anti_cheat.py`
- `config/constants.py`
- `config/settings.py`
- `data/real_rfqs/gold/*` (human gold is sacrosanct)

## 4. STEPS

1. Read every file in Section 2. Do not skip `AGENTS.md` or `SCOPE_GUARD.md`.
2. Run the frozen honest eval to confirm the current baseline:
   ```bash
   python3 scripts/eval_honest.py
   python3 scripts/eval_honest_rows.py
   ```
   Save outputs. These are your before-numbers.
3. Anti-cheat audit: prove the pipeline is not caching. For each of the 10 SWA files:
   ```bash
   md5sum data/real_rfqs/swa_enquiries/*/*  # record
   python3 -c "
   from src.pipeline import Pipeline
   p = Pipeline()
   for f in sorted(__import__('pathlib').Path('data/real_rfqs/swa_enquiries').rglob('*')):
       if f.suffix.lower() in {'.pdf', '.xlsx'}:
           r = p.run(str(f))
           print(f.name, len(r.boq_items))
   "
   ```
   The output count for each file must match what the engine actually finds at runtime, not what a cache returns. If any number is suspiciously fast (<10 ms on a multi-page PDF) and constant across reruns, **stop and report it** — that is a cache leak.
4. Diagnose: open `results/eval_honest.json`, look at `unmatched_gold` and `unmatched_pred` for the 0.0 F1 PDFs (01_gsecl, 04_adani, 09_gem, 10_petc). Write `results/diagnosis_pdf.md` with concrete examples. The expected diagnosis is the gold/pred granularity mismatch, not "model is dumb."
5. Implement `src/nlp/patterns/material_phrases.py` with this signature:
   ```python
   def extract_canonical_material(sentence: str) -> list[str]:
       """Split a long pipeline sentence into short canonical material phrases
       matching the granularity of human gold. Conservative: prefer miss over
       false split. Must be deterministic — same input, same output."""
   ```
   Add unit tests covering: short single-material, "X, Y and Z" lists, parentheticals, units, dimensions.
6. Modify the matcher in `src/eval/matchers.py` so that a short gold phrase counts as a TP if it appears (case-insensitive, normalized whitespace) as a substring of any single pred entity, with a token-overlap fallback at ≥ 0.6 Jaccard. Do NOT lower the threshold below 0.6.
7. Write `scripts/eval_honest_v2.py` that re-runs the 10 SWA files using the new phrase extractor + matcher, writes `results/eval_honest_v2.json`, and prints a per-file table.
8. Add the held-out test: pick any 1 RFQ from `data/real_rfqs/reference_real/` or `data/real_rfqs/raw/` that is NOT in `swa_enquiries/`. Run the pipeline. Assert it returns ≥ 1 BOQ item and a non-empty `project_name`. Assert the JSON output for this file is NOT byte-identical to the output for any SWA file (proves no shared cache key).
9. Run `make verify`. It must be green.
10. Append a Z1 section to `docs/wave_status.md` with the new per-file F1 table and a one-line verdict (BETTER / SAME / WORSE than baseline).

## 5. VERIFICATION

```bash
# Baseline (before)
$ python3 scripts/eval_honest.py
EXPECT: entity macro F1 ≈ 0.14 (the current broken number)

# After
$ python3 scripts/eval_honest_v2.py
EXPECT: entity macro F1 ≥ 0.45 on the 10 SWA files
EXPECT: 04_adani F1 > 0.0 (currently 0.0)
EXPECT: 01_gsecl F1 > 0.0 (currently 0.0)

# Held-out freshness
$ pytest tests/integration/test_held_out_fresh_rfq.py -v
EXPECT: 1 passed, asserts no caching

# Anti-cheat still green
$ pytest tests/unit/test_anti_cheat.py -v
EXPECT: all pass

# Full suite
$ make verify
EXPECT: 0 failed

# Lint
$ ruff check src tests scripts
EXPECT: All checks passed!
```

## 6. ACCEPTANCE CRITERIA

ALL must be true:

- [ ] `results/eval_honest_v2.json` shows entity macro F1 ≥ 0.45 (up from 0.142)
- [ ] At least 2 of the 0.0-F1 PDFs (01_gsecl, 04_adani, 09_gem, 10_petc) now have F1 > 0.0
- [ ] XLSX F1 did not regress (still ≥ 0.85)
- [ ] Held-out RFQ test passes — proves no shared cache between files
- [ ] `tests/unit/test_anti_cheat.py` is still green
- [ ] `make verify` is green
- [ ] `ruff check` clean
- [ ] `mypy src/eval src/nlp/patterns --ignore-missing-imports` clean
- [ ] `docs/wave_status.md` updated with new numbers
- [ ] No file under `data/real_rfqs/gold/` was modified

## 7. CONSTRAINTS

- All imports use `src.` prefix. Never `code.`.
- BIOES tagging. Never BIO.
- Entity types from `config.constants.EntityType`. No new entity types.
- Python 3.11–3.13 (NOT 3.14 — typer breaks). Use `python3`, not `python`.
- No back-compat shims, no dead code, no speculative features.
- Do NOT modify `scripts/eval_honest.py` (frozen baseline).
- Do NOT modify any file under `data/real_rfqs/gold/`.
- Do NOT re-train BERT as the solution. The data is the problem; the pattern engine is the fix.
- Do NOT lower the matcher token-overlap threshold below 0.6. That is cheating.
- Do NOT add a "demo mode" that returns canned JSON for known files.
- Do NOT enable the Redis LLM cache (`src/llm/client.py`) for PDF extraction. If it is on, turn it off and prove the numbers do not change.

## 8. DEPENDENCIES

- **Blocked by:** None. Start now.
- **Blocks:** Any follow-up task that wants to ship PDF extraction as production-ready.
- **Parallel-safe with:** `prompts/wave4/AGENT-G2_insulation_ontology.md` and `AGENT-G3_ner_retrain_insulation.md` (different files). NOT safe with anything touching `src/eval/matchers.py` or `src/nlp/patterns/`.
- **Shared files:** `src/eval/matchers.py` is touched only by this task. `docs/wave_status.md` is append-only — coordinate with other agents by reading the file first and adding a clearly-labeled Z1 section.

## 9. GOTCHAS

- Python 3.14 segfaults on this machine. Always `python3` (which is 3.13) for CLI / pipeline runs. CI may run 3.11.
- `data/annotations/*.json` uses `ner_tags` key, but some loaders also accept `labels` — handle both.
- `ConstructionOntology` uses `lookup_material`, `lookup_standard` — not the older `.load()` API.
- The matcher change is the most likely place to accidentally cheat. The test `test_no_self_comparison_any_script` will catch pipeline-output-as-gold, but a loosened matcher threshold is a different kind of cheat and is not auto-caught. Read every `assert` in `src/eval/matchers.py` and prove to yourself that a 0.55-overlap match would still be a real find, not a forced pairing.
- The pattern engine is the production NER. Adding patterns is encouraged; re-training BERT is not. If you find yourself reaching for `scripts/train_lora_ner_v5.py`, stop — that script produces a model that scores 0.188 on real docs.
- `scripts/eval_honest_v2.py` is a NEW script. It calls into the same logic as `eval_honest.py` (do not duplicate the gold-loading code; import it).
- The held-out RFQ must be a file the pipeline has never been run on before. Do not pick from `swa_enquiries/`. Use `data/real_rfqs/reference_real/` or `data/real_rfqs/raw/`.

---

## End-of-task report format

When done, produce a single block:

```
## REPORT: Z1 PDF Honest Recovery

Before: entity macro F1 = 0.142 (results/eval_honest.json)
After:  entity macro F1 = X.XXX (results/eval_honest_v2.json)

Per-file delta (file: before → after):
- 01_gsecl.pdf:    0.000 → X.XXX
- 02_isro.xlsx:   0.857 → X.XXX
- 03_zydus.xlsx:  0.848 → X.XXX
- 04_adani.pdf:   0.000 → X.XXX
- 05_zydus.xlsx:  0.931 → X.XXX
- 09_gem.pdf:     X.XXX → X.XXX
- 10_petc.pdf:    X.XXX → X.XXX

Held-out test: PASS / FAIL
Anti-cheat:    PASS / FAIL
make verify:   PASS / FAIL

Blockers: [none / list]
Deviations from spec: [none / list]
Files modified outside spec: [none / list]
```
