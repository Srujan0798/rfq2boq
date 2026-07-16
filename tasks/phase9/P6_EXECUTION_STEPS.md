# Phase 6 — Literal Execution Steps (anti-fabrication version)

**Why this file exists:** a prior agent claimed all of Phase 6 was done (07_grew fixed, files deleted, mypy/ruff clean, .git shrunk, force-pushed) — every single claim was false when independently re-verified. Zero commits, zero file changes, .git still 18GB. This file replaces vague task descriptions with literal commands and the *exact current error output*, so there is no ambiguity to hide behind.

**Rule for the agent doing this:** after every step, paste the raw terminal output here or back to the owner. "Done" without pasted output is not accepted. The owner (or Claude, reviewing on their behalf) will re-run every command independently before believing any of this is complete.

---

## STEP 0 — Baseline (run first, save the output)

```bash
cd ~/rfq2boq-phase9
git log --oneline -3
git status --short
du -sh .git
mypy src/ --ignore-missing-imports 2>&1 | tail -3
ruff check src/ ui/ scripts/ 2>&1 | tail -3
PYTHONPATH=. python3.12 scripts/audit_fidelity_per_doc.py --all 2>&1 | tail -3
```
Paste this whole block's output before doing anything else. This is the "before" picture everything else gets compared against.

---

## STEP 1 — Delete the two out-of-scope files (P6_02, ~2 minutes, lowest risk)

```bash
cd ~/rfq2boq-phase9
grep -rn "from src.api.ab_test\|from src.api.metrics_observability\|import ab_test\|import metrics_observability" --include="*.py" .
```
This must return **nothing** — confirmed already: neither file is imported anywhere, they are dead code.

```bash
rm src/api/ab_test.py src/api/metrics_observability.py
PYTHONPATH=. python3.12 -c "from src.api.main import app; print('OK')"
```
**Expected:** `OK` — the app still imports fine with the files gone.

```bash
PYTHONPATH=. python3.12 -m pytest tests/integration/test_api.py -v
```
**Expected:** same pass count as Step 0's baseline (these files were unused, so nothing should break).

---

## STEP 2 — Fix mypy errors one by one (P6_03, ~32 errors currently)

Do NOT run a bulk auto-fixer. Fix each of these by hand, in this order (grouped by pattern so the same fix repeats):

### 2a. `Flag(code="...")` should use the `FlagCode` enum, not a raw string (11 occurrences)

Files/lines right now: `src/domain/flags.py:241,252,264,276,286,296,306,317,327,337`, `src/pipeline.py:91,117,1039,1047`

For each one: open `config/constants.py`, find the `FlagCode` enum (line 92), confirm the member name matches the string (e.g. `code="LOW_CONFIDENCE"` → check `FlagCode.LOW_CONFIDENCE` exists). Then change:
```python
code="LOW_CONFIDENCE",
```
to:
```python
code=FlagCode.LOW_CONFIDENCE,
```
If a string used doesn't have a matching `FlagCode` member, that's a real bug (a flag code that isn't in the closed set) — add it to the `FlagCode` enum in `config/constants.py` rather than inventing a workaround.

### 2b. Duplicate function definitions (2 occurrences — likely real bugs, not just typing)
```
src/ingest/pdf_extractor.py:1011  Name "extract_column_aware_tables" already defined on line 814
src/ingest/pdf_extractor.py:1115  Name "extract_column_aware_diagnostics" already defined on line 936
```
Open the file, compare both definitions of each function. One is almost certainly dead/leftover code from a merge. Confirm which one is actually called (`grep -n "extract_column_aware_tables(" src/`), delete the other, do not silently rename.

### 2c. `Returning Any from function declared to return X` (6 occurrences)
```
src/domain/fidelity.py:240, src/export/excel_generator.py:110,
src/preproc/document_structure.py:261, src/preproc/document_structure.py:741,
src/ingest/table_extractor.py:69, src/pipeline.py:512
```
Each of these returns a value mypy can't narrow to the declared return type. Add an explicit cast or an assertion at the return site, e.g. `return cast(list[DocumentSection], result)` or add a runtime type check. Do not just widen the return type to `Any` — that hides the bug instead of fixing it.

### 2d. Remaining one-off errors (fix individually, read the actual line):
```
src/preproc/document_structure.py:946   Incompatible types in assignment (DocumentSection | None vs DocumentSection)
src/preproc/document_structure.py:1105  Incompatible types in assignment (set[str] vs list[dict])
src/preproc/document_structure.py:1106  Unsupported left operand type for & (list[dict])
src/domain/models.py:162                Cannot assign to a type
src/domain/boq_assembler.py:606,612     Item "None" of "EntitySpan | None" has no attribute "conf"
src/nlp/catalog_matcher.py:317,318      Item "None" of "CatalogMatch | None" has no attribute "confidence"
src/api/routes/upload.py:285,286        Incompatible types (NLPPipeline vs XLSXRowPipeline; no .process())
```
For the `X | None has no attribute` errors: add a None-check before use (`if span is None: continue` or similar) — do not just add `# type: ignore`, these usually indicate a real code path where a None can reach a `.conf`/`.confidence` access unguarded, which is worth understanding before dismissing.

Verify after every 3-4 fixes:
```bash
mypy src/ --ignore-missing-imports 2>&1 | tail -3
```
Watch the error count actually drop.

---

## STEP 3 — Fix the 28 ruff findings (P6_03 continued)

```bash
ruff check src/ ui/ scripts/ --fix
```
This auto-fixes what it safely can. Then fix the rest by hand — full current list is in `tasks/phase9/P6_03_lint_typecheck_cleanup.md`. Key ones needing manual attention:
- `scripts/train_lora_ner_swa10.py:96` — `Dataset` used in a return type annotation before its deferred import; add `from typing import TYPE_CHECKING` + `if TYPE_CHECKING: from datasets import Dataset` at module top
- Multiple `json.load(open(path))` → change to `with open(path) as f: json.load(f)`
- `scripts/generate_all_bioes_training.py:507` — unused `results = {}` variable, delete it if truly unused (check first)

Verify:
```bash
ruff check src/ ui/ scripts/
```
**Expected:** `All checks passed!`

---

## STEP 4 — Fix the 07_grew regression and broader corpus fidelity (P6_01 — the hard one)

```bash
PYTHONPATH=. python3.12 scripts/audit_fidelity_per_doc.py --doc 07_grew_solar_narmadapuram
cat "results/fidelity/07_grew_solar_narmadapuram.audit.md"
```
Read the actual audit report — it tells you exactly which rows are missing. Cross-reference against the real PDF (`data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/`). Full task detail is in `tasks/phase9/P6_01_corpus_fidelity_hardening.md` — follow it exactly, especially the constraint against editing `source_truth.json` without documented proof.

Verify:
```bash
PYTHONPATH=. python3.12 scripts/audit_fidelity_per_doc.py --all 2>&1 | tail -5
```
**Expected:** `07_grew_solar_narmadapuram` shows `verdict=PASS`, and the final `PASS: N/33` line shows N ≥ 13 (must not regress below the current baseline).

---

## STEP 5 — Full regression check (run before claiming anything is done)

```bash
PYTHONPATH=. python3.12 -m pytest tests/ --tb=short -q 2>&1 | tail -20
mypy src/ --ignore-missing-imports 2>&1 | tail -3
ruff check src/ ui/ scripts/ 2>&1 | tail -3
PYTHONPATH=. python3.12 scripts/audit_fidelity_per_doc.py --all 2>&1 | tail -3
git status --short
```
Paste all five outputs. This is what gets independently re-checked before anything is accepted as complete.

---

## STEP 6 — Commit (only after Step 5's output is clean/improved)

```bash
git add -A
git commit -m "Phase 6: remove scope-drift modules, fix mypy/ruff, fix fidelity regressions"
git log --oneline -3
```
Paste the commit hash. This is checked against `git log` independently — a claim without a real commit hash in the actual repo history is not accepted.

---

## STEP 7 — Docs audit (P6_04 — do this last, after Steps 1-6 are verified)
Follow `tasks/phase9/P6_04_final_docs_audit.md` exactly.

---

## NOT in this list: GitHub branch/history consolidation
The `.git` history rewrite + force-push to `main` is being handled directly by the owner, not an agent — a bad force-push to a shared branch has no undo. Do not attempt this step.
