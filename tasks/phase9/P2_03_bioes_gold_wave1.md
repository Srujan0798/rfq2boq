# TASK P2_03: Draft-annotate the TRAIN pool — 1500+ candidate sentences queued for owner review — Agent-P2-3

## 1. GOAL
Run the annotation factory over the whole 70-doc TRAIN pool to produce high-quality DRAFT annotations (≥1500 candidate sentences, prioritized), so the owner's review time (P2_04) converts directly into the 1000+ verified sentences the literature target requires.

## 2. CONTEXT
Files to read FIRST (in order):
- `tasks/phase9/P2_02_annotation_tooling.md` + the factory quickstart from its report
- `data/real_rfqs/split_test.json` — the 70 TRAIN doc ids (NEVER dev/test)
- `docs/ANNOTATION_GUIDELINES.md` — entity definitions the drafts must follow
- P1_04's final `results/corpus_run/<run_id>/status.json` — per-doc processed outputs to draft from

Current state:
- Factory exists (P2_02); zero drafts at scale. 70 train docs ≈ 50 spec_only + ~20 boq_bearing/other → thousands of raw sentences; not all are worth owner time (boilerplate, legal clauses, contact blocks are worthless for NER).

## 3. DELIVERABLES
- [ ] `data/annotations/drafts/` — drafts for ALL 70 train docs
- [ ] `data/annotations/drafts/PRIORITY_QUEUE.json` — ordered review queue: sentence refs ranked by annotation value (entity-dense BOQ/spec sentences first; boilerplate last or excluded), with per-sentence `predicted_entity_count`, `doc_id`, `rank_reason`
- [ ] `scripts/annotation_factory.py` — `queue` subcommand added: builds/refreshes the priority queue; `review` gains `--queue` mode (walks the queue across docs instead of one file)
- [ ] `results/annotation_wave1/DRAFT_STATS.md` — honest stats: sentences drafted, predicted entity distribution by type (all 8 — flag starved types), docs covered, estimated owner hours to 1000 verified (at measured sentences/hour from a 20-sentence timing sample YOU run in dryrun mode)
- [ ] `tests/unit/test_priority_queue.py` — ≥4 tests (ranking sanity: entity-dense > empty; TEST-doc exclusion; determinism; queue-resume)

## 4. STEPS
1. Read context; confirm P1_04 artifacts cover all 70 train docs (missing docs → run them or report why).
2. Draft all 70 docs (`annotation_factory.py draft --split train --docs all`). Record per-doc sentence counts.
3. Build the ranking: `score = predicted_entities_weighted (rare types weight-boosted) − boilerplate_penalty (regex families: legal/terms/contact/signature blocks)`. Document the exact formula in the module docstring.
4. Generate queue + stats; timing sample; tests; commit.
5. Report ends with the exact command the owner runs to start reviewing (feeds P2_04).

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 - <<'EOF'
import json, glob
drafts = glob.glob('data/annotations/drafts/*.draft.json')
q = json.load(open('data/annotations/drafts/PRIORITY_QUEUE.json'))
total = sum(len(json.load(open(d))['sentences']) for d in drafts)
assert len(drafts) >= 60 and total >= 1500, (len(drafts), total)
assert q['items'][0]['predicted_entity_count'] >= q['items'][-1]['predicted_entity_count']
print(f"{len(drafts)} docs, {total} sentences, queue {len(q['items'])}")
EOF
python3 scripts/validate_annotations.py data/annotations/drafts/    # EXPECT: 0 errors
python3 -m pytest tests/unit/test_priority_queue.py -v              # EXPECT: 4+ passed
python3 scripts/check_split_leakage.py                               # EXPECT: exit 0 (no test docs drafted)
make lint && python3 -m pytest tests/unit -q
```

## 6. ACCEPTANCE CRITERIA
- [ ] ≥60 of 70 train docs drafted (list + reason for any skip), ≥1500 candidate sentences
- [ ] Queue top-100 manually spot-checked by you: ≥80 are genuinely annotation-worthy (include the spot-check tally in the report)
- [ ] Entity-type starvation honestly reported (if e.g. GRADE has <50 candidates, say so — P4_01 needs to know)
- [ ] Zero TEST/DEV docs in drafts; leakage check green
- [ ] Everything remains `human_verified:false`

## 7. CONSTRAINTS
- Rule 3 / Rule 8 as always; drafts only, owner stamps only via P2_04
- Do not "improve" pre-annotation models mid-task (consistency of drafts > cleverness; factory changes go through P2_02's file with orchestrator sign-off)
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P2_02, P1_04
- **Blocks:** P2_04, P4_01
- **Parallel-safe with:** P3_01, P3_02
- **Shared files:** `scripts/annotation_factory.py` (owned by P2_02→you in sequence)

## 9. GOTCHAS
- spec_only docs are prose-heavy: expect 100–400 sentences each; boq_bearing docs contribute fewer but entity-denser sentences — the queue interleaving matters more than raw volume.
- DEV docs (15) are deliberately NOT drafted in wave 1 — DEV sentences get annotated later only as an eval-tuning set if P4 needs it; keep the pools clean.
- Hindi/bilingual passages exist in some tenders: draft them, tag rank_reason `"non_english"`, rank low (English primary per charter) — do not silently drop.
- Watch memory: 70 docs of pdfplumber output in one process → draft doc-by-doc, write incrementally.
