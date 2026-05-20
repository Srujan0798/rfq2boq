# TASK: P2T4 — Update Docs to Slim Scope — Agent-4

**Phase:** 2 | **Effort:** 1 day | **Priority:** P1

## 1. GOAL
Bring all top-level documentation (CLAUDE.md, README.md, docs/conventions.md, docs/wave_status.md, docs/architecture.md) in line with the slimmed codebase after P2T1–P2T3. Anything mentioning archived features must be removed or marked archived.

## 2. CONTEXT
Read first:
- `CLAUDE.md` — orchestration charter (mentions all waves)
- `README.md` — user-facing
- `docs/conventions.md` — coding rules
- `docs/architecture.md` — system overview
- `docs/wave_status.md` — wave tracker
- `docs/api.md` — endpoint reference
- `docs/deployment.md` — deployment guide
- `attic/README.md` — should already list what was archived
- [docs/HYBRID_PLAN.md](../../../docs/HYBRID_PLAN.md)

## 3. DELIVERABLES
- [ ] `CLAUDE.md` — Section 3 (Project structure) reflects slimmed layout; Section 5 (Wave status) marks archived items
- [ ] `README.md` — features list, project structure, tech stack updated; archived features removed or footnoted
- [ ] `docs/architecture.md` — diagrams updated; no Neo4j/SpERT/MLflow references unless marked archived
- [ ] `docs/api.md` — voice/billing/tenant routes removed; current routes documented
- [ ] `docs/conventions.md` — unchanged unless rules altered (most stay)
- [ ] `docs/wave_status.md` — clean DONE/ARCHIVED notation
- [ ] `docs/deployment.md` — Docker compose explanation no longer mentions Neo4j/MLflow
- [ ] `docs/HYBRID_PLAN.md` — Phase 2 marked as DONE if applicable
- [ ] `docs/HYBRID_EXECUTION_PLAN.md` — P2T1–P2T4 status updated

## 4. STEPS
1. Read every file in §3 Deliverables.
2. For each, do a search-and-replace pass:
   - Remove or footnote references to: Neo4j, SpERT, MLflow, voice, drawing, sub-domain models, multi-tenant, Stripe, public benchmark, mutation testing, chaos engineering, load testing
   - If a reference is removed: replace with a note like "(moved to `attic/`, see `attic/README.md`)" if context warrants
   - Keep references to: BERT-BiLSTM-CRF, LayoutLM, Camelot, IndicBERT, ARCBERT, OmniClass, CPWD DSR, risk engine, LLM ambiguity resolver, JWT auth
3. Update `CLAUDE.md` Section 3 project structure to match the actual slim layout.
4. Update `CLAUDE.md` Section 5 wave status — mark archived items clearly.
5. Update `README.md` project structure tree.
6. Update `docs/architecture.md` diagrams (text-based diagrams ok; ASCII art).
7. Update `docs/api.md` to list only active routes.
8. Update `docs/wave_status.md`: mark archived task rows as ARCHIVED with link to `attic/`.
9. Update `docs/HYBRID_EXECUTION_PLAN.md` task statuses.
10. Run verification.

## 5. VERIFICATION
```bash
# No active references to archived modules
$ grep -lr "Neo4j\|SpERT\|MLflow tracking\|voice\.transcriber\|drawing\.analyzer\|src\.billing\|public benchmark" \
    CLAUDE.md README.md docs/ 2>/dev/null | grep -v attic | grep -v HYBRID
EXPECT: empty or only mentions in HYBRID_PLAN.md / HYBRID_EXECUTION_PLAN.md (those are allowed)

# API doc reflects current routes
$ grep -c "/v1/" docs/api.md
EXPECT: positive count (≥5 endpoints)

# Architecture diagram doesn't show Neo4j
$ grep -i "neo4j\|spert\|mlflow" docs/architecture.md
EXPECT: empty or only in archived/historical note

# README structure tree matches reality
$ ls -d src/*/ | wc -l > /tmp/dirs.txt
$ grep -c "│   ├──\|│   └──" README.md
EXPECT: README mentions roughly the right number of src/ subdirs

# All cross-references resolve (broken-link grep)
$ for f in $(find docs CLAUDE.md README.md -name "*.md"); do grep -oE '\[.+\]\(([^)]+)\)' "$f" | grep -oE '\([^)]+\)' | tr -d '()'; done | grep -E '\.md$' | sort -u | while read link; do test -f "$link" || echo "DEAD: $link"; done
EXPECT: no DEAD lines (or only known-historical ones)

# Tests still pass (sanity)
$ python3 -m pytest tests/unit tests/integration tests/golden --tb=no
EXPECT: all pass
```

## 6. ACCEPTANCE CRITERIA
- [ ] No active doc references archived features (or they're explicitly marked archived)
- [ ] Project-structure tree in CLAUDE.md + README matches `ls -d */`
- [ ] API doc lists only active routes
- [ ] Wave status uses DONE / ARCHIVED labels clearly
- [ ] No dead markdown links

## 7. CONSTRAINTS
- DO NOT edit `attic/` docs except to clean references
- DO NOT delete `docs/historical/` content — it's the project history
- Keep docs concise; cut anything that no longer applies
- Honest framing: the project is slimmer, more focused, better

## 8. DEPENDENCIES
- **Blocked by:** P2T1, P2T2, P2T3
- **Blocks:** Phase 3 (clean docs before adding more features)
- **Parallel-safe with:** None (final Phase 2 step)

## 9. GOTCHAS
- Cross-references in markdown can break easily — verify with the dead-link grep
- Tables in CLAUDE.md may need re-formatting after edits
- Some terms (e.g., "knowledge graph") appear in many places — search holistically
- HYBRID_PLAN.md and HYBRID_EXECUTION_PLAN.md may mention archived features in context — that's fine; they explain the cut
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)
