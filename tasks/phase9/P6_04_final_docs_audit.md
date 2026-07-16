# TASK: Final Documentation Audit — Agent-P6-D

## 1. GOAL
This project will not be actively developed after this wave. Make every document tell the truth about the final repo state — not the state at whatever point it was last edited — so whoever opens this repo next (SWA's team, a future developer) gets an accurate picture on day one.

## 2. CONTEXT
This task runs LAST, after P6_01 (fidelity), P6_02 (scope drift removal), and P6_03 (lint/typecheck) have all landed and been verified. Do not start until all three report done and their verification commands actually pass — re-run them yourself, don't trust the report.

Files to audit:
- `README.md` — repo structure, quickstart, feature list
- `HANDOFF.md` — metrics, repo layout table, "core problem" framing
- `CLAUDE.md` — status section (§6), especially any numbers or "active blocker" language
- `deliverables/SWA_HANDOFF_GUIDE.md` — setup steps, fidelity numbers, GitHub branch status
- `docs/CORE_UNDERSTANDING.md` — the grounded-truth doc; numbers must match current reality
- `tasks/phase9/04_LEDGER.md` — should have entries for P6_01/02/03/04 by the time you're done

## 3. DELIVERABLES
- [ ] Every fidelity/F1/pass-rate number in the above files matches a command you personally ran today (paste the actual command output in your task report, not a paraphrase)
- [ ] `README.md` repo structure section matches `ls -d */` output exactly (no stale/removed folders mentioned, no new folders missing)
- [ ] `HANDOFF.md` and `CLAUDE.md` §6 status section rewritten to reflect: fidelity hardening results (P6_01), scope-drift removal (P6_02), lint/type state (P6_03)
- [ ] `deliverables/SWA_HANDOFF_GUIDE.md` §7 (GitHub branch status) updated if the owner has completed the branch consolidation (Track E) by the time you run this — otherwise leave the existing accurate "pending" language alone
- [ ] One final entry appended to `tasks/phase9/04_LEDGER.md` summarizing the whole Phase 6 wave with a timestamp

## 4. STEPS
1. Re-run every verification command from P6_01, P6_02, P6_03's task files yourself — confirm they still pass right now, in this exact repo state
2. `ls -d */` at repo root, diff against what `README.md` claims
3. Update every doc listed in §3 with real, current, re-verified numbers
4. Run the full verification gate one more time:
   ```bash
   make lint && make type && make test
   ```
5. Write the final ledger entry

## 5. VERIFICATION
```bash
make lint
EXPECT: clean (per P6_03's work)

make type
EXPECT: clean or documented remainder (per P6_03's work)

make test
EXPECT: full pass count, no regressions from the pre-Phase-6 baseline

PYTHONPATH=. python3.12 scripts/audit_fidelity_per_doc.py --all
EXPECT: numbers match exactly what you wrote into the docs — copy this exact output into your task report
```

## 6. ACCEPTANCE CRITERIA
- [ ] Every number in every doc is traceable to a command output you ran today
- [ ] Zero references to folders/files that no longer exist
- [ ] Zero references to out-of-scope items removed in P6_02 (ab_test, metrics_observability)
- [ ] `04_LEDGER.md` has a clear, dated, final Phase 6 summary entry

## 7. CONSTRAINTS
- Do not soften or inflate any number to make the project look further along than it is — this is the last chance to get the record straight
- Do not delete `04_LEDGER.md` history — append only
- If P6_01/02/03 haven't actually landed cleanly when you start, stop and report that instead of writing docs against a broken state

## 8. DEPENDENCIES
- **Blocked by:** P6_01, P6_02, P6_03 (all three must be verified-complete first)
- **Blocks:** Nothing (this is the last automated task)
- **Parallel-safe with:** None (must run after the others)

## 9. GOTCHAS
- The ledger (`04_LEDGER.md`) has a long history of agents writing premature "done" entries that turned out to be false when independently re-checked — do not repeat that pattern; every claim in your entry must be something you personally re-ran
