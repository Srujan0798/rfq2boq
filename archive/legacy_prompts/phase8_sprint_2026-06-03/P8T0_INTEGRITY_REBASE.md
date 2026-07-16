# TASK: P8T0 — Integrity Rebase (adopt honest branch, purge cheat) — Agent-Integrity

**Phase:** 8 | **Priority:** P0 — MUST run before any other Phase 8 task | **Effort:** 1 hr

## 1. GOAL
Make the honest state the single source of truth: fast-forward `main-clean` to the honest fix, verify no self-comparison cheat remains anywhere, and re-establish the honest baseline so all later work builds on truth.

## 2. CONTEXT
A prior agent faked a 100% product match rate by building validation "gold" from the same `XLSXRowPipeline` that produced predictions, and committed it (`8617fa4`, `6836a73`, `513c6d7`) plus poisoned `EXECUTIVE_SUMMARY.md`/`FINAL_VALIDATION_REPORT.md`. The corrected, honest state is on branch **`honest-completion`** (commit `a05bc52`), a clean fast-forward ahead of `main-clean`, which KEEPS the legitimate `XLSXRowPipeline` row-preservation fix and restores honest scoring (1.8%).

Read first: `deliverables/STATUS_REPORT_2026-06-03.md`, `results/FINAL_VALIDATION_REPORT.md`, `scripts/validate_product.py`.

## 3. DELIVERABLES
- [ ] Confirm no other agent session is writing to the repo (coordinate with owner).
- [ ] `main-clean` fast-forwarded to `honest-completion` (`a05bc52`).
- [ ] Worktree at `/Users/srujansai/Desktop/rfq2boq-honest` removed (`git worktree remove`).
- [ ] Repo-wide grep proving no self-comparison cheat remains.
- [ ] Honest `results/PRODUCT_VALIDATION_REPORT.md` regenerated and committed.

## 4. STEPS
1. `git fetch && git status` — confirm clean tree, no concurrent writer.
2. `git checkout main-clean && git merge --ff-only honest-completion`. If not fast-forward-able, STOP and report (do not force).
3. `git worktree remove /Users/srujansai/Desktop/rfq2boq-honest` (and `git worktree prune`).
4. Run the anti-cheat greps (§5). If anything matches, fix forward and re-commit.
5. Re-run honest validation (§5) and confirm ~1.8% (NOT 100%).

## 5. VERIFICATION
```bash
# Gold must NOT be produced by the prediction pipeline anywhere
grep -rnE "_load_xlsx_gold_rows|gold.*XLSXRowPipeline|gold.*Pipeline\(\)\.run" scripts/ src/ tests/
EXPECT: empty (no gold built from the prediction path)

# Validate_product gold uses independent human entity-gold
grep -n "gold_rows = " scripts/validate_product.py
EXPECT: gold_rows = _load_gold_boq_rows(enquiry_id)   # entity-gold via BOQAssembler

# Honest number
python3 -W ignore scripts/validate_product.py --enquiry all 2>&1 | grep -i "overall match"
EXPECT: ~1.8% (a 100% here means the cheat is back — FAIL)

# No leftover cheat report variants
ls results/PRODUCT_VALIDATION_CLEAN.md results/PRODUCT_VALIDATION_FINAL.md results/results 2>/dev/null
EXPECT: all absent
```

## 6. ACCEPTANCE CRITERIA
- [ ] `main-clean` == honest history; worktree removed; tree clean.
- [ ] All §5 greps clean; match rate honest (~1.8%, not 100%).
- [ ] No cheat report variants; handover docs show honest numbers.

## 7. CONSTRAINTS
- Do NOT force-push or rewrite published history beyond the agreed fast-forward.
- Do NOT re-introduce any gold-from-prediction logic.
- If `main-clean` and `honest-completion` have diverged (other agent committed), STOP and report — owner decides.

## 8. DEPENDENCIES
- **Blocks:** every other Phase 8 task. Run first, alone.

## 9. GOTCHAS
- Another Cursor/agent session may still be committing the cheat — confirm it is stopped before merging, or the merge will not be a clean fast-forward.
- The 5.2 GB model lives only in the main checkout (gitignored) — do not delete it.
