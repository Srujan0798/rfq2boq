# TASK P1_04: Crash-free pipeline across ALL corpus documents — Agent-P1-4

## 1. GOAL
The pipeline must process every one of the corpus documents (127 pre-sweep; use the post-P1_00 count) without crashing or hanging — the precondition for corpus-wide annotation (Phase 2) and honest corpus metrics. Extraction QUALITY beyond the sacred 10 is Phase 3; this task is about survival + honest run inventory.

## 2. CONTEXT
Files to read FIRST (in order):
- `data/real_rfqs/ALL_RFQS_README.md` + `corpus_manifest.json` — the docs, paths, types
- `tasks/sonnet/LEDGER.md` rows for T4b + "live upload test" (2026-07-05) — the crash classes already found: `KeyError: 'boq_rows'` on blank pages; excel export crash on `list[str]` standard/grade cells; compliance-checklist false-positive tables
- `src/pipeline.py`, `src/pipeline_xlsx.py` — the two entry paths
- `scripts/batch_process_dir_robust.py` — prior art for batch running (may be reusable or cruft; judge)
- Branch `w3-tip-untriaged` (this clone): 2 unverified commits (`cc61c7a` multi-sheet workbook processing, `fe1e305` qty-column serial-number monotonicity) — READ their diffs as reference; if either fixes a crash/drop class you hit, re-verify it properly (fresh tests, full sacred-10 before/after) and re-implement or cherry-pick WITH verification evidence — never adopt blind

Current state:
- Only the sacred 10 + ~19 boq_bearing docs have ever been systematically run in a verified context. 78 spec_only + 16 non_training docs are largely untested through the pipeline.
- Known crash fixes from 2026-07-05 happened across different worktrees and may be absent from this clone's clean stack — part of your job is establishing which fixes are present and re-applying missing ones PROPERLY (with tests).

## 3. DELIVERABLES
- [ ] `scripts/run_corpus.py` — batch runner: iterates the manifest (`--split all|train|dev|test`, `--type boq_bearing|spec_only|non_training|all`), per-doc timeout (default 300s, configurable), catches exceptions, writes `results/corpus_run/<run_id>/status.json` (per doc: ok/crash/timeout, duration, rows extracted, output paths) + `run.log`
- [ ] Fixes for every crash/hang found, each with: root cause (1 paragraph in report), minimal fix in `src/`, and a unit test reproducing the failure shape
- [ ] `tests/unit/test_corpus_crash_fixes.py` (or extend existing suitable files) — one test per fixed crash class
- [ ] `results/corpus_run/<run_id>/` — the final full-corpus run artifact: all docs ok

## 4. STEPS
1. Read context. Check which known fixes exist in the clean stack:
   ```bash
   grep -n "get('boq_rows'" src/preproc/sections.py || grep -n "\['boq_rows'\]" src/preproc/sections.py
   grep -n "_looks_like_compliance_checklist" src/ingest/table_extractor.py
   grep -n "join" src/export/excel_generator.py | head
   ```
   Report present/absent for each; re-implement absent ones (fresh, with tests — do NOT copy code from the Desktop repo).
2. Build `run_corpus.py` (subprocess-per-doc or signal-based timeout — must survive a single doc hanging).
3. Run over the full manifest; triage failures into crash classes; fix root causes one class at a time, re-running only affected docs between fixes.
4. Full clean re-run at the end (fresh `run_id`); verify sacred-10 fidelity untouched:
   ```bash
   python3 scripts/audit_fidelity_per_doc.py --all   # numbers must equal the last accepted run
   ```
5. Commit per crash-class fix (separate commits) + final run artifacts.

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 scripts/run_corpus.py --split all --type all
python3 - <<'EOF'
import json, glob
run = sorted(glob.glob('results/corpus_run/*/status.json'))[-1]
s = json.load(open(run))
bad = [d for d in s['docs'] if d['status'] != 'ok']
assert not bad, bad
print(f"CORPUS RUN: {len(s['docs'])} docs ok, slowest: {max(d['duration'] for d in s['docs']):.1f}s")
EOF
python3 -m pytest tests/unit tests/integration -q     # EXPECT: 0 failed
python3 scripts/audit_fidelity_per_doc.py --all       # EXPECT: sacred-10 verdicts unchanged
make lint && make typecheck
```

## 6. ACCEPTANCE CRITERIA
- [ ] All manifest documents process to completion (ok status) within per-doc timeout
- [ ] Every fix has a reproducing test; no fix is a bare try/except-pass (silent failure = R1 violation — a doc that can't be processed must FAIL loudly in status, not pretend)
- [ ] Sacred-10 fidelity byte-identical before/after (Gate 4)
- [ ] No eval/gold/frozen changes; no quality "improvements" smuggled in (quality is Phase 3 — scope discipline)
- [ ] Report lists every crash class: symptom → root cause → fix commit; and a verdict on each w3-tip-untriaged commit (adopted-with-verification / rejected / not-relevant)

## 7. CONSTRAINTS
- Do NOT chase extraction quality (wrong rows, missed rows) on non-sacred docs here — record observations in the report for P3_* instead
- Per-doc timeout must not be raised above 600s to make a hang "pass" — a >600s doc is a real problem to fix or report
- OCR-heavy GeM PDFs: optimize only if a doc times out; otherwise note duration and move on
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P0_03
- **Blocks:** P2_03 (annotation drafts need every train doc processable), P3_*
- **Parallel-safe with:** P1_02, P2_01 (different files); NOT with P1_03's implementation half (both may touch `pipeline_xlsx.py`)
- **Shared files:** `src/pipeline.py`, `src/pipeline_xlsx.py`, `src/ingest/*`, `src/preproc/*`

## 9. GOTCHAS
- The blank-page `KeyError` fix pattern: `analyse_page()` early-returns a dict without `boq_rows` for empty pages; the correct fix is `.get(key, 0)` at the consumer (`find_boq_pages`) — semantically "blank page = zero BOQ signal".
- `BoqRow.standard` / `grade` are `list[str]` BY DESIGN; exporters must join for display, never change the schema.
- Some corpus paths contain spaces and unicode (e.g. `Specification 2/`, `Copy of Insulation Enquiry - SAEL.xlsx`) — quote everything; use pathlib.
- Non-training docs (make-lists, GCC annexures, prebid queries) legitimately yield 0 rows — that's `ok` with 0 rows, not a crash; do NOT force extraction out of them.
- macOS open-file limits can bite a full-corpus batch if handles leak — close workbooks/PDFs explicitly.
