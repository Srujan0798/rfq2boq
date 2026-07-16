# TASK P1_03: Sacred-10 close-out — D5 decision pack + verified 100% — Agent-P1-3 (+ OWNER)

## 1. GOAL
Close the last open item on the frozen TEST anchor: prepare the owner's decision pack for 05_zydus_animal's multi-quantity-column question (D5), implement whichever rule the owner picks, and land the sacred-10 at a verified, audited 10/10 PASS — the demo-able R1 statement.

## 2. CONTEXT
Files to read FIRST (in order):
- `results/fidelity/05_zydus_animal_pharmez.audit.md` (from P1_02) — the current FAIL detail
- `data/real_rfqs/swa_enquiries/` — find the 05_zydus_animal source XLSX; study its column layout directly
- `data/real_rfqs/gold/rows/05_zydus_animal_pharmez.rowgold.json` — current gold (20 rows)
- `docs/GOLD_METHODOLOGY.md` — D4 precedent for how rulings get recorded

Current state:
- The pipeline extracts 48 rows; owner-verified gold says 20. Diagnosis (ledger 2026-07-05): the source sheet has MULTIPLE quantity columns per material row (e.g. per-area or per-package breakdowns), and the pipeline emits one row per (material × qty-column) instead of one per material line. Nobody has yet laid out the actual column semantics for the owner to rule on.
- This is a business-rule question ("what does one BOQ line mean when the source has qty breakdown columns?"), NOT a bug hunt. Decision is the owner's (D5).

## 3. DELIVERABLES
- [ ] `tasks/phase9/D5_DECISION_PACK.md` — one page for the owner: transcription of the source sheet's header + 3 example rows; the 2–3 candidate rules, each with: resulting row count, what the BOQ output looks like for the example rows, pros/cons for an estimator; a recommendation
- [ ] **[OWNER GATE — STOP HERE until Srujan writes his ruling into the pack]**
- [ ] Implementation of the chosen rule in the XLSX extraction path (exact files depend on the ruling; expected: `src/pipeline_xlsx.py` and/or `src/ingest/table_extractor.py`)
- [ ] If the ruling changes gold or source-truth counts: a written instruction for the ORCHESTRATOR to apply (agents don't touch gold — Rule 3); orchestrator applies + re-pins hashes
- [ ] `tests/integration/test_sacred10_fidelity.py` — asserts, for each of the 10 docs, verdict==PASS via `FidelityAuditor` (this becomes the permanent R1 regression test)
- [ ] Updated `results/fidelity/` artifacts for all 10

## 4. STEPS
1. Read context; transcribe 05's actual sheet structure (openpyxl, raw cell dump of header rows + rows 1–5) into the decision pack.
2. Define candidate rules. At minimum: (A) one row per material line, total qty = sum of qty columns (20 rows); (B) one row per material × qty-column with column-name suffixed into description/location (48 rows); (C) parent row + flagged child breakdown rows. For each: show the exact output for the same 3 example rows.
3. Write recommendation + submit pack; REPORT "BLOCKED — awaiting D5 ruling". Do not proceed.
4. (After ruling) Implement; keep the change narrowly scoped to multi-qty-column table shapes — the other 9 docs' extraction paths must be byte-identical before/after (prove with the auditor).
5. Write the sacred-10 regression test; regenerate audits; commit.

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 scripts/audit_fidelity_per_doc.py --all
python3 - <<'EOF'
import json
s = json.load(open('results/fidelity/summary.json'))
sacred = [d for d in s['docs'] if d['doc_id'].startswith(('01_','02_','03_','04_','05_','06_','07_','08_','09_','10_'))]
assert all(d['verdict']=='PASS' for d in sacred), [d['doc_id'] for d in sacred if d['verdict']!='PASS']
print("SACRED 10: 10/10 PASS")
EOF
python3 -m pytest tests/integration/test_sacred10_fidelity.py -v    # EXPECT: 10 passed
python3 -m pytest tests/unit tests/integration -q                   # EXPECT: 0 failed (all prior tests intact)
make lint && make typecheck
```

## 6. ACCEPTANCE CRITERIA
- [ ] Decision pack written BEFORE any implementation; ruling recorded verbatim with date
- [ ] 10/10 sacred docs PASS under the frozen ruler + auditor
- [ ] Zero diff in extraction results for the other 9 docs (auditor artifacts byte-comparable except timestamps)
- [ ] The ruling is documented in `docs/GOLD_METHODOLOGY.md` (orchestrator adds alongside D4 if gold changed)
- [ ] Regression test locks the achievement permanently

## 7. CONSTRAINTS
- HARD STOP at the owner gate — implementing your own recommendation without the ruling = incident-#7-class violation
- No gold edits by you under any ruling (write orchestrator instructions instead)
- No eval/frozen-file edits; the auditor and ruler measure you, you don't adjust them
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P1_02; owner ruling D5 (mid-task gate)
- **Blocks:** P5_02, P5_03 (the "10/10" claim)
- **Parallel-safe with:** P1_04, P2_01, P2_02 (while blocked at the owner gate, these may dispatch)
- **Shared files:** `src/pipeline_xlsx.py` (also touched by P3_03 — P1_03's implementation half must complete before P3_03 starts)

## 9. GOTCHAS
- The pure-dimension filter in `pipeline_xlsx.py` has been fought over 5+ times (incident #8, re-poisoned in incident #13's fake wave5). Its CORRECT form (conditional: only filter bare dimensions lacking item#+qty+unit) is in this clone's clean stack via `bbc00fc`. Whatever you do for D5 must not weaken that guard — 03_zydus's 33/33 is the canary; the regression test will catch you.
- If the owner picks rule (A) (sum columns): beware unit mismatch across qty columns — if columns carry different units, summing is invalid; that variant needs flagging, cover it in the pack.
- 05 has TWO similarly-named Zydus docs (03_zydus_matoda_osd vs 05_zydus_animal_pharmez) — triple-check you're reading the right file.
