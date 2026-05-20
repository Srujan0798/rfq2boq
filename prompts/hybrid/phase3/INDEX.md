# Phase 3 — Improve Unique 30%

| ID | Task | Owner | Effort |
|----|------|-------|--------|
| [P3T1](P3T1_FINETUNE_FINAL_MODEL.md) | Fine-tune final NER (ARCBERT + real RFQs) | Agent-2 | 3 days |
| [P3T2](P3T2_POLISH_UI.md) | Polish Streamlit UI | Agent-3 | 2 days |
| [P3T3](P3T3_POLISH_EXCEL_EXPORT.md) | Polish Excel export (CPWD format) | Agent-3 | 2 days |
| [P3T4](P3T4_STRENGTHEN_CONFLICT.md) | Strengthen hybrid conflict resolution | Agent-2 | 2 days |
| [P3T5](P3T5_DEMO_VIDEO.md) | Demo video | Owner | 1 day |

## Order

1. **P3T1 first** (sequential) — produces the final model everything else uses
2. **P3T2, P3T3, P3T4 in parallel** (different agents/files)
3. **P3T5 last** (Owner) — uses outputs of all above

## Exit gate (project complete)

- [ ] Real-world F1 ≥ 75% on gold test set
- [ ] Streamlit UI usable by non-technical estimator
- [ ] Excel output matches CPWD format with DSR codes + totals
- [ ] Conflict resolution accuracy improved on ground truth
- [ ] 3–5 min demo video recorded
- [ ] README + docs reflect final state
- [ ] Git tagged `v1.0-handover`
