# Phase 7 — File Triage & Cleanup (runs BEFORE the code fixes)

## Purpose
Turn `phase9-final` into a genuinely clean, professional repository that can be handed to SWA as the final `main` — not just code-fixed, but file-level sorted: valuable data kept, contamination quarantined, nonsense removed, the good pieces from the Desktop repo merged in.

## The one rule that governs everything here: QUARANTINE, NEVER DELETE
The owner has stated there may be valuable data buried in the clutter. So **nothing is hard-deleted.** Everything questionable is *moved* into `archive/quarantine_2026-07/` with a manifest line explaining why. The owner reviews the quarantine folder and gives the final delete/keep call. `git mv` (history-preserving) for tracked files; plain `mv` + manifest for untracked ones.

Order: **T1 → T2 → T3 → T4 → T5**, then the code tasks **C1–C7** in `P7_CONSOLIDATION_PLAN.md`.

All work in `~/rfq2boq-phase9` on `phase9-final`. The Desktop repo (`~/Desktop/rfq2boq`) is READ-ONLY here — we read from it to salvage good parts, we never write to it and never copy its files in blindly (its history is rooted in the fabricated "v1.0.0 100% F1" commit).

---

## T1 — Cross-repo inventory (read-only; produces a report, changes NOTHING)

**Goal:** know exactly what each repo has that the other doesn't, so the merge is deliberate, not guessed.

```bash
cd ~
# Compare the two working trees, excluding heavy/irrelevant dirs
diff -rq ~/rfq2boq-phase9 ~/Desktop/rfq2boq \
  -x '.git' -x 'models' -x '__pycache__' -x '*.pyc' -x '.pytest_cache' \
  -x 'node_modules' -x '.venv' -x 'venv' 2>&1 | tee ~/rfq2boq-phase9/tasks/phase9/TRIAGE_INVENTORY_raw.txt
```
Then classify every line into a written report `tasks/phase9/TRIAGE_INVENTORY.md` with four buckets:
- **ONLY IN DESKTOP — valuable data** (real tender files, real annotations, real ontology entries not present in phase9-final) → candidates for T3 port
- **ONLY IN DESKTOP — superseded/nonsense** (old drafts, fabrication artifacts) → ignore, stays in Desktop
- **ONLY IN PHASE9-FINAL** (our deliverables, honest history) → keep, no action
- **IN BOTH BUT DIFFERENT** → note which version is newer/correct; flag any where Desktop's is genuinely better

**Deliverable:** `tasks/phase9/TRIAGE_INVENTORY.md`. **No file moves in this task.**
**Accept only if:** the report accounts for every differing path, each with a bucket and a one-line reason.

---

## T2 — Quarantine nonsense inside phase9-final (move, don't delete)

**Goal:** get the clutter out of the working tree without losing anything.

```bash
cd ~/rfq2boq-phase9
mkdir -p archive/quarantine_2026-07
```
Move into `archive/quarantine_2026-07/` (use `git mv` for tracked, `mv` for untracked), and add a line to `archive/quarantine_2026-07/MANIFEST.md` for each:
- Stray logs: `*.log`, `.opencode_run_*.log`, `logs/*.log`
- OS/editor junk: `.DS_Store`, `*.swp`, `*~`
- Scratch/temp output dirs not meant to ship: `results/*_scratch/`, regenerable draft dumps
- Duplicate/superseded deliverable drafts already replaced by the real report/slides
- The scope-drift API modules **only if C1 hasn't already removed them** (coordinate — don't double-handle)

**Hard limits:**
- Do NOT quarantine anything under `data/real_rfqs/`, `data/ontology/`, `resources/`, `config/`, `src/`, `tests/` without explicit per-file justification in the manifest — these are presumed valuable.
- Do NOT touch `data/real_rfqs/source_truth.json`, gold, or eval scripts.

**Verify:**
```bash
git status --short
PYTHONPATH=. python3.12 -m pytest tests/ --tb=no -q   # EXPECT: no new failures (moving non-code must not break anything)
```
**Accept only if:** every moved file has a MANIFEST line, tests are unchanged, and nothing under the protected paths above moved without justification.

---

## T3 — Port valuable Desktop-only data (hash-verified, DATA only)

**Goal:** pull in the genuinely-valuable files that exist ONLY in the Desktop repo (per T1's inventory) — but safely.

For each file bucketed "ONLY IN DESKTOP — valuable data" in T1:
```bash
# 1. Hash the source
shasum -a 256 "~/Desktop/rfq2boq/<path>"
# 2. If it's a corpus/tender file, check that hash against data/real_rfqs/corpus_manifest.json provenance
# 3. Copy into phase9-final
cp "~/Desktop/rfq2boq/<path>" "~/rfq2boq-phase9/<path>"
# 4. Re-hash the copy — must match step 1 byte-for-byte
shasum -a 256 "~/rfq2boq-phase9/<path>"
```
Log every port (source path + sha256 + destination) into `tasks/phase9/TRIAGE_PORT_LOG.md`.

**Hard limits:**
- **DATA only** — never port code, config, gold, eval scripts, or `source_truth.json` from Desktop (those are the contaminated surfaces).
- If a "valuable" file is annotation/gold data, it does NOT go into the training/gold set here — it goes to `archive/quarantine_2026-07/from_desktop/` for owner review (its provenance can't be trusted from the contaminated repo).

**Accept only if:** every ported file's before/after hash matches and is logged; nothing outside the DATA-only rule was copied.

---

## T4 — Contamination sweep (find fabrication artifacts, quarantine them)

**Goal:** make sure no product of Incident #13 (the fabrication swarm) rides into the final repo.

Read first: `tasks/phase9/04_LEDGER.md` (Incident #13 entry) and the known cheating-patterns list. Then sweep phase9-final for:
- `data/annotations/verified/*.json` with NO `reviewer` field or `reviewer` != a real owner session (the 198 forged files had `reviewer` absent) — quarantine any that fail the provenance check
- Any results/report file asserting "100%" / "v1.0.0 ship it" / fabricated F1 that isn't backed by a reproducible command
- Orphaned "FINAL_HANDOFF" / "complete session merge" docs that describe work that was later shown false

```bash
cd ~/rfq2boq-phase9
# provenance check on verified annotations
PYTHONPATH=. python3.12 scripts/check_gold_provenance.py 2>&1 | tail -20   # if this script exists
# find suspect claims
grep -rln "100.0% row F1\|ship it\|all sessions deleted" --include="*.md" . | grep -v archive/
```
Quarantine failures into `archive/quarantine_2026-07/contamination/` with a manifest line each. Do NOT delete — the owner decides.

**Accept only if:** every `verified/` annotation remaining in the live tree passes the provenance check (real reviewer stamp), and every quarantined item is logged with the reason it failed.

---

## T5 — Final structure polish

**Goal:** every inch professional — clean root, every folder purposeful, docs match reality.

```bash
cd ~/rfq2boq-phase9
ls -la              # root: only intended files (README, CLAUDE.md, HANDOFF.md, Makefile, pyproject.toml, Dockerfile, docker-compose.yml, .env.example, .gitignore, CHANGELOG.md, CONTRIBUTING.md)
ls -d */            # every top-level dir must have a clear purpose + a README or be self-evident
```
- Ensure `.gitignore` correctly excludes: `*.log`, `__pycache__`, models, `drafts/`, scratch, `.DS_Store`, big regenerable data
- Update `README.md` repo-structure section so it matches actual `ls -d */` exactly — no phantom folders, no missing ones
- Confirm `deliverables/` contains ONLY: the signed report (`.md` + `.pdf`), `presentation.html`, `Presentation_Slides.md`, `SWA_HANDOFF_GUIDE.md`, `demo_live.py`, `signature.jpg`

**Verify:**
```bash
git status --short
PYTHONPATH=. python3.12 -m pytest tests/ --tb=no -q
```
**Accept only if:** root and dir listing are clean, README structure matches reality, deliverables folder is exactly the intended set, tests unchanged.

---

## After T1–T5: run the code tasks
Proceed to `P7_CONSOLIDATION_PLAN.md` → C1 (scope removal), C2 (mypy), C3 (ruff), C4 (fidelity), C5 (commit), C6 (gate), C7 (owner-only GitHub replace + 18GB history shrink).

## The 18GB `.git` — note for C7, not for the triage tasks
File-triage (T1–T5) cleans the *working tree*. The 18GB is git *history* bloat (old large blobs in past commits) — quarantining files today does NOT shrink it. That's fixed only by the history rewrite in C7, which is owner-only. Don't attempt `filter-repo` as part of triage.

## Dispatch note
T1 is read-only and blocks the rest (T2/T3/T4 all consume its inventory) — run T1 first, alone. T2, T3, T4 can then run in parallel (different target folders). T5 runs after them. Every task appends a real, dated line with actual command output to `tasks/phase9/04_LEDGER.md`. Quarantine manifests are the audit trail — the owner reviews `archive/quarantine_2026-07/` before anything is permanently deleted.
