# RFQ2BOQ Task Assignment Template

Every task assigned to an external agent (MiniMax/Codex/etc.) must follow this 9-section structure. Vague task specs waste tokens — every prompt must be a complete, executable contract.

---

## How to use this template

1. Copy the section structure below
2. Fill every section — do not skip
3. Be specific: file paths, function signatures, exact commands, expected output
4. Hand the completed prompt to one external agent
5. After agent reports done, run the VERIFICATION commands yourself before accepting

---

## TEMPLATE STRUCTURE

```markdown
# TASK: [Short Name] — Agent-[N]

## 1. GOAL
[One sentence: why this exists and what it unlocks]

## 2. CONTEXT
Files to read FIRST (in order):
- `path/to/file1.py` — [what to learn from it]
- `path/to/file2.md` — [what to learn from it]

Current state of the area being modified:
- [What exists]
- [What's broken or missing]
- [What depends on this]

## 3. DELIVERABLES
Create or modify EXACTLY these files:
- [ ] `path/to/new_file.py` — [class/function name and one-line purpose]
- [ ] `tests/path/test_new_file.py` — [expected test count]
- [ ] `path/to/existing.py` — [specific edit description]

## 4. STEPS
1. Read context files (Section 2)
2. Run `[exact command]` to verify [precondition]
3. Implement `ClassName` in `path/file.py` with this signature:
   ```python
   class ClassName:
       def method(self, arg: Type) -> ReturnType:
           ...
   ```
4. Add tests in `tests/path/test_X.py`
5. Run verification (Section 5)

## 5. VERIFICATION
Run these commands. Each must produce the expected output:

```bash
# Test the new code
$ python3 -m pytest tests/path/test_X.py -v
EXPECT: N passed, 0 failed

# Verify imports resolve
$ python3 -c "from src.module import Class; print(Class().method())"
EXPECT: [specific output]

# No regressions
$ python3 -m pytest tests/ --tb=no
EXPECT: All previously-passing tests still pass

# Lint
$ python3 -m ruff check src/module
EXPECT: All checks passed!
```

## 6. ACCEPTANCE CRITERIA
Objective pass/fail checks. ALL must be true:
- [ ] All commands in Section 5 produce expected output
- [ ] Coverage of new code ≥ 80% (verify via `pytest --cov=src.module`)
- [ ] No ruff errors
- [ ] No mypy errors (`mypy src/module --ignore-missing-imports`)
- [ ] [Domain metric] ≥ [threshold] — e.g., F1 ≥ 0.65 on real test set
- [ ] Documentation updated in [specific files]

## 7. CONSTRAINTS
Hard rules — violating ANY of these = task failure:
- All imports use `src.` prefix (NOT `code.`)
- BIOES tagging (NOT BIO) — use `config.constants.BIOES_LABELS`
- Entity types come from `config.constants.EntityType` enum
- Relation types from `config.constants.RelationType`
- Python 3.11+ syntax, type hints required
- DO NOT modify: `config/constants.py`, `config/settings.py`, existing passing tests
- DO NOT add: backwards-compat shims, dead code, speculative features

## 8. DEPENDENCIES
- **Blocked by:** [Task IDs that must complete first, or "None"]
- **Blocks:** [Task IDs that wait on this]
- **Parallel-safe with:** [Task IDs that can run concurrently with this]
- **Shared files:** [List any files this task touches that another task also touches — flag conflicts]

## 9. GOTCHAS
Known pitfalls and how to avoid them:
- Python 3.14 has a typer/click `make_metavar()` bug — use Python 3.11-3.13 for CLI testing
- MPS available on this machine, CUDA is not — use `torch.device("mps" if torch.backends.mps.is_available() else "cpu")`
- `data/annotations/*.json` uses `ner_tags` key, but `dataset.py` may expect `labels` — handle both
- Real-world F1 << synthetic F1 (~67% vs ~99%) due to template overfitting — calibrate expectations
- ConstructionOntology has lookup methods (lookup_material, lookup_standard), not the older `.load()` API
- LayoutLMv3 needs bboxes in 0-1000 normalized range
- [Add task-specific gotchas as discovered]

---

## End-of-task report format
When agent reports done, they must produce a one-block summary like:

```
## REPORT: [Task Name]

Deliverables:
- [path] — [created/modified]
- [path] — [created/modified]

Verification:
- pytest: N passed, 0 failed
- ruff: clean
- coverage: XX%
- [metric]: X.XX

Blockers encountered: [none / list]
Deviations from spec: [none / list with rationale]
Files modified outside spec: [none / list]
```

This format makes my audit fast.
```

---

## Example: a fully-filled task prompt

See `prompts/EXAMPLE_FILLED_TASK.md` for a complete example using this template.
