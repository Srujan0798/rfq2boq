# TASK P1_02: Per-document fidelity audit tool — the R1 proof artifact — Agent-P1-2

## 1. GOAL
Build the tool that PROVES R1 per document: source rows (from the P1_01 ruler) vs pipeline output rows, with an exact diff of misses, over-captures, and flagged rows — the artifact shown to SWA to demonstrate 100% conversion fidelity.

## 2. CONTEXT
Files to read FIRST (in order):
- `docs/SWA_REQUIREMENTS_2026-06-11.md` — R1 verbatim ("flag, never drop"; "per-document fidelity audit" is named there as the proof)
- `data/real_rfqs/source_truth.json` — the ruler (complete after P1_01)
- `scripts/measure_fidelity.py` — existing corpus fidelity measurement (frozen — you build alongside, not into)
- `scripts/fidelity_audit.py` — existing audit with the restored independence gate (frozen)
- `schema/` — BOQ output JSON schema

Current state:
- `measure_fidelity.py` gives capture percentages but not an SWA-presentable per-document diff.
- Row matching today is count+content heuristics scattered across eval scripts; there is no single canonical "does output row X correspond to source row Y" matcher with documented rules.

## 3. DELIVERABLES
- [ ] `src/domain/fidelity.py` — `FidelityAuditor` class:
  ```python
  class FidelityAuditor:
      def audit(self, doc_id: str, boq_output: BoqDocument, source_truth: SourceTruth) -> FidelityReport: ...
  ```
  `FidelityReport` (dataclass): `captured: list[RowMatch]`, `missing: list[SourceRow]`, `extra: list[OutputRow]`, `flagged: list[OutputRow]`, `verdict: Literal["PASS","FAIL"]` (PASS = 0 missing AND 0 extra; flagged rows do not fail)
- [ ] Row-matching rules DOCUMENTED in the module docstring: match on (normalized description similarity ≥ threshold) AND (qty exact or both-empty) AND (unit normalized-equal); one source row matches at most one output row (greedy best-first); thresholds as module constants
- [ ] `scripts/audit_fidelity_per_doc.py` — CLI: `--doc <id>` or `--all`; writes `results/fidelity/<doc_id>.audit.md` (human table: every source row → matched/missing, every extra row, every flag+reason) and `results/fidelity/summary.json`
- [ ] `tests/unit/test_fidelity_auditor.py` — ≥8 tests: perfect match; 1 missing; 1 extra; flagged-not-failing; duplicate-description disambiguation; qty mismatch = not a match; unit-normalization match (MT vs tonne); empty doc
- [ ] `tests/integration/test_fidelity_audit_e2e.py` — runs the auditor on 2 sacred docs end-to-end against source_truth

## 4. STEPS
1. Read context files. Confirm `source_truth.json` is complete (`needs_manual_count` absent) — if not, STOP: P1_01 isn't actually done.
2. Design the row matcher; write the matching rules in the docstring FIRST, then implement to the documented rules.
3. Implement `FidelityAuditor` + report rendering (markdown table per doc; description column truncated at 80 chars for display but full text stored in JSON).
4. CLI script; unit tests; integration tests.
5. Run `--all` over the boq_bearing docs; commit code + the generated `results/fidelity/` artifacts.
6. Report the honest corpus table: per doc — source rows, captured, missing, extra, flagged, verdict.

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 -m pytest tests/unit/test_fidelity_auditor.py tests/integration/test_fidelity_audit_e2e.py -v   # EXPECT: 10+ passed, 0 failed
python3 scripts/audit_fidelity_per_doc.py --all
ls results/fidelity/*.audit.md | wc -l                    # EXPECT: 33 (or post-P1_00 count)
python3 - <<'EOF'
import json
s = json.load(open('results/fidelity/summary.json'))
print({d['doc_id']: d['verdict'] for d in s['docs']})
print("PASS:", sum(1 for d in s['docs'] if d['verdict']=='PASS'), "/", len(s['docs']))
EOF
# cross-check one doc by hand: open results/fidelity/03_zydus_matoda_osd.audit.md and its worksheet side by side
make lint && make typecheck && python3 -m pytest tests/unit tests/integration -q   # EXPECT: clean / 0 failed
```

## 6. ACCEPTANCE CRITERIA
- [ ] All §5 commands pass; audit artifacts exist for every boq_bearing doc
- [ ] Sacred-10 verdicts consistent with the P0_02-era fidelity numbers (01,02,03,04,06,07,08,09,10 PASS; 05 FAIL-extra pending D5) — any inconsistency explained by documented matcher rules, not hand-waving
- [ ] The auditor NEVER reads pipeline-derived gold — its source side comes exclusively from `source_truth.json` (grep the module for gold paths → none)
- [ ] Coverage of `src/domain/fidelity.py` ≥ 85%
- [ ] Matching rules readable by a non-programmer (SWA will see these)

## 7. CONSTRAINTS
- Frozen files untouched (`measure_fidelity.py`, `fidelity_audit.py`, gold, manifests). Your new tool COEXISTS; consolidation is considered only after Phase 5
- No fuzzy-matching libraries beyond stdlib + already-installed deps (check `pyproject.toml`; rapidfuzz acceptable IF already a dependency)
- Standing constraints: `CLAUDE.md` §7 (type hints, tests, src. imports)

## 8. DEPENDENCIES
- **Blocked by:** P1_01 (needs the complete ruler)
- **Blocks:** P1_03, P3_*, P5_02
- **Parallel-safe with:** P1_04, P2_01
- **Shared files:** none frozen; writes only new paths + `results/fidelity/`

## 9. GOTCHAS
- Similarity thresholds: too loose → over-capture hides as "matched"; too strict → real matches read as missing+extra pairs. Calibrate on 03_zydus (33 rows incl. near-duplicate dimension rows "15MM" vs "15mm OD" — these are DIFFERENT rows and must not cross-match; qty equality is what separates them).
- Unit normalization for MATCHING may use `src/rules/` unit tables but must not mutate the rows.
- A doc with `row_count: 0` + `counting_method: manual` (confirmed-zero) must yield PASS when output is also empty — and FAIL-extra if the pipeline invents rows (the Gopin compliance-checklist scenario).
- `results/` may contain stale reports from earlier eras; write only under `results/fidelity/`, never delete others (they're evidence).
