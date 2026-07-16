# Non-Client Data Disposition Record — P1_00 owner ruling 2026-07-06

> **Owner ruling (Srujan, 2026-07-06):** all 18 unmanifested files from the
> P1_00 sweep are **non-client material** — none are SWA documents. They are
> quarantined (left in place, excluded from the client corpus) per this record.

## Disposition: NON-CLIENT QUARANTINE for all 18 files (12 unique hashes)

| Group | Files | Disposition | Reason |
|-------|-------|-------------|--------|
| Academic papers / surveys / industry studies | 8 (4 unique) | non-client — leave in `resources/` | Research literature, NOT client RFQs. NER training reference. |
| Project brief / SOW | 2 (1 unique) | non-client — leave in `resources/` | SWA project brief, NOT a tender. |
| GeM product catalog | 2 (1 unique) | non-client — leave in `resources/` + `data/real_rfqs/` | GeM catalog (P2_01 ingests as NER reference), NOT a tender. |
| UI demo sample | 1 | non-client — leave in `ui/assets/` | UI demo file, NOT a real client doc. |
| Export template | 1 | non-client — leave in `src/export/templates/` | Excel export template, NOT an RFQ. |
| IREPS / CPWD reference docs | 3 | non-client — leave in `data/real_rfqs/reference_real/` | Public government tender reference docs, NOT SWA-client. |

## Effect on the corpus

- **Corpus confirmed at 127 client docs.** UNMANIFESTED = 0 after this ruling.
- No files moved or deleted (per §7: resources/ is SACRED; nothing deleted without
  explicit owner instruction).
- These files are excluded from fidelity/accuracy claims to SWA (client claims are
  made on client docs only — the manifest's `source_batch` field is what keeps
  reporting honest).

## Path-drift note (separate from this ruling)

108 manifest entries reference `data/specifications/...` paths absent from this clone;
all 108 exist with matching sha256 under `resources/Specifications/` + `data/real_rfqs/ALL_RFQS/`.
Path drift, not missing data. Orchestrator may re-pin manifest paths in a future gate.