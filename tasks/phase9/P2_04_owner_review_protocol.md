# TASK P2_04: Owner review sessions — the ONLY source of verified gold — OWNER (Srujan) + orchestrator support

## 1. GOAL
Convert draft annotations into ≥1000 owner-verified BIOES sentences via short daily review sessions — the single input that moves real NER F1 from ~0.43 toward the literature's 0.88. **No agent executes this task. This file is Srujan's runbook.**

## 2. CONTEXT
Read (10 min, once):
- `docs/ANNOTATION_GUIDELINES.md` — entity definitions with examples (updated by P2_02)
- `results/annotation_wave1/DRAFT_STATS.md` — what's queued, expected hours
- This file, fully

Why you, why manual: every automated shortcut was tried by previous agents and produced garbage or fraud (regex-auto-gold → F1 0.43; forged stamps → incidents #7 and #13's 198 reviewer-less files; pipeline-mirrored gold → incident #12). The literature and the SWA guide both say the same thing: real human labels are the lever. Your domain judgment (what is a MATERIAL vs a spec phrase; when "MS" is a grade vs an abbreviation) is exactly what the model lacks.

## 3. DELIVERABLES (cumulative across sessions)
- [ ] `data/annotations/verified/` — ≥1000 sentences, `reviewer:"srujan"`, all 8 entity types represented (≥50 each where corpus supports it)
- [ ] Session log rows appended to `tasks/phase9/04_LEDGER.md` by orchestrator after each session (date, sentences verified, minutes, notes)
- [ ] Judgment calls that generalize → 1-line additions to `docs/ANNOTATION_GUIDELINES.md` "Rulings" section (orchestrator writes them from your notes; they keep future sessions consistent)

## 4. STEPS (per session — target 30–45 min, ~100–150 sentences)
1. `cd /Users/srujansai/rfq2boq-phase9`
2. `python3 scripts/annotation_factory.py review --queue`
3. Per sentence: ACCEPT if spans are right; FIX if a span/label is wrong (the UI shows keys); REJECT if the sentence is garbage (OCR noise, boilerplate). When unsure >20 seconds: REJECT with note — a smaller clean set beats a bigger noisy one, and rejected sentences can be revisited.
4. Quit anytime (autosaves). Run `python3 scripts/annotation_factory.py stats` and paste the output to the orchestrator.
5. Orchestrator runs `python3 scripts/check_gold_provenance.py` + `validate_annotations.py` on the new files and appends the ledger row.

## 5. VERIFICATION (orchestrator, after each session)
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 scripts/validate_annotations.py data/annotations/verified/   # EXPECT: 0 errors
python3 scripts/check_gold_provenance.py                              # EXPECT: exit 0, all stamps reviewer=srujan, plausible timestamps
python3 scripts/annotation_factory.py stats                           # progress toward 1000
git add data/annotations/verified/ && git commit -m "gold: owner review session $(date +%F) — N sentences"
```

## 6. ACCEPTANCE CRITERIA (phase-gate to P4)
- [ ] ≥1000 verified sentences (literature Phase-1 threshold)
- [ ] Entity distribution reported; starved types acknowledged in writing (P4 will report per-type F1 honestly against this)
- [ ] Every verified file passes provenance + validation
- [ ] Inter-session consistency: orchestrator re-shows you 20 previously-verified sentences at ~500 mark (blind); if you'd change >3, a guidelines clarification pass happens before continuing

## 7. CONSTRAINTS
- Sessions are interactive-terminal only; nobody batch-stamps, including you (the tool blocks non-tty verified writes by design)
- If an agent ever offers to "help speed up review" by pre-accepting — that is incident #7/#13; refuse and tell the orchestrator
- TEST docs never appear in the queue; if you ever see a sacred-10 sentence, STOP the session and report (leakage bug)

## 8. DEPENDENCIES
- **Blocked by:** P2_03
- **Blocks:** P4_01 (hard gate: no training until ≥1000)
- **Parallel-safe with:** ALL Phase-3 tasks (they don't touch annotations) — Phase 3 runs while you review
- **Shared files:** `data/annotations/verified/` (yours alone)

## 9. GOTCHAS
- The accept key becomes automatic after ~50 sentences — that's when errors slip in. The UI inserts a mandatory 2-sec preview on entity-dense sentences; don't fight it.
- Common tender traps (from the guidelines, worth memorizing): "IS 456" = STANDARD (not DIMENSION); "M20" = GRADE; "50mm dia" = DIMENSION (not QUANTITY); "Supply and laying" = ACTION; bare numbers in a qty column = QUANTITY only with a UNIT nearby, else leave untagged.
- 100 sentences/day ≈ 10 working days to gate. Batching 3 giant sessions produces worse labels than 10 short ones (fatigue is measurable in accept-rate drift — the stats command tracks it).
