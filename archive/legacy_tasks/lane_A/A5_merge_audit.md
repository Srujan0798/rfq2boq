# TASK: Lane A — Merge audit + A5 continuous gate — Agent-A

**Worktree:** `/Users/srujansai/Desktop/rfq2boq-laneA`
**Branch:** `phase8-laneA`
**Model:** Strongest available (integrity audit)

---

## 1. GOAL
Audit the completed work on laneC, laneD, laneE against the anti-cheat harness before Srujan merges any lane to `phase8-clean-slate`. Produce a signed-off verdict per lane.

## 2. CONTEXT
Files to read FIRST:
- `results/honest_baseline_2026-06-22.md` — the true baseline numbers
- `scripts/check_gold_provenance.py` — provenance checker
- `scripts/check_eval_hacks.py` — hack detector
- `tests/unit/test_anti_cheat.py` — 11 tests
- `tests/integration/test_self_attack.py` — 16 tests
- `Makefile` — `make verify` (runs 6 checks)

Lane branches to audit:
- `phase8-laneC` (committed) — structure-first extraction
- `phase8-laneD` (will be committed by D agent) — ontology/GeM
- `phase8-laneE` (committed) — pipeline fidelity

## 3. DELIVERABLES
- [ ] `results/lane_merge_audit_2026-06-22.md` — verdict for each lane (PASS/FAIL per check)
- [ ] No code changes unless a genuine cheat is found (document instead)

## 4. STEPS
For each lane (C, D, E):

1. Read the lane's commit diff:
   ```bash
   git log --oneline phase8-lane<X> ^phase8-clean-slate
   git diff phase8-clean-slate...phase8-lane<X> --stat
   git show phase8-lane<X> -1 --format='%b'
   ```

2. Check for cheat patterns (run in main worktree):
   ```bash
   cd /Users/srujansai/Desktop/rfq2boq
   # Pattern 1: self-comparison
   git diff phase8-clean-slate...phase8-lane<X> -- 'data/real_rfqs/gold/' | head -50
   # Pattern 2: threshold lowering
   git diff phase8-clean-slate...phase8-lane<X> | grep -E "threshold|mat_threshold|fuzzy_threshold" | head
   # Pattern 3: filename hacks
   git diff phase8-clean-slate...phase8-lane<X> | grep -E "if.*filename.*==|enquiry.*==|eid.*==" | head
   # Pattern 4: hardcoded perfect scores
   git diff phase8-clean-slate...phase8-lane<X> | grep -E "1\.0|100%" | grep -v "test\|comment\|#" | head
   ```

3. Run anti-cheat suite **in the lane worktree**:
   ```bash
   cd /Users/srujansai/Desktop/rfq2boq-lane<X>
   source .venv-lora/bin/activate
   python3 -m pytest tests/unit/test_anti_cheat.py tests/integration/test_self_attack.py -q --tb=short
   python3 -m ruff check src/ --quiet
   ```

4. For laneE only — run pipeline smoke on the 4 XLSX files; confirm no regression:
   ```bash
   python3 -c "
   from src.pipeline import Pipeline
   p = Pipeline()
   r = p.process_file('data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/05_zydus_animal_pharmez.xlsx')
   print(f'05_zydus: {len(r.rows)} rows')
   assert len(r.rows) >= 40, 'regression: expected 40+ rows'
   "
   ```

5. Write `results/lane_merge_audit_2026-06-22.md`:
   ```markdown
   # Lane Merge Audit — 2026-06-22
   
   | Lane | Commits | Cheat checks | Tests | Verdict |
   |------|---------|-------------|-------|---------|
   | C    | 1       | PASS/FAIL   | N/N   | MERGE/HOLD |
   | D    | 1       | PASS/FAIL   | N/N   | MERGE/HOLD |
   | E    | 1       | PASS/FAIL   | N/N   | MERGE/HOLD |
   
   [Detail per lane]
   ```

6. Commit the audit doc:
   ```bash
   git add results/lane_merge_audit_2026-06-22.md
   git commit -m "audit: lane merge audit A5 — C/D/E verdict"
   ```

## 5. VERIFICATION
```bash
cd /Users/srujansai/Desktop/rfq2boq-laneA
python3 -m pytest tests/unit/test_anti_cheat.py tests/integration/test_self_attack.py -q
cat results/lane_merge_audit_2026-06-22.md
```

## 6. ACCEPTANCE CRITERIA
- [ ] Every lane gets explicit PASS/FAIL on: (a) no gold edits, (b) no threshold lowering, (c) no filename hacks, (d) anti-cheat tests pass, (e) lint clean
- [ ] Any FAIL must describe exactly what was found
- [ ] Audit doc committed to `phase8-laneA`

## 7. CONSTRAINTS
- Read-only analysis of other lanes' branches — no changes to laneC/D/E
- Do not lower any threshold to make tests pass
- Report honestly even if a lane fails

## 8. DEPENDENCIES
- Needs laneD to commit first (D agent runs in parallel)
- Parallel-safe with laneB (B has disjoint paths)

## 9. GOTCHAS
- Use `.venv-lora` (Python 3.12) not `.venv` (3.14) in each worktree
- laneD gold is insulation ontology data only — not row-gold. Self-comparison check doesn't apply to ontology JSON, but verify no pipeline output was copy-pasted as "gold"

---

## REPORT FORMAT
```
## REPORT: Lane A5 — Merge audit

Deliverables:
- results/lane_merge_audit_2026-06-22.md — created

Verdict:
- laneC: PASS / HOLD — [reason]
- laneD: PASS / HOLD — [reason]
- laneE: PASS / HOLD — [reason]

Blockers: none / list
```
