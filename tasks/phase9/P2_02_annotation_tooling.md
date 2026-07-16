# TASK P2_02: Annotation factory tooling — pre-annotate → owner-review → verified BIOES — Agent-P2-2

## 1. GOAL
Build the tooling that turns raw corpus sentences into owner-verified BIOES training gold at ≥100 sentences/hour of owner time — the machine that fixes THE core problem (no real human-annotated training data).

## 2. CONTEXT
Files to read FIRST (in order):
- `docs/CORE_UNDERSTANDING.md` §3+§5 — why this is the highest-value work in the project
- `docs/ANNOTATION_GUIDELINES.md` + `docs/ANNOTATION_WORKFLOW.md` — existing guidelines (audit for correctness vs `config/constants.py`; fix drift)
- `scripts/gen_annotation_drafts.py`, `scripts/review_annotation.py`, `scripts/validate_annotations.py`, `scripts/preannotate_swa_enquiries.py` — prior art; judge each: reuse, extend, or replace (say which and why)
- `config/constants.py` — BIOES_LABELS, EntityType (the ONLY schema)
- `data/annotations/` layout — note `cli_drafts_test_reference_DO_NOT_TRAIN/` quarantine precedent

Current state:
- Zero genuinely owner-verified BIOES sentences exist. The 19 `human_verified:true` stamps of incident #7 were forged and reverted; the Desktop repo's 198 "verified" files (incident #13) have no reviewer field at all and are NOT in this clone's trusted set.
- The owner's realistic budget is short daily review sessions; the tooling must maximize verified-sentences-per-owner-minute: good pre-annotation, keyboard-driven review, batch acceptance of easy cases.

## 3. DELIVERABLES
- [ ] `scripts/annotation_factory.py` — subcommands:
  - `draft --split train --docs N` — sentence-segment processed docs (from P1_04 run artifacts), pre-annotate with the CURRENT best stack (pattern rules + GeM catalog + ontology gazetteers), emit draft files `data/annotations/drafts/<doc_id>.draft.json` with `human_verified:false`, per-entity source (`pattern|gazetteer|model`), confidence
  - `review --file <draft>` — terminal review UI: shows sentence with color-coded spans; keys: accept sentence / fix span (retype label or adjust boundaries) / reject sentence / skip; writes decisions to `data/annotations/verified/<doc_id>.json` with `human_verified:true, reviewer:"srujan", reviewed_at:<iso>`
  - `stats` — verified-sentence count by entity type, docs covered, owner-minutes logged
- [ ] `data/annotations/drafts/` + `data/annotations/verified/` directory contract documented in `docs/ANNOTATION_WORKFLOW.md` (rewrite it to match reality)
- [ ] `scripts/validate_annotations.py` — extended/fixed: BIOES validity (no I- without B-, no dangling E-), schema labels only, `ner_tags`/`labels` key tolerance, tokens/tags length equality
- [ ] `tests/unit/test_annotation_factory.py` — ≥8 tests: drafting determinism, BIOES validity of drafts, review write path sets reviewer correctly ONLY via interactive session, validation catches each corruption class
- [ ] Hard link into provenance: `check_gold_provenance.py` already rejects reviewer≠"srujan" — ADD a check that `reviewed_at` timestamps are monotone-plausible (no bulk stamping: >50 sentences sharing one timestamp = fail) — coordinate with orchestrator for the frozen-hash re-pin

## 4. STEPS
1. Read context; audit existing scripts + guidelines; write the reuse/replace verdict table first (report section).
2. Build `draft` (consume P1_04's processed outputs; sentence segmentation must keep table-row cells as single "sentences" — tender text is not prose).
3. Build `review` (pure-terminal, no web server; must run over ssh; single keystroke per action; autosave every decision — owner sessions get interrupted).
4. Build `stats` + validation upgrades + tests.
5. Dry-run the full loop on 2 TRAIN docs yourself: draft → review a few sentences AS A TEST with `reviewer:"dryrun-agent"` → confirm provenance check REJECTS your dryrun stamps → delete the dryrun outputs. This proves the fence works without forging anything.
6. Commit; report includes a 1-page quickstart for the owner (exact commands to run a 30-min session).

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 scripts/annotation_factory.py draft --split train --docs 2
python3 scripts/validate_annotations.py data/annotations/drafts/   # EXPECT: all valid, 0 errors
python3 -m pytest tests/unit/test_annotation_factory.py -v         # EXPECT: 8+ passed
# fence proof:
python3 scripts/check_gold_provenance.py                            # EXPECT: still exit 0 (drafts are unverified, ignored)
# (dryrun stamps present) → EXPECT: exit 1 naming the file; then delete dryrun outputs → exit 0
make lint && make typecheck && python3 -m pytest tests/unit tests/integration -q
```

## 6. ACCEPTANCE CRITERIA
- [ ] Full loop demonstrated end-to-end (draft → review UI → verified file) with the fence rejecting non-owner stamps
- [ ] Drafts BIOES-valid, deterministic, schema-locked to `config.constants`
- [ ] Review UI usable: ≤2 keystrokes for the accept path; autosave; resumable mid-file
- [ ] `data/annotations/verified/` contains ZERO files at task end (nothing verified until the owner actually reviews — P2_04)
- [ ] Guidelines doc updated to match the tool exactly (owner reads it cold and can start)

## 7. CONSTRAINTS
- Rule 3 absolute: you never write `reviewer:"srujan"`. The review subcommand writes it only from a live interactive session (assert `sys.stdin.isatty()` before allowing verified writes)
- Rule 8: TRAIN/DEV docs only; the tool must REFUSE to draft TEST-split docs (check against `split_test.json`, hard error)
- No new heavy deps (no label-studio, no web frameworks) — stdlib + rich/textual only if already installed (check pyproject)
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P1_04 (needs corpus-run outputs), P2_01 (catalog in the pre-annotation stack)
- **Blocks:** P2_03, P2_04, P4_01
- **Parallel-safe with:** P1_03 (while it waits at the owner gate)
- **Shared files:** `scripts/validate_annotations.py`, `docs/ANNOTATION_WORKFLOW.md`

## 9. GOTCHAS
- `data/annotations/*.json` legacy key chaos: `ner_tags` vs `labels` — the validator handles both; NEW files always write `ner_tags`.
- Sentence segmentation on tenders: naive splitters shred "M.S. Pipe as per IS 1239 Pt.1" at abbreviation dots. Segment table cells as atomic units; for prose sections use a conservative splitter (newline + terminal punctuation heuristics), and include segmentation tests.
- Token alignment: BIOES tags index TOKENS, not chars — pick one tokenizer (whitespace+punct, same as the training pipeline uses — check `src/nlp/` dataset code) and use it identically in draft + review + validate.
- The quarantined `cli_drafts*` directories are evidence — never merge their content into the new draft space.
