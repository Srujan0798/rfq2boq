# DISPATCH NOW — Single Master Sheet (UPDATED 2026-05-19)

**Most of the work is DONE.** Per `docs/wave_status.md`, only 2 substantive tasks remain. Everything else is either complete or skipped.

---

## ✅ WHAT'S DONE (no dispatch needed)

| Task | Status |
|------|--------|
| P1T1 OmniClass mapping | DONE |
| P1T2 IndicBERT module + 12 tests | DONE (partial — model download network-blocked) |
| P1T3 ARCBERT module + 10 tests | DONE (partial — model download network-blocked) |
| P1T4 CPWD DSR (507 items) | DONE |
| P1T5 117 PDFs + 20 gold annotations | DONE |
| P3T1 Fine-tune NER (F1 0.68) | DONE |
| P3T2 Polish Streamlit UI (470 lines, 15 tests) | DONE |
| P3T3 Polish CPWD Excel (14 tests) | DONE |
| P3T4 Strengthen conflict resolution (62 tests) | DONE |
| P3T5 Demo video | SKIPPED (owner choice) |

---

## 🎯 DISPATCH THESE TWO (the only real remaining work)

### Task 1 — Internship Report + Slides

**Send to Agent-4:**
**File:** `prompts/hybrid/phase3/P3T6_INTERNSHIP_REPORT.md`
**Effort:** 1-2 days
**Output:** `deliverables/report/internship_report.md` + PDF + slides + executive summary

Notes for agent: report scaffold already exists at `deliverables/report/internship_report.md` — needs to be filled with REAL F1 numbers from `results/final_model_eval.json` (currently 0.68) and `results/real_world_metrics_v2.json` (currently 0.506). Both numbers are honest; report them with sample-size caveats. Cite Zhang & El-Gohary 2015.

### Task 2 — Final QA & Handover Verification

**Send to Agent-4 (after P3T6 done):**
**File:** `prompts/hybrid/phase3/P3T7_FINAL_QA.md`
**Effort:** 0.5 day
**Output:** `docs/handover_verification_report.md` + `results/handover_metrics.json` + git tag `v1.0-handover` if all gates pass

---

## 🛠️ ORCHESTRATOR TASKS (I do these, not agents)

These are MINE, not agent work. Listed here for transparency:

| Task | Owner | Status |
|------|-------|--------|
| Git push (when network stable) | Me/Owner | ⚠️ blocked — repo is 1.58 GiB, can't push over flaky connection |
| Clean .git temp garbage | Me | DONE this session |
| Update wave_status.md | Me | Done by linter |
| Maintain DISPATCH_NOW.md | Me | This file |
| Verify agent REPORTs | Me | Ongoing |

---

## ⚠️ Optional enhancements (only if you want them)

Both are network-blocked downloads — can be done later when you have a stable connection to Hugging Face:

1. **P1T3 ARCBERT actual model** — download `lsj126/arcbert-base` weights to `models/arcbert-base/`. Currently using SciBERT fallback. Would give +5-8% F1.
2. **P1T2 IndicBERT actual model** — download `ai4bharat/indic-bert` weights. Only needed if you want real Hindi support.

Neither is required for the SWA handover.

---

## 🚀 Push the 1.58 GiB repo

Network failure mid-push. Options when you want to retry:

1. **Best** — push from a stable WiFi/ethernet connection, give it 10-15 minutes
2. **If still failing** — large binaries in `resources/` and `attic/` are bloating the repo. Move them out of git tracking with `git rm --cached -r resources/ attic/` then re-commit (loses the ability to clone these from GitHub, but they stay local). I can do this for you if you want.
3. **Best long-term** — Git LFS for `resources/*.pdf` and `attic/*.bin`

Tell me which option and I'll execute. Otherwise just retry from a stable connection.

---

## TIMELINE

| Day | What |
|-----|------|
| Now | Dispatch P3T6 to Agent-4 |
| ~2 days later | Agent-4 returns report + slides → I verify |
| ~3 days later | Dispatch P3T7 to Agent-4 |
| ~3.5 days later | P3T7 produces verification report → if READY, tag `v1.0-handover` |
| Day 4 | Owner reviews report + hands to SWA |

Realistically you're 3-4 days from handover, not a week.

---

## SCOPE GUARD — still locked

Any agent suggesting paper/patent/dataset/multi-tenant/observability work → refuse via `docs/SCOPE_GUARD.md`.
