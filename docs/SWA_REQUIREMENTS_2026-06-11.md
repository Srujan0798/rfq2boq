# SWA Requirements — from the 2026-06-11 review meeting (CANONICAL)

**Status:** Locked requirements from SWA's review of the project (internship presentation + mentor feedback, 2026-06-11).
**Every agent must read this together with:**
1. `resources/RFQ to BOQ Scope Extraction using NLP system.pdf` — the original SWA brief (SACRED, never move)
2. `docs/CORE_UNDERSTANDING.md` — the grounded core problem + honesty rules
3. `tasks/phase9/00_README.md` — the active dispatch protocol

These requirements come from SWA's own mentor. They are **the acceptance bar the client stated** — treat them as product requirements, not suggestions.

---

## R1 — 100% data-conversion fidelity (the acceptance bar)

> "Whatever data is present in the document must be converted with 100% accuracy. There is no tolerance for missing information, incorrect mappings, or data loss. Every field, value, and detail available in the source document should be captured correctly during processing."

**What this means in engineering terms:**
- This is a **completeness/fidelity requirement on conversion**, not a statistical NER F1 target. If a BOQ row exists in the source, it must appear in the output with its exact description, quantity, and unit. Dropping rows, truncating descriptions (e.g., the 60-char material cut), or silently swallowing parse errors are all violations.
- Required behavior: when the pipeline is *unsure*, it must **flag, never drop** (low-confidence rows surface for review instead of disappearing).
- Build toward a **per-document fidelity audit**: count of source BOQ rows vs output rows, with a diff of misses. This is how we prove R1 to SWA per file.
- **Honesty rule still applies:** R1 is the bar we engineer toward and measure against — it is NOT permission to claim 100% before the audit proves it. (This project has a 5-incident fake-100% history; see `docs/CORE_UNDERSTANDING.md`.)

**Owned by:** every extraction task; fidelity-audit tooling is future NW work.

---

## R2 — GeM portal catalogs are authoritative NER reference data

> "In the GeM portal, tenders are based on predefined product catalogs. Buyers select products directly from an existing list — no paraphrasing, spelling variations, or inconsistencies. Sellers select from the same catalog. SWA can provide the product list already submitted in the GeM portal as a reliable reference dataset for entity extraction and validation."

**What this means in engineering terms:**
- For GeM tenders, material extraction is (near) **closed-vocabulary**: extracted materials should match catalog entries exactly. Validate GeM extractions against the catalog; a non-catalog material on a GeM tender is a red flag for an extraction bug.
- Current state: an initial 60+ product GeM gazetteer is integrated (`src/nlp/patterns/gem_catalog.py`, wired into `DictionaryLookup`, 132 material keys total).
- **When SWA delivers their actual submitted GeM product list, it replaces/extends the hand-built one** — ingest it verbatim as the authoritative catalog, with provenance noted.

**Owned by:** NW-02 ordering preserved (GeM check first); catalog ingestion task when the list arrives. **Owner:** ask SWA for the GeM list export.

---

## R3 — ~100 real PDF dataset is coming (the data foundation)

> "Coordinate with the Sales team, through Jineth, or Softnil's archive (historical RFQs, quotations, procurement documents). Around 100 PDF documents as an initial dataset for development, testing, and validation. Additional documents have been requested; currently only one more document is available — the rest will be shared once received."

**What this means in engineering terms:**
- This is the same prescription as the SWA implementation guide in `resources/` (50+ real PDFs + 1000+ human-annotated sentences → ~0.88 F1). **The client and the source literature agree: data volume is the lever.** Nothing else materially moves real NER F1.
- The intake → pre-annotate → human-review → BIOES pipeline must be ready **before** the documents arrive (that is `tasks/phase9/P2_02_annotation_tooling.md`).
- Every received document gets provenance recorded (who sent it, when, client, format) in the intake manifest. The 10 SWA enquiries stay sacred/held-out regardless of what arrives.

**Owned by:** NW-04 (agent); collection itself is **owner-only** (Srujan ↔ Sales/Jineth/Softnil).

---

## R4 — Structure-first extraction for large PDFs (mentor-endorsed method)

> "For 50–100+ page government tenders: first create a structure from the PDF — titles, subtitles, sections, subsections, annexures. Government formats rarely change. Find the section that is relevant; in that section find the subsection that mentions the BOQ — maybe one, maybe multiple, maybe annexures — and run extraction only on those relevant parts. This mirrors how a human estimator works."

**What this means in engineering terms:**
- This is now the **endorsed architecture** for the PDF path: outline extraction → BOQ-likely section routing → targeted extraction. Implemented 2026-06-11 in `src/preproc/document_structure.py` (PyMuPDF fast scan, Schedule/Annexure/Appendix boosting; GSECL's 62-page tender now resolves to pages 60–69).
- Remaining work: false-positive filtering (1281 candidate sections on one 29MB PDF) and honoring the "maybe multiple subsections / annexures" case — the extractor must support multiple BOQ ranges per document, not just the single best one.

**Owned by:** NW-02.

---

## R5 — Our working method (stated to SWA — agents must keep it true)

What Srujan told SWA, on record: a **hybrid orchestration approach** — he gives strategic direction and protocols to an orchestration agent; it decomposes work into tasks for specialized worker agents that run through the day; he steers rather than micromanages.

**For agents, that means the discipline in `tasks/phase9/00_README.md` is part of the product story:** one task at a time on `phase9-final`, REPORT back with real command output, orchestrator independently verifies (`make verify` + reproduced numbers + gold-provenance check) before anything is committed. Keeping this true is what makes the statement to SWA honest.

---

## R6 — Out of scope here (do not drift)

A second, parallel project exists (ERP for the startup — business-logic implementation, separate ZIP, separate repo). It is **not** part of rfq2boq. Per `CLAUDE.md` §1: any agent tempted to plan or build ERP features in this repo must stop.

---

## Requirement → current status → owner

| Req | Status today | Next action | Who |
|-----|--------------|-------------|-----|
| R1 fidelity | Extraction lossy in places (truncation, dropped rows on 04) | P3_01/P3_03/P3_04 + fidelity audit (P1_02) | agents |
| R2 GeM catalog | Initial 60+ gazetteer integrated | Get SWA's real GeM list → ingest verbatim | **Srujan** asks; agent ingests |
| R3 100 PDFs | 1 extra doc received; pipeline not yet ready | P2_02 builds intake loop; chase documents | **Srujan** + agent |
| R4 structure-first | Implemented; precision + multi-range pending | P3_01 | agent |
| R5 method | Protocol live in tasks/phase9/00_README.md | follow it | everyone |
| R6 ERP | separate project | keep out of this repo | everyone |

*Presentation/speaking versions of these points (for Srujan's own use, not for agents): `tasks/MEETING_VOICES_FINAL.md`.*
