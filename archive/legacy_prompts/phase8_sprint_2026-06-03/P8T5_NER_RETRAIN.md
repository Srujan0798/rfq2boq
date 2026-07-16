# TASK: P8T5 — NER Retrain to Beat Production (0.430) — Agent-Model

**Phase:** 8 | **Priority:** P1 | **Effort:** 1 day (after data lands)

## 1. GOAL
Train an NER model that **beats the production Micro F1 of 0.430** on a held-out real test set — using the expanded, cleaned gold (P8T2/T3), proper hyperparameters, and a leakage-free split — on Python 3.11–3.13. Adopt it ONLY if it genuinely wins.

## 2. CONTEXT
v1 retrain → F1=0.0 (all-O, too little data). v2 → F1=0.213 (escaped collapse, still below production 0.430), trained on Python 3.14 (segfault-prone). Production model (synthetic-trained) = 0.430 and remains in use. With ≥28 cleaned gold docs (P8T2/T3) there's finally enough to retrain properly.

Read first: `scripts/train_real_only_v2.py`, `models/rfq2boq-ner-final/` (production), `models/rfq2boq-ner-real-only-v2/metrics.json`, `config/constants.py`.

## 3. DELIVERABLES
- [ ] `scripts/train_ner_v3.py` — train from the expanded gold; **split BEFORE augmentation**; augment train only; warmup + class weighting; early stopping on val.
- [ ] A fixed, documented **held-out test set** (never seen in train/val/aug) used for the headline number.
- [ ] `models/rfq2boq-ner-v3/metrics.json` with test P/R/F1 (micro + per entity).
- [ ] `results/NER_V3_REPORT.md`: v3 vs production (0.430) vs v2 (0.213), honest verdict + adopt/not-adopt decision.
- [ ] If (and only if) v3 > production on the held-out set: wire it as the runtime model behind a settings flag; else leave production in place and document why.

## 4. STEPS
1. Confirm interpreter is 3.11–3.13 (`python3 --version`). If 3.14, switch — do not train on 3.14.
2. Build leakage-free split (by document, not by sentence); freeze the test set IDs in the report.
3. Train with augmentation on train only; track val F1; early stop.
4. Evaluate on the frozen test set; compare to production on the SAME test set.
5. Decide adoption honestly; wire flag only if it wins.

## 5. VERIFICATION
```bash
python3 --version   # must be 3.11/3.12/3.13
cat models/rfq2boq-ner-v3/metrics.json | python3 -c "import sys,json;d=json.load(sys.stdin);print('test_f1',d['test_f1'])"
# Evaluate BOTH models on the SAME frozen test set
python3 scripts/eval_ner.py --model models/rfq2boq-ner-v3 --test <frozen_ids>
python3 scripts/eval_ner.py --model models/rfq2boq-ner-final --test <frozen_ids>
EXPECT: apples-to-apples; adopt only if v3 > 0.430 on the frozen real test set

# Leakage guard: no train/val doc appears in test
python3 scripts/check_split_leakage.py
EXPECT: 0 overlap
```

## 6. ACCEPTANCE CRITERIA
- [ ] Split is document-level, leakage-free (verified); augmentation on train only.
- [ ] v3 test F1 reported on a frozen real test set, compared to production on the SAME set.
- [ ] Adoption decision matches the evidence (no adopting a worse model; no claiming a win without the head-to-head).
- [ ] Trained on Python 3.11–3.13.

## 7. CONSTRAINTS
- NO augmented/synthetic data in val or test. NO hand-picking the test set to flatter the model.
- A test F1 ≈ 1.0 or a giant jump is a leakage red flag — investigate, don't celebrate.
- Keep production model available for rollback.

## 8. DEPENDENCIES
- **Blocked by:** P8T2, P8T3 (need enough clean gold). **Feeds:** P8T4 (better NER helps PDF path), P8T8.

## 9. GOTCHAS
- MPS only (no CUDA). Expect slow training; checkpoint.
- xlm-roberta multilingual path tried to download at runtime — if used, cache locally (coordinate with P8T6); never depend on a live download.
- Tiny test sets give noisy F1 — report the test size and treat small-sample results as indicative.
