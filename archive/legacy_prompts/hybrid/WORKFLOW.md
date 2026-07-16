# Hybrid Workflow — How to Execute

The protocol for running the hybrid plan from start to finish.

---

## Daily loop

1. **Open** [docs/HYBRID_EXECUTION_PLAN.md](../../../docs/HYBRID_EXECUTION_PLAN.md). Identify the next PENDING task.
2. **Copy** the prompt file referenced for that task.
3. **Paste** to one external agent (MiniMax, Codex, or whichever you use).
4. **Wait** for the agent to return its REPORT block.
5. **Verify** by running the Section 5 verification commands yourself.
6. **Mark** DONE in `docs/HYBRID_EXECUTION_PLAN.md` and `docs/wave_status.md`.
7. **Commit** to git with a descriptive message.

---

## Parallel dispatch rules

Tasks listed as "parallel-safe" in the phase INDEX can run simultaneously across multiple agents. Conditions:

- Different agents (Agent-1, Agent-2, Agent-3, Agent-4)
- No overlapping files in Section 3 (Deliverables) of each prompt
- No logical dependency stated in Section 8 (Dependencies)

Sequential tasks must complete in order — check Section 8 before assigning.

---

## Verification before accepting

Never accept a task as DONE based on the agent's self-report alone. Always:

1. Run the **exact** commands from Section 5
2. Compare actual output to "EXPECT" lines
3. Run `make test` to verify no regression
4. Check the new files in `git status` match Section 3 Deliverables

If any check fails: copy the failing command + actual output back to the agent and request a fix. Do NOT mark DONE.

---

## Phase gates

End of each phase, run the gate check from [docs/HYBRID_EXECUTION_PLAN.md](../../../docs/HYBRID_EXECUTION_PLAN.md). Do not start the next phase until all gate items pass.

- Phase 1 gate: OmniClass map exists, IndicBERT loads, DSR rates ≥500 items, 50 real PDFs collected
- Phase 2 gate: heavy infra archived, tests pass in ≤30s, docs reflect slim scope
- Phase 3 gate: real F1 ≥ 75%, polished UI + Excel, demo video recorded

---

## Communication template (when handing a prompt to an agent)

Paste this header above each task prompt when assigning:

```
# RFQ2BOQ task assignment

Project: https://github.com/<your-org>/rfq2boq
Conventions: read CLAUDE.md + docs/conventions.md before starting.
Common gotchas: docs/WAVE_GOTCHAS.md
Strategic context: docs/HYBRID_PLAN.md

When done, return ONLY the standard REPORT block. Do not edit any
files outside Section 3 Deliverables.

---

[paste the 9-section task here]
```

---

## When things go wrong

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Agent's REPORT says done but Section 5 commands fail | Hallucinated deliverable | Send back actual output, request fix |
| Tests fail after a task delivery | Agent broke something outside Section 3 | Run `git diff` to find the actual change; revert the unwanted edit |
| File paths in REPORT don't match Section 3 | Agent picked their own path | Insist on canonical path; do not accept alternative |
| Agent invents a new dependency | Off-spec | Reject; require dependency justification first |
| Coverage drops | Tests skipped or removed | Compare `pytest --co` output before/after; restore tests |

---

## End-of-week checkpoint

Every Friday (or whenever you finish a phase):

1. Run full verification gate from `HYBRID_EXECUTION_PLAN.md`
2. Update `docs/wave_status.md` with the week's progress
3. Update `README.md` if user-visible behavior changed
4. Commit + tag (e.g., `git tag phase1-complete`)
5. Send a one-paragraph status to your SWA Consultancy contact

---

## Hand-off checklist (final day)

When all 3 phases done:

- [ ] All tests pass: `make test`
- [ ] Real-world F1 measured + documented
- [ ] Streamlit UI usable by non-technical user
- [ ] Excel export looks professional
- [ ] Demo video recorded
- [ ] README updated with results + limitations
- [ ] Technical report (`deliverables/report/technical_report.md`) finalized
- [ ] Slides (`deliverables/slides/presentation.md`) finalized
- [ ] Patent decision made (file / waive) with SWA
- [ ] Git history clean; tagged `v1.0-handover`

When all those check, you're done.
