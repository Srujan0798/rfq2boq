# Corpus Definition — what counts, how splits work, the frozen policy

> **Authoritative for Phase 9.** Written by P1_00 (2026-07-06). The manifest
> (`data/real_rfqs/corpus_manifest.json`) and the frozen split
> (`data/real_rfqs/split_test.json`) are the machine-readable forms; this doc is
> the human-readable policy. If anything here disagrees with those files, the
> files win until this doc is brought into line.

---

## 1. What is the corpus

The corpus is the set of **client documents** SWA has delivered for RFQ→BOQ
extraction. As of the P1_00 sweep (2026-07-06), the manifest records **127
unique client docs** (hash-verified). Non-client material (academic papers,
the project brief, GeM catalog, UI samples, export templates, public reference
PDFs) is NOT part of the corpus and is not counted in the 127 — it lives in
`resources/`, `ui/assets/`, `src/export/templates/`, or
`data/real_rfqs/reference_real/` and is excluded from fidelity/accuracy claims
to SWA.

The sweep (`results/corpus_sweep/SWEEP_REPORT.md`) is the evidence: every on-disk
document file is either a manifest entry, a duplicate of one (by sha256), or
owner-ruled non-client material. Zero unexplained files.

## 2. Splits — the frozen policy

| Split | Count | Rule |
|-------|-------|------|
| **TEST** | 42 | **FROZEN FOREVER.** Includes the sacred 10. Never added to, never removed from, never trained on, never mined for gazetteer/pattern terms. The ruler never moves — new-doc generalization is measured by the intake fidelity audit, not by growing TEST. |
| **DEV** | 15 | First 15 spec1 paths alphabetically (excluding TEST). Used for threshold tuning. |
| **TRAIN** | 70 | The remainder. Used for NER training (P4_01, real verified gold only). |

## 3. Split assignment for NEW docs (intake policy)

When `scripts/intake_rfq.py` intakes a new doc:

1. **Default: TRAIN.** New docs enter the TRAIN pool.
2. **Every 5th intake → DEV.** By counter on the manifest total, the 5th, 10th,
   15th… new doc goes to DEV to keep DEV growing slowly alongside TRAIN.
3. **TEST is never assigned.** There is no code path in `intake_rfq.py` that
   can assign `split: "test"`. This is enforced by `assign_split()` returning
   only `"train"` or `"dev"`, and by `tests/unit/test_intake.py`'s
   TEST-immutability test.

## 4. Who may change the corpus

- **Adding:** only via `intake_rfq.py` (one command, duplicate-safe, provenance-complete).
- **Removing/dispositioning:** only the owner (Srujan) per the P1_00 owner gate.
  Agents never delete corpus files.
- **Split reassignment:** TEST is immutable. DEV/TRAIN reassignment requires an
  owner ruling and a manifest re-pin (frozen file).

## 5. The retrain cadence

A P4_01-style retrain + P4_02-style honest eval rerun is scheduled as a new
ledger-tracked cycle when EITHER threshold is met since the last training:

- **+200 newly owner-verified BIOES sentences**, OR
- **+10 new boq_bearing docs** intake'd and source-truth-counted

See `docs/INTAKE_PROTOCOL.md` for the full runbook.