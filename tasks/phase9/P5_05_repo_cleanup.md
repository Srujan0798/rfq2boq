# TASK P5_05: Repository cleanup — professional structure for submission — Agent-P5-5

## 1. GOAL
Turn a repo that accumulated 8+ duplicate handoff docs, 27+ superseded task files, and 46 dated/stale reports into something a stranger (or SWA) could open and immediately understand — without deleting a single byte of real history. Archive, never delete. Verify functionality is untouched after every step.

## 2. CONTEXT
Files to read FIRST (in order):
- `tasks/phase9/00_README.md`, `01_STATE_OF_THE_WORLD.md`, `02_ANTI_CHEAT_PROTOCOL.md` — the current, correct picture of the project
- `config/FROZEN_HASHES.sha256` — the exact list of files that must never move, rename, or change content
- `CLAUDE.md` — the project charter (this task must not contradict it; update its file-path references if you move things it names)

Current state (surveyed 2026-07-07, exact inventory below):

**Root-level clutter (8 overlapping handoff/plan docs, unclear which is current):**
`AGENTS.md`, `AGENT_TASKS.md`, `CLAUDE_MERGED_HANDOFF.md`, `FINAL_COMPLETION_PLAN.md`, `GROK_MERGED_HANDOFF.md`, `HANDOFF.md`, `HIERARCHY.md`, `ULTIMATE_HANDOFF.md`, `kleenhand.md`. `CLAUDE.md`, `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md` are legitimate and stay.

**`tasks/` — 20+ files/folders superseded by `tasks/phase9/` (per `tasks/phase9/00_README.md`'s own statement: "supersedes tasks/NEXT_WAVE.md, tasks/sonnet/, and any wave5"):**
`MEETING_VOICES.md`, `MEETING_VOICES_FINAL.md`, `NEXT_WAVE.md`, `NW01`–`NW09_*.md`, `REPORT_NW05.md`, `SONNET_EXECUTION_PLAN.md`, `TASK_01`–`TASK_06_*.md`, `VALIDATION_CHECKLIST.md`, `lane_A/` through `lane_E/`, `sonnet/`. **`tasks/phase9/` is untouched — it is the only active plan.**

**`prompts/` — `wave4/` superseded by the same statement; `archive/` is already correctly archived (leave as-is); `TASK_TEMPLATE.md`, `EXAMPLE_FILLED_TASK.md`, `INDEX.md` are still-referenced by `CLAUDE.md` and stay.**

**`docs/` — 36 files, mixed: some current and load-bearing (`CORE_UNDERSTANDING.md`, `GOLD_METHODOLOGY.md`, `SWA_REQUIREMENTS_2026-06-11.md`, `CORPUS_DEFINITION.md`, `ANNOTATION_GUIDELINES.md`, `ANNOTATION_WORKFLOW.md`, `ANNOTATION_FACTORY_PATCH.md`, `INTAKE_PROTOCOL.md`, `conventions.md`, `architecture.md`, `ui_guide.md`, `excel_format.md`, `api.md`, `model_card.md`), some dated/superseded era-artifacts (`PHASE8_UNIFIED_TIMELINE_AND_FLOW.md`, `ULTRA_PLAN_WEEK_2026-06-22.md`, `STRATEGIC_REVIEW.md`, `INTERN_100_GENERALIZABLE_PLAN.md`, `HR_DEMO_GUIDE.md`, `WAVE_GOTCHAS.md`, `wave_status.md`, `handover_verification_report.md`, `CORPUS_FILTER.md`, `SCOPE_GUARD.md`, `TRAINING_CORPUS.md`, `ONBOARDING.md`, `omniclass_mapping.md`, `arcbert.md`, `indicbert.md`, `hindi_support.md`, `conflict_resolution.md`, `data_collection.md`, `deployment.md`, `operations.md`, `orchestration.md`).

**`results/` — 46 top-level entries, mostly dated one-off reports from past waves** (e.g. `eval_honest_rows_2026-06-18.txt`, `insulation_batch_run_2026-06-22.*`, `lane_merge_audit_2026-06-22.md`, `honest_baseline_2026-06-22.md`, `PROJECT_HONEST_STATUS_2026-06-25.md`, `insulation_eval_2026-06-26.md`, `w7_head_provenance_audit.md`, `w8_extracted_data_provenance.md`, `gold_trust_audit.md`, `gold_spotcheck_report.md`, `model_audit_report.md`, `MASTER_CONSOLIDATED_ANALYSIS.md`, `PROJECT_VALIDATION_REPORT.md`, `NER_REAL_REPORT.md`, `LORA_DECISION.md`, `diagnosis_pdf.md`, `entity_error_analysis.md`, `generalization_smoke*.{json,md}`, `new_tenders_2026-06-18.json`, `swa10_training_eval.json`, plus assorted `*.json`/`*.txt` eval snapshots). **`results/fidelity/`, `results/FIDELITY_REPORT.md`, `results/PRODUCT_EVAL.md`/`product_eval.json`, `results/annotation_wave1/`, `results/column_eval/`, `results/corpus_run/`, `results/corpus_sweep/`, `results/structure_eval/`, `results/ui_dropin/` are CURRENT and stay exactly where they are.**

**`scripts/` — 59 files, some clearly one-off/superseded** (e.g. `push_and_tag.sh`, `git_push.sh` if unused by any current task, `final_integration_test.py` if superseded by `tests/`) — audit each before moving; do not archive a script any current `tasks/phase9/*.md` file references.

**`logs/`** — 1 file; check its content and age before deciding to keep or archive.

## 3. DELIVERABLES
- [ ] `archive/legacy_root_docs/` — the 8 root-level handoff docs moved here verbatim (git `mv`, preserving history), each with its original filename unchanged
- [ ] `archive/legacy_tasks/` — the ~20 superseded `tasks/` files/folders moved here (NW*, TASK_*, lane_*, sonnet/, MEETING_VOICES*, SONNET_EXECUTION_PLAN.md, VALIDATION_CHECKLIST.md, REPORT_NW05.md)
- [ ] `archive/legacy_prompts/` — `prompts/wave4/` moved here
- [ ] `archive/legacy_docs/` — the ~18 dated/superseded `docs/` files moved here
- [ ] `archive/legacy_results/` — the ~35 dated one-off `results/` files moved here (NOT the current ones listed above as "stay")
- [ ] `archive/README.md` — one page: what's in each subfolder, why it was archived, and the one-line pointer to what replaced it (e.g. "tasks/legacy_tasks/NW01-09 → superseded by tasks/phase9/P1-P5")
- [ ] `CLAUDE.md` updated: any path reference to something you moved gets corrected; the "Project structure" section (§3) updated to reflect reality
- [ ] `HANDOFF.md` — the ONE canonical, current handoff doc left at root, rewritten to point at `tasks/phase9/00_README.md` as the active plan and `archive/README.md` for history (do not just delete the old content — synthesize anything genuinely still-relevant from the 8 legacy docs into this one before archiving them)
- [ ] `scripts/` — a short `scripts/README.md` categorizing what's active (referenced by any `tasks/phase9/*.md`) vs one-off (safe to leave, not urgent to move — scripts are lower priority than docs/tasks/results clutter; only move a script into `archive/legacy_scripts/` if you are CERTAIN nothing references it, including other scripts)
- [ ] `tests/unit/test_repo_structure.py` (optional but recommended) — a lightweight test asserting the frozen files listed in `config/FROZEN_HASHES.sha256` still exist at their exact paths, so a future cleanup pass can't accidentally break this again

## 4. STEPS
1. Read context. Confirm current git status is clean (commit or stash anything uncommitted before you start — you need a clean starting point to `git mv` safely).
2. Run `PYTHONPATH=. python3.12 scripts/check_frozen_hashes.py` and save the output — this is your before-baseline. Every file it lists is off-limits for moving/renaming/deleting.
3. Archive root docs: `git mv` each of the 8 files into `archive/legacy_root_docs/`. Before archiving, skim each for anything not already captured elsewhere (a stray true fact, a contact, a decision) and fold it into the new `HANDOFF.md` if genuinely missing.
4. Archive `tasks/` clutter: `git mv` each NW*/TASK_*/lane_*/sonnet/MEETING_VOICES*/SONNET_EXECUTION_PLAN.md/VALIDATION_CHECKLIST.md/REPORT_NW05.md into `archive/legacy_tasks/`, preserving the internal folder structure (e.g. `lane_A/` becomes `archive/legacy_tasks/lane_A/`).
5. Archive `prompts/wave4/` into `archive/legacy_prompts/wave4/`.
6. Archive the ~18 dated `docs/` files into `archive/legacy_docs/`.
7. Archive the ~35 dated `results/` files into `archive/legacy_results/` — go file by file against the "stay" list above; when unsure whether a `results/` file is current or legacy, check its content for a date and cross-reference against `tasks/phase9/04_LEDGER.md` (if the ledger doesn't reference it and it has an old date in the filename or first line, it's legacy).
8. Write `archive/README.md`.
9. Update `CLAUDE.md` §3 (project structure) and any other stale path references.
10. Rewrite `HANDOFF.md` as the single canonical pointer.
11. Write `scripts/README.md` (categorize only, minimal moves).
12. Run the full verification (Section 5). This is the step that proves you didn't break anything — do not skip it or shortcut it.
13. Commit in logical chunks (one commit per archive category is fine), not one giant commit — makes review and any future revert trivial.

## 5. VERIFICATION
Run these after EVERY archiving step, not just at the end — catch a break immediately, not after 20 file moves:
```bash
cd /Users/srujansai/rfq2boq-phase9
PYTHONPATH=. python3.12 scripts/check_frozen_hashes.py          # EXPECT: ALL FROZEN FILES INTACT (same count as before-baseline)
PYTHONPATH=. python3.12 scripts/check_gold_provenance.py        # EXPECT: exit 0
PYTHONPATH=. python3.12 scripts/check_split_leakage.py          # EXPECT: exit 0
PYTHONPATH=. python3.12 -m pytest tests/unit tests/integration -q --timeout=120   # EXPECT: same pass count as before you started (no new failures from broken imports)
PYTHONPATH=. python3.12 -m pytest tests/regression/ -q          # EXPECT: same pass count as before (48 passed, per the last accepted run)
PYTHONPATH=. python3.12 scripts/measure_fidelity.py --all       # EXPECT: identical numbers to before cleanup (0 dropped, 100.5% overall) — cleanup must not touch a single byte of src/ logic
grep -rn "NW0\|lane_A\|SONNET_EXECUTION_PLAN\|wave4" CLAUDE.md tasks/phase9/*.md docs/*.md 2>/dev/null   # EXPECT: no dangling references to what you archived (or only inside archive/ itself)
make lint                                                        # EXPECT: clean (archiving shouldn't touch lint-checked code, but confirm)
```

## 6. ACCEPTANCE CRITERIA
- [ ] Every frozen file still exists at its exact original path, byte-identical (hash check proves this)
- [ ] Zero files deleted — everything moved via `git mv` into `archive/`, full history preserved
- [ ] Root directory has ≤ 5 markdown files (README, CLAUDE, CHANGELOG, CONTRIBUTING, HANDOFF)
- [ ] `tasks/` root has only `phase9/` as an active folder (everything else under `archive/`)
- [ ] All test suites (unit, integration, regression) show identical pass/fail counts before vs after
- [ ] `measure_fidelity.py` output byte-identical before vs after (proves zero functional impact)
- [ ] `archive/README.md` makes every archived item's "why" and "replaced-by" traceable in under 2 minutes of reading
- [ ] `CLAUDE.md` has no stale path references

## 7. CONSTRAINTS
- **NEVER delete anything.** Archive only. If in doubt about whether something is safe to move, don't move it — leave it and note the uncertainty in your report for the orchestrator.
- **NEVER touch anything in `config/FROZEN_HASHES.sha256`'s list**, `data/` (any of it — corpus, gold, annotations, ontology), `src/`, `tests/` (except adding the optional new test), `ui/`, `schema/`, `config/`, `resources/` (SACRED, never touch), `tasks/phase9/` (the only active plan), `results/fidelity/`, `results/FIDELITY_REPORT.md`, `results/final_eval/` if it exists.
- Do not "improve" or rewrite content while archiving — move verbatim. Content editing is only in scope for the NEW synthesized `HANDOFF.md` and `archive/README.md`.
- Do not touch git history (no rebase, no squash, no force-push) — `git mv` preserves history naturally, that's the whole point.
- If a file you're about to archive is referenced by name inside `tasks/phase9/*.md` (any of the 27 files), STOP — that means it's not actually superseded, leave it in place and flag it in your report instead of guessing.
- Standing constraints: `CLAUDE.md` §7.

## 8. DEPENDENCIES
- **Blocked by:** nothing — this can run in parallel with Phase 4 (retrain) since it touches zero model/pipeline code
- **Blocks:** nothing downstream, but should complete before P5_03 (final report) so the repo looks professional when SWA opens it
- **Parallel-safe with:** everything (P4_01, P4_02, ongoing annotation review) — this task touches docs/tasks/results/root files only, never `src/`
- **Shared files:** `CLAUDE.md` (read by every other task — coordinate if another task is mid-edit on it)

## 9. GOTCHAS
- `tasks/phase9/04_LEDGER.md` references specific `results/` filenames as evidence in past entries (e.g. "results/FIDELITY_REPORT.md", "results/fidelity/summary.json") — never archive anything the ledger cites as evidence, even if it looks dated, without checking first.
- Some `docs/` files may be referenced by `ui/app.py`'s help text or `README.md` — grep before archiving each one.
- `git mv` on a directory with many files can be slow one-by-one; `git mv olddir newdir/olddir` moves the whole tree in one operation and preserves history correctly.
- If `scripts/push_and_tag.sh` or `scripts/git_push.sh` reference the OLD Desktop repo or old branch names, they're candidates for archiving, but double check `tasks/phase9/P5_04_reconcile_and_handover.md` doesn't expect one of them to exist for the final push step.
- Two full test-suite runs (before/after) at ~2 minutes each plus a fidelity run — budget ~10-15 minutes just for verification overhead; don't skip it to go faster, that's exactly how the earlier real regression this session slipped through once already.
