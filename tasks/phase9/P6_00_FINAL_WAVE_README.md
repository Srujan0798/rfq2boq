# Phase 6 — FINAL WAVE (project close-out)

**Status:** This is the last planned wave. The internship report has been submitted (or is about to be). After this wave lands and is verified, this project will not be actively developed again — treat every task below as "make it right, because no one is coming back to fix it later."

**Dispatch order:** Tracks A–C are parallel-safe (different file sets, no shared state). Track D (docs audit) must run LAST, after A–C land, because it verifies the final repo state. The GitHub branch/history consolidation (Track E) is handled by the owner directly — not dispatched to an agent — because a botched force-push or history rewrite is very hard to undo and there is no one left to catch it afterward.

```
Track A (corpus fidelity)  ─┐
Track B (scope-drift)       ├─→  Track D (final docs audit)  →  Track E (owner: git history + branch merge)
Track C (lint/typecheck)   ─┘
```

---

## Track A — `P6_01_corpus_fidelity_hardening.md`
Fix the 20/33 broader-corpus documents currently failing the fidelity audit, including the `07_grew` regression (was 100%, now 9/11).

## Track B — `P6_02_scope_drift_removal.md`
Remove `src/api/ab_test.py` and `src/api/metrics_observability.py` — explicitly out of scope per CLAUDE.md ("no A/B routing, no observability stack") — without breaking `src/cli/main.py` or `tests/integration/test_api.py`.

## Track C — `P6_03_lint_typecheck_cleanup.md`
Clear the remaining 28 ruff findings and run a full mypy pass across `src/`.

## Track D — `P6_04_final_docs_audit.md`
After A–C land: verify every doc (README, HANDOFF.md, CLAUDE.md, SWA_HANDOFF_GUIDE.md) states numbers and repo structure that match reality, not history. Run the full verification gate one last time and record the final honest numbers in `04_LEDGER.md`.

## Track E — Owner-only: GitHub branch consolidation
`main` on GitHub currently holds old contaminated history (including a fabricated "100% F1 — ship it" commit) at 18GB of `.git` history. `phase9-final` (this branch) needs to become the new `main`. Requires `git filter-repo` to strip oversized historical blobs before a force-push will succeed. Handled directly with the owner present, not dispatched.

---

## Non-negotiable for every task in this wave
- Read `tasks/phase9/02_ANTI_CHEAT_PROTOCOL.md` before starting.
- Never grade your own change against your own output — use `scripts/audit_fidelity_per_doc.py --all`, which compares against `data/real_rfqs/source_truth.json` (independent of the pipeline).
- Report using the format in `prompts/TASK_TEMPLATE.md` §"End-of-task report format".
- Append your result to `tasks/phase9/04_LEDGER.md` when done — one line, dated, with the actual command output, not a paraphrase.
