# TASK P0_02: Restore poisoned gold, apply the D4 ruling, checksum-lock all gold — Agent-P0-2

## 1. GOAL
Make every gold file in the clean room provably owner-trusted: restore the 9 poisoned sacred BIOES gold files to their last trusted state (owner-authorized decision D2), apply the owner's section-header ruling (D4) to 2 rowgold files, then lock everything with a checksum manifest so future tampering fails loudly.

## 2. CONTEXT
Files to read FIRST (in order):
- `tasks/phase9/02_ANTI_CHEAT_PROTOCOL.md` — Rules 2, 3, 5 (this task is their foundation)
- `tasks/phase9/01_STATE_OF_THE_WORLD.md` — §4 topology, §5 problem table
- `scripts/check_gold_provenance.py` — the existing provenance checker you will extend
- `data/real_rfqs/gold/rows/02_isro_vssc.rowgold.json` and `08_sael.rowgold.json` — the two D4 targets

Current state:
- **Incident #12:** on the contaminated branch, 9 sentence-gold files `data/real_rfqs/gold/swa_02_*.json` … `swa_10_*.json` were grown in-place to mirror pipeline output. This clone's copies (from the clean stack) predate the poisoning commits, but their equality to the trusted `b2546b6` state has NOT been proven — that proof is your job. (`b2546b6` exists in this clone's history.)
- **Owner ruling D4 (2026-07-06):** rows that are section titles only (have an item number but no quantity and no unit, and exist solely to introduce child items) are NOT BOQ line items. Two rowgold entries violate this: 02_isro's `"Structure & civil"` row and 08_sael's `"THERMAL INSULATION"` (row 11). They must be removed from rowgold, with the ruling recorded.
- Gold layout: sentence gold `data/real_rfqs/gold/swa_*.json` (10 files + others); row gold `data/real_rfqs/gold/rows/*.rowgold.json` (10 files).

## 3. DELIVERABLES
- [ ] `data/real_rfqs/gold/swa_02…swa_10` (9 files) — byte-identical to their `b2546b6` versions (restore only if they differ; prove it either way)
- [ ] `data/real_rfqs/gold/rows/02_isro_vssc.rowgold.json` — section-header row removed; file gains top-level `"ruling_D4": "section-title rows excluded per owner 2026-07-06"` note field
- [ ] `data/real_rfqs/gold/rows/08_sael.rowgold.json` — same treatment for row 11
- [ ] `data/real_rfqs/gold/GOLD_LOCK.sha256` — sha256 of EVERY file under `data/real_rfqs/gold/` (recursive), one line each
- [ ] `scripts/check_gold_provenance.py` — extended: also verifies `GOLD_LOCK.sha256` matches on-disk gold; any mismatch = hard fail with the offending path
- [ ] `tests/unit/test_gold_lock.py` — ≥4 tests: lock passes on pristine gold; fails on modified file; fails on added file; fails on deleted file (use tmp_path fixtures, never real gold)
- [ ] `docs/GOLD_METHODOLOGY.md` — 1 page: what counts as a gold row (incl. D4 ruling verbatim), who may change gold (owner only), how the lock works, how a legitimate owner edit re-pins hashes

## 4. STEPS
1. Read context files.
2. Prove current-vs-trusted state for the 9 sentence-gold files:
   ```bash
   cd /Users/srujansai/rfq2boq-phase9
   for f in data/real_rfqs/gold/swa_0[2-9]*.json data/real_rfqs/gold/swa_10*.json; do
     git diff --stat b2546b6 -- "$f"
   done
   ```
   For any file that differs, restore: `git checkout b2546b6 -- "$f"`. Record per-file: identical / restored (+insertions/deletions reverted).
3. Apply D4 to the two rowgold files: remove exactly the one offending entry each (match on the description text quoted in §2), decrement any stored row-count fields consistently, add the ruling note. Do NOT touch any other entry.
4. Generate the lock: `find data/real_rfqs/gold -type f ! -name GOLD_LOCK.sha256 -exec shasum -a 256 {} \; | sort -k2 > data/real_rfqs/gold/GOLD_LOCK.sha256`
5. Extend `check_gold_provenance.py` (keep all existing checks; add the lock verification as a new function `verify_gold_lock() -> list[str]` returning offending paths).
6. Write tests; run verification (Section 5).
7. Run the fidelity measurement — 02_isro and 08_sael should now judge as full PASS since the phantom rows left gold:
   ```bash
   python3 scripts/measure_fidelity.py --all | tail -15
   ```
8. Commit as TWO commits: (a) "gold: restore to b2546b6 state + apply D4 ruling (owner-authorized 2026-07-06)", (b) "gold: sha256 lock + provenance hard-fail + tests".

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 scripts/check_gold_provenance.py            # EXPECT: 0 forged, lock INTACT, exit 0
python3 -m pytest tests/unit/test_gold_lock.py -v   # EXPECT: 4+ passed, 0 failed
python3 scripts/measure_fidelity.py --all | tail -15  # EXPECT: 02_isro PASS, 08_sael PASS, others unchanged from P0_01 baseline
python3 -m ruff check scripts/check_gold_provenance.py tests/unit/test_gold_lock.py   # EXPECT: clean
```

## 6. ACCEPTANCE CRITERIA
- [ ] Every one of the 9 files proven identical-or-restored to `b2546b6`, with per-file evidence in the report
- [ ] Exactly 2 rowgold entries removed, nothing else in those files changed (`git diff` shows only those hunks + note fields)
- [ ] Lock file covers 100% of gold files; provenance script hard-fails on any mismatch
- [ ] Fidelity: 02_isro and 08_sael PASS; 01/03/04/06/07/09/10 byte-identical results to P0_01 baseline; 05 unchanged (D5 still open)
- [ ] `make lint` and `make typecheck` clean on touched files

## 7. CONSTRAINTS
- This is the ONLY task ever authorized to modify gold, and only exactly as specified — authority: owner decisions D2 + D4, 2026-07-06
- DO NOT touch `data/annotations/` (draft space, different task), `corpus_manifest.json`, `split_test.json`
- DO NOT "improve" gold content while you're in there — no reformatting, no re-tokenizing, no fixing typos
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P0_01
- **Blocks:** P0_03, all Phase 1+
- **Parallel-safe with:** nothing
- **Shared files:** `scripts/check_gold_provenance.py` (also frozen by P0_03 afterward)

## 9. GOTCHAS
- If git says `b2546b6` is an unknown revision, the clone is damaged — STOP and report; do not improvise a different base.
- The 9 legacy rowgold files carry `human_verified` WITHOUT a reviewer field (legitimate history, restored via commits 5e9bcbb/5478a1c/95e4c39) — the provenance script warns but must not fail on them; keep that behavior.
- 05_zydus_animal's gold is NOT yours to touch — D5 is decided in P1_03 by the owner.
- shasum on macOS = `shasum -a 256` (there is no `sha256sum` by default).
