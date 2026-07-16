# VERIFICATION GATE — run by the ORCHESTRATOR after every task, before acceptance

The agent's REPORT is input, not evidence. The gate re-derives everything. A task is CLOSED in `04_LEDGER.md` only when every applicable step below passes with output the orchestrator saw itself.

All commands run **inside `/Users/srujansai/rfq2boq-phase9`** (referred to below as `$W`).

---

## Gate 0 — Workspace integrity (every task, first)

```bash
cd $W
git status --short                  # EXPECT: only files the task's §3 DELIVERABLES lists
git log --oneline -3                # EXPECT: HEAD is the task's commit(s) on phase9-final, parent unchanged
git merge-base --is-ancestor 0e1cd4e HEAD && echo BASE-OK   # EXPECT: BASE-OK
git branch --show-current           # EXPECT: phase9-final
```
Any modified file NOT in the task's deliverables list → reopen the task ("Files modified outside spec"). Any fetch/merge from `origin` → instant reopen (Rule 7).

## Gate 1 — Frozen-file checksums (every task)

```bash
cd $W && python3 scripts/check_frozen_hashes.py     # created by P0_03
# EXPECT: "ALL FROZEN FILES INTACT" and exit 0
```
Covers: all `data/real_rfqs/gold/**`, `corpus_manifest.json`, `split_test.json`, `source_truth.json`,
`scripts/{measure_fidelity,fidelity_audit,eval_honest_rows,eval_ner,check_gold_provenance,check_eval_hacks,check_split_leakage}.py`,
`tests/regression/**`, `config/constants.py`.
If the TASK legitimately changes a frozen file (only P0_02, P0_03, P1_00, P1_01, P1_03 §D5, P2_04, P5_02 may), the orchestrator — not the agent — re-pins hashes and records old→new in the ledger row.

## Gate 2 — Provenance + leakage (every task)

```bash
cd $W
python3 scripts/check_gold_provenance.py            # EXPECT: 0 forged, exit 0
python3 scripts/check_split_leakage.py              # EXPECT: no TEST-derived data in train paths, exit 0
python3 -m pytest tests/regression/ -x -q           # EXPECT: passes (skips allowed only with reasons)
```

## Gate 3 — Code health (any task touching src/, scripts/, tests/)

```bash
cd $W
make lint                                           # EXPECT: clean
make typecheck                                      # EXPECT: clean (no new errors vs pre-task baseline)
python3 -m pytest tests/unit tests/integration -q --timeout=120   # EXPECT: N passed, 0 failed (timeout plugin from P0_03)
```

## Gate 4 — Fidelity reproduction (any task touching extraction, ingest, pipeline, export)

```bash
cd $W && python3 scripts/measure_fidelity.py --all > /tmp/gate_fidelity.txt
diff <(grep -E "^(doc|TOTAL)" /tmp/gate_fidelity.txt) <(grep -E "^(doc|TOTAL)" results/FIDELITY_REPORT.md)
# EXPECT: the agent's committed report matches a fresh run, byte-for-byte on the numbers
```
Then compare against the PREVIOUS task's accepted numbers: any doc that regressed → reopen. Any doc that jumped to 100% → apply Rule 2 skepticism: inspect the actual diff that explains it before accepting.

## Gate 5 — Metric-claim audit (every task)

For each number in the agent's REPORT:
1. Find the command in the report that produced it. No command → number rejected.
2. Re-run that command. Different result → task reopened, discrepancy quoted in ledger.
3. Scan the diff for red-flags (`02_ANTI_CHEAT_PROTOCOL.md` checklist): eval edits, test-expectation edits, new gating flags, gold touches.

```bash
cd $W && git diff <parent>..HEAD --stat   # eyeball every file against §3; then:
git diff <parent>..HEAD -- scripts/ tests/ data/real_rfqs/ config/   # EXPECT: empty unless §3 says otherwise
```

## Gate 6 — Task-specific acceptance

Run every command in the task file's §5 VERIFICATION exactly as written; check every §6 ACCEPTANCE box. Partial pass = reopen (or ledger-record an owner-approved descope, never a silent one).

## Recording

Ledger row format (append to `04_LEDGER.md`):
```
| date | task-id | gate result (G0–G6 pass/fail each) | key evidence (command + 1-line output) | CLOSED / REOPENED(reason) |
```

## Owner escalation triggers (stop dispatching, message Srujan)

- Gate 1 checksum mismatch not explained by the task's charter
- Any gold/provenance/leakage failure
- ANY sign the Desktop-repo swarm wrote into this clone (mtime anomalies, unexplained refs, origin fetches)
- An agent argues an eval script is wrong (may be right! — but it's an owner/orchestrator ruling, not a code change)
- Two consecutive reopens of the same task (spec is probably wrong — revise the task file instead of burning attempts)
