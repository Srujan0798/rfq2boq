# T0 — Freeze motion (quarantine unproven work) · ~30 min

## 1. GOAL
Stop all in-flight training and quarantine the unproven `lora-real` checkpoints so nothing untrusted leaks into production while the foundation is rebuilt.

## 2. CONTEXT (read first)
- `tasks/sonnet/RULES.md`, `tasks/ETERNAL_PROTOCOL.md` §AUDIT
- `models/rfq2boq-ner-lora-real/` — trained 2026-07-03/04 with NO data provenance (no training log, no manifest hash) → untrusted by default.

## 3. DELIVERABLES
- `models/quarantine/rfq2boq-ner-lora-real/` (moved, not deleted)
- `models/quarantine/README.md` — one paragraph: why quarantined, date, restoration condition (provenance proof)
- Ledger entry in `tasks/sonnet/LEDGER.md`

## 4. STEPS
1. `ps aux | grep -i -E "train_lora|train.*ner" | grep -v grep` — list any running training processes; kill them (`kill <pid>`), record pids.
2. `mkdir -p models/quarantine && git mv models/rfq2boq-ner-lora-real models/quarantine/ 2>/dev/null || mv models/rfq2boq-ner-lora-real models/quarantine/` (models/ is gitignored — plain `mv` is fine).
3. Write `models/quarantine/README.md`.
4. Check no other job schedulers/launchd/cron entries reference training: `crontab -l 2>/dev/null; ls ~/Library/LaunchAgents 2>/dev/null | grep -i rfq`.
5. Ledger entry + REPORT.

## 5. VERIFICATION
```bash
ps aux | grep -i train_lora | grep -v grep   # expect: empty
ls models/ | grep lora-real                   # expect: empty
ls models/quarantine/                          # expect: rfq2boq-ner-lora-real + README.md
```

## 6. ACCEPTANCE CRITERIA
No training process running; lora-real under quarantine with README; ledger entry with real command output.

## 7. CONSTRAINTS
Do not delete checkpoints (quarantine = reversible). Do not touch other model dirs. No other file changes.

## 8. DEPENDENCIES
Blocks: everything. Blocked by: nothing. Parallel-safe: no.

## 9. GOTCHAS
- Training may have been launched from an opencode worktree (`~/Desktop/rfq2boq-lane*`) — check `ps` output for those paths too.
- `models/` is gitignored: use `mv`, don't fight git.
