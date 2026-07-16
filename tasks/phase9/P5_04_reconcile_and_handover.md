# TASK P5_04: Triage-salvage from the chaos repo, push, and hand over — Agent-P5-4 (+ OWNER)

## 1. GOAL
Close the project cleanly: salvage anything genuinely valuable from the abandoned Desktop repo (phase9 is the base; chaos-repo material enters only after re-verification), push the final state to GitHub, and leave a repository a stranger could pick up.

## 2. CONTEXT
Files to read FIRST (in order):
- `tasks/phase9/01_STATE_OF_THE_WORLD.md` §4 — the topology this task finally resolves
- `tasks/sonnet/LEDGER.md` + `tasks/phase9/04_LEDGER.md` — the full incident record (what in the chaos repo is known-poisoned vs unknown)
- `git fetch origin && git log 6f46588..origin/main --oneline` — the divergence to triage (read-only fetch; the ONE sanctioned origin interaction)

Current state (verify — it will have drifted):
- `phase9-final` (this repo) holds the complete verified project. The Desktop repo's `main` + `phase8-clean-slate` hold dozens of rogue commits (tampered gold, eval edits, fake reports, a fake "v1.0.0" tag, fake "wave5" work items) INTERLEAVED with possibly-salvageable fragments. The `w3-tip-untriaged` branch here (2 commits) was already handled by P1_04/P3_03 — confirm its ledger disposition.
- The rogue swarm must be DEAD before this task starts (owner gate #1). If it was never killed, its repo kept mutating the whole time — triage the final frozen state only.
- Remote: `github.com/Srujan0798/rfq2boq` — verify current reality with `git ls-remote` at task start; the swarm may have attempted pushes since the last check.

## 3. DELIVERABLES
- [ ] **[OWNER GATE #1 — Srujan confirms the opencode swarm is dead** (`ps aux | grep opencode` clean) **and the Desktop repo has stopped moving** (`git -C ~/Desktop/rfq2boq log -1` stable across an hour). A moving target can't be triaged.]
- [ ] `results/reconciliation/CHAOS_TRIAGE.md` — every commit `6f46588..origin/main` (and `..origin/phase8-clean-slate`) classified: POISONED (touches gold/eval/tests-expectations — discard) / DUPLICATE (phase9 has it better — discard) / CANDIDATE (potentially valuable, named diff hunks); for each CANDIDATE: what it is, why valuable, what re-verification it needs
- [ ] Owner-approved CANDIDATEs re-implemented (never cherry-picked — rewritten from the diff as reference, with tests, through the normal task discipline) — expect ZERO to few; the default answer is discard
- [ ] Repo end-state executed with owner: this repo's `phase9-final` merged to a fresh `main` here; Desktop repo archived (owner moves the folder to e.g. `~/archive/rfq2boq-chaos-2026-07/` or keeps it — his call; it is never deleted, it's evidence)
- [ ] Push: **owner runs it** (his credentials; rotate the possibly-leaked token FIRST): this repo → `github.com/Srujan0798/rfq2boq` as the new `main` (owner decides force-push vs new-repo; prepared commands + tradeoffs in the triage doc)
- [ ] `HANDOFF.md` rewritten: current state, how to run, where gold/models live, model-weights distribution (weights gitignored — document the local path + packaging), the annotation runway (how to continue toward 0.88), the intake protocol pointer
- [ ] `CLAUDE.md` §6 + `docs/wave_status.md` updated in THIS repo: phase9 complete, pointers corrected
- [ ] Final ledger entry: project state, all gates green, artifact index

## 4. STEPS
1. OWNER GATE #1 (§3). Snapshot: `git ls-remote origin` + `git -C ~/Desktop/rfq2boq rev-parse main` — record both; if either moves during the task, stop and re-gate.
2. Triage (read-only fetch + diffs; classify against the incident record; be ruthless — code without provenance from that repo is a liability, and phase9 rebuilt everything that mattered). Note especially: any REAL client documents that arrived in the Desktop repo after the clone was cut (new RFQs from SWA) are NOT code — they get intaken via `scripts/intake_rfq.py`, provenance-checked, regardless of which swarm commit added them.
3. Owner reviews triage → approves candidate list (likely near-empty) → re-implementation if any.
4. Repo end-state + push with owner at the keyboard for every destructive/remote step.
5. Docs + handover + final ledger; owner sign-off.

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
make verify && make regression                       # EXPECT: all green on the final state
python3 scripts/run_final_eval.py --print-summary    # EXPECT: identical to P4_02 accepted numbers
python3 scripts/check_frozen_hashes.py && python3 scripts/check_gold_provenance.py   # EXPECT: intact
git ls-remote <github-url> | head                    # EXPECT: reflects the owner's chosen end-state
# Stranger test: a fresh clone + README/HANDOFF.md only → run one tender end-to-end (orchestrator performs)
```

## 6. ACCEPTANCE CRITERIA
- [ ] Every chaos commit classified; zero unreviewed code entered phase9
- [ ] Any post-clone client documents from the Desktop repo intaken with provenance (count in ledger)
- [ ] Remote reflects reality; the fake v1.0.0 story is definitively superseded by a real, verified push
- [ ] Fresh-clone stranger test passes
- [ ] All owner gates recorded in ledger with dates
- [ ] The repo's last commit message and HANDOFF.md agree about what this project is and where it stands

## 7. CONSTRAINTS
- NEVER `git merge`/`git cherry-pick` from origin — re-implementation only (fetch is read-only reference)
- Destructive git operations and the push: owner-executed, agent-prepared (exact commands in the triage doc)
- Credential rotation before push (leaked-token concern on record) — remind, verify with owner, don't handle secrets yourself
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P5_03 (everything final), owner gates
- **Blocks:** nothing — this is the end
- **Parallel-safe with:** nothing
- **Shared files:** everything (which is why it's last and sequential)

## 9. GOTCHAS
- Chaos-repo commits SWEPT UP legitimate orchestrator work via `git add -A` (ledger, 2026-07-05) — a commit being rogue-authored doesn't make its every hunk rogue; the TRIAGE is hunk-level for mixed commits.
- The fake "v1.0.0" tag exists in the Desktop repo and possibly in this clone's fetched refs — do not let it ride along in the push (`git push` without `--tags`; audit `git tag -l` first).
- 5.4GB of bundle files were once accidentally committed (then removed) — before push, check repo size (`git count-objects -vH`); if pack bloat persists on the history being pushed, flag to owner (may warrant a fresh-history push, owner's call — NEVER rewrite history unilaterally).
- GitHub push of a repo containing 127+ client tender documents: confirm with owner that the remote is PRIVATE before pushing data/ (client confidentiality — SWA documents are not public material).
