# TASK P0_01: Verify the clean-room workspace + capture the fidelity baseline — Agent-P0-1

## 1. GOAL
Confirm the protected Phase-9 workspace is exactly what it claims to be (clean stack, isolated, importable) and record the sacred-10 fidelity baseline that every later task is measured against.

> NOTE: the workspace-creation half of this task was executed by the orchestrator on 2026-07-06 after the rogue swarm deleted the first plan copy (see `04_LEDGER.md` incident #13). This repo is a **standalone clone**, not a worktree. Your job is independent verification + baseline capture.

## 2. CONTEXT
Files to read FIRST (in order):
- `tasks/phase9/00_README.md` — protocol + owner decisions D1–D5, incl. the workspace change
- `tasks/phase9/01_STATE_OF_THE_WORLD.md` — repo topology (§4)
- `tasks/phase9/02_ANTI_CHEAT_PROTOCOL.md` — Rules 7 (clean room) and 6 (honest reporting)

Current state:
- This repo `/Users/srujansai/rfq2boq-phase9` is on `phase9-final`, expected base `0e1cd4e` (clean stack: `6f46588 → 4ff09cd → bbc00fc → f3affab → 0e1cd4e`) plus the plan-folder commit(s).
- `origin` points at the CONTAMINATED Desktop repo — read-only for P5_04 triage; you never fetch from it.
- Branch `w3-tip-untriaged` holds 2 unverified extra commits — reference only, not yours to use.

## 3. DELIVERABLES
- [ ] Verification outputs for every command in §5, pasted verbatim in your REPORT
- [ ] `results/FIDELITY_REPORT.md` — fresh sacred-10 fidelity baseline from `scripts/measure_fidelity.py --all`, committed
- [ ] One commit: "P0_01: workspace verified + fidelity baseline"

## 4. STEPS
1. Read context files (Section 2).
2. Verify the base and isolation (MANDATORY — refuse to continue on any failure):
   ```bash
   cd /Users/srujansai/rfq2boq-phase9
   git branch --show-current                          # EXPECT: phase9-final
   git merge-base --is-ancestor 0e1cd4e HEAD && echo BASE-OK
   git log --oneline 0e1cd4e~4..0e1cd4e               # EXPECT: exactly the 5-commit clean stack
   git log --oneline 0e1cd4e..HEAD                    # EXPECT: only plan-folder/docs commits, no src/ or data/ changes
   git diff 0e1cd4e..HEAD --stat -- src/ data/ config/ scripts/ tests/   # EXPECT: empty
   ```
3. Environment sanity:
   ```bash
   python3 -c "from src.nlp.pipeline import NLPPipeline" && echo IMPORTS-OK
   python3 scripts/check_gold_provenance.py           # EXPECT: 0 forged, exit 0
   ```
4. Capture the baseline:
   ```bash
   python3 scripts/measure_fidelity.py --all | tee /tmp/p001_baseline.txt | tail -15
   ```
   Copy the full per-doc table into `results/FIDELITY_REPORT.md` (fresh file content, dated).
5. Commit; produce the REPORT (template in `CLAUDE.md` §11) including the fidelity baseline table verbatim.

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
git branch --show-current                 # EXPECT: phase9-final
ls tasks/phase9 | wc -l                   # EXPECT: 27
git status --short                        # EXPECT: empty after your commit
python3 scripts/check_gold_provenance.py  # EXPECT: 0 forged, exit 0
python3 scripts/measure_fidelity.py --all | tail -15   # EXPECT: matches your committed report exactly
```

## 6. ACCEPTANCE CRITERIA
- [ ] All §5 commands produce expected output
- [ ] No src/data/config/scripts diffs between `0e1cd4e` and HEAD (plan/docs only)
- [ ] Fidelity baseline captured and matches the clean-stack expectation: 01,03,04,06,07,09,10 PASS; 02/08 missing exactly 1 section-header row each; 05 over-capture 48-vs-20
- [ ] Zero interaction with the Desktop repo or `origin`

## 7. CONSTRAINTS
- DO NOT fetch/pull from `origin`; DO NOT read anything from `/Users/srujansai/Desktop/rfq2boq`
- DO NOT touch `data/real_rfqs/gold/` (that is P0_02) or any eval script (P0_03)
- DO NOT check out or merge `w3-tip-untriaged`
- All the standing constraints in `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** None (first task)
- **Blocks:** everything else
- **Parallel-safe with:** nothing
- **Shared files:** `results/FIDELITY_REPORT.md`

## 9. GOTCHAS
- If the fidelity baseline differs from the §6 expectation, do not chase it — report the exact table and stop; the orchestrator decides.
- Python deps: this clone shares the machine's Python environment; if an import fails, report the exact ImportError — do not pip-install anything without listing it in the report.
- `measure_fidelity.py` on the full set takes minutes (big GeM PDFs) — that's normal; a HANG (>15 min on one doc) is a finding to report, not to wait out.
