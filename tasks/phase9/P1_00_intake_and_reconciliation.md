# TASK P1_00: Corpus reconciliation sweep + the standing NEW-RFQ intake protocol — Agent-P1-0

## 1. GOAL
Prove the corpus is complete (no client document anywhere in the repo is missing from the manifest), and build the permanent intake pipeline so every FUTURE RFQ SWA sends gets the identical treatment — manifest, extraction, fidelity audit, flag review — automatically. This is what makes "100% fidelity, now and on every new document" a provable claim forever, not a one-time snapshot.

## 2. CONTEXT
Files to read FIRST (in order):
- `data/real_rfqs/corpus_manifest.json` + `ALL_RFQS_README.md` — the current 127-doc truth
- `data/real_rfqs/INTAKE_MANIFEST.csv` — prior intake records
- `scripts/intake_tender.py` — prior intake tooling (judge: reuse/extend/replace)
- `tasks/sonnet/LEDGER.md` row "INCIDENT-CANDIDATE — eval-methodology gaming" (2026-07-05) — the `data/real_rfqs/extracted/` provenance question (114 files, dated 2026-05-17, likely old scraped/synthetic robustness material, NOT client docs — owner disposition pending)
- `docs/SWA_REQUIREMENTS_2026-06-11.md` R3 — more documents keep coming; intake must be ready

Current state:
- Owner believes "150+ RFQs" exist. On-disk file census (2026-07-06): manifest = 127 unique client docs; `resources/Specifications/` = 53 files (rar duplicate of ingested content — 3 were net-new, already counted); `data/real_rfqs/extracted/` = 114 non-client leftovers (pending owner confirmation); `data/real_rfqs/raw/` = 5 (scraped-era, e.g. `rfq_bridge_*.pdf`). The sweep must settle this with evidence, file by file.
- No repeatable, verified intake path exists for a NEW document arriving tomorrow.

## 3. DELIVERABLES
- [ ] `scripts/corpus_sweep.py` — scans the WHOLE repo (excluding `.git`, `attic/`, `models/`, quarantines) for document files (pdf/xlsx/xls/doc/docx); for each: sha256 → in manifest? duplicate-of-manifest-entry (same hash, different path)? or UNMANIFESTED; writes `results/corpus_sweep/SWEEP_REPORT.md` with three sections: manifested / duplicates (path → manifest doc it duplicates) / unmanifested (each with best-guess provenance from path+mtime)
- [ ] **[OWNER GATE: Srujan reviews the unmanifested list and rules per file: client-doc-ingest / non-client-quarantine / delete.** The `extracted/` 114 and `raw/` 5 get their final disposition here.]
- [ ] Rulings executed: ingested docs → manifest + split assignment; non-client material → `attic/non_client_data/` with a README (nothing deleted without an explicit owner instruction naming the path)
- [ ] `scripts/intake_rfq.py` — the STANDING intake command: `python3 scripts/intake_rfq.py <file> --source "email from X" --client "Y"` → copies into `data/real_rfqs/incoming/<date>/`, appends manifest entry (sha256, provenance, date, doc_type=pending), refuses duplicates (hash match → reports which existing doc), assigns split per the frozen POLICY below, runs the pipeline + fidelity-relevant checks, emits an intake report (rows extracted, flags raised, needs source-truth count? needs annotation?)
- [ ] **Split policy for new docs, written into `docs/CORPUS_DEFINITION.md`:** new docs default to TRAIN pool; every 5th intake (by counter) goes to DEV; TEST stays frozen at the current 42 forever (the ruler never moves — new-doc generalization is measured by the intake fidelity audit itself, not by growing TEST)
- [ ] `docs/INTAKE_PROTOCOL.md` — the runbook: what happens when SWA sends a document (owner runs one command; what the report means; when a retrain is triggered — see cadence below)
- [ ] Retrain cadence rule (written into the protocol doc): +200 newly verified sentences OR +10 new boq_bearing docs since last training → schedule a P4_01-style retrain + P4_02-style eval rerun as a new ledger-tracked cycle
- [ ] `tests/unit/test_intake.py` — ≥6 tests: duplicate refusal, manifest append correctness, split-counter policy, TEST-split immutability (intake can NEVER assign test), provenance fields required, sweep classifies a fixture tree correctly
- [ ] `corpus_manifest.json` updated (frozen file — orchestrator re-pins after gate); `ALL_RFQS/` symlink folder + README regenerated to the post-sweep count

## 4. STEPS
1. Read context; run the sweep; produce SWEEP_REPORT.md; STOP at the owner gate with a clean summary table (count by disposition category, your recommendation per group).
2. (After rulings) execute dispositions; regenerate manifest artifacts; reconcile the final number — the README headline count changes from "127" to whatever is TRUE, with the sweep as evidence.
3. Build `intake_rfq.py` + policy + protocol doc + tests.
4. End-to-end intake drill: run a duplicate-refusal drill on a copy of an existing doc, plus a full intake on one genuinely unmanifested file if the sweep found any; attach the intake report to your REPORT.
5. Commit: sweep + dispositions / intake tool / docs+tests.

## 5. VERIFICATION
```bash
cd /Users/srujansai/rfq2boq-phase9
python3 scripts/corpus_sweep.py                     # EXPECT: 0 UNMANIFESTED remaining after dispositions
python3 -m pytest tests/unit/test_intake.py -v      # EXPECT: 6+ passed
python3 - <<'EOF'
import json
m = json.load(open('data/real_rfqs/corpus_manifest.json'))
print("corpus:", len(m['files']), "docs")           # the true post-sweep number
assert all('sha256' in f and 'source_batch' in f for f in m['files'])
EOF
python3 scripts/intake_rfq.py <any-existing-doc> --source drill --client drill   # EXPECT: REFUSED as duplicate, names the existing doc
python3 scripts/check_split_leakage.py               # EXPECT: exit 0; TEST list unchanged (42)
make lint && make typecheck && python3 -m pytest tests/unit -q
```

## 6. ACCEPTANCE CRITERIA
- [ ] Every document file in the repo accounted for: manifested, duplicate (mapped), or owner-ruled disposition — zero unexplained files
- [ ] The "how many RFQs do we actually have" question answered with a number backed by hashes, and the README/manifest/ALL_RFQS all agree
- [ ] Intake is one command, duplicate-safe, TEST-frozen, provenance-complete
- [ ] Retrain cadence rule documented and referenced from `00_README.md`'s definition of done
- [ ] Drill executed and reported

## 7. CONSTRAINTS
- `resources/` remains SACRED and read-only — its Specifications copies are recorded as duplicates in the sweep report, never moved or deleted
- Owner gate is hard: no disposition without a per-file (or per-group) ruling
- TEST split immutable — no code path may add to it
- Frozen-file changes (manifest, CORPUS_DEFINITION) go through orchestrator re-pin
- Standing constraints: `CLAUDE.md` §7

## 8. DEPENDENCIES
- **Blocked by:** P0_03 (needs the frozen-hash machinery to exist)
- **Blocks:** P1_01 (the ruler must be built on the RECONCILED corpus — if the sweep adds boq_bearing docs, P1_01's scope grows accordingly)
- **Parallel-safe with:** nothing (it can change the corpus everyone else works on)
- **Shared files:** `corpus_manifest.json`, `split_test.json` (read-only), `docs/CORPUS_DEFINITION.md`

## 9. GOTCHAS
- Hash-identical files with different names across batches are how the original 127 was deduped — the sweep must compare by sha256, never by filename.
- `data/real_rfqs/extracted/*.json` are pipeline OUTPUTS of the old scraped batch, not source documents — classify their SOURCE files (`raw/`), not the JSONs.
- Email-bundle files (14) legitimately duplicate sacred-10 content in places — they're already manifested as their own source_batch; don't "dedupe" them away.
- If the owner rules some scraped docs (bridge RFQs etc.) as useful robustness material: they enter the manifest with `source_batch: "scraped_non_client"` and are EXCLUDED from fidelity/accuracy claims to SWA (client claims are made on client docs only) — the manifest field is what keeps reporting honest.
- New incoming docs may be formats we've never seen (scanned image PDFs, .doc) — intake must never crash: unprocessable → manifest entry + `intake_status: needs_conversion` flag, reported, not dropped (R1 applies at intake too).
- This clone was made from the Desktop repo BEFORE the swarm's latest commits — the sweep covers THIS repo only; Desktop-repo file salvage is P5_04's problem, not yours.
