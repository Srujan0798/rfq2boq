# TASK: P8T6 — UI Hardening (robust, no runtime downloads) — Agent-UI

**Phase:** 8 | **Priority:** P1 | **Effort:** half–1 day

## 1. GOAL
Make the Streamlit demo UI robust and demo-proof: accept PDF + Excel, never crash on a bad/odd file, cache models locally (no runtime HuggingFace downloads), show progress/timeouts, and cover it with tests.

## 2. CONTEXT
An emergency fix made `ui/app.py` accept `.xlsx/.xls/.pdf`, preserve file extension, and guard the PDF preview (was crashing with `UnidentifiedImageError`), and raised the size limit to 50 MB. That fix is **uncommitted in main** and **untested** — make it permanent and tested. Also: enquiry 09 took 219s and tried to **download xlm-roberta from HF at runtime** — unacceptable for a live/offline demo.

Read first: `ui/app.py`, `ui/components.py`, `ui/pdf_viewer.py`, `src/pipeline.py`.

## 3. DELIVERABLES
- [ ] Commit + finalize the multi-format upload + preview guard (PDF and Excel both supported; Excel shows a sensible "no PDF preview" panel).
- [ ] Replace the runtime HF download with a **locally cached** model load; if the model is missing, show a clear message and fall back — never hang on a network call. No live downloads during a demo.
- [ ] Progress indicator + a hard timeout per file with a friendly message (so a slow doc like 09 never looks frozen).
- [ ] Optional batch upload (process several enquiries, show a summary table).
- [ ] Tests: `tests/unit/test_ui_app.py` (upload routing by extension, size limit, preview-guard, error handling) using Streamlit's `AppTest`.

## 4. STEPS
1. `verify` the current emergency fix end-to-end via `AppTest`; write tests first (TDD) capturing the bugs that bit us (xlsx rejected, .pdf-suffix misroute, preview crash).
2. Make model loading offline-first (use local cache dir; set `HF_HUB_OFFLINE` or pre-fetch at build time; never block on network in the request path).
3. Add per-file timeout + progress; friendly errors for unreadable files.
4. (Optional) batch mode.

## 5. VERIFICATION
```bash
python3 -m pytest tests/unit/test_ui_app.py -v
EXPECT: pass — xlsx accepted, routed by real extension, preview never raises, oversize rejected gracefully

# Offline guard: run with network disabled (or HF_HUB_OFFLINE=1) and confirm no hang/download
HF_HUB_OFFLINE=1 python3 -W ignore -c "from src.pipeline import Pipeline; Pipeline().run('data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx')"
EXPECT: completes; no network call, no exception

# Smoke: UI serves
streamlit run ui/app.py --server.port 8501 --server.headless true & sleep 7
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8501   # 200
```

## 6. ACCEPTANCE CRITERIA
- [ ] PDF + Excel upload both work; bad files produce a friendly error, never a crash/stacktrace in the UI.
- [ ] No runtime model download; works with `HF_HUB_OFFLINE=1`.
- [ ] Progress + per-file timeout; UI tests green; serves 200.

## 7. CONSTRAINTS
- Keep it a single-machine demo app (Streamlit) — NOT a SaaS/website (scope per CLAUDE.md).
- Do NOT show the validation metrics in the UI; the UI demonstrates the live tool only.
- `src.` imports, type hints.

## 8. DEPENDENCIES
- **Blocked by:** P8T0. **Coordinate with:** P8T5 (model location/flag). **Parallel-safe with:** P8T2/T3/T7.

## 9. GOTCHAS
- The 5.2 GB model is gitignored and lives only in the main checkout — the UI must locate it via config, not assume cwd.
- Streamlit caches resources with `@st.cache_resource`; ensure a model swap (P8T5 flag) invalidates the cache.
