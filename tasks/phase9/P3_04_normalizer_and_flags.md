# TASK P3_04: Unified unit normalizer + flag-never-drop wired end-to-end — Agent-P3-4

## 1. GOAL
One canonical unit-normalization module used by every stage, and the R1 flag system made real end-to-end: every uncertainty anywhere in the pipeline becomes a visible, typed flag that survives into Excel/JSON output — nothing is ever silently dropped or silently guessed.

## 2. CONTEXT
Files to read FIRST (in order):
- `tasks/NW05_unified_unit_normalizer.md` + `tasks/REPORT_NW05.md` — the prior partial attempt (what exists, what was left)
- `src/rules/` — current unit handling; `src/domain/boq_assembler.py` — the unit-normalization tie-breaker from the clean stack
- `schema/` BOQ output schema — where flags must live
- Flag producers already created by Phase 3: `structure_fallback` (P3_01), `column_fallback` (P3_02), table-type flags + GeM validation flags (P3_03/P2_01) — inventory ALL flag-like fields currently emitted (grep for `flag` across src/)

Current state:
- Unit knowledge is scattered (patterns, rules, assembler tie-breaker, exporters). Indian tender units are wild: `Rmt/RMT/R.M./running meter`, `Sqm/SQM/M2/Sq.Mtr`, `MT/T/tonne`, `Nos/No./Each/EA`, `Cum/M3`.
- Flags exist ad-hoc; no schema, no severity, no guaranteed export surfacing. R1's "flag, never drop" is only as real as its weakest stage.

## 3. DELIVERABLES
- [ ] `src/rules/units.py` — `UnitNormalizer`: `normalize(raw: str) -> NormalizedUnit` (canonical form, dimension class [length/area/volume/mass/count/set], original preserved); table-driven from `data/ontology/units.json` (extend the existing ontology file, provenance-noted); UNKNOWN units normalize to themselves + produce a flag, never an exception
- [ ] All unit-touching call sites migrated to the one normalizer (list every call site in the report); duplicated tables deleted
- [ ] `src/domain/flags.py` — `Flag` dataclass: `code` (closed enum addition to `config/constants.py` — prepared as a patch for the ORCHESTRATOR to apply + re-pin), `severity` (info/review/error), `stage`, `message`, `row_ref`; document-level + row-level attachment
- [ ] Every existing ad-hoc flag migrated onto the typed system; every `continue`/`return None`/silent-except in extraction paths audited: each either (a) provably safe (comment why) or (b) now emits a flag — audit table in report
- [ ] `schema/` updated: flags arrays on document + row objects (schema version bump)
- [ ] JSON exporter carries flags through NOW (Excel visual treatment is P5_01)
- [ ] `tests/unit/test_units.py` — ≥12 tests (each dimension class, Indian variants above, unknown-unit flag, idempotence)
- [ ] `tests/unit/test_flags.py` — ≥6 tests (typing, attachment, JSON round-trip)

## 4. STEPS
1. Read context; produce the two inventories FIRST (unit call sites; silent-drop audit) — paste both in the report before changing code.
2. Build normalizer + ontology table (seed from all variants observed in corpus outputs — grep the P1_04 run artifacts for distinct unit strings; that's your real-world test vector list).
3. Migrate call sites one commit per subsystem (patterns / assembler / exporters).
4. Build flag system; migrate producers; close silent-drop audit items.
5. Full regression battery; commit.

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 -m pytest tests/unit/test_units.py tests/unit/test_flags.py -v    # EXPECT: 18+ passed
python3 - <<'EOF'
from src.rules.units import UnitNormalizer
n = UnitNormalizer()
for raw, canon in [("Rmt","rmt"),("R.M.","rmt"),("SQM","sqm"),("Sq.Mtr","sqm"),("M2","sqm"),("Nos","nos"),("EA","nos"),("MT","mt"),("tonne","mt"),("Cum","cum")]:
    assert n.normalize(raw).canonical == canon, (raw, n.normalize(raw))
print("UNIT VECTORS OK")
EOF
python3 scripts/audit_fidelity_per_doc.py --all      # EXPECT: verdicts unchanged (normalization must not move row matching)
python3 scripts/run_corpus.py --split all --type all # EXPECT: all ok; flag counts per doc in status.json
python3 -m pytest tests/unit tests/integration -q && make lint && make typecheck
```

## 6. ACCEPTANCE CRITERIA
- [ ] ONE normalizer; grep proves no duplicate unit tables remain (`grep -rn "sqm\|rmt" src/ | grep -iv units` reviewed in report)
- [ ] Silent-drop audit: 100% of extraction-path early-exits classified (a) or (b); zero unexplained
- [ ] Flags typed, enumerated in constants (via orchestrator patch), carried through JSON export
- [ ] Sacred-10 + corpus regressions: none
- [ ] Unknown unit → flagged row present in output (prove with one real corpus example)

## 7. CONSTRAINTS
- `config/constants.py` is frozen — your FlagCode enum addition is prepared as a patch the ORCHESTRATOR applies + re-pins (include the exact diff in your report; do not commit it yourself)
- Scope: unpriced BOQ — no currency/rate units in the ontology
- Frozen files untouched; Rule 8
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P3_02, P3_03 (their flag producers must exist to migrate)
- **Blocks:** P5_01 (export/UI surfacing), P5_02
- **Parallel-safe with:** P2_04, P4_01 prep
- **Shared files:** `src/domain/boq_assembler.py`, exporters, `schema/`

## 9. GOTCHAS
- The assembler's unit tie-breaker (clean-stack commit) resolves conflicting unit signals per row — the normalizer must slot UNDER it (normalize both candidates first), not replace its resolution logic.
- "MT" is metric tonne in tenders, never "empty"; "M" alone is ambiguous (meter vs thousand) — ambiguous singles normalize to UNKNOWN+flag rather than guess (R1: a wrong guess is worse than a flag).
- Dimension class matters downstream (a qty in sqm attached to a length-dimensioned material is a red-flag combo P5_02's invariance tests can use) — get the classes right even where canonical strings are easy.
- JSON schema bump: keep a `schema_version` field; the UI and tests read it — grep for consumers before bumping.
