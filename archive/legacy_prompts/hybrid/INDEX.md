# Hybrid Plan — Active Task Index

The canonical task path for the internship. See [`docs/HYBRID_PLAN.md`](../../../docs/HYBRID_PLAN.md) for rationale and [`prompts/archive/hybrid/WORKFLOW.md`](WORKFLOW.md) for dispatch protocol. (Note: this hybrid/ is now under archive/ for historical reference.)

## Phase 1 — Plug in free official tools

| ID | Task | Owner | Status | Effort |
|----|------|-------|--------|--------|
| P1T1 | [OmniClass mapping](phase1/P1T1_OMNICLASS_MAPPING.md) | Agent-1 | **DONE** | 2 h |
| P1T2 | [IndicBERT integration](phase1/P1T2_INDICBERT_INTEGRATION.md) | Agent-2 | PENDING (optional) | 1 day |
| P1T3 | [ARCBERT integration](phase1/P1T3_ARCBERT_INTEGRATION.md) | Agent-2 | PENDING | 2–3 days |
| P1T4 | [CPWD DSR rates](phase1/P1T4_CPWD_DSR_RATES.md) | Agent-1 | **PENDING — actual blocker** | 2 days |
| P1T5 | [Real RFQ collection](phase1/P1T5_REAL_RFQ_COLLECTION.md) | Owner + Agent-1 | **PARTIAL — actual blocker** | 2 days |

**Exit gate:** P1T4 has ≥500 DSR items + P1T5 has ≥50 real PDFs + ≥20 gold annotations. P1T2/P1T3 optional.

## Phase 2 — Slim codebase

**Status: DONE** (via direct orchestrator cleanup on 2026-05-17, not via P2T1–P2T4 dispatch). Original Phase 2 prompts are in `prompts/archive/superseded/phase2_done_via_direct_cleanup/`.

What this means: `attic/` is populated, `src/` is slim (16 modules), out-of-scope code archived, docs updated. The Phase 2 work is complete — just not via the prompt-dispatch workflow.

## Phase 3 — Polish unique 30% (blocked until Phase 1 exit gate)

| ID | Task | Owner | Status | Effort |
|----|------|-------|--------|--------|
| P3T1 | [Fine-tune final NER](phase3/P3T1_FINETUNE_FINAL_MODEL.md) | Agent-2 | BLOCKED (needs P1T3 + P1T4 + P1T5) | 3 days |
| P3T2 | [Polish Streamlit UI](phase3/P3T2_POLISH_UI.md) | Agent-3 | BLOCKED (needs P3T1) | 2 days |
| P3T3 | [Polish CPWD Excel](phase3/P3T3_POLISH_EXCEL_EXPORT.md) | Agent-3 | BLOCKED (needs P1T4) | 2 days |
| P3T4 | [Strengthen conflict resolution](phase3/P3T4_STRENGTHEN_CONFLICT.md) | Agent-2 | BLOCKED (needs P3T1) | 2 days |
| P3T5 | [Demo video](phase3/P3T5_DEMO_VIDEO.md) | Owner | BLOCKED (needs P3T1–P3T4) | 1 day |

P3T1 first (sequential). Then P3T2/T3/T4 parallel. Then P3T5.

## What to dispatch right now

1. **P1T4** (Agent-1) — real CPWD DSR rate library (500+ items)
2. **P1T5** (Owner + Agent-1) — finish collecting real RFQs + gold annotations

Once both done, you have everything needed to run Phase 3.

P1T2 (Hindi) and P1T3 (ARCBERT) are nice-to-have; dispatch if you have spare capacity.
