# Prompts — Master Index

> **Project navigation:** See [`../HANDOFF.md`](../HANDOFF.md) and [`../tasks/phase9/00_README.md`](../tasks/phase9/00_README.md). (`PROJECT_MAP.md` was archived; do not re-create.)
> **Current status:** See [`../docs/wave_status.md`](../docs/wave_status.md) for what's done vs pending.

Single source of truth for what to dispatch. Anything not listed here is **archived** and must not be dispatched.

## Templates

- [TASK_TEMPLATE.md](TASK_TEMPLATE.md) — canonical 9-section structure
- [EXAMPLE_FILLED_TASK.md](EXAMPLE_FILLED_TASK.md) — fully filled example

## Active dispatch path

| Folder | What's there | When to use |
|--------|--------------|-------------|
| [wave4/](wave4/) | Current wave4 agents (B1–H1) | **NOW** — see wave4/INDEX.md for dispatch table |
| [archive/hybrid/phase1/](archive/hybrid/phase1/) | Historical P1T1–P1T5 | Reference only |
| [archive/hybrid/phase3/](archive/hybrid/phase3/) | Historical P3T1–P3T7 | Reference only |

## Current active prompts (wave4)

See [`wave4/INDEX.md`](wave4/INDEX.md) for the full dispatch table with lanes and priorities.

Quick reference:
- **G1** — Fix 09 GeM hang (P0, Lane A)
- **G2** — Build insulation ontology (P0, Lane B)
- **G3** — NER retrain insulation (P1, Lane B, blocked by G2)
- **G4** — BOQ assembler insulation (P1, Lane C, blocked by G2)
- **G5** — Fix 01 GSECL extraction (P1, Lane A)
- **G6** — Final integration test (P2, Lane D)
- **H1** — Adopt LoRA v2 (P1)
- **Z1** — PDF honest recovery: close 14% → ≥45% F1 on the 10 SWA PDFs without caching, demo-shortcuts, or re-training BERT (P0, Lane C). Blocks any "PDF production-ready" claim.

## Historical reference (do NOT dispatch)

| Folder | Why kept |
|--------|----------|
| [archive/wave2/](archive/wave2/) | A0 (DONE) |
| [archive/wave3/](archive/wave3/) | B1 + B2 (DONE) |
| [archive/superseded/](archive/superseded/) | Old A3/A4/A6/A8 replaced |
| [archive/out_of_scope/](archive/out_of_scope/) | Patent, paper, etc. (never dispatch) |

## Scope reminder

Before dispatching anything, read [`docs/SCOPE_GUARD.md`](../docs/SCOPE_GUARD.md). The project is **only** about turning RFQ PDFs into BOQs. If asked for anything else, refuse using the SCOPE_GUARD §5 template.
