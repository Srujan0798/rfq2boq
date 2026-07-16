# TASK P1_01: Complete the independent source-truth ruler for all 33 boq_bearing docs — Agent-P1-1

## 1. GOAL
Produce an independent, human-checkable count + listing of the real BOQ rows in every boq_bearing document in the corpus, so R1 fidelity can be measured against source truth instead of against the pipeline's own opinion.

## 2. CONTEXT
Files to read FIRST (in order):
- `docs/GOLD_METHODOLOGY.md` (from P0_02) — what counts as a row (incl. D4: section-title rows do NOT count)
- `scripts/draft_source_truth.py` + `scripts/draft_source_truth_extras.py` — the existing auto-counter, including the `needs_manual_count` / `header_found` mechanics added 2026-07-05
- `data/real_rfqs/source_truth.json` — current draft output
- `data/real_rfqs/corpus_manifest.json` — filter `doc_type == "boq_bearing"` (33 docs, or more if P1_00's sweep ingested new ones)

Current state:
- The auto-counter handles standard header-row tables; 7 docs are flagged `needs_manual_count` (e.g. 08_sael's numbered-clause-outline XLSX; two spec1 insulation PDFs) where the heuristic finds no header row.
- Sacred-10 counts are largely settled through the P0 work; the other boq_bearing docs have draft counts of varying confidence.
- A false zero ("0 rows found" because parsing failed) is the dangerous failure mode — it lets a doc "pass" fidelity trivially. The `header_found` flag distinguishes confirmed-zero from failed-count; preserve that distinction religiously.

## 3. DELIVERABLES
- [ ] `data/real_rfqs/source_truth.json` — complete: for ALL boq_bearing docs: `doc_id, source_files[], row_count, counting_method (auto|manual), evidence (page/sheet + row-range refs), needs_manual_count:false everywhere, d4_exclusions[] (any section-title rows explicitly excluded)`
- [ ] `data/real_rfqs/source_truth_worksheets/<doc_id>.md` — for each of the 7 manual docs (plus any doc whose auto-count you had to override): a human-readable row listing (item no · description(first 60 chars) · qty · unit) transcribed from the SOURCE document, so the owner can spot-check in minutes
- [ ] `scripts/draft_source_truth.py` — improvements ONLY of the form "recognize more real header/table shapes"; never of the form "guess when unsure" (unsure must stay `needs_manual_count` until a human transcribes)
- [ ] `tests/unit/test_source_truth.py` — schema validation test + a test that `needs_manual_count:true` records are rejected from the final file

## 4. STEPS
1. Read context files. List the boq_bearing docs: `python3 -c "import json; m=json.load(open('data/real_rfqs/corpus_manifest.json')); [print(f['path']) for f in m['files'] if f.get('doc_type')=='boq_bearing']"`
2. Re-run the auto-counter; triage every doc into: confident-auto / auto-but-verify / manual.
3. For each manual doc: open the source file directly (openpyxl for XLSX; pdfplumber page dumps for PDF), transcribe the real line items into the worksheet file, count them. Apply D4 (exclude title-only rows; record them in `d4_exclusions`).
4. For every AUTO-counted doc, spot-verify at least the first + last row against the source (cheap insurance against off-by-header errors); note the spot-check in the worksheet or evidence field.
5. Assemble the final `source_truth.json`; run tests; commit.
6. Flag in your report any doc where the count is genuinely ambiguous (e.g. multi-quantity-column layouts like 05_zydus_animal) — list them as OWNER-DECISION-NEEDED with the specific question, and record the count both ways.

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 -m pytest tests/unit/test_source_truth.py -v      # EXPECT: all passed
python3 - <<'EOF'
import json
st = json.load(open('data/real_rfqs/source_truth.json'))
docs = st['docs'] if isinstance(st, dict) and 'docs' in st else st
assert not any(d.get('needs_manual_count') for d in docs), "manual counts incomplete"
print("SOURCE TRUTH COMPLETE:", len(docs), "docs")
EOF
ls data/real_rfqs/source_truth_worksheets/ | wc -l         # EXPECT: >= 7
python3 scripts/check_frozen_hashes.py                     # EXPECT: FAIL on source_truth.json ONLY (expected — orchestrator re-pins on acceptance)
make lint                                                  # EXPECT: clean
```

## 6. ACCEPTANCE CRITERIA
- [ ] Every boq_bearing doc has a final count with method + evidence; zero `needs_manual_count`
- [ ] Every manual doc has a transcription worksheet an owner can check against the source in <5 min
- [ ] D4 exclusions explicitly recorded (02_isro: 1, 08_sael: 1, plus any newly found)
- [ ] No count was produced by running the pipeline (Rule 2 — the ruler is independent by construction; evidence fields cite source pages/sheets, not pipeline output)
- [ ] Ambiguous docs listed for owner with the exact question and both candidate counts

## 7. CONSTRAINTS
- The pipeline (`src/…`) must NOT be invoked anywhere in this task — the ruler must be derived from source documents only
- DO NOT modify gold, manifests, split, or eval scripts (frozen); `source_truth.json` is the one frozen file you legitimately change — orchestrator re-pins after gate
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P1_00 (the ruler is built on the RECONCILED corpus — if the sweep ingested new boq_bearing docs, they are in scope here too)
- **Blocks:** P1_02, P1_03
- **Parallel-safe with:** nothing (first post-reconciliation task establishes the ruler)
- **Shared files:** `data/real_rfqs/source_truth.json` (frozen)

## 9. GOTCHAS
- 04_adani spans TWO PDFs (`BOQ PAGEadani proj.pdf` = 43 rows + `BOQ PAGE2adani proj.pdf` = 2); source_truth must model multi-file docs (the `source_files[]` list exists for this).
- Merged cells in XLSX make `max_row` lie; iterate rows and test content, don't trust dimensions metadata.
- Sub-items (11.1, 11.1.1…) ARE rows; their section-title parents are NOT (D4). A row with qty but no unit, or unit but no qty, still counts — it's a flagging case for the pipeline, not an exclusion.
- Scanned PDFs (some GeM docs) may need the OCR text layer — if a doc is truly unreadable without pipeline OCR, transcribe from visual inspection of the PDF and say so in evidence; do not run the pipeline "just for reading".
