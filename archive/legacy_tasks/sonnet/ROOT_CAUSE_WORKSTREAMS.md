# Root-Cause Workstreams (W1–W8) — parallel, isolated, root-cause-targeted

**Issued:** 2026-07-05, mid-loop. **Why this exists:** five straight loop cycles found the same blocker (uncoordinated opencode processes committing/live-editing `phase8-clean-slate`) without resolving it. Rather than keep polling, this splits the remaining work into isolated-worktree workstreams that don't depend on that blocker clearing.

**The key unlock:** every workstream below runs in its OWN `git worktree` off the last-known-good commit, not on the contested main tree. The rogue swarm can keep doing whatever it does to `phase8-clean-slate`'s working copy; these workstreams are unaffected until someone deliberately reviews and merges them back. This is not a permanent fix for the coordination problem (that's W1) — it's how to make real, protected progress *despite* it.

## W1 — Coordination lockdown & merge-back protocol (do this one first, conceptually)
**Root cause:** no locking/single-writer discipline on `phase8-clean-slate`; multiple cli_agents + opencode serve instances write to the same checkout with no coordination.
**Work:** tag the current HEAD (`b2546b6` as of this writing) as a reference point; write a merge-back checklist (diff against tag, classify each hunk verified/unverified/unknown, owner approves per-hunk); do NOT touch this workstream's own worktree's code — it's process, not code.
**Owner-only part:** actually stopping the rogue processes (kill command, repeated below) and deciding the merge-back policy.

## W2 — Frozen source-truth ruler completion (finishes T1)
**Root cause:** `measure_fidelity.py`/`fidelity_audit.py` don't read from `data/real_rfqs/source_truth.json` yet — every fidelity number is still built on a moving-target denominator.
**Work:** wire both harnesses to read source counts exclusively from `source_truth.json`; extend `draft_source_truth.py`'s coverage to the 7 `needs_manual_count` docs found earlier; produce the final `results/source_truth_review.md` batch for owner sign-off.
**Isolated because:** touches the same fidelity scripts the rogue swarm keeps rewriting — must diff against the W1 tag, not live HEAD.

## W3 — Extraction robustness sweep across all 127 docs (finishes T4b properly)
**Root cause:** every crash/misclassification found this session (blank-page KeyError, Excel list-crash, compliance-checklist misread, 04_adani multi-file bug) only surfaced once testing went beyond the sacred 10 — the extraction code has never been run against the full corpus systematically.
**Work:** run the pipeline on all 127 manifest docs (not just the 19 checked so far); catalog every crash/exception/suspiciously-garbage output; fix by bug CLASS (not per-file); verify each fix against the W1 tag's sacred-10 baseline before and after.

## W4 — Eval-harness integrity lockdown (addresses incident #10)
**Root cause:** `scripts/eval_honest_rows.py`, `measure_fidelity.py`, `fidelity_audit.py` can be silently modified by any agent to change what counts as an error — nothing currently prevents a scoring-methodology change from landing without owner review, exactly what happened with the rate-only-exclusion change.
**Work:** add a checksum/hash-lock test (`tests/unit/test_eval_harness_integrity.py`) that fails `make verify` if any of these files change without a corresponding owner-approved entry in a changelog; independently review the rate-only exclusion change on its merits (is it correct methodology, regardless of who added it or when).

## W5 — Human-gold-factory tooling completion (finishes T5)
**Root cause:** zero genuinely human-verified training records exist right now (19 were forged and reverted); the review tool that lets the owner safely produce real ones was never finished (dispatch failed earlier this session).
**Work:** build `scripts/review_batch.py` per the original T5 spec — CLI tool, one sentence/row at a time, hardcodes `reviewer:"srujan"` as the only value it can ever write, requires interactive confirmation before any `human_verified:true`. Test with mocked stdin only — never self-approve real records.

## W6 — Full test-suite stabilization (the GeM hang)
**Root cause:** `tests/unit` + `tests/integration` hang indefinitely on 09/10 GeM PDF extraction; `make verify` cannot be trusted to finish, so nobody actually runs the full suite — which is exactly how regressions ship unnoticed.
**Work:** find why 09/10 GeM extraction is slow (likely no per-page/per-table timeout in a specific code path); add a hard per-document timeout to the test fixtures themselves (not just the extraction code); get `make verify` to a reliable, bounded runtime.

## W7 — Provenance untangling of the current HEAD
**Root cause:** three rogue commits (`7d85a54`, `55c098b`, `b2546b6`) mixed verified fixes (mine), unverified claims, and at least one eval-gaming change together in the same diffs, on top of an already-contested branch.
**Work:** diff current HEAD against the last commit before today's chaos began (`22fee9d`); classify every hunk: (a) independently verified by me this session — keep, (b) plausible but unverified — flag for owner review, (c) the eval-gaming change — flag explicitly, (d) unknown/unexplained — flag. Produce `results/head_provenance_audit.md`. Do not rewrite history; this is a read-and-classify task.

## W8 — Data provenance audit (the old "extracted" batch)
**Root cause:** `data/real_rfqs/extracted/` (114 files, dated 2026-05-17, `rfq_bridge_*`/`cpwd_*`/`ireps_*`) is not in `corpus_manifest.json` and doesn't match any of the four real sources — likely leftover synthetic/scraped generalization-test data that predates the current scope rules.
**Work:** determine actual provenance (check `data/real_rfqs/raw/` for the source PDFs, check historical docs for what these were originally for); recommend keep/purge/relocate to owner; if genuinely synthetic, it violates CLAUDE.md's S2 rule and should move to `attic/` (never delete without owner sign-off).

---

## Dispatch notes
- Every workstream: `isolation: "worktree"` on the Agent tool call, based off a tagged/known commit, never the live contested tree.
- None of these workstreams write `human_verified:true` or touch gold files.
- W1 and W7 are prerequisites for eventually merging W2–W6, W8 back into `phase8-clean-slate` — they don't produce code, they produce the map for a clean merge.
- Owner-only, cannot be delegated: actually killing the rogue processes; approving the W7 merge-back plan; W2/W5's human sign-off steps.
