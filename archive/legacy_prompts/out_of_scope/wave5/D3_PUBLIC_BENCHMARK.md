# TASK: Public Benchmark Suite — Agent-4

**Wave:** 5 | **Tier:** D | **Priority:** P3

## 1. GOAL
Establish RFQ2BOQ as the reference benchmark for construction NER. Standardized test sets, leaderboard, submission system.

## 2. CONTEXT
Read first:
- `data/RFQ-BOQ-NER/` — released dataset from D1
- `scripts/benchmark.py` — eval script
- [docs/conventions.md](../../../../docs/conventions.md)

Current state: Internal evaluations only. No standardized public benchmark.

## 3. DELIVERABLES
- [ ] `benchmark/__init__.py`
- [ ] `benchmark/README.md` — protocol description
- [ ] `benchmark/synthetic_test/` — frozen synthetic test set
- [ ] `benchmark/real_test/` — frozen real-world test set
- [ ] `benchmark/adversarial_test/` — adversarial examples (typos, OCR errors)
- [ ] `benchmark/benchmark.py` — evaluation runner
- [ ] `benchmark/evaluate.py` — span F1 + per-entity breakdown
- [ ] `benchmark/leaderboard.md` — public leaderboard (Papers With Code format)
- [ ] `benchmark/submissions/` — directory for model submissions
- [ ] `benchmark/SUBMISSION_GUIDE.md` — how to submit
- [ ] `.github/workflows/benchmark.yml` — auto-eval on PR

## 4. STEPS
1. Freeze test sets (no further modifications, version-tagged)
2. Adversarial set: programmatically inject typos, OCR-like errors, missing spaces
3. Evaluation script: standardized span F1 calculation (seqeval)
4. Submission protocol: PR with model + benchmark JSON
5. Auto-eval via GitHub Action
6. Leaderboard renders top-10 models with metrics
7. Citation requirements documented

## 5. VERIFICATION
```bash
$ python3 benchmark/benchmark.py --model models/ner-bert-bilstm-crf-v1
EXPECT: outputs per-entity F1, overall F1

$ test -f benchmark/leaderboard.md
EXPECT: exit 0

$ test -f .github/workflows/benchmark.yml
EXPECT: exit 0
```

## 6. ACCEPTANCE CRITERIA
- [ ] Test sets frozen and version-tagged
- [ ] Evaluation reproducible (deterministic seeds)
- [ ] Submission guide clear enough for external researchers
- [ ] Initial leaderboard entry: our model

## 7. CONSTRAINTS
- Test sets must NOT leak into training
- Adversarial examples: documented generation process
- Submissions: code must be runnable in sandbox

## 8. DEPENDENCIES
- **Blocked by:** D1 (dataset release)
- **Blocks:** None
- **Parallel-safe with:** D2, D4

## 9. GOTCHAS
- Frozen test sets must NEVER be modified — version-control them
- Adversarial examples should be principled, not random noise
- Leaderboard maintenance: who curates submissions long-term?
- Auto-eval workflow: limit runtime (~10 min per submission)
