# Annotation Workflow — RFQ2BOQ (P2_02)

**Goal:** Process one real tender PDF/XLSX into verified BIOES gold in < 15 minutes.

**The fence (Rule 3 / incident #7 + #13):** `human_verified:true` may ONLY be written from a live interactive terminal session via `scripts/annotation_factory.py review`. A non-interactive session (CI, scripts, agents) is hard-refused with exit 3. The only reviewer string is `"srujan"`.

**Hard rules (never violate):**
- Drafts are ALWAYS `human_verified:false`, `reviewer:null`, `reviewed_at:null`. The factory writes them that way; the lock (`scripts/check_gold_provenance.py`) rejects any other configuration.
- The `review` subcommand requires `sys.stdin.isatty()` — there is no `--auto-accept` and never will be.
- TEST-split docs (per `data/real_rfqs/split_test.json`) are REFUSED at draft time (Rule 8). The factory only drafts from the TRAIN pool.

---

## 1. One-tender < 15-minute checklist

This is the workflow for the owner. The factory is the only interface.

```bash
# 1. (Owner/agent one-time) generate drafts for the TRAIN pool.
#    Run a few times to grow the draft set incrementally.
python3 scripts/annotation_factory.py draft --split train --docs 70
#    -> writes data/annotations/drafts/<doc_id>.draft.json, all human_verified:false

# 2. Owner review session (THE fence)
python3 scripts/annotation_factory.py review --file data/annotations/drafts/<doc_id>.draft.json
#    Keys: [a]ccept / [e]dit / [r]eject / [s]kip / [q]uit
#    On accept+quit: writes data/annotations/verified/<doc_id>.json with
#    human_verified:true, reviewer:"srujan", reviewed_at:<iso>

# 3. Validate BIOES before training
python3 scripts/validate_annotations.py
#    -> scans data/annotations/drafts/ AND legacy train/val/test
#    -> exit 0 iff all BIOES tags valid, all tags in config.constants.BIOES_LABELS,
#       all tokens/tags length-aligned
```

## 2. Subcommands (quick reference)

```
annotation_factory.py draft   --split train --docs N   # pre-annotate N TRAIN docs
annotation_factory.py review  --file <draft>           # interactive owner review
annotation_factory.py stats                           # verified-sentence stats
annotation_factory.py validate --file <path>          # validate one file
annotation_factory.py validate                        # validate all drafts/
annotation_factory.py self-test                       # internal: fence smoke check
```

## 3. Data directory contract

| Directory | What lives here | human_verified? |
|---|---|---|
| `data/annotations/drafts/` | Machine pre-annotations (fence output) | `false` (always) |
| `data/annotations/verified/` | Owner-reviewed, fence-stamped | `true` (only from `review`) |
| `data/annotations/owner_minutes.jsonl` | Append-only audit log: ts, doc_id, accepted, rejected, reviewer | n/a (audit) |
| `data/annotations/cli_drafts/` | LEGACY/QUARANTINED — never train on these | varies |
| `data/annotations/cli_drafts_test_reference_DO_NOT_TRAIN/` | Evidence — never merge | varies |

Quarantined directories are evidence of past attempts; do not import their content into the new draft space.

## 4. Sentence segmentation rules

The factory's segmenter (`annotation_factory._segment_into_sentences`) is conservative on tender text:

- **Table rows stay atomic.** A cell with a number+unit pair (e.g. `9 mm thick 600.0 sqm supply`) is kept as one sentence. Naive splitters would shred `M.S. Pipe as per IS 1239 Pt.1` at the abbreviation dot.
- **Newlines > punctuation.** Tender documents use a lot of newlines for table rows. The segmenter splits on newlines first, then refines prose with a terminal-punctuation splitter.
- **Prose-only lines use terminal punctuation.** A line without a number+unit pair is split at `.;:?!` boundaries.

## 5. BIOES contract

- Tag set: `config.constants.BIOES_LABELS` (33 entries: O + 8 entities × 4 prefixes).
- All tag writers (drafts, review output) use this set exactly. Anything else fails `validate_annotations.py` and the lock.
- BIOES strictness enforced by `validate_annotations.validate_bioes`:
  - I-X or E-X must be preceded by B-X or I-X of the same type.
  - E-X must not be followed by I- (entity must terminate at E-).
  - No I- or E- outside an entity run.

## 6. Provenance fence (Rule 3)

| Event | Stamps `reviewer:"srujan"`? | Source |
|---|---|---|
| `annotation_factory.py review` (live tty) | YES | `cmd_review` after `sys.stdin.isatty()` assert |
| `annotation_factory.py review` (CI / piped) | NO (refused, exit 3) | tty check |
| `annotation_factory.py review --reviewer <other>` | NO (refused, exit 2) | reviewer hard-coded to "srujan" path |
| `scripts/intake_tender.py` (intake path) | NO | writes `status: draft-needs-review` only |
| `scripts/review_annotation.py` (legacy) | **DEPRECATED** — does not enforce tty; do not use |

The fence is verified by the **dryrun proof**:

1. Make a `data/annotations/verified/<name>.json` with `human_verified:true, reviewer:"dryrun-agent"`.
2. `python3 scripts/check_gold_provenance.py` → must exit 1 with `FORGED` line.
3. Delete the dryrun file.
4. `python3 scripts/check_gold_provenance.py` → must exit 0.

## 7. What this contract protects against

- **Incident #7 (2026-07-03):** 19 files stamped verified with a justification-note reviewer string. The `VALID_REVIEWERS = {"srujan"}` whitelist would have rejected all 19.
- **Incident #13 (2026-07-06):** 198 files in the chaos repo stamped verified with no reviewer field at all and a "v1.0.0 ship it" tag. The `reviewer` field absence is now a WARNING (not hard fail) so legacy sacred-10 rowgold can still pass; for any NEW file the fence rejects anything that doesn't have a real owner identity.
- **Bulk stamping attacks:** the proposed provenance patch (see `docs/ANNOTATION_FACTORY_PATCH.md`) adds a monotonicity check — `>50` sentences sharing one timestamp fails. This blocks a single 30-min session from stamping a thousand sentences (the realistic rate is ~50 sentences / owner session).

## 8. Quickstart for the owner (a 30-min session)

```bash
# Pick a draft from the queue
ls data/annotations/drafts/

# Review it. Use a/e to accept, q to save and quit, [s] to skip a sentence
python3 scripts/annotation_factory.py review --file data/annotations/drafts/<doc_id>.draft.json

# How am I doing?
python3 scripts/annotation_factory.py stats

# Spot-check the file landed correctly
python3 scripts/annotation_factory.py validate --file data/annotations/verified/<doc_id>.json
```

The factory's target rate is **≥100 sentences/hour** (≈ 1.7 sentences/min, ≈ 2 keystrokes per accepted sentence for the [a]ccept path).

## 9. Constraints recap

- **Rule 3 (gold is owner-only):** `human_verified:true` only from `cmd_review` with tty.
- **Rule 8 (frozen split):** `draft --split` only accepts `train`. TEST is hard-refused.
- **No new heavy deps:** stdlib + `rich` (if already installed; check pyproject).
- **Settings:** paths come from `annotation_factory.py` constants; the env-prefix `RFQ2BOQ_` is unused here (no env-overridable paths in v1).

See `docs/ANNOTATION_GUIDELINES.md` for the entity taxonomy and the relation schema.
