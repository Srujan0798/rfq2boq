# Phase 8 — Monday Sprint (intense, all-directions, honest)

**Goal:** Move RFQ2BOQ from "demonstrable" to "genuinely measurable and improving" across every layer of the *one tool* — without faking a single number. By next Monday: a fair end-to-end metric, more & cleaner gold, better PDF extraction, an NER model that beats production, a hardened UI, green CI, and an honest handover.

**Scope (locked):** ONE RFQ→BOQ extraction tool. NO website/SaaS, NO papers/patent, NO MLOps showcase, NO outbound automation. See `CLAUDE.md` §1. Any agent tempted to drift: STOP.

---

## 🔴 GLOBAL RULES — every task, every agent, no exceptions

**Honesty / anti-cheat (this project has been cheated twice — zero tolerance):**
1. **Never grade a component against itself.** Gold/ground-truth must be produced **independently** of the thing being measured. (The last agent built "gold" from the same pipeline that made predictions → fake 100%. Forbidden.)
2. **Never lower a matcher/threshold to inflate a number.** Fix the system, not the ruler.
3. **Never hardcode per-enquiry outputs or `if id == "05"` fast paths.**
4. **A sudden jump to ~100% (or a perfect score) is a RED FLAG, not a win.** Investigate and report it as suspicious.
5. **Report real numbers.** If it fails, say it failed, with the command output. No soft language.
6. Every reported metric must be **independently reproducible** by a single documented command.

**Use your full toolset / skills (do not freestyle):**
- `brainstorming` before any design decision.
- `test-driven-development` for all new code (test first, watch it fail, then implement).
- `systematic-debugging` for every bug/failure before proposing a fix.
- `verification-before-completion` before claiming anything is done (run the command, paste the output).
- `requesting-code-review` before declaring a task complete.
- Use sub-agents / parallel exploration where it genuinely speeds correct work.

**Engineering constraints (from `docs/conventions.md` + `CLAUDE.md`):**
- Imports: `src.` prefix only. Entities/relations from `config.constants`. Tagging: BIOES.
- **Python 3.11–3.13 — NOT 3.14** (3.14 caused the NER segfault/instability; pin the interpreter).
- Type hints on all new code. Every new module gets tests in the matching `tests/` dir.
- Settings via `config.settings.settings` (env prefix `RFQ2BOQ_`).
- Return the 9-section REPORT format (`CLAUDE.md` §11). List every outside-spec edit.

---

## Starting truth (honest baseline — 2026-06-03)

| Metric | Value |
|---|---|
| NER Micro F1 (production, real tenders) | 0.430 |
| NER v2 retrain | 0.213 (below prod, not adopted) |
| Product XLSX row-match vs human gold | 1.8% (and the metric is unfair — see P8T1) |
| Gold | 8 final + 2 draft |
| Tests | 838 passing |
| All 10 enquiries run end-to-end | yes (none crash) |

Honest fix from last session lives on branch `honest-completion` (commit `a05bc52`).

---

## The sprint — tasks, lanes, dependencies

| ID | Task | Lane | Priority | Blocked by |
|---|---|---|---|---|
| **P8T0** | Integrity rebase — adopt honest branch, purge cheat, re-baseline | integrity | **P0 (do first)** | — |
| **P8T1** | Fair end-to-end evaluation (independent row-gold + entity-level product score) | measurement | **P0** | P8T0 |
| **P8T2** | Gold expansion — finish 09/10, collect + annotate +20 real docs | data | **P0** | P8T0 |
| **P8T3** | Gold quality pass — clean material names, drop header/spec noise | data | P1 | P8T0 |
| **P8T4** | PDF extraction quality — sections, tables, material↔qty↔unit pairing | extraction | **P0** | P8T1 |
| **P8T5** | NER retrain — augment + more gold, proper HP, beat 0.43, off 3.14 | model | P1 | P8T2, P8T3 |
| **P8T6** | UI hardening — formats, errors, batch, local model cache, UI tests | product | P1 | P8T0 |
| **P8T7** | Test + CI hardening — fast green `make test`, e2e on all 10, coverage | quality | P1 | P8T0 |
| **P8T8** | Honest handover — deck/exec-summary/demo with real numbers, reproducibility | handover | P2 (last) | all |

**Parallel lanes after P8T0:**
- Lane A (measurement→extraction): P8T1 → P8T4
- Lane B (data): P8T2 ‖ P8T3 → feed P8T5
- Lane C (product/quality): P8T6 ‖ P8T7
- P8T8 closes after the rest report green.

**Dispatch order suggestion:** P8T0 alone → then {P8T1, P8T2, P8T3, P8T6, P8T7} in parallel → P8T4 (after P8T1) ‖ P8T5 (after P8T2/T3) → P8T8.

---

## Definition of done for the sprint
1. `make lint && make type && make test` green, in <5 min, on Python 3.11–3.13.
2. A **fair** end-to-end product metric exists and is reproducible by one command (P8T1) — and it is honest (not a self-comparison).
3. ≥ 28 gold docs total, cleaned (P8T2/T3).
4. NER model that **beats 0.430** on a held-out real set, or a written, evidenced explanation of why not.
5. UI accepts PDF + Excel, never crashes on a bad file, no runtime model download.
6. Honest handover deck/summary with the real numbers and the known gaps.
7. Zero self-comparison metrics anywhere (grep clean).
