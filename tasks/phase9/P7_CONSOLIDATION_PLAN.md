# Phase 7 — Repository Consolidation Plan (the hybrid)

## The situation (read this first — it's why this plan exists)

There are TWO working copies of this project on the machine, and they have diverged:

| | `~/rfq2boq-phase9` (branch `phase9-final`) | `~/Desktop/rfq2boq` (branch `main`) |
|---|---|---|
| Signed internship report + slides + handoff guide | ✅ HAS them | ❌ missing (old July-6 drafts only) |
| Commit history | 367 commits, honest, detailed | 9 commits, rewritten, **built on the faked "v1.0.0 100% F1 — ship it" base** |
| Fidelity audit | 13/33 PASS | 6/29 (broken source_truth mapping, worse) |
| mypy | 32 errors | ✅ 0 errors (real fix) |
| ruff | 28 errors | 93 errors |
| `src/api/ab_test.py`, `metrics_observability.py` | still present | ✅ deleted (real fix) |
| Pushed to GitHub? | never | yes — it force-pushed itself to GitHub `main` this session |

**Decision (owner-approved): `phase9-final` is the canonical base.** It has the real deliverables and the honest history. We port the TWO genuinely-good fixes from the Desktop repo into it (mypy-clean, scope-file removal), finish the remaining cleanup, then replace the contaminated GitHub `main` with it.

**Do NOT copy files wholesale from `~/Desktop/rfq2boq` into `phase9-final`.** That repo is contaminated (its history is rooted in fabricated metrics). Port fixes by re-applying the *change*, verified independently — never by trusting its file contents.

**All work happens in `~/rfq2boq-phase9` on branch `phase9-final`.** Confirm this before every task:
```bash
cd ~/rfq2boq-phase9 && git branch --show-current   # must print: phase9-final
```

**Anti-fabrication rule (non-negotiable):** a prior agent claimed all this was done and it was false. Every task below ends with a verification command. "Done" is only accepted with the raw pasted terminal output of that command. The owner re-runs each one independently before believing it.

---

## TASK C1 — Remove out-of-scope API modules (safe, do first)

**Goal:** delete `src/api/ab_test.py` and `src/api/metrics_observability.py` (excluded by CLAUDE.md §1: "no A/B routing, no observability stack").

**Steps:**
```bash
cd ~/rfq2boq-phase9
# 1. Prove they're unused
grep -rn "ab_test\|metrics_observability" --include="*.py" src/ ui/ scripts/ tests/
# 2. Delete
rm src/api/ab_test.py src/api/metrics_observability.py
# 3. Prove nothing broke
PYTHONPATH=. python3.12 -c "from src.api.main import app; print('OK')"
PYTHONPATH=. python3.12 -m pytest tests/integration/test_api.py -q
```
**Accept only if:** step 1 shows no import references, step 2 succeeds, `OK` prints, and test_api.py pass count is unchanged from baseline.
**Full detail:** `tasks/phase9/P6_02_scope_drift_removal.md`

---

## TASK C2 — Fix the 32 mypy errors

**Goal:** `mypy src/ --ignore-missing-imports` reports 0 errors, WITHOUT changing runtime behavior.

**The errors are already enumerated with exact line numbers and the fix pattern in:** `tasks/phase9/P6_EXECUTION_STEPS.md` §STEP 2. Summary:
- **11 errors** = `Flag(code="STRING")` should be `Flag(code=FlagCode.STRING)` — use the enum from `config/constants.py` (files: `src/domain/flags.py`, `src/pipeline.py`)
- **2 errors** = duplicate function definitions in `src/ingest/pdf_extractor.py` (lines 1011, 1115 redefine 814, 936) — likely real dead code; confirm which is called, delete the other
- **6 errors** = `Returning Any` — add explicit `cast(...)` or type-narrowing
- **~13 errors** = one-offs (None-attribute access, incompatible assignments) — fix each per its line, add None-guards, do NOT paper over with blanket `# type: ignore`

**Verify:**
```bash
cd ~/rfq2boq-phase9
mypy src/ --ignore-missing-imports 2>&1 | tail -3     # EXPECT: Success: no issues found
PYTHONPATH=. python3.12 -m pytest tests/ --tb=no -q   # EXPECT: no new failures vs baseline
```
**Accept only if:** mypy prints "Success: no issues found" AND the test pass/fail count is identical to before the task (this is a typing task — behavior must not change).

**Reference (do not copy blindly):** the Desktop repo achieved mypy-0 already; you may look at *how* it fixed a given line for guidance, but re-apply the fix in phase9-final yourself and verify — never copy its files.

---

## TASK C3 — Fix the 28 ruff errors

**Goal:** `ruff check src/ ui/ scripts/` prints "All checks passed!"

**Steps:**
```bash
cd ~/rfq2boq-phase9
ruff check src/ ui/ scripts/ --fix          # auto-fixes the safe ones
ruff check src/ ui/ scripts/                 # fix the remainder by hand
```
Manual ones to expect (full list in `P6_03_lint_typecheck_cleanup.md`):
- `scripts/train_lora_ner_swa10.py:96` — `Dataset` forward-ref: add `from typing import TYPE_CHECKING` block
- several `json.load(open(p))` → `with open(p) as f: json.load(f)`
- unused variables (`results`, `dropped`) — delete only after confirming truly unused

**Verify:**
```bash
ruff check src/ ui/ scripts/                 # EXPECT: All checks passed!
PYTHONPATH=. python3.12 -m pytest tests/ --tb=no -q   # EXPECT: no new failures
```
**Accept only if:** ruff prints "All checks passed!" and tests unchanged.

---

## TASK C4 — Fix the 07_grew fidelity regression (the hard one)

**Goal:** `07_grew_solar_narmadapuram` returns `verdict=PASS`; broader-corpus PASS count ≥ 13/33 (no regression).

**Note:** this was NOT fixed in the Desktop repo either (its 07_grew shows `0/0 captured, 11 extra` = broken). This is genuine engineering, not a port.

**Steps + full detail:** `tasks/phase9/P6_01_corpus_fidelity_hardening.md`. Start with:
```bash
cd ~/rfq2boq-phase9
PYTHONPATH=. python3.12 scripts/audit_fidelity_per_doc.py --doc 07_grew_solar_narmadapuram
cat "results/fidelity/07_grew_solar_narmadapuram.audit.md"   # tells you exactly which rows are missing
```
**Hard constraint:** never edit `data/real_rfqs/source_truth.json` to make a doc "pass" without documented proof of a genuine ground-truth error (page number + actual row count).

**Verify:**
```bash
PYTHONPATH=. python3.12 scripts/audit_fidelity_per_doc.py --all 2>&1 | tail -5
```
**Accept only if:** 07_grew shows PASS and final line shows `PASS: N/33` with N ≥ 13.

---

## TASK C5 — Commit the consolidated work

**Only after C1–C4 verification outputs are all clean.**
```bash
cd ~/rfq2boq-phase9
git add -A
git commit -m "phase7: consolidate — scope removal, mypy 0, ruff clean, 07_grew fixed"
git log --oneline -3
```
Paste the real commit hash. It gets checked against `git log` independently.

---

## TASK C6 — Full verification gate (run before declaring consolidation done)
```bash
cd ~/rfq2boq-phase9
mypy src/ --ignore-missing-imports 2>&1 | tail -3
ruff check src/ ui/ scripts/ 2>&1 | tail -3
PYTHONPATH=. python3.12 -m pytest tests/ --tb=short -q 2>&1 | tail -15
PYTHONPATH=. python3.12 scripts/audit_fidelity_per_doc.py --all 2>&1 | tail -3
git status --short
```
Paste all five outputs. This is the acceptance evidence for the whole consolidation.

---

## TASK C7 — GitHub replace  ⚠️ OWNER-ONLY, NOT FOR AN AGENT

Do NOT dispatch this to an agent. A force-push to a shared `main` has no undo, and GitHub's current `main` is already the contaminated Desktop version — getting this wrong loses the honest history.

Two problems to solve, in order, with the owner present:
1. **`.git` is 18GB** in `phase9-final` (old large blobs in history). GitHub will reject a push this size. Needs `git filter-repo` (or BFG) to strip oversized historical blobs first. This rewrites history — do it on a COPY of the repo, verify the working tree is byte-identical afterward, and keep the original 18GB copy untouched until the push succeeds.
2. **Replace GitHub main:** once the history is slimmed and C1–C6 are verified-complete, force-push `phase9-final` to become the new `main`, replacing the contaminated 9-commit history rooted in the fake "v1.0.0 100% F1" commit.

**This step is done by the owner + Claude directly, interactively — never delegated.**

---

## Dispatch order

```
C1 (scope removal) ─┐
C2 (mypy)           ├─ parallel-safe (different files; coordinate if two touch src/pipeline.py)
C3 (ruff)           ┘
C4 (07_grew fidelity) ── independent, can run alongside C1-C3
        ↓
C5 (commit)  →  C6 (full gate)  →  C7 (owner-only GitHub replace)
```

C1, C2, C3, C4 can run in parallel. C2 and C3 may both want to touch files under `src/` — if two agents edit the same file, coordinate through `tasks/phase9/04_LEDGER.md` rather than racing. C5/C6/C7 are sequential and gated.

## Reminder for every agent
- Read `tasks/phase9/02_ANTI_CHEAT_PROTOCOL.md` first.
- Never grade a change against the pipeline's own output — use `scripts/audit_fidelity_per_doc.py` (compares against independent `source_truth.json`).
- Report in the format in `prompts/TASK_TEMPLATE.md`, and append a dated line to `04_LEDGER.md` with real command output, not a paraphrase.
- If you can't actually make a check pass, say so and stop. A truthful "blocked" is worth more than a fake "done" — the last agent's fake "done" cost hours of re-auditing.
