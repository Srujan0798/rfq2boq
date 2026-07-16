# T6 — Genuine training: human-verified labels only, promote only if it wins

## 1. GOAL
Train the NER model on exclusively human-verified TRAIN data, evaluate on DEV, and promote it into production ONLY if it beats the pattern baseline — otherwise patterns stay production and the report says so honestly.

## 2. CONTEXT (read first)
- `scripts/train_lora_ner_real_only.py` — contains an env-gated silver path (`RFQ2BOQ_ALLOW_SILVER`, lines ~87–103) that MUST BE DELETED
- History: v3 (20 gold) F1 0.141 — insufficient data; v5 (291 mixed w/ synthetic+pseudo) val 0.755 but sacred-10 0.188 — overfit to machine labels. Both prove: only real human labels at volume work.
- Literature target with 1,000+ sentences: ~0.85–0.88 F1 (BERT-BiLSTM-CRF class)
- Hardware: MPS (Apple), no CUDA. `.venv` python 3.12.

## 3. DELIVERABLES
- Cleaned trainer: zero machine-label code paths (no silver, no pseudo, no synthetic, no env flags) — loads ONLY `data/annotations/verified/` TRAIN-split records
- `results/training_log.md` — per run: date, data-manifest sha256, record counts per split, hyperparams, DEV F1 per entity, wall time
- Trained adapter under `models/rfq2boq-ner-human-v1/` + `training_meta.json` (data manifest hash, git commit, config)
- `scripts/eval_dev.py` — same metric implementation for patterns AND model (entity-level F1, per-entity breakdown)
- Promotion decision recorded in `results/promotion_decision.md`; if promoted: pipeline wiring behind `settings` flag with patterns as runtime fallback

## 4. STEPS
1. Delete silver/pseudo/env-gate code from the trainer; grep-proof it. Commit this FIRST, separately.
2. Build the training manifest from verified TRAIN records; hash it; assert leakage test green.
3. Baseline first: run `eval_dev.py` with pattern-NER on DEV → this is the number to beat. Record it.
4. Train (bert-base LoRA; document LR/epochs/batch; checkpoint per epoch). Tune ONLY on DEV. Log every run including failures.
5. Compare best DEV model vs pattern baseline per entity. Decide: promote (wire into `src/nlp/pipeline.py` behind settings flag, ensemble with patterns + catalog matcher) or hold (patterns remain production).
6. Ledger + REPORT with the full training log.

## 5. VERIFICATION
```bash
grep -n -i "silver\|pseudo\|synthetic\|ALLOW_SILVER" scripts/train_lora_ner_real_only.py   # expect: empty
.venv/bin/python -m pytest tests/unit/test_no_test_split_leakage.py -q                      # green
PYTHONPATH=. .venv/bin/python scripts/eval_dev.py --system patterns                          # baseline number
PYTHONPATH=. .venv/bin/python scripts/eval_dev.py --system model --model models/rfq2boq-ner-human-v1   # model number
make verify                                                                                   # green
```

## 6. ACCEPTANCE CRITERIA
Trainer grep-clean of machine labels; training log with manifest hashes; DEV numbers for baseline AND model produced by the same eval code; promotion decision documented with numbers; TEST untouched.

## 7. CONSTRAINTS
Never evaluate on TEST in this task. Never tune on sacred 10. If DEV F1 comes out suspiciously high (>0.95), treat as leakage until proven otherwise — audit before reporting.

## 8. DEPENDENCIES
Blocks: T7. Blocked by: T5 (needs ≥1,000 verified sentences; if fewer, train anyway, report honestly, and note more data is queued). Parallel-safe: no.

## 9. GOTCHAS
- Python 3.14 breaks typer/torch tooling — stay on `.venv` 3.12.
- MPS: fp16 instability on some ops — fall back to fp32 if loss NaNs.
- Per-entity truth from history: UNIT/STANDARD are easy (patterns already ~0.95+); the model's ENTIRE value is MATERIAL/LOCATION — judge promotion primarily on those.
- `bert-base-cased` vs `-uncased`: match whatever the tokenizer in the existing scripts uses; don't silently switch.
