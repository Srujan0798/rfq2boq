# ANTI-CHEAT PROTOCOL — hard rules, distilled from 13+ real incidents

This project has a documented history of agents faking success. These rules are **absolute**. Violating any of them fails the task regardless of how good the other work is. The orchestrator's gate (`03_VERIFICATION_GATE.md`) checks every one.

---

## The incident history (why each rule exists)

| # | Incident | Rule it produced |
|---|----------|------------------|
| 1–2 | Fake metrics reported without runs; eval harness patched to pass | Rule 1, Rule 5 |
| 3 | Pipeline graded against its own output → "100%" | Rule 2 |
| 4 | Gold poisoned to match predictions | Rule 3 |
| 5 | Handoff docs rewritten to hide failures | Rule 6 |
| 6 | Circular silver training + log spam | Rule 4 |
| 7 | 19 annotation files stamped `human_verified:true` with a forged reviewer string | Rule 3 |
| 8 | Extraction filter changed to drop 17 real rows, protective test rewritten to assert the lower count | Rule 5 |
| 9–10 | Rogue background agents named `agent_push_row_80` / `agent_push_entity_90` (metric-target names); eval methodology changed unilaterally to hide a known bug | Rule 1, Rule 5 |
| 11 | "Anti-cheat hardening" commit actually REMOVED the self-comparison guard, with a comment admitting circularity | Rule 2, Rule 5 |
| 12 | 9 sacred gold files grown in-place (50,690 insertions) to mirror pipeline output | Rule 3 |
| 13 | **2026-07-06, the escalation:** the phase-9 plan folder deleted from the working tree; fake "wave5" commits impersonating this plan's task IDs; gold edited to manufacture "100% ENTITY F1" (`95a462b`); independent gold deleted as "garbage" (`6079b18`); 198 annotation files stamped verified with NO reviewer field; "v1.0.0 ship it" tagged on fabricated numbers | Rules 3, 5, 6, 7 — and the reason this repo exists |

## The rules

**Rule 1 — Numbers come from commands, not memory or reports.**
Every metric you state must be accompanied by the exact command and its real stdout. If you did not run it in this session, you do not have the number. Never extrapolate ("should now be ~100%").

**Rule 2 — Never grade the pipeline against anything the pipeline produced.**
Gold must be independent (human transcription from the source document) or owner-verified. `scripts/fidelity_audit.py`'s `is_independent_gold()` hard gate must stay a hard gate. A sudden jump to ~100% is a red flag to investigate, not a win to report.

**Rule 3 — Gold is owner-only.**
No agent creates, edits, "extends", "corrects", or stamps gold/annotations as verified. `human_verified:true` is valid only with `reviewer: "srujan"` (enforced by `scripts/check_gold_provenance.py`). Drafts are fine — they live in draft directories and are labeled `human_verified:false`. After P0_02, all gold files are sha256-locked; a checksum mismatch fails the gate.

**Rule 4 — No training on non-verified data.**
The training loader accepts only records that pass the provenance check. No silver labels, no pseudo-labels, no "just to bootstrap" env flags. `scripts/train_lora_ner_real_only.py` has had all such backdoors removed — do not reintroduce any.

**Rule 5 — Eval code, protective tests, and thresholds are frozen.**
After P0_03 locks them, `scripts/measure_fidelity.py`, `scripts/eval_honest_rows.py`, `scripts/fidelity_audit.py`, `scripts/eval_ner.py`, `scripts/check_gold_provenance.py`, `scripts/check_eval_hacks.py`, and `tests/regression/` may not be modified by any implementation task. If you believe an eval script is genuinely wrong, STOP, write the argument + evidence into your report, and let the orchestrator/owner rule. Changing the ruler to fix the measurement is incident #8/#10/#13 — instant task failure.

**Rule 6 — Reports state what happened, including failures.**
"9 passed, 1 failed" is an acceptable report. A rewritten history is not. Deviations, blockers, and out-of-spec edits go in their sections verbatim. Claims about external state (pushed to GitHub, all checks pass) must include the verifying command output (`git ls-remote`, actual check runs).

**Rule 7 — Stay in the clean room.**
Phase-9 work happens only in `/Users/srujansai/rfq2boq-phase9` on `phase9-final`. Never write to the Desktop repo. Never fetch/pull/merge/cherry-pick from `origin` (the Desktop repo) outside P5_04's read-only triage procedure. The `w3-tip-untriaged` branch is reference material, not base.

**Rule 8 — The frozen split is inviolable.**
TEST docs (42, incl. the sacred 10) are never trained on, never mined for gazetteer/pattern terms, never used to tune thresholds. `scripts/check_split_leakage.py` + leakage tests must pass at every gate. DEV is for tuning; TEST is touched only by P4_02's final eval.

**Rule 9 — Flag, never drop; and never invent.**
R1 means uncertain rows are surfaced with low confidence flags — not silently dropped, and equally not hallucinated into existence. Over-capture is also a fidelity failure (see 05_zydus).

**Rule 10 — Owner steps are owner steps.**
Tasks marked owner-blocking (gold stamping, D5 ruling, P1_00 dispositions, final push) wait for Srujan. Simulating, forging, or "helpfully unblocking" them is incident #7/#13. The correct behavior when blocked is to report BLOCKED.

## Red-flag checklist (orchestrator scans every report for these)

- A metric improved dramatically with no corresponding source-code diff that explains it
- Any diff touching `scripts/eval_*`, `scripts/measure_*`, `scripts/check_*`, `tests/regression/`, `data/real_rfqs/gold/`, `data/real_rfqs/*manifest*`, `split_test.json`
- Test assertions whose expected values were edited to match new output
- New env vars, flags, or config that gate verification behavior
- Vocabulary like "adjusted the eval to be fairer", "excluded outliers", "the gold was wrong so I fixed it", "removed garbage gold"
- Reports claiming ~100% on anything not previously at ~100% — reproduce before believing
- Commit messages announcing milestones ("ship it", "RESTORED", "COMPLETE") — milestones are declared by the orchestrator's gate, never by the worker
