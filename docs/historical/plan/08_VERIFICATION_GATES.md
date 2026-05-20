# VERIFICATION GATES (ORC + Reverse-Role Self-Attack)
## "What blocks shipping, by gate"

Each gate is automated where possible; manual sign-offs are explicit.

---

## GATE-1: CODE QUALITY  (every PR, blocks merge)

- [ ] `ruff check .` zero errors
- [ ] `black --check .` clean
- [ ] `mypy --strict code/` zero errors
- [ ] `pre-commit run -a` green
- [ ] No `# TODO` / `print(` / `breakpoint()` in non-test code
- [ ] All new functions have docstrings + types

Automated in `.github/workflows/ci.yml` step `lint`.

---

## GATE-2: TESTING  (every PR + nightly, blocks merge)

- [ ] `pytest -q` all green
- [ ] Coverage report ≥ 80% line / 70% branch
- [ ] No new flaky tests (rerun 3x)
- [ ] Integration tests on shipped sample all green
- [ ] Performance benchmark within budget

Automated in CI step `test`.

---

## GATE-3: MODEL QUALITY  (weekly from W4; blocks training merges)

- [ ] Span-F1 micro on dev ≥ last-known minus 1 pp
- [ ] Per-type F1 above floor (see ontology doc)
- [ ] Latency p95 within budget
- [ ] Calibration ECE ≤ 0.05 (model not over/underconfident)
- [ ] Error analysis notebook updated

Automated in `.github/workflows/eval.yml`.

---

## GATE-4: DATA QUALITY  (per batch in Step 2/4)

- [ ] Annotation IAA Cohen's κ ≥ 0.75
- [ ] No PII leakage (regex audit)
- [ ] License audit passes
- [ ] No train/test source overlap
- [ ] Per-source class balance reported

Manual sign-off by orchestrator on weekly batch.

---

## GATE-5: DOMAIN CORRECTNESS  (Step 6 onward)

- [ ] Output schema matches `schema/boq.v1.json` (auto)
- [ ] Excel template round-trips (auto)
- [ ] Confidence column present and calibrated (auto)
- [ ] Warning column populated when applicable (auto)
- [ ] SCOPE_GAP_WARNING fires on seeded gap (auto)
- [ ] Unit normalization correct on 100-case golden table (auto)
- [ ] Standards regex coverage report shipped (manual sign-off)

---

## GATE-6: RELIABILITY  (Step 7 onward)

- [ ] Crash-safe: `kill -9` during processing → resumable from last stage
- [ ] 100 concurrent requests p95 < 90s (auto, load test)
- [ ] Memory ceiling proven (no OOM under 4GB)
- [ ] Malformed PDF inputs raise typed errors, never crash worker

---

## GATE-7: REPRODUCIBILITY  (W8 sign-off)

- [ ] Cold-clone → `make demo` works on Linux, macOS, Windows (WSL)
- [ ] Same seed → bytewise-identical canonical JSON
- [ ] Model card + checkpoint + tokenizer in git-LFS
- [ ] All deps pinned; `uv.lock` committed
- [ ] Docker image builds offline (after pull)

---

## GATE-8: DOCUMENTATION  (W9-10)

- [ ] README quickstart works as written (doctest CI)
- [ ] API docs auto-generated and committed
- [ ] Architecture diagrams up-to-date
- [ ] Runbook covers: deploy, restart, common failures, log locations
- [ ] All ADRs accepted/superseded (no "draft" status)

---

## ORC BRUTAL REVIEW — STEP 8

Orchestrator sits as adversarial reviewer for one full day. Checks:

### Code review pass
- Open every file under `code/`. Anything I wouldn't ship as a senior engineer? File issue.
- Is each module under 500 lines, single responsibility, named clearly?
- Is the public API of each module minimal?

### Architecture review pass
- Re-read `01_ARCHITECTURE.md` against current code. Drifts? Fix code or update doc (no third option).
- Stage interfaces still match? Pydantic models still load every saved artifact?

### Risk register pass
- Walk every P0/P1 in `03_RISK_REGISTER.md`. Evidence of mitigation? Pointer to test/code/log?

### Domain pass
- Show output to a quantity surveyor (mentor). Their first 3 complaints become issues.

### "Could this lose a contract?" pass
- Take 1 RFQ. Run system. Read output. If the gap between BOQ output and what an estimator would charge for is > 5% of total scope, **system is not ready.**

---

## SIGN-OFF CHECKLIST (W10 final)

| Item | Owner | Status |
|---|---|---|
| All gates 1-8 green | A-4 | ☐ |
| Risk register: 0 P0 / 0 P1 open | Orch | ☐ |
| Mentor sign-off on output quality | Orch | ☐ |
| Demo recorded | A-3 | ☐ |
| Report PDF committed | Orch | ☐ |
| Slides committed | Orch | ☐ |
| Final eval report committed | A-2 | ☐ |
| Repo zipped + handed off | Orch | ☐ |

---

## "WHAT IF THIS FAILS" — runbook for each gate

- **Gate-1 red** → block PR, request rewrite.
- **Gate-2 red** → block PR; if main is red, revert last merge automatically.
- **Gate-3 model regression** → block model merge; investigate; allow only with explicit ADR.
- **Gate-4 IAA drop** → halt annotation; recalibrate; redo affected batch.
- **Gate-5 schema break** → version bump; migration in `normalize/`.
- **Gate-6 reliability** → backpressure + queue size cap; degraded mode flag.
- **Gate-7 repro** → fix path before ship; non-negotiable.
- **Gate-8 docs** → release blocked until docs caught up.

---

**Status:** Gates locked. Each one has a CI hook or an explicit human sign-off slot.
