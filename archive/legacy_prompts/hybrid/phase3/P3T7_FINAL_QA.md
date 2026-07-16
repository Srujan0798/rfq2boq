# TASK: P3T7 — Final QA & Handover Verification — Agent-4

**Phase:** 3 | **Effort:** 0.5 day | **Priority:** P0 (gates handover to SWA)

## 1. GOAL
Final pre-handover verification gate. Runs every check that matters, confirms nothing is broken, produces a single verification report Srujan can show SWA. Catches any regressions before the project is declared "v1.0".

## 2. CONTEXT
Read first:
- `CLAUDE.md` §8 verification gates (the canonical list)
- `docs/wave_status.md` — what's claimed done
- `docs/SCOPE_GUARD.md` — what should NOT exist in active code
- `HANDOFF.md` — top-level handoff
- `HIERARCHY.md` — directory map
- `Makefile` — available targets
- [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)

This is a READ-ONLY verification task. Make NO code changes. Only produce the report.

## 3. DELIVERABLES
- [ ] `docs/handover_verification_report.md` — comprehensive verification record
- [ ] `results/handover_metrics.json` — machine-readable metrics snapshot
- [ ] Git tag `v1.0-handover` at HEAD (after verification passes)

## 4. STEPS

1. **Code quality gates** — run and record:
   ```bash
   python3 -m pytest tests/unit tests/integration tests/golden tests/fuzz --tb=line -q
   python3 -m ruff check src config tests scripts
   python3 -m mypy src --ignore-missing-imports
   ```
   Record: pass count, fail count, lint clean?, mypy clean?

2. **Pipeline smoke test** — run end-to-end on a known sample:
   ```bash
   python3 -c "
   from src.nlp.pipeline import NLPPipeline
   p = NLPPipeline()
   r = p.process('Supply 500 kg cement as per IS 456 M20 grade at ground floor')
   assert len(r.entities) > 0, 'no entities extracted'
   print(f'entities: {len(r.entities)}, relations: {len(r.relations)}')
   "
   ```

3. **API smoke test**:
   ```bash
   timeout 8 python3 -m uvicorn src.api.main:app --port 8765 &
   sleep 4
   curl -fsS http://localhost:8765/v1/health
   kill %1 2>/dev/null
   ```

4. **UI smoke test**:
   ```bash
   timeout 8 python3 -m streamlit run ui/app.py --server.port 8766 --server.headless true &
   sleep 5
   curl -fsS http://localhost:8766/_stcore/health
   kill %1 2>/dev/null
   ```

5. **Real-world F1 check** — read `results/real_world_metrics_v2.json` or latest `final_model_eval.json`:
   - Real micro F1
   - Per-entity F1
   - Number of test documents
   - Compare against the "honest baseline" of ~0.51 to see if Phase 3 improved it

6. **Data presence check**:
   ```bash
   find data/real_rfqs/raw -name "*.pdf" | wc -l               # >= 50 target
   ls data/real_rfqs/gold/*.json 2>/dev/null | wc -l            # >= 20 target
   python3 -c "import json; d = json.load(open('data/rates/cpwd_dsr_2023.json')); print(len(d['items']))"  # >= 500
   ls data/ontology/omniclass_map.json                          # exists
   ```

7. **Scope guard check** — make sure nothing out-of-scope leaked back into `src/`:
   ```bash
   for path in src/voice src/vision src/drawing src/billing src/mlflow src/observability src/cache src/db src/blockchain src/onnx; do
     [ -d "$path" ] && echo "VIOLATION: $path exists in active src/"
   done

   # Also: no api routes named kg, async, ab_test, voice, billing, tenants
   for r in kg async_routes ab_test voice billing tenants; do
     [ -f "src/api/routes/$r.py" ] && echo "VIOLATION: src/api/routes/$r.py exists"
   done
   ```

8. **Docs cross-reference check** — verify all markdown links in active docs resolve:
   ```bash
   for f in CLAUDE.md HANDOFF.md HIERARCHY.md docs/*.md prompts/INDEX.md; do
     [ -f "$f" ] || continue
     grep -oE '\]\(([^)]+\.md)\)' "$f" | sed -E 's/\]\(([^)]+)\)/\1/' | while read link; do
       [[ "$link" =~ ^https?:// ]] && continue
       dir=$(dirname "$f")
       target=$(python3 -c "import os; print(os.path.normpath('$dir/$link'))")
       [ -f "$target" ] || echo "DEAD LINK in $f -> $link"
     done
   done
   ```

9. **Git state check**:
   ```bash
   git status --short          # should be clean or only known wip
   git log @{u}.. --oneline    # should be empty (all pushed)
   ```

10. **Compose the report** in `docs/handover_verification_report.md`:
    - Project metadata: date, version, branch, commit SHA
    - All 9 sections above with pass/fail + actual output
    - Final verdict: READY / NOT READY (with reasons)
    - List of any scope violations found
    - List of any failing tests

11. **Compose `results/handover_metrics.json`**:
    ```json
    {
      "verified_at": "2026-05-19T...",
      "git_commit": "abc123...",
      "tests": {"passed": N, "failed": N, "skipped": N},
      "lint_clean": true,
      "mypy_errors": N,
      "real_world_f1": 0.XX,
      "real_pdfs": N,
      "gold_annotations": N,
      "dsr_items": N,
      "scope_violations": [],
      "dead_links": [],
      "verdict": "READY"
    }
    ```

12. **Tag** — only if verdict is READY:
    ```bash
    git tag v1.0-handover
    git push origin v1.0-handover
    ```
    If NOT READY, do NOT tag. List blockers in report.

## 5. VERIFICATION

```bash
$ test -f docs/handover_verification_report.md && wc -l docs/handover_verification_report.md
EXPECT: >= 150 lines

$ python3 -c "import json; m = json.load(open('results/handover_metrics.json')); print(m['verdict'])"
EXPECT: READY (or NOT READY with explanation)

$ git tag | grep v1.0-handover
EXPECT: exists IF verdict was READY

$ python3 -m pytest tests/unit tests/integration tests/golden tests/fuzz --tb=no -q
EXPECT: all pass

$ python3 -m ruff check src config tests scripts
EXPECT: clean
```

## 6. ACCEPTANCE CRITERIA

- [ ] Verification report exists and is complete
- [ ] Metrics JSON has all required keys
- [ ] All tests pass (or every failure documented)
- [ ] Lint + type check clean (or every issue documented)
- [ ] No scope violations found (or every one documented)
- [ ] No dead markdown links (or every one documented)
- [ ] Git tag `v1.0-handover` exists IF verdict was READY

## 7. CONSTRAINTS

- READ-ONLY task on `src/`, `tests/`, `data/`, `models/`, `config/`. Make NO code changes.
- May only WRITE to `docs/handover_verification_report.md` and `results/handover_metrics.json`.
- DO NOT skip tests, hooks, or gates to make things pass — report failures honestly.
- DO NOT inflate metrics — copy from source files.
- If something is broken, DOCUMENT it. Do not fix it (that's a separate task).

## 8. DEPENDENCIES

- **Blocked by:** All Phase 1 + Phase 3 tasks (need real metrics + final model)
- **Blocks:** Handover to SWA
- **Parallel-safe with:** None (final gate)

## 9. GOTCHAS

- `tests/property/`, `tests/chaos/`, `tests/load/` may be archived — skip if absent
- Markdown link checker may report false positives for `attic/` paths — exclude attic from the check
- `git status` may show uncommitted log files in `logs/` — those are gitignored, fine
- If `models/rfq2boq-ner-final/` is bloated (>1 GB), flag in report but don't delete
- If real F1 < 0.65, mark verdict as "READY WITH CAVEATS" not "NOT READY" — the project is shippable; the metric just needs honest communication
- The `results/handover_metrics.json` file is the artifact SWA will reference — make it accurate

## End-of-task REPORT

```text
## REPORT: P3T7 Final QA

Deliverables:
- docs/handover_verification_report.md (N lines)
- results/handover_metrics.json
- git tag v1.0-handover: created / NOT created (with reason)

Verification:
- Tests: N passed, N failed, N skipped
- Lint: clean / N issues
- mypy: clean / N errors
- Pipeline smoke: pass / fail
- API smoke: pass / fail
- UI smoke: pass / fail
- Real F1: X.XX
- Real PDFs: N
- Gold annotations: N
- DSR items: N
- Scope violations: N
- Dead links: N

Verdict: READY / READY WITH CAVEATS / NOT READY

Blockers: [list]
Deviations: [list]
Outside-spec edits: [none / list]
```
