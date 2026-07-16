# NW-06 — Repo hygiene: restore reference PDFs, port phase8 prompts, fix doc errors (P2, run last)

You are working on RFQ2BOQ at /Users/srujansai/Desktop/rfq2boq, branch `phase8-clean-slate`.

## 1. GOAL
Close the loose ends found in the 2026-06-11 full audit so the repo tells one consistent, honest story.

## 2. CONTEXT
- `attic/data_purged_2026_06_11/additional_real/` — today's purge swept REAL reference PDFs (cpwd_*, ireps_*, delhi_pwd_*, epi_*, rfq_road_RFQ9740_050.pdf) out together with the synthetic ones; `deliverables/slides/DEMO_SCRIPT.md` still references the road PDF that no longer exists in data/.
- `main-clean` branch holds `prompts/phase8/` (12 files incl. DISPATCH_PLAYBOOK.md) that exist nowhere on this branch.
- `MASTER_HANDOFF.md` inaccuracies: references `src/ingest/xlsx_pipeline.py` (real file is `src/pipeline_xlsx.py`); states Python 3.14.3 as if fine (charter pins 3.11–3.13).
- `data/real_rfqs/swa_enquiries/manifest.csv` — only 4 legacy entries; should catalog the 10 SWA enquiries (19 files).
- Entity-gold files for non-SWA refs exist: `data/real_rfqs/gold/{cpwd_Guidelines,delhi_pwd_Tender,ireps_*}.json` — their source PDFs are in attic.

## 3. STEPS
1. Create `data/real_rfqs/reference_real/` and restore from attic ONLY the genuinely-real non-SWA files that have gold or demo use: the 2 ireps PDFs, delhi_pwd PDF, 1 cpwd PDF, `rfq_road_RFQ9740_050.pdf`. Add a README explaining they are eval/demo references, NOT training data, NOT synthetic. Leave everything synthetic in attic.
2. `git checkout main-clean -- prompts/phase8/` then `git mv prompts/phase8 prompts/archive/phase8_sprint_2026-06-03/` — preserved as reference, clearly archived (their baseline numbers are stale; add a 3-line README saying so).
3. Fix `MASTER_HANDOFF.md`: correct the module filename, add one line noting the Python-version pin discrepancy, and append a "verified honest metrics" pointer to `results/eval_honest_rows.json` + `HANDOFF.md` instead of per-file ✅-only statuses.
4. Update `deliverables/slides/DEMO_SCRIPT.md` paths to the restored reference file location.
5. Rebuild `manifest.csv` to list all 19 SWA source files (id, client, filename, type, SHA) — script it, don't hand-type.

## 4. VERIFICATION (run, paste real output)
```bash
ls data/real_rfqs/reference_real/
ls prompts/archive/phase8_sprint_2026-06-03/ | head -5
python3 -c "import csv; rows=list(csv.reader(open('data/real_rfqs/swa_enquiries/manifest.csv'))); print(len(rows)-1, 'entries')"
grep -n "xlsx_pipeline" MASTER_HANDOFF.md   # → empty
make verify
```

## 5. ACCEPTANCE CRITERIA
- Reference PDFs restored + documented; synthetic stays archived; manifest lists 19 files; phase8 prompts preserved under prompts/archive/; MASTER_HANDOFF corrections in place; `make verify` passes.

## 6. FORBIDDEN
Restoring synthetic data. Merging any main-clean CODE (prompts only). Touching gold. Rewriting HANDOFF.md numbers.
