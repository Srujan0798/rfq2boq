# T7 — One-shot honest evaluation + the eternal guarantee (regression & combinations)

## 1. GOAL
(a) Produce the project's real, final numbers on the frozen TEST split + one never-seen document — one shot, no fix-and-rerun. (b) Lock the "100% on every RFQ, every combination" guarantee into CI forever.

## 2. CONTEXT
- Frozen TEST (T3): sacred 10 + 5 Spec-2 docs. `split_test.json`.
- Production config decided in T6 (patterns or ensemble).
- The corpus regression demand (owner, 2026-07-04): every doc with owner-verified gold must yield its exact BOQ, in any combination/order, forever.

## 3. DELIVERABLES
- `results/FINAL_EVAL.md` — per-doc + macro: entity F1, row fidelity (captured/flagged/dropped), catalog-match accuracy on GeM docs; pattern-vs-model comparison if promoted; verbatim numbers, better or worse
- Fresh-doc result appended: one document Srujan supplies that the repo has NEVER contained (request it; if unavailable, use a documented held-back doc that appears in no manifest)
- `tests/regression/test_corpus_exact.py` — for every owner-verified doc: pipeline output == verified BOQ exactly (description/qty/unit normalized per documented rules); wired into `make verify`
- `tests/regression/test_combinations.py` — seeded random: subsets (2–10 docs), bundles (spec+BOQ+TDS), orderings → output == union of per-doc verified BOQs; order-invariant; zero cross-document bleed; dedupe policy asserted; wired into `make verify`
- `docs/EVAL_PROTOCOL.md` — how these numbers were produced, so anyone can reproduce

## 4. STEPS
1. Freeze the production config (git tag `eval-config-v1`).
2. Run the FULL pipeline once over TEST; compute all metrics; write FINAL_EVAL.md. **Any bug found on TEST goes into a "known issues" section — you do NOT fix and rerun within this task** (fixes go through DEV, then a new tagged eval).
3. Request + run the never-seen doc; append results (plausibility, flags, timing — its gold, if owner provides one afterward, gets scored too).
4. Build both regression suites over all owner-verified docs (from T4/T5 output); wire into `make verify`; run twice from a clean checkout (`git stash && make verify && make verify`).
5. Ledger + REPORT.

## 5. VERIFICATION
```bash
git tag | grep eval-config-v1
.venv/bin/python -m pytest tests/regression/ -q     # green, twice consecutively
make verify                                          # green (now includes regression + combinations + leakage)
```

## 6. ACCEPTANCE CRITERIA
FINAL_EVAL.md committed with per-doc numbers exactly as produced; fresh-doc section present; both suites green twice from clean checkout; `make verify` permanently carries the guarantee.

## 7. CONSTRAINTS
One shot on TEST. No threshold/config changes after the tag. If a TEST number is embarrassing, it ships as-is — that is the point.

## 8. DEPENDENCIES
Blocked by: T4a, T4b, T5, T6. Blocks: T8. Parallel-safe: no.

## 9. GOTCHAS
- Combination tests need deterministic seeds committed in the test file — "random" failures that can't be reproduced are useless.
- Union-invariance requires a documented dedupe key (doc_sha + row_index is safe; description-text matching is NOT — two docs can share identical rows legitimately).
- Runtime: full-corpus regression may be slow — mark the big suite `@pytest.mark.slow` with a fast sacred-10 subset in default `make verify`, full suite in `make verify-full` (BOTH must exist and BOTH green before closing).
