# NER_REAL_REPORT (S5)

Date: 2026-06-08
Status: Leakage-free split verified. Owner gold sign-off pending for 09/10 (ai-precleaned-needs-human-signoff). Full retrain on verified real gold not executed in this session (long on MPS + owner first per spec). Current production ~0.43 F1 on real (per CORE; synthetic 99% misleading). Literature target 0.88 with 50+ real PDFs + 1000+ human BIOES.

## Leakage Check
`python3 scripts/check_split_leakage.py`: ✓ 0 overlap (train on non-swa + some, test frozen includes swa_01/10 + others; clean per spec).

## Gold Status (10 SWA)
- All 10 have gold in data/real_rfqs/gold/swa_*.json (1636+ ents total from prior).
- 01-08: pre-cleaned + human_curated elements (XLSX rowgold for 02/03/05/08).
- 09/10: ai-precleaned (entities ~921/218); status 'ai-precleaned-needs-human-signoff'. Owner (Srujan) must review/annotate (focus MATERIAL, every 5th, ~55min/file per REVIEW_QUEUE in prior). Agent pre-drafted (recall-biased); owner signs off to human_verified.

## Training Setup
- Scripts: train_lora_ner.py ready (BIOES, 80/10/10 leakage-free, early stop val F1, per-entity, explicit swa_heldout exclude 10 + synthetic).
- Env: Python 3.14.3 (MPS; CLAUDE.md/STEPs mandate 3.11-13 for stability — segfault risk; use python3).
- No synthetic/regex-auto data (per CORE + constraints; purged S2).
- Split: document-level, freeze test IDs (swa_01, swa_10 + cpwd etc for honest held-out).

## Eval vs Current (on same frozen real held-out)
- Current production: ~0.43 F1 real (honest; 0.000 in some broken model reports per handoff — regex/assembler carry pipeline).
- With real human gold (target 1000+ sentences): guide says 0.88 achievable.
- Head-to-head not run (owner gold + time). Adopt only if new > current on same test (honest; F1~1.0 = red flag leakage).
- Verdict: Setup ready. After owner sign-off + train: re-eval, adopt if wins. Keep current for rollback. No self-gold.

## Next
Owner: annotate/sign off 09/10 (and spot others) → human_verified.
Agent: run full train on verified gold (python3 scripts/train_lora_ner.py), re-eval, update this report + adopt.

See CORE_UNDERSTANDING.md (data volume is limiter; real gold is fix). No pipeline output as gold.
