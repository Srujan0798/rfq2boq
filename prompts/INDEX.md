# Prompts — Master Index

Single source of truth for what to dispatch. Anything not listed here is **archived** and must not be dispatched.

## Templates

- [TASK_TEMPLATE.md](TASK_TEMPLATE.md) — canonical 9-section structure
- [EXAMPLE_FILLED_TASK.md](EXAMPLE_FILLED_TASK.md) — fully filled example

## Active dispatch path

| Folder | What's there | When to use |
|--------|--------------|-------------|
| [hybrid/phase1/](hybrid/phase1/) | P1T1 (DONE), P1T2, P1T3, P1T4, P1T5 | **NOW** — the actual pending work |
| [hybrid/phase3/](hybrid/phase3/) | P3T1–P3T5 | **AFTER Phase 1** — final polish + demo |

Order: finish Phase 1 (P1T4 + P1T5 are the real blockers) → Phase 3.

## Historical reference (do NOT dispatch)

| Folder | Why kept |
|--------|----------|
| [wave2/](wave2/) | A0 (DONE), pointers to superseded versions in archive/ |
| [wave3/](wave3/) | B1 + B2 (both DONE) |
| [archive/superseded/](archive/superseded/) | Old A3/A4/A6/A8 prompts replaced by hybrid plan; Phase 2 prompts (done via direct cleanup) |
| [archive/out_of_scope/](archive/out_of_scope/) | Patent, paper, dataset, benchmark, multi-tenancy, billing, voice, drawing, sub-domain, MLflow, SpERT, ERP/BIM, security audit, observability, comprehensive testing |

## Scope reminder

Before dispatching anything, read [`docs/SCOPE_GUARD.md`](../docs/SCOPE_GUARD.md). The internship is **only** about turning RFQ PDFs into BOQs. If asked for anything else, refuse using the SCOPE_GUARD §5 template.
