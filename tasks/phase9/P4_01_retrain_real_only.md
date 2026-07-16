# TASK P4_01: Retrain NER on owner-verified real gold ONLY — Agent-P4-1

## 1. GOAL
Replace the regex-auto-trained model (the project's root-cause failure) with one trained exclusively on the ≥1000 owner-verified BIOES sentences — the single change the SWA guide and the literature say moves real F1 from ~0.43 toward 0.88.

## 2. CONTEXT
Files to read FIRST (in order):
- `docs/CORE_UNDERSTANDING.md` §3 — the root cause you are fixing; §5 — the fix path
- `scripts/train_lora_ner_real_only.py` — the cleaned trainer (all silver/pseudo backdoors removed — keep it that way); also `scripts/train_lora_ner.py` lineage for architecture reference
- `src/nlp/` model + dataset code — BERT-BiLSTM-CRF architecture per the brief; check what the LoRA scripts actually fine-tune (the architecture decision below depends on it)
- `data/annotations/verified/` — the training data (exists only after P2_04's gate)
- `models/quarantine/` — precedent: models without training provenance get quarantined; yours must carry provenance

Current state:
- No production-trustworthy model exists. Prior checkpoints: trained on auto-generated data (useless on real text) or quarantined (no provenance).
- Hardware: MPS only. Training must fit a MacBook (LoRA/adapter fine-tuning of a BERT-class encoder is the proven-feasible path here; full BERT-BiLSTM-CRF training from scratch likely isn't — decide and justify from what `src/nlp/` actually supports).

## 3. DELIVERABLES
- [ ] Preflight gate in the trainer (extend `train_lora_ner_real_only.py` or a successor): refuses to start unless (a) `check_gold_provenance.py` exits 0, (b) every training record is `human_verified:true, reviewer:"srujan"`, (c) zero records from TEST/DEV docs (`check_split_leakage.py` green), (d) sentence count ≥1000 — each violation named in the error
- [ ] Trained model at `models/ner_real_v1/` with `TRAINING_MANIFEST.json`: data files + their sha256s, sentence/entity counts per type, hyperparameters, seed, train/val split (from TRAIN-pool sentences only, e.g. 90/10), epochs, loss curves, wall time, git commit
- [ ] `src/nlp/` model-loading wired so the pipeline uses `ner_real_v1` (config-switchable via `config.settings`, default = new model)
- [ ] `tests/unit/test_training_gate.py` — ≥5 tests: each preflight violation blocks (fixture data, tiny)
- [ ] `results/training_v1/TRAINING_REPORT.md` — honest: final train/val metrics per entity type, starved types called out (from P2_03's known distribution), what val F1 does and does NOT imply (val ≠ held-out TEST)

## 4. STEPS
1. Read context. Confirm P2_04's gate is truly met (run the stats + provenance commands yourself; paste output). If <1000: STOP, report BLOCKED.
2. Decide + document architecture path (LoRA-adapter on the existing encoder vs full train) from what the code supports and MPS can do; 1-paragraph justification in the report.
3. Implement the preflight gate + tests FIRST (they're cheap and they're the integrity fence).
4. Train (seed fixed; save intermediate checkpoints; MPS fallback to CPU must not silently change dtype semantics — log device).
5. Wire model into the pipeline behind settings; quick smoke: the CLAUDE.md §8 sanity sentence must yield entities.
6. Val-set numbers into the training report — do NOT run anything against TEST/DEV docs (that is exclusively P4_02).
7. Commit code + manifest + report. Model weights: gitignored (per charter) — record the local path + sha256 of weights in the manifest; note Git LFS/external distribution as the handover mechanism (P5_04).

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 -m pytest tests/unit/test_training_gate.py -v        # EXPECT: 5+ passed
python3 scripts/check_gold_provenance.py && python3 scripts/check_split_leakage.py   # EXPECT: both exit 0
python3 - <<'EOF'
import json
m = json.load(open('models/ner_real_v1/TRAINING_MANIFEST.json'))
assert m['sentence_count'] >= 1000
print("MANIFEST OK:", m['sentence_count'], "sentences, seed", m['seed'])
EOF
python3 -c "from src.nlp.pipeline import NLPPipeline; p=NLPPipeline(); r=p.process('Supply 500 kg cement as per IS 456 M20 grade at ground floor'); print(r.entities); assert len(r.entities) > 0"
python3 -m pytest tests/unit tests/integration -q && make lint && make typecheck
```

## 6. ACCEPTANCE CRITERIA
- [ ] Preflight gate unit-proven; training literally cannot start on bad data
- [ ] Full provenance manifest; reproducible (seed + data hashes + commit)
- [ ] Val metrics reported per entity type, honestly framed (no "F1 achieved!" language for val numbers)
- [ ] Pipeline runs on the new model; sanity sentence passes
- [ ] ZERO contact with TEST/DEV documents in any part of training or validation

## 7. CONSTRAINTS
- Rule 4 absolute: no silver, no pseudo-labels, no augmentation that manufactures labels (mechanical augmentation like case-jitter is also OFF for v1 — pure real data so the v1 number is interpretable)
- Rule 8: TEST/DEV untouched; the frozen split file governs
- Sacred-10 fidelity (row extraction) must be unaffected — row capture is rule/table-driven; if swapping the NER model changes row COUNTS anywhere, that's a wiring bug to fix before acceptance
- Standing constraints: `CLAUDE.md` §7 + gitignored models

## 8. DEPENDENCIES
- **Blocked by:** P2_04 (≥1000 verified sentences — HARD gate), P2_01 (catalog features if the model consumes gazetteer signals)
- **Blocks:** P4_02
- **Parallel-safe with:** P5_01 (different files)
- **Shared files:** `src/nlp/` model loading; `config/settings.py` read-only (new setting via env default if needed — propose, don't edit frozen constants)

## 9. GOTCHAS
- MPS: `pin_memory` warnings are benign; half-precision CRF layers historically NaN — keep CRF in fp32 if the architecture includes it.
- Label mapping: `ner_tags` string labels ↔ id mapping must come from `config.constants.BIOES_LABELS` order, not from a sorted set (a re-derived mapping silently permutes classes between runs — classic silent killer).
- Class imbalance is severe (O dominates; GRADE/DIMENSION sparse) — report per-type support; if you weight losses, record weights in the manifest.
- ~1000 sentences is SMALL: expect val F1 well below the 0.88 target on starved types; that is an honest finding, not a failure to hide. The 0.88 is the literature's number at maturity, not the acceptance bar for v1.
- Wall-clock budget: if a config exceeds ~4h on MPS, downscope (fewer epochs, smaller adapter) and note it — don't leave a training job unattended overnight on the owner's laptop without saying so in the report.
