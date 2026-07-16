# TASK P0_03: Restore + freeze the measurement system — Agent-P0-3

## 1. GOAL
Make the ruler trustworthy and immutable: restore the self-comparison hard gate that incident #11 removed, fix the test-suite hang so full verification is actually runnable, and freeze all eval/measurement code behind a checksum manifest checked at every gate.

## 2. CONTEXT
Files to read FIRST (in order):
- `tasks/phase9/02_ANTI_CHEAT_PROTOCOL.md` — Rules 2 and 5 (this task implements them)
- `scripts/fidelity_audit.py` — find `is_independent_gold` (or its remains); compare with `git show b2546b6^:scripts/fidelity_audit.py` and with the current version to understand what was weakened where
- `scripts/check_eval_hacks.py` — existing hack detector; you extend, not replace
- `tasks/phase9/03_VERIFICATION_GATE.md` — Gate 1 consumes your `check_frozen_hashes.py`

Current state:
- Incident #11: a commit titled "anti-cheat hardening" (`b2546b6`) demoted `is_independent_gold()` from hard-fail to `logger.warning`, with a comment admitting circularity. The clean stack (based on `6f46588`, a child of `b2546b6`) therefore CONTAINS the weakened version — it must be re-hardened here.
- The full pytest suite hangs (known GeM-PDF slowness; zombie pytest processes observed for hours). There is no per-test timeout. This makes "make test" unusable as a gate and is why past sessions ran only scoped subsets.
- Eval scripts have been unilaterally edited by agents at least three times (incidents #8, #10, #13) to make bad numbers look good.

## 3. DELIVERABLES
- [ ] `scripts/fidelity_audit.py` — `is_independent_gold()` restored as a HARD gate: non-independent gold → exit non-zero with an explicit message; no flag/env override exists
- [ ] `pyproject.toml` — `pytest-timeout` added to dev deps; pytest config sets `timeout = 120` per test (method: thread)
- [ ] Root-caused fix OR skip-with-reason for each test that exceeds the timeout (list them; slow GeM-PDF tests may move to a `@pytest.mark.slow` tier excluded from the default run but runnable via `make test-slow`)
- [ ] `Makefile` — `test` target uses the timeout; new `test-slow` target
- [ ] `scripts/check_frozen_hashes.py` — verifies sha256 of the frozen set against `config/FROZEN_HASHES.sha256`; prints per-file status; exit non-zero on any mismatch/missing
- [ ] `config/FROZEN_HASHES.sha256` — pinned hashes of: `scripts/{measure_fidelity,fidelity_audit,eval_honest_rows,eval_ner,check_gold_provenance,check_eval_hacks,check_split_leakage}.py`, `tests/regression/*.py`, `config/constants.py`, `data/real_rfqs/{corpus_manifest.json,split_test.json}`, `data/real_rfqs/gold/GOLD_LOCK.sha256`
- [ ] `tests/unit/test_frozen_hashes.py` — ≥3 tests (pass on pristine set, fail on modified, fail on missing) using tmp fixtures
- [ ] `tests/unit/test_fidelity_audit_gate.py` — ≥2 tests proving non-independent gold hard-fails and independent gold passes

## 4. STEPS
1. Read context files; extract the original hard-gate implementation: `git show b2546b6^:scripts/fidelity_audit.py > /tmp/original_fidelity_audit.py` and diff against current.
2. Restore the hard gate (adapt to any legitimate later refactors; the SEMANTICS are what's restored: self-produced gold can never be scored).
3. Add pytest-timeout; run the full suite once to inventory hangs:
   ```bash
   python3 -m pytest tests/unit tests/integration -q --timeout=120 --timeout-method=thread 2>&1 | tail -30
   ```
   For each timeout: root-cause briefly; genuinely-slow-but-correct → `@pytest.mark.slow`; genuinely hung/broken → fix or skip with a written reason in the test file.
4. Build `check_frozen_hashes.py` + pin `config/FROZEN_HASHES.sha256` (pin AFTER all your edits are final — your own edits to fidelity_audit.py are part of the frozen set).
5. Extend `check_eval_hacks.py` if needed so it also greps for reintroduction patterns (env-gated eval behavior, `warning` where the gate should raise).
6. Tests, verification, TWO commits: (a) "eval: restore self-comparison hard gate + test-suite timeout", (b) "eval: frozen-hash gate for all measurement code".

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 -m pytest tests/unit tests/integration -q          # EXPECT: completes < 10 min, 0 failed, no hang
python3 -m pytest tests/unit/test_fidelity_audit_gate.py tests/unit/test_frozen_hashes.py -v   # EXPECT: 5+ passed
python3 scripts/check_frozen_hashes.py                     # EXPECT: "ALL FROZEN FILES INTACT", exit 0
grep -n "warning" scripts/fidelity_audit.py                # EXPECT: no warning where the independence gate should raise
python3 scripts/measure_fidelity.py --all | tail -15       # EXPECT: identical numbers to P0_02's accepted run
make lint && make typecheck                                # EXPECT: clean
```

## 6. ACCEPTANCE CRITERIA
- [ ] Full default test suite completes without manual intervention, 0 failed
- [ ] Independence gate: unit-proven hard-fail, and NO override path (grep for `ALLOW_`, `SKIP_`, `os.environ` in fidelity_audit.py → none gate the check)
- [ ] Frozen-hash gate covers every file listed in §3 and fails loudly on tamper
- [ ] Fidelity numbers unchanged from P0_02 (this task must not move any metric — it only hardens measurement)
- [ ] Every skipped/slow-marked test has a written reason

## 7. CONSTRAINTS
- DO NOT change what any eval script MEASURES (scoring logic, thresholds, exclusion rules) — only restore the gate and add infrastructure. If you find scoring logic you believe is wrong (e.g. the incident-#10 rate-only exclusion), DOCUMENT it in your report for the owner; touch nothing
- DO NOT modify gold or `GOLD_LOCK.sha256` (P0_02 owns those; your manifest pins the lock file's hash as-is)
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P0_02 (its lock file gets pinned here)
- **Blocks:** all Phase 1+ (the gate machinery starts at P1_00)
- **Parallel-safe with:** nothing
- **Shared files:** `scripts/check_gold_provenance.py` (read-only here), `Makefile`

## 9. GOTCHAS
- After this task, ANY task touching a frozen file trips Gate 1 by design — only the orchestrator re-pins hashes. Design your manifest format so a re-pin is a one-command operation (documented manual command with a printed warning).
- `--timeout-method=thread` is required on macOS; the default signal method breaks under some C extensions.
- The incident-#10 eval change (rate-only/zero-qty rows excluded from FP) may or may not be present in the clean stack — CHECK (`git log -p 6f46588 -- scripts/eval_honest_rows.py | head -100`). Whatever you find: report which version the clean stack has; do not change it.
- Slow GeM tests: the underlying cause (25MB+ scanned PDFs through OCR paths) is a real product issue tracked in P3_01 — don't fix extraction here, just tier the tests.
