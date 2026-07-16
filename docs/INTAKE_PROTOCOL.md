# Intake Protocol — what happens when SWA sends a document

> **Authoritative for Phase 9.** Written by P1_00 (2026-07-06). This is the
> runbook the owner (Srujan) follows when a new RFQ arrives. One command. The
> report tells you what to do next.

---

## 1. The one command

When SWA sends a new RFQ (PDF/XLSX/DOC/DOCX), run:

```bash
cd /Users/srujansai/rfq2boq-phase9
python3 scripts/intake_rfq.py <path-to-new-file> \
    --source "email from <who> <date>" \
    --client "<client name>"
```

## 2. What the report tells you

The command prints a JSON report. Three statuses:

| Status | Meaning | What you do |
|--------|---------|-------------|
| `refused_duplicate` | The file's sha256 already matches a manifest entry. | Nothing — it's already in the corpus. The report names the existing doc. |
| `intaked` | New doc copied into `data/real_rfqs/incoming/<date>/`, manifest appended, pipeline ran. | Review the `pipeline.rows_extracted` and `pipeline.needs_source_truth_count` fields. If `needs_source_truth_count` is true, a human needs to count source rows (P1_01) for the fidelity audit. |
| `intaked` with `intake_status: needs_conversion` or `pipeline_error` | The format couldn't be processed (e.g. scanned image PDF, .doc). | Convert the file to PDF/XLSX and re-run intake on the converted copy. The original manifest entry stays with `needs_conversion` so nothing is lost (R1 at intake). |

## 3. What intake does automatically

1. **Duplicate check** by sha256 — refuses if the file is already in the corpus.
2. **Copy** into `data/real_rfqs/incoming/<date>/` (original stays wherever you pointed).
3. **Manifest append** — sha256, provenance (`intake_source`), date, client, `doc_type: pending`, split assignment.
4. **Split assignment** — TRAIN default, every 5th → DEV, never TEST (frozen policy, `docs/CORPUS_DEFINITION.md`).
5. **Pipeline run** — XLSX or PDF path; counts rows; never crashes on bad input.
6. **Intake report** — rows extracted, flags raised, whether a source-truth count is needed.

## 4. When a retrain is triggered

A retrain cycle (P4_01 retrain + P4_02 honest eval) is scheduled when EITHER:

- **+200 newly owner-verified BIOES sentences** since last training, OR
- **+10 new boq_bearing docs** intake'd and source-truth-counted since last training.

The owner tracks the counter; `scripts/intake_rfq.py` does not auto-trigger
retraining. When the threshold is hit, the owner opens a new P4 cycle as a
ledger-tracked task. This keeps the model climbing honestly on the frozen TEST
split — measured, never inflated.

## 5. What intake does NOT do

- It does **not** mark anything `human_verified: true` (Rule 3 — only the owner does that, in P2_04).
- It does **not** add to TEST (Rule 8 — TEST is frozen at 42 forever).
- It does **not** delete or overwrite the original file.
- It does **not** auto-train or auto-eval.
- It does **not** touch gold or eval scripts (frozen by P0_02/P0_03).

## 6. The cadence rule in one line

> Every new doc is captured, flagged-not-dropped, and counted toward the next
> retrain threshold — that is how "100% fidelity, now and on every new document"
> stays a provable claim forever.