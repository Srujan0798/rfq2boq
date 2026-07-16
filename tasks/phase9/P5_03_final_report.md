# TASK P5_03: The internship deliverables — honest report + slides — Agent-P5-3 (+ OWNER sign-off)

## 1. GOAL
Write the two handover artifacts the internship is judged on: a technical report and a presentation deck that tell the TRUE story — correct architecture, the data-quality root cause, the honest fix, and the verified final numbers — compelling because it's real.

## 2. CONTEXT
Files to read FIRST (in order):
- `results/final_eval/EVAL_REPORT.md` — the canonical numbers (P4_02); use NO others
- `docs/CORE_UNDERSTANDING.md`, `docs/SWA_REQUIREMENTS_2026-06-11.md` — the narrative spine
- `results/fidelity/summary.json` + audit artifacts — the R1 proof
- `resources/RFQ to BOQ Scope Extraction using NLP system.pdf` — the original brief (the report must map deliverables to it, requirement by requirement)
- `deliverables/` — whatever exists (previous drafts contain UNVERIFIED claims — mine for structure only, never copy a number without matching it to P4_02/P1_02 artifacts)

Current state:
- `deliverables/` contains rogue-era files with fabricated claims. These are superseded: move to `deliverables/superseded_unverified/` with a README ("claims unverified; retained as history").

## 3. DELIVERABLES
- [ ] `deliverables/RFQ2BOQ_Internship_Report.md` (export-ready; owner converts to PDF) — structure:
  1. Problem + brief mapping (RFQ→BOQ, the SWA requirements R1–R4, how each is met/partially met — a requirements-traceability table)
  2. Architecture (the pipeline, structure-first method R4, diagrams — text/mermaid)
  3. The data journey — honest centerpiece: auto-generated-data root cause → 127-doc real corpus → annotation factory → owner-verified gold → retrain (the ~0.43 → measured-v1 arc with the controlled comparison)
  4. Fidelity engineering (R1): ruler, auditor, flag-never-drop, per-doc audit artifacts, sacred-10 result
  5. Evaluation (verbatim from EVAL_REPORT.md incl. limitations)
  6. Engineering integrity (the verification-gate discipline, split hygiene, provenance locks — R5's story, told professionally without incident melodrama)
  7. Limitations + roadmap (starved entity types, remaining annotation runway to 0.88, layout-model future work)
- [ ] `deliverables/RFQ2BOQ_Presentation.md` — 12–15 slides (marp/pandoc-compatible markdown): hook (real tender → BOQ in 60s), demo path, the honest-data story arc, numbers, live-demo cue slide, roadmap
- [ ] `deliverables/DEMO_SCRIPT.md` — 10-min live-demo runbook: exact docs to upload (one clean BOQ, one GeM with catalog validation, one compliance checklist showing the classified-document banner), what to say at each step, fallback if something breaks
- [ ] Superseded-file quarantine as described in §2
- [ ] **[OWNER GATE: Srujan reads both artifacts fully and signs off in the ledger before they're final]**

## 4. STEPS
1. Read all context; build the requirements-traceability table FIRST (it exposes any gap while there's still time to flag it).
2. Number audit: every metric you intend to cite → its artifact path; anything without an artifact doesn't get cited. Include the mapping as an appendix.
3. Write report → slides → demo script (in that order; slides compress the report).
4. Quarantine superseded files; commit; submit to owner gate.
5. Apply owner's edits; final commit.

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 - <<'EOF'
import re
t = open('deliverables/RFQ2BOQ_Internship_Report.md').read()
nums = re.findall(r'\b\d{1,3}(?:\.\d+)?%', t)
print(f"{len(nums)} percentage claims — each must appear in the appendix artifact map")
assert 'Limitations' in t and 'traceability' in t.lower()
EOF
grep -rn "Rate\|Amount\|₹\|DSR" deliverables/RFQ2BOQ_Internship_Report.md   # EXPECT: no priced-BOQ scope creep (context-check any hits)
ls deliverables/superseded_unverified/            # EXPECT: old unverified reports + README
# Manual: render slides (marp or pandoc) — no broken diagrams
```

## 6. ACCEPTANCE CRITERIA
- [ ] Every number traces to a P4_02/P1_02/P5_02 artifact (appendix map complete; orchestrator spot-checks 10)
- [ ] The 0.43 origin story told plainly — the report's credibility IS the differentiator
- [ ] Traceability table covers every brief/meeting requirement with status (met / partial / roadmap) — no requirement silently omitted
- [ ] Demo script executes cleanly on the named docs (actually run it once)
- [ ] Owner sign-off recorded in ledger

## 7. CONSTRAINTS
- No new measurements in this task — if a number you want doesn't exist, request it via orchestrator; never "estimate"
- No paper/patent/benchmark/SaaS framing (charter §1) — this is an internship engineering report
- Professional tone; zero hype adjectives around metrics
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P4_02, P5_01, P5_02 (all numbers + demo surface final)
- **Blocks:** P5_04
- **Parallel-safe with:** nothing (it consumes everything)
- **Shared files:** `deliverables/**`

## 9. GOTCHAS
- The strongest slide is the controlled old-vs-new comparison — resist inflating it with the meaningless synthetic ~99%; if synthetic numbers appear at all, they appear as the cautionary tale they are.
- SWA's mentor stated R1 as "100% accuracy" — the report must connect R1 to the fidelity-audit mechanism (how we PROVE per-document conversion) rather than claiming a blanket 100%; the distinction is exactly what makes the claim defensible.
- Mermaid renders differently across viewers — keep diagrams simple (boxes + arrows), test in the target renderer.
- The demo's riskiest moment is a large GeM PDF live — the script's fallback is a pre-generated output directory, prepared and named in the runbook.
