# TASK: Lint + Typecheck Final Cleanup — Agent-P6-C

## 1. GOAL
Clear the remaining 28 ruff findings and get a clean (or fully-documented) mypy pass across `src/` — this is the last wave, so lint/type debt does not get another chance to be paid down later.

## 2. CONTEXT
Files to read FIRST:
- `pyproject.toml` — current ruff/mypy configuration
- Run `ruff check src/ ui/ scripts/ --statistics` yourself first — do not trust any count from an earlier session, the codebase has changed since

Known remaining findings (verify current state yourself, this may have shifted):
- Files with issues: `scripts/audit_fidelity_per_doc.py`, `scripts/clean_gold.py`, `scripts/clean_pseudo_labels.py`, `scripts/draft_source_truth_extras.py`, `scripts/eval_lora_on_swa_holdout.py`, `scripts/generate_all_bioes_training.py`, `scripts/train_lora_ner_real_only.py`, `scripts/train_lora_ner_swa10.py`, `scripts/train_lora_ner_v5.py`, `scripts/verify_swa10_demo.py`
- Categories: `SIM102` (collapsible-if), `E402` (import not at top), `SIM115` (open without context manager), `SIM103`/`SIM108` (needless bool / if-else), `B007` (unused loop var), `F841` (unused variable), `F821` (undefined name — one false-positive in a string type annotation in `train_lora_ner_swa10.py:96`, verify before "fixing")

## 3. DELIVERABLES
- [ ] `ruff check src/ ui/ scripts/` returns zero findings, OR each remaining finding has an explicit `# noqa: CODE` with a one-line reason (not a blanket suppression)
- [ ] `mypy src/ --ignore-missing-imports` run and either clean or every error triaged (fixed, or documented as a known pydantic/streamlit typing limitation)
- [ ] No behavior changes — this is a cleanup task, not a refactor. If a fix changes runtime behavior, stop and flag it instead of applying it.

## 4. STEPS
1. `ruff check src/ ui/ scripts/ --statistics` — get true current count
2. Fix each finding file by file — for `E402` (import not at top), only reorder if it's safe (some intentional late imports exist for lazy-loading heavy deps like `torch`/`transformers` — check `git log` or a comment before moving them)
3. For `SIM115` (file opened without context manager) in `scripts/verify_swa10_demo.py` and similar: convert to `with open(...) as f:` pattern
4. For `F821` in `scripts/train_lora_ner_swa10.py:96`: this is a string-quoted forward-reference type annotation (`"Dataset"`) where the import happens inside the function body — this is valid Python, not a real bug. Either add `from datasets import Dataset` under `TYPE_CHECKING` at module level, or add a scoped `# noqa: F821` with a comment explaining why.
5. Run `mypy src/ --ignore-missing-imports`, fix straightforward type errors, document (don't silently ignore) anything caused by third-party stub gaps
6. Re-run the full test suite to confirm zero behavior change

## 5. VERIFICATION
```bash
ruff check src/ ui/ scripts/
EXPECT: All checks passed!

mypy src/ --ignore-missing-imports
EXPECT: Success: no issues found (or a documented, justified remainder)

PYTHONPATH=. python3.12 -m pytest tests/ --tb=no -q
EXPECT: identical pass/fail counts to the pre-task baseline — this task must not change behavior
```

## 6. ACCEPTANCE CRITERIA
- [ ] Zero unexplained ruff findings
- [ ] mypy clean or every remaining error has a one-line documented reason
- [ ] Test suite pass/fail counts unchanged from before this task started
- [ ] No runtime behavior changes anywhere (this is the acid test — if in doubt, don't apply the "fix")

## 7. CONSTRAINTS
- Do not touch `src/pipeline.py`, `src/ingest/` (owned by P6_01) or `src/api/` (owned by P6_02) if avoidable — if a lint fix is needed there, coordinate rather than silently editing files another task owns
- Do not use `--unsafe-fixes` without manually reviewing every resulting diff
- Do not add `# type: ignore` or `# noqa` without a same-line reason comment

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** P6_04
- **Parallel-safe with:** P6_01, P6_02 (avoid touching `src/pipeline.py`, `src/ingest/`, `src/api/` if those tasks are running concurrently — coordinate via the ledger if a conflict shows up)
- **Shared files:** Potential overlap with P6_01/P6_02 only if lint fixes touch their owned files — check the ledger before editing those paths

## 9. GOTCHAS
- Some "unused imports" in training scripts are intentionally lazy-loaded to avoid pulling in `torch`/`transformers` at module import time for scripts that don't always need them — verify before removing
- Python 3.14 has a typer/click bug — run all verification with 3.11–3.13
