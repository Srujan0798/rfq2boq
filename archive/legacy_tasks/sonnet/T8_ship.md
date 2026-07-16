# T8 — Ship: deliverables, demo, handoff, owner checklist

## 1. GOAL
Package the finished, honest product: deliverables carry T7's exact numbers, the demo works on a real tender end-to-end, and the owner-only actions are laid out for Srujan to close the project.

## 2. CONTEXT
- `results/FINAL_EVAL.md`, `results/fidelity_full_corpus.md` (the only permitted number sources)
- `deliverables/` (FINAL_HONEST_REPORT.md, EXECUTIVE_SUMMARY.md, SWA_DEMO_GUIDE.md, slides/), `HANDOFF.md`, `README.md`
- `ui/app.py` (Streamlit), `src/cli/`, `src/api/`, `deployment/`

## 3. DELIVERABLES
- All deliverables + HANDOFF.md + README.md updated with final numbers VERBATIM (grep-check: no stale claims like "89%", "24.2%", "100% COMPLETE" unless T7 actually produced them)
- `results/demo_smoke.md` — evidence of: CLI run on a real tender → xlsx+json out; API upload round-trip; Streamlit renders BOQ + flags + catalog matches; Docker build+run
- `docs/FUTURE_RFQ_RUNBOOK.md` — one page: how SWA processes a brand-new RFQ (upload → review flags → export), and how new docs enter the annotation loop
- Final ledger closure entries in `tasks/sonnet/LEDGER.md` + gate closures in `tasks/ETERNAL_PROTOCOL.md`

## 4. STEPS
1. Sweep every doc in `deliverables/`, `HANDOFF.md`, `README.md`, `docs/` for stale/false numbers: `grep -rn -E "100% COMPLETE|89%|0\.890|24\.2|32\.3" deliverables/ HANDOFF.md README.md docs/` — replace with T7/T4 finals, cite the results file next to each number.
2. Demo smoke tests (record real commands + output in `results/demo_smoke.md`):
   - `PYTHONPATH=. .venv/bin/python -m src.cli --file "data/specifications/Specification 2/boq.pdf" --out /tmp/demo_boq.xlsx`
   - `uvicorn src.api.main:app --port 8000 &` → curl upload → JSON back → kill
   - `streamlit run ui/app.py` → manual check note (upload, flags visible, catalog column)
   - `docker build -t rfq2boq -f deployment/Dockerfile . && docker run --rm rfq2boq python -c "import src.pipeline"`
3. Write the runbook. Update slides talking points to the final numbers.
4. `make verify` + `make verify-full` green. Final ledger + REPORT.

## 5. VERIFICATION
```bash
grep -rn "100% COMPLETE" deliverables/ HANDOFF.md README.md   # expect: empty
make verify && make verify-full                                # green
cat results/demo_smoke.md                                      # 4 sections with real output
```

## 6. ACCEPTANCE CRITERIA
No document claims a number that T7/T4 didn't produce; demo evidence committed; runbook exists; both verify targets green.

## 7. CONSTRAINTS
The completion claim is EXACTLY: "100% capture-or-flag fidelity per document on owner-verified source truth; corpus regression + combination invariance enforced in CI; held-out F1 = <T7 value>; catalog accuracy = <T7 value>; non-cheating proven by fresh-document audit." Nothing stronger, anywhere.

## 8. DEPENDENCIES
Blocked by: T7. Blocks: project completion.

## 9. OWNER CHECKLIST (Srujan — hand this to him verbatim; agents CANNOT do these)
1. `git push -u origin phase8-clean-slate` from a stable network; set as default branch on GitHub (until pushed, one disk failure loses everything).
2. Rotate the GitHub token embedded in `git remote -v`; switch to a credential helper.
3. Sign off any remaining T1/T2/T5 batches.
4. Send SWA the final report + demo; request their real GeM catalog export (ingest verbatim when it arrives) and the remaining R3 documents.
5. Rebuild `.venv` on python 3.12 if it has drifted (charter pins 3.11–3.13).
