# TASK: P8T3 — Gold Quality Pass (clean material names, drop noise) — Agent-Data2

**Phase:** 8 | **Priority:** P1 | **Effort:** half day

## 1. GOAL
Raise gold quality: MATERIAL spans should be clean material names, not section headers, spec paragraphs, or whole sentences. This directly lifts both NER training quality and the fairness of evaluation.

## 2. CONTEXT
`docs/wave_status.md` §9 flags an over-counting / noisy-gold problem. Example bad spans seen in drafts: full clauses tagged MATERIAL ("manifold will be duly insulated with…per Schedule"), generic tokens ("wire", "Pipe"), or headers ("THERMAL INSULATION"). These poison training and metrics.

Read first: `config/constants.py` (entity defs), existing gold in `data/real_rfqs/gold/`, `docs/conventions.md` (annotation rules if present).

## 3. DELIVERABLES
- [ ] `docs/ANNOTATION_GUIDELINES.md` — crisp rules: what is/ isn't a MATERIAL/QUANTITY/UNIT/etc., span minimality, header/spec exclusion, examples of good vs bad.
- [ ] A quality pass over ALL gold (existing 8 + any new from P8T2): tighten MATERIAL spans, remove section-header/spec-paragraph/note spans, fix obvious mis-tags.
- [ ] `scripts/validate_gold.py` extended with quality lints: warn on MATERIAL spans >120 chars, spans equal to known headers, duplicate/whitespace-only spans.
- [ ] `tests/unit/test_validate_gold.py` covering the new lints.

## 4. STEPS
1. Write the guidelines (use real examples from the corpus).
2. Add quality lints to the validator; run to surface offenders.
3. Hand-fix offenders (human authority; do not auto-rewrite spans).
4. Re-run; commit cleaned gold + report of what changed (counts before/after).

## 5. VERIFICATION
```bash
python3 scripts/validate_gold.py --quality 2>&1 | tail -20
EXPECT: 0 errors; warnings triaged/resolved

python3 - <<'PY'
import json,glob
long=0
for f in glob.glob("data/real_rfqs/gold/swa_*.json"):
    for e in json.load(open(f)).get("entities",[]):
        if (e.get("type") or e.get("label"))=="MATERIAL" and len(e.get("text",""))>120: long+=1
print("MATERIAL spans >120 chars:", long)
PY
EXPECT: 0 (or each justified in writing)

python3 -m pytest tests/unit/test_validate_gold.py -v
EXPECT: pass
```

## 6. ACCEPTANCE CRITERIA
- [ ] Guidelines doc exists and is concrete.
- [ ] No over-long MATERIAL spans; no header/spec spans tagged as entities.
- [ ] Validator quality lints + tests green; before/after counts reported.

## 7. CONSTRAINTS
- Human reviews every span change; no automated span rewriting that could fabricate or drop real items silently.
- Keep `ner_tags` in sync with edited entity spans.
- Don't reduce recall by deleting legitimate materials — only remove genuine noise.

## 8. DEPENDENCIES
- **Blocked by:** P8T0. **Coordinate with:** P8T2 (apply guidelines to new gold too). **Feeds:** P8T5.

## 9. GOTCHAS
- "THERMAL INSULATION" as a section header vs as a real line item — context decides; document the call.
- Offsets must stay valid after edits; re-tokenize if needed.
