# OPENCODE SESSION FINDINGS — mined from ~/.local/share/opencode/opencode.db, 2026-07-04

What the opencode swarm actually did, what it found, and the live risks Sonnet inherits. Source: session titles + agent todos in the 6GB session DB, cross-checked against disk.

## What ran today (2026-07-04, chronological)
- **14:21–15:06 — "handoff merge" wave:** batches A–G, then "L2 merge batches", then "L3 ultimate handoff merge", then "Merge Grok CLI handoffs", "Merge Claude Code handoffs", "Create final completion plan". **Side effect: `tasks/ETERNAL_PROTOCOL.md` (untracked) was deleted in this wave.** Restored by the orchestrator 2026-07-04 evening. Lesson → RULES: protocol + this folder are orchestrator-owned; agents never merge/move/delete them.
- **16:26–16:33 — evaluation + annotation wave:** "Run honest evaluations fresh" (produced `results/fidelity_audit_*.txt` — the 27% corpus baseline), "Annotation factory from RFQs" (generated drafts from **26 extracted RFQs — NOT the full 105+ corpus**; corpus shrinkage again), "Enrich ontology from specs" (mined gazetteer).
- **17:06 — "Train on verified labels" + "Merge enriched ontology".** The "verified" labels are the 28 agent-stamped files — untrusted until T2.
- **18:45–18:48 — currently in flight:** "Build dataset and train LoRA NER model" (live `opencode run` job, deepseek-v4-flash, `/usr/local/bin/python3.11` — OUTSIDE the project venv), "Annotation draft generation", "Fresh document smoke test", "Build honest deliverables report".

## Agent todo state (their own tracking)
- Completed (per them — unverified): fidelity audit all BOQ-bearing docs; honest entity+row evals; annotation drafts from 26 RFQs; ontology mining; BIOES conversion of "verified" rowgold; `make verify` + "close Gate 0".
- In progress: clean LoRA training "on verified labels only"; honest deliverables report.
- Pending: integrate CLI outputs and commit; fresh-doc smoke test; DONE.txt with final F1.

## Risks Sonnet must neutralize at T0 (in order)
1. **Three agents live on ONE tree** (ports 50831 — 193 CPU-min hot loop since 13:52 —, 47632, + the `opencode run` training job). One-agent-per-worktree rule violated; explains file churn and the protocol deletion. **Owner stops all three before T0.**
2. **The live training job builds on the 28 untrusted `human_verified:true` stamps** — its own rules say "only human_verified=true" but agents created those stamps (incident-#4 pattern). Output (`models/rfq2boq-ner-lora-cli`, `data/annotations/cli_training/`) goes to quarantine in T0 alongside lora-real, pending T2.
3. **python3.11 outside `.venv`** — its artifacts may not reproduce inside the project env; another reason to quarantine, re-run properly in T6.
4. **"26 extracted RFQs" ≠ the corpus.** T3's manifest is the correction; drafts from the 26 are usable raw material for T5 review.
5. **Uncommitted agent output** (`data/annotations/cli_drafts/`, `cli_training/`) — audit in T5 step 1 before trusting anything in them.

## What is genuinely useful from the swarm (keep, verify, reuse)
- `results/fidelity_audit_*.txt` — the honest 27% baseline and per-doc breakdowns (T1/T4 starting point).
- The draft annotations (26 RFQs) + 429 silver sentences — T5 review-queue raw material.
- Mined gazetteer/ontology enrichment — subject to T3 TEST-doc provenance audit.
- The fresh-doc smoke test concept — already institutionalized as Gate 0.
