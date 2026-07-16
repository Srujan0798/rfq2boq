# T2 — Gold trust reset: audit the 28 `human_verified:true` stamps · owner-gated

## 1. GOAL
Make `human_verified:true` mean exactly one thing — Srujan personally reviewed it — by auditing every existing stamp (28 files, stamped by agent commits) and hardening the provenance checker so agents can never stamp again.

## 2. CONTEXT (read first)
- Incident #4 in `tasks/ETERNAL_PROTOCOL.md` §AUDIT: agents stamped `human_verified:true` after modifying gold (2026-06-08). It happened again ~2026-07-01 (commits `986d88c`, `03d3459`).
- `scripts/check_gold_provenance.py` — current checker
- Gold locations: `data/real_rfqs/gold/`, `data/annotations/`

## 3. DELIVERABLES
- `results/gold_trust_audit.md` — table: file · stamped-by commit · commit author · content summary (docs/rows/sentences) · verdict (owner-confirmed / reverted-to-false)
- All unaudited stamps flipped to `human_verified:false` (content preserved as draft)
- Hardened `scripts/check_gold_provenance.py`: `true` requires `reviewer: "srujan"` + `review_date`; anything else fails `make verify`
- Extended `tests/unit/test_anti_cheat.py`: a gold file with `true` but no reviewer field fails

## 4. STEPS
1. Enumerate: `grep -rl '"human_verified": true' data/ | sort` → for each, `git log --oneline -3 -- <file>` to find the stamping commit + author.
2. Build `results/gold_trust_audit.md` from that evidence.
3. **STOP — owner step:** present the table. For each file Srujan says "I reviewed this" → keep `true` and ADD `reviewer/review_date` fields. Everything else → flip to `false` (content intact).
4. Harden the checker + test. Run `make verify`.
5. Also verify the frozen v1 gold edits (02_isro 10→5, 04_adani 13→45, 06 20→31, 07 5→9 source-row changes): list the commits that changed them for the owner's T1 review session — the two audits are done together in one sitting.
6. Ledger entry + REPORT.

## 5. VERIFICATION
```bash
grep -rl '"human_verified": true' data/ | xargs grep -L '"reviewer"' | wc -l   # expect: 0
PYTHONPATH=. .venv/bin/python scripts/check_gold_provenance.py                  # green
.venv/bin/python -m pytest tests/unit/test_anti_cheat.py -q                     # green
make verify                                                                      # green
```

## 6. ACCEPTANCE CRITERIA
Zero `true` stamps without reviewer+date; audit table committed; checker + test enforce it permanently.

## 7. CONSTRAINTS
Never delete annotation content — reverting trust ≠ deleting drafts. Never decide yourself that a stamp is legitimate; only the owner's word converts a stamp.

## 8. DEPENDENCIES
Blocks: T5, T6. Blocked by: T0. Parallel-safe: with T1/T3 (different files).

## 9. GOTCHAS
- Loaders read both `ner_tags` and `labels` keys — don't normalize schemas in this task; trust flags only.
- Some gold lives in worktree copies (`~/Desktop/rfq2boq-lane*`) — audit ONLY the main tree; note stragglers in the report.
