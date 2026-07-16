# W8 — Provenance audit: `data/real_rfqs/extracted/` (114 files, dated 2026-05-17)

**Read-only investigation. No files moved, deleted, or modified.**

## 1. Does `data/real_rfqs/raw/` contain the source PDFs?

`data/real_rfqs/raw/` exists but does **not** contain the PDFs the 114 `extracted/*.json` files
point to via their `source_file` field (e.g. `data/real_rfqs/raw/rfq_bridge_RFQ1900_045.pdf`).

Current contents of `data/real_rfqs/raw/`:
- `download_log.json` — 10 files from `epi.gov.in` / `nhai.gov.in` / `pc.odisha.gov.in` (a
  **different**, unrelated real-PDF collection effort; none of these are `rfq_bridge`/`cpwd`/`ireps`).
- `manifest.json` (57 entries) and `manifest.csv` (57 rows) — metadata-only, no PDFs alongside them.
  Crucially, **these manifests self-label their own entries**:
  - 53 entries have `"source": "synthetic"` and `manifest.csv` gives them the path prefix
    `synthetic_archive/rfq_bridge_...pdf`, `synthetic_archive/rfq_building_...pdf`, etc. That
    `synthetic_archive/` subfolder does not exist anywhere in the current checkout — a full
    repo-wide filename search (`find … -iname "*rfq_bridge*"`) found **zero** PDF files, only the
    `extracted/*.json` outputs. The source PDFs were deleted/never checked in; only extraction
    output survives.
  - 4 entries have `"source": "real"`: `cpwd_Guidelines_for_Hassle_Free_Bid_Submission_1778959268.pdf`,
    `delhi_pwd_Tender_1778958751.pdf`, `ireps_2724bb1eff78.pdf`, `ireps_bc341034058b.pdf`. These
    **do** physically exist, but under `data/real_rfqs/reference_real/` (3 of the 4 — no
    `delhi_pwd_Tender...pdf` was found anywhere), not under `raw/`.
- `metadata.json` — empty placeholder (`total_collected: 0`).
- `insulation_hvac/` — a separate, later (dated Jun 22), legitimate real-tender collection
  (SAEL/SWPL insulation RFQs + BOQ references), unrelated to this investigation.

**Conclusion: `extracted/` is an orphaned artifact.** Its source PDFs (for the 53 synthetic docs)
never persisted in this checkout in any form; only JSON extraction output remains.

## 2. Historical trace: the "Generalization Results (50 Unseen RFQs)" test

`git log --all -- HANDOFF.md` surfaced pre-Phase-8 commits (`edbd7d6`, `2d3bf6f`, `9895c7c`,
`a411751`, all superseded by the later `55c098b`/clean-slate rewrite) containing this exact
section:

```
## Generalization Results (50 Unseen RFQs)

| Domain     | Files | Avg Items | Range |
|------------|-------|-----------|-------|
| Building   | 15    | 11.5      | 9-15  |
| Road       | 6     | 9.2       | 8-10  |
| Bridge     | 11    | 8.0       | 8     |
| Plumbing   | 9     | 3.7       | 3-4   |
| Electrical | 9     | 5.7       | 5-6   |

**All 50 files produced valid BOQ items. Zero failures.**
```

This matches the `extracted/` filename prefixes exactly: `rfq_building_*`, `rfq_road_*`,
`rfq_bridge_*`, `rfq_plumbing_*`, `rfq_electrical_*` (50 files across those 5 domains), plus 3
`rfq_sample_{simple,medium,complex}` demo docs and a `summary.json` rollup (`total: 53,
processed: 53, failed: 0` — the same "zero failures" claim from the old HANDOFF.md). The
supporting task spec, `prompts/archive/superseded/A8_REAL_RFQ_COLLECTION.md`, independently
confirms the same 4 "real" filenames (cpwd/delhi_pwd/ireps×2) as "existing" alongside a mandate to
collect 50 more — i.e., this folder is the union of that old wave-2 real-PDF-collection effort
**and** the 50-doc synthetic generalization/robustness smoke test that ran against it.

**Yes — `extracted/` is confirmed leftover from that old generalization test batch.**

## 3. Real vs. synthetic — content inspection

`manifest.json`/`manifest.csv` already self-declare the split (53 synthetic / 4 real), and the
actual JSON content corroborates it. Example, `rfq_bridge_RFQ1900_045.json`:

```json
{"text": "Department", "type": "UNIT", "confidence": 0.9}
{"text": "Mumbai",     "type": "UNIT", "confidence": 0.9}
{"text": "22",         "type": "QUANTITY", "confidence": 0.9}
{"text": "2026",       "type": "QUANTITY", "confidence": 0.9}
```

Every entity in every `rfq_bridge/building/road/plumbing/electrical_*` file carries a flat,
suspiciously uniform confidence (~0.90–0.91, varying only in the 3rd decimal) — the signature of
a rule-based/template generator, not real extraction variance. Misclassifications ("Mumbai" as
UNIT, a bare "22" and "2026" — clearly split-apart date fragments — as QUANTITY) read as templated
filler text run through the regex pipeline, not prose from an actual tender. This is the same
"regex-auto-generated, not human-annotated real tenders" pattern `docs/CORE_UNDERSTANDING.md`
already identifies as the project's core historical data problem.

The 4 `"source": "real"` files (cpwd, delhi_pwd, ireps×2) are genuinely real government-portal
scrapes — 3 of the 4 source PDFs still exist under `data/real_rfqs/reference_real/` — but they are
**not** part of the current verified 127-doc `corpus_manifest.json`, whose `sources` field
enumerates exactly four origins (`sacred10`, `spec1`, `spec2`, `bundle:<name>`, `rar`), all
SWA-client-derived. A direct string search confirmed none of the 4 real filenames appear anywhere
in `corpus_manifest.json`. So even the real subset of `extracted/` is orphaned relative to
today's corpus definition — it's real data, just from a different, earlier, now-superseded intake
effort (wave-2 "A8 Real RFQ Collection", not the SWA-focused corpus).

## 4. Is anything active consuming this folder?

No active script or pipeline reads `data/real_rfqs/extracted/` for training or evaluation.
Grep across `scripts/`, `src/`, `tests/` for `real_rfqs/extracted` found only:
- `tests/unit/test_no_test_split_leakage.py` — lists it in a set of directories **excluded** from
  leakage scanning (defensive, not consumption).
- `scripts/extract_insulation_corpus.py` — writes to `data/real_rfqs/extracted/insulation_hvac/`,
  a **different**, not-yet-created subfolder for the unrelated insulation corpus effort. It does
  not read or write the 114 flat files under investigation.

All other references are historical/aspirational, in archived or superseded docs:
`prompts/archive/superseded/A8_REAL_RFQ_COLLECTION.md`, `docs/data_collection.md` (describes an
old `process_real_rfqs.py` workflow — that script no longer exists in `scripts/`),
`data/annotations/expanded/README.md` (a forward-looking TODO suggesting this data *could* be
converted to BIOES someday — never executed), and `docs/ULTRA_PLAN_WEEK_2026-06-22.md` /
`tasks/lane_B/B1_extract_insulation_tenders.md` (both about the unrelated insulation subfolder).

**Conclusion: truly orphaned.** Nothing currently reads it; nothing currently would break if it
moved.

## 5. Cross-reference against CLAUDE.md's S2 scope rule

CLAUDE.md §7 locks: *"no demo/samples/synthetic in data/ (only real_rfqs + attic/)"*. The 53
`rfq_bridge/building/road/plumbing/electrical_*` files plus 3 `rfq_sample_*` demo files plus
`summary.json` (57 of the 114) are confirmed synthetic/demo data sitting directly under
`data/real_rfqs/` — a folder whose name is itself a scope commitment ("real"). This is a direct,
unambiguous violation of the rule's intent: synthetic material inside `real_rfqs/` defeats the
purpose of the folder split the rule describes (synthetic is supposed to live in `attic/` only).

The remaining 4 files (cpwd/delhi_pwd/ireps×2 extractions) are real data, not a synthetic-scope
violation, but they are stale duplicate extraction output from a superseded intake wave, disjoint
from the current 127-doc corpus and its `corpus_manifest.json`.

## Recommendation

**Split disposition — not a single verdict:**

1. **MOVE TO ATTIC** (57 files: `rfq_bridge_*`, `rfq_building_*`, `rfq_road_*`, `rfq_plumbing_*`,
   `rfq_electrical_*`, `rfq_sample_{simple,medium,complex}.json`, `summary.json`) —
   confirmed synthetic/demo, directly violates the CLAUDE.md S2 rule by sitting under
   `real_rfqs/`, nothing currently consumes them, and they document a historically real milestone
   (the old "50 unseen RFQs" generalization smoke test referenced in pre-clean-slate HANDOFF.md)
   worth preserving for the record rather than deleting. `attic/` is exactly where the project
   charter already puts this class of material.

2. **FLAG FOR OWNER DECISION** (4 files: `cpwd_Guidelines_...json`, `delhi_pwd_Tender_...json` —
   note: no matching JSON for delhi_pwd was actually found in `extracted/`, only in the manifest;
   verify — `ireps_2724bb1eff78.json`, `ireps_bc341034058b.json`). These are extractions of
   genuinely real government tender PDFs, and 3 of the 4 source PDFs are still present and usable
   under `data/real_rfqs/reference_real/`. Two live paths exist for these: (a) fold them into the
   current corpus (re-run extraction fresh with today's pipeline and add to
   `corpus_manifest.json` as a new source batch, since the 2026-05-17 extraction predates the
   current pipeline and its confidence/entity output is likely stale/superseded), or (b) archive
   them alongside the synthetic batch since they came from the same superseded wave-2 collection
   effort and were never integrated into the SWA-client-scoped corpus. This is a genuine judgment
   call about corpus scope (should non-SWA public-portal tenders ever be added to the "real"
   corpus at all?) that only the owner should make — it's not clearly in-scope or out-of-scope
   under the current rules.

Also worth the owner's attention: `data/real_rfqs/raw/manifest.json` / `manifest.csv` themselves
are the metadata record for this same batch and would logically travel with whichever disposition
is chosen for the synthetic files (or split, mirroring the file-level split above).

No files were moved, deleted, or modified as part of this audit.
