# TASK: P8T8 — Honest Final Handover — Agent-Docs

**Phase:** 8 | **Priority:** P2 (run LAST, after others report) | **Effort:** half day

## 1. GOAL
Produce the final SWA handover — deck, executive summary, demo guide, reproducible README — using the **real Phase 8 numbers**, with every known gap stated plainly. No fabricated metrics anywhere.

## 2. CONTEXT
Earlier handover docs were poisoned with a fake 100% and had to be rewritten. This task assembles the final, honest package once P8T1 (fair eval), P8T4 (PDF), P8T5 (NER) land. Source of truth for numbers: `results/PRODUCT_EVAL.md`, `results/NER_V3_REPORT.md`, `docs/wave_status.md`.

Read first: `deliverables/EXECUTIVE_SUMMARY.md`, `deliverables/HR_DEMO_RUNBOOK.md`, `deliverables/STATUS_REPORT_2026-06-03.md`, `results/PRODUCT_EVAL.md`, `deliverables/TIMELINE_AND_OBJECTIVES.html`.

## 3. DELIVERABLES
- [ ] `deliverables/EXECUTIVE_SUMMARY.md` updated with final honest numbers (fair product score + NER F1) and the real gaps.
- [ ] `deliverables/TIMELINE_AND_OBJECTIVES.html` regenerated (`scripts/daily_snapshot.sh`) with current metrics.
- [ ] `deliverables/SWA_DEMO_GUIDE.md` — end-to-end steps SWA can follow themselves (start UI, upload, read BOQ, download Excel), reusing `HR_DEMO_RUNBOOK.md`.
- [ ] `README.md` quickstart verified: clone → install → `make serve-ui` → demo, on a clean 3.11–3.13 env.
- [ ] A one-page honest "where it stands / what's next" for SWA.

## 4. STEPS
1. Pull final numbers from `results/PRODUCT_EVAL.md` + `results/NER_V3_REPORT.md` (do not hand-type — quote them).
2. Update exec summary, regenerate the HTML deck, write the demo guide.
3. Verify the README quickstart on a fresh checkout/env.
4. Grep the whole `deliverables/` for stale/fake numbers (100%, old F1) and fix.

## 5. VERIFICATION
```bash
# No fake/stale numbers in deliverables
grep -rnE "100% match|100\.0% match|perfect accuracy" deliverables/ && echo "FAIL: stale fake claim" || echo "✓ clean"

# Numbers match the eval reports (no hand-edited divergence)
grep -E "F1|match" deliverables/EXECUTIVE_SUMMARY.md
grep -E "F1|match" results/PRODUCT_EVAL.md results/NER_V3_REPORT.md
EXPECT: consistent

test -f deliverables/SWA_DEMO_GUIDE.md && echo "✓ demo guide"
```

## 6. ACCEPTANCE CRITERIA
- [ ] Every number in `deliverables/` traces to a committed results file (no invented figures).
- [ ] No "100%"/"perfect" claims; gaps stated honestly.
- [ ] README quickstart works on a clean 3.11–3.13 env; demo guide is followable by SWA unaided.

## 7. CONSTRAINTS
- Honesty over polish. If the product isn't shippable end-to-end, say so and quantify.
- Stay in scope: internship handover for ONE tool — no SaaS/paper/patent framing.
- Quote metrics from results files; never hand-edit a number to look better.

## 8. DEPENDENCIES
- **Blocked by:** P8T1, P8T4, P8T5 (and ideally P8T2/T3/T6/T7). Run last.

## 9. GOTCHAS
- `scripts/daily_snapshot.sh` regenerates the HTML deck — run it after metrics finalize, don't hand-edit the HTML.
- Keep the "Integrity note" (the cheat was caught and corrected) — it demonstrates rigor, not weakness.
