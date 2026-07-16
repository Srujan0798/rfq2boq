# Phase 8 — Dispatch Playbook (how to assign so agents finish the whole mission)

Hand each task to ONE agent. Prepend the **Mission Directive** below, then point it at the task file. Wait for its 9-section REPORT, then run the **Owner Verification** before you trust a word of it.

---

## 🔱 THE MISSION DIRECTIVE (paste this before every task)

> **You are executing a Phase 8 task on the RFQ2BOQ project. Operate at the highest level — take the whole mission, finish it completely, return with proof.**
>
> 1. **OWN IT END-TO-END.** Read the task file fully and every file it lists in CONTEXT. Do the entire job, not a slice. Do not stop until every ACCEPTANCE CRITERION is met — or you hit a real blocker you can name precisely.
> 2. **USE EVERY SKILL YOU HAVE.** `brainstorming` before design · `test-driven-development` before writing code · `systematic-debugging` on any failure before guessing a fix · `verification-before-completion` before you claim anything works · `requesting-code-review` before you call it done. Use sub-agents / parallel exploration where it genuinely speeds correct work.
> 3. **HONEST OR NOTHING.** This project was cheated twice — a fake 100% was produced by grading the pipeline against itself. **Never** grade a component against itself, **never** lower a threshold to inflate a score, **never** hardcode outputs, **never** report a number you didn't reproduce with a command. A perfect or near-100% result is a RED FLAG to investigate, not a victory. If it fails, say it failed and paste the output.
> 4. **STAY IN SCOPE.** One RFQ→BOQ extraction tool. No website / SaaS / paper / patent / MLOps. If you feel pulled outside the tool, STOP and report.
> 5. **PROVE IT.** Run the task's VERIFICATION block, paste the real command output, and return the 9-section REPORT (`CLAUDE.md` §11): every deliverable path, the exact metrics, blockers, deviations, and every outside-spec edit.
>
> First read `prompts/phase8/INDEX.md` for the global rules. Then execute this task to completion:
> **`<TASK FILE PATH>`**

---

## Dispatch order (one agent per task)

**Step 1 — alone, first:**
```
[Mission Directive] + execute prompts/phase8/P8T0_INTEGRITY_REBASE.md
```
Wait for P8T0 REPORT + your verification BEFORE anything else. Nothing builds on poisoned history.

**Step 2 — fan out in parallel (5 agents):**
```
Agent-1: [Directive] + prompts/phase8/P8T1_FAIR_EVAL.md
Agent-2: [Directive] + prompts/phase8/P8T2_GOLD_EXPANSION.md
Agent-3: [Directive] + prompts/phase8/P8T3_GOLD_QUALITY.md
Agent-4: [Directive] + prompts/phase8/P8T6_UI_HARDENING.md
Agent-5: [Directive] + prompts/phase8/P8T7_TEST_CI.md
```

**Step 3 — after their blockers clear:**
```
P8T4 (after P8T1 reports done): [Directive] + prompts/phase8/P8T4_PDF_EXTRACTION.md
P8T5 (after P8T2 + P8T3 done):  [Directive] + prompts/phase8/P8T5_NER_RETRAIN.md
```

**Step 4 — last, after all green:**
```
[Directive] + prompts/phase8/P8T8_HANDOVER.md
```

---

## 🛡️ OWNER VERIFICATION — run this when an agent says "done" (do NOT trust the report)

For EVERY task, before accepting:
```bash
# 1. The anti-cheat sweep — no component graded against itself
grep -rnE "gold.*Pipeline\(\)\.run|gold.*XLSXRowPipeline|_load_xlsx_gold_rows" scripts/ src/ tests/
# EXPECT: empty

# 2. Reproduce the headline number yourself (don't read it from the report)
#    -> run the task's VERIFICATION block commands; confirm the numbers match

# 3. A perfect score is suspicious
#    -> any ~100% / F1≈1.0 means: investigate for leakage/self-comparison, don't celebrate

# 4. Tests + lint actually pass
make test && make lint && make type

# 5. Git sanity — what did they really change?
git log --oneline -5 ; git show --stat HEAD
```
If any check fails or a number can't be reproduced → **send it back**, quote the failing command. Adopt nothing on the agent's word alone.

---

## Per-task acceptance one-liners (what "done" really means)

- **P8T0:** `validate_product.py` shows ~1.8% (NOT 100%); anti-cheat grep empty; `main-clean` on honest history.
- **P8T1:** one command prints row-level + entity-level honest scores; gold builder does NOT import the pipeline (grep + test prove it).
- **P8T2:** ≥28 validated gold docs; 09/10 no longer draft; 20 new raw docs with provenance.
- **P8T3:** no MATERIAL span >120 chars; annotation guidelines exist; validator quality lints green.
- **P8T4:** PDF entity-F1 rises vs the P8T1 baseline (real delta), GSECL stops emitting front-matter; XLSX path unchanged.
- **P8T5:** v3 beats 0.430 on a frozen, leakage-checked real test set — or an evidenced "it didn't, here's why."
- **P8T6:** PDF+Excel upload work, no crash on bad files, runs with `HF_HUB_OFFLINE=1`.
- **P8T7:** `make test` green < 5 min; e2e on all 10; anti-cheat regression test present.
- **P8T8:** every number in `deliverables/` traces to a committed results file; zero "100%/perfect" claims.

---

## Rules of engagement (tell the agents, enforce as owner)
1. One task, one agent, finished completely — no half-deliveries.
2. Honest or nothing. A number you can't reproduce doesn't exist.
3. Stay inside the tool. Drift = stop + ask.
4. Report with evidence (9-section, real command output) or it isn't done.
5. Owner verifies independently every time. Trust is earned per task, not assumed.
