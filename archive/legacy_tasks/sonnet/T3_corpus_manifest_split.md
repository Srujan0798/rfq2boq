# T3 — Full-corpus manifest + frozen TRAIN/DEV/TEST split

## 1. GOAL
One manifest covering every client document (~105+), and a document-level split frozen forever, so training/eval can never leak and "the corpus" can never again be misread as just 10 files.

## 2. CONTEXT (read first)
- `tasks/sonnet/00_START_HERE.md` §CORPUS (the four sources)
- Existing partial manifests: `data/real_rfqs/manifest.json`, `data/real_rfqs/CORPUS.md`, anything under `data/annotations/cli_*` (uncommitted agent output — audit, don't trust)
- `resources/Specifications.rar` — extract with `unar` to scratch, dedupe (NEVER modify `resources/`)

## 3. DELIVERABLES
- `data/real_rfqs/corpus_manifest.json` — every doc: `{sha256, path, source_batch (sacred10|spec1|spec2|bundle:<name>|rar), client, received_date, doc_type (boq_bearing|spec_only|non_training), format, pages_or_sheets}`
- `data/real_rfqs/split_test.json` — frozen TEST: sacred 10 + exactly 5 never-processed Spec-2 docs (list them explicitly); DEV ≈15; TRAIN = remaining usable docs. Split at client-project level (all docs of one project in one split).
- `tests/unit/test_no_test_split_leakage.py` — fails if any TEST sha256 appears in any training data manifest, BIOES export, or gazetteer-mining source list; wired into `make verify`
- `results/gazetteer_provenance_audit.md` — which mined gazetteer terms came from which docs; terms mined ONLY from TEST docs removed from `data/ontology/*mined*.json`
- `docs/CORPUS_DEFINITION.md` — one page stating the corpus definition (mirrors 00_START_HERE §CORPUS) for all future agents

## 4. STEPS
1. `unar -o /tmp/rar_extract resources/Specifications.rar` → sha256 every extracted file → compare against `data/specifications/Specifications/`; add only genuinely new files (copy into `data/specifications/rar_extra/` if any).
2. Walk all four corpus sources + sacred 10; compute sha256; classify doc_type by inspection heuristics (BOQ table present? spec prose only? make-list/GCC/prebid = non_training) — record the heuristic per doc so the owner can spot-check.
3. Choose the 5 never-processed Spec-2 TEST docs: must have NO gold, NO prior extraction results, NO gazetteer terms mined from them (grep the mining provenance). Justify each pick in the manifest.
4. Freeze the split; write the leakage test; wire into `make verify`.
5. Audit `data/ontology/insulation_gazetteer_mined.json` (and any `*mined*` files) for TEST-doc-derived terms; remove them; document in the audit file.
6. Ledger entry + REPORT.

## 5. VERIFICATION
```bash
.venv/bin/python -c "import json;m=json.load(open('data/real_rfqs/corpus_manifest.json'));print(len(m));import collections;print(collections.Counter(d['source_batch'] for d in m));print(collections.Counter(d['doc_type'] for d in m))"
.venv/bin/python -m pytest tests/unit/test_no_test_split_leakage.py -q   # green
make verify                                                               # green
shasum -a 256 "data/specifications/Specification 2/boq.pdf" | awk '{print $1}' | xargs -I{} grep -c {} data/real_rfqs/corpus_manifest.json   # 1 (spot-check)
```

## 6. ACCEPTANCE CRITERIA
Manifest ≥105 docs, every file under the four sources present; split frozen and committed; leakage test green inside `make verify`; gazetteer TEST-terms removed with audit trail.

## 7. CONSTRAINTS
`resources/` read-only. Sacred 10 always TEST. Never re-pick TEST docs after freezing (additions to TEST later are allowed; removals are not).

## 8. DEPENDENCIES
Blocks: T4b, T5, T6, T7. Blocked by: T0. Parallel-safe: with T1/T2.

## 9. GOTCHAS
- Duplicate filenames across batches with different content — sha256 is identity, path is not.
- `.docx`/`.xlsx` in bundles count as corpus docs too.
- The email-bundle docs are the ORIGIN of some sacred-10 gold (e.g. Zydus, SAEL) — put such docs in the same split as their project (TEST), else you leak TEST content into TRAIN via near-duplicates. Check by client name matching.
