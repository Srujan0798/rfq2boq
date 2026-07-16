# ULTRA PLAN — 1 Week, Continuous, 5 Parallel Agent Lanes

**Author:** Claude (orchestrator/planner) — 2026-06-22
**Status:** DRAFT — awaiting Srujan's approval before any task is dispatched
**Branch base:** `phase8-clean-slate` (canonical)
**Execution:** Srujan's OpenCode CLI, multiple parallel agent windows, top model from each of 4 token plans
**Governing docs:** [CLAUDE.md](../CLAUDE.md), [docs/CORE_UNDERSTANDING.md](CORE_UNDERSTANDING.md), [docs/SWA_REQUIREMENTS_2026-06-11.md](SWA_REQUIREMENTS_2026-06-11.md), [docs/PHASE8_UNIFIED_TIMELINE_AND_FLOW.md](PHASE8_UNIFIED_TIMELINE_AND_FLOW.md)

---

## 0. The genuine goal of this week

Turn the brand-new **HVAC insulation corpus** (11 real tenders + 9 real BOQ references + 53 spec PDFs from `Specifications.rar`, received 2026-06-22) into the project's **first independently-verified second domain**, while honestly re-grounding the suspicious "100% on 10 SWA" claim. Every lane serves a locked SWA requirement:

| SWA req | Meaning | Lane that serves it |
|---------|---------|---------------------|
| R1 | 100% data-conversion fidelity (flag, never drop) | Lane E |
| R2 | GeM catalog = authoritative NER reference | Lane D |
| R3 | ~100 real PDFs; annotation loop must be ready | Lane B |
| R4 | Structure-first extraction for large PDFs | Lane C |
| Honesty | Never grade pipeline against itself; ~100% = red flag | **Lane A (gates all)** |

**This is NOT** (per CLAUDE.md §1): SaaS, paper, patent, benchmark, voice, CAD, MLOps theater. Any agent drifting there = stop.

---

## 1. The honesty problem we open the week by fixing

- [COMPLETE_PROJECT_HANDOFF.md](../COMPLETE_PROJECT_HANDOFF.md) claims **100% row-level F1 on the 10 SWA enquiries**.
- [docs/CORE_UNDERSTANDING.md](CORE_UNDERSTANDING.md) + [PHASE8 timeline](PHASE8_UNIFIED_TIMELINE_AND_FLOW.md) say honest is **~32% row / ~0.43 NER F1**, match rate ~1.8–2.8%.
- Commit `c8fc7fa "update honest row-level eval to 100%"` changed **only `results/eval_honest_rows.json`** (10 lines), and the eval shows `gold_material` byte-identical to `pred_material`.
- Project's own rule: *"A sudden ~100% is a red flag to investigate, not celebrate."*

**Verdict:** the 100% is unverified and possibly a gold-poisoning / self-comparison artifact (cheat patterns #3/#4 in the catalog). **Lane A re-derives the truth before anything builds on it.** No headline number is trusted until Lane A's harness passes and Srujan reproduces it.

---

## 2. New asset inventory (sorted & placed)

```
resources/Specifications/                         53 spec PDFs — SACRED, read-only reference (ontology fuel)
data/real_rfqs/raw/insulation_hvac/               11 real tenders/RFQs  → pipeline INPUTS + annotation targets
data/real_rfqs/raw/insulation_hvac/boq_references/ 9 real BOQs         → EXPECTED OUTPUTS (row-gold source)
resources/meeting requirments                     SWA meeting voices (R1–R4 confirmed; ~100 PDF target)
```

Best first annotation pairs (RFQ ↔ expected BOQ, same enquiry):
- `TENDER.pdf` ↔ `boq_references/BOQ.pdf`
- `SWPL-PER-HVAC-RFQ-02 (Thermal & Acoustic Insulation).pdf` ↔ `boq_references/BOQ - INSULATION.pdf`

---

## 3. The 5-lane parallel architecture (disjoint file ownership = no collisions)

The historical rule "ONE agent at a time" existed because parallel agents on a **shared tree deleted gold**. We keep parallelism **safe** by giving every lane its **own git worktree + own lane branch**, and **disjoint file ownership**. Lanes never write the same paths, so merges back to `phase8-clean-slate` are conflict-free. Srujan merges each lane at its checkpoint after reproducing its headline number.

| Lane | Theme | Owns (writes only here) | Model tier | Depends on |
|------|-------|--------------------------|-----------|------------|
| **A** | Anti-cheat & honest baseline (GATE) | `scripts/eval_*`, `tests/unit/test_anti_cheat.py`, `tests/integration/test_self_attack.py`, `results/` | **Strongest / most-trusted reasoning** | none — runs first |
| **B** | Insulation gold + annotation loop | `data/real_rfqs/raw/insulation_hvac/**`, `data/annotations/**`, `scripts/annotate_*`, `data/real_rfqs/gold/rows/insul_*` | Strong | A's harness exists |
| **C** | Structure-first extraction (R4) | `src/ingest/structure_*.py`, `src/ingest/table_extractor.py`, `tests/unit/test_structure_*`, `tests/integration/test_ingest_*` | Strong coding | A's harness exists |
| **D** | Ontology + GeM reference (R2) | `data/ontology/**`, `src/ontology/**`, `config/` gazetteers | Free / lighter (mechanical) | A's harness exists |
| **E** | Pipeline robustness + 100% fidelity (R1) | `src/domain/**`, `src/rules/**`, `src/export/**`, `tests/unit/test_validator.py`, `tests/unit/test_boq_assembler.py` | Strong coding | A's harness exists |

Shared read-only for all: `config/constants.py` (schema — never edit), `resources/**` (sacred), `docs/`.

### Isolation mechanism (post-approval setup)
```
git worktree add ../rfq2boq-laneA -b phase8-laneA phase8-clean-slate
git worktree add ../rfq2boq-laneB -b phase8-laneB phase8-clean-slate
git worktree add ../rfq2boq-laneC -b phase8-laneC phase8-clean-slate
git worktree add ../rfq2boq-laneD -b phase8-laneD phase8-clean-slate
git worktree add ../rfq2boq-laneE -b phase8-laneE phase8-clean-slate
```
One OpenCode window per worktree. Lane branches are short-lived integration branches; Srujan merges verified work to `phase8-clean-slate` at each checkpoint, then the lane rebases. (This is the safe exception to "never create branches" — flagged for approval.)

---

## 4. Per-lane backlog (enough work for a continuous week)

Existing task files in `tasks/` and `prompts/wave4/` map cleanly into lanes — reused, not reinvented.

**Lane A — Anti-cheat & honest baseline**
1. A1 Re-derive 10-SWA row-gold from SOURCE (XLSX cells / PDF text), never from pipeline output; diff vs current gold; document drift. (seed: `tasks/NW01_fix_row_eval_artifacts.md`)
2. A2 Re-run honest row eval + entity eval; publish REAL numbers to `results/` with provenance notes.
3. A3 Harden `tests/unit/test_anti_cheat.py` + `tests/integration/test_self_attack.py`: fail CI if gold provenance == pred, if matcher thresholds lowered, if `if filename ==` hacks, if "100% COMPLETE" claims reappear.
4. A4 Wire the harness into `make verify` as a required gate; document in `docs/`.
5. A5 (continuous) Audit each other lane's merged output against the harness before sign-off.

**Lane B — Insulation gold + annotation (R3, the data lever)**
1. B1 Extract text + tables from 11 insulation tenders + 9 BOQ refs → `data/real_rfqs/extracted/insulation_hvac/`.
2. B2 Stand up the human-in-the-loop annotation loop (seed: `tasks/NW04_annotation_pipeline_for_100pdfs.md`) ready for the ~100 PDFs.
3. B3 Produce **draft** BIOES gold + row-gold for the 2 best RFQ↔BOQ pairs → owner verifies (HUMAN sign-off gate; agent never finalizes gold).
4. B4 Extend to remaining insulation pairs; maintain manifest + provenance.
5. B5 Intake protocol for new tenders (seed: `tasks/NW09_intake_two_new_tenders.md`).

**Lane C — Structure-first extraction (R4)**
1. C1 Structure/outline extractor: titles→sections→annexures; route extraction to BOQ sections only (seed: `tasks/NW02_structure_extractor_precision.md` — kill the 1281 false-positive sections).
2. C2 Merged-cell splitting (seed: `prompts/wave4/AGENT-B1_merged_cells.md`).
3. C3 Header inference (seed: `AGENT-B2_header_inference.md`).
4. C4 PDF timeout/robustness on the larger insulation tenders (seed: `AGENT-B3_pdf_timeout.md`).
5. C5 Validate structure-first on `Tender (2).pdf`/`Tender (4).pdf` (2.4 MB multi-page).

**Lane D — Ontology + GeM reference (R2)**
1. D1 Mine 53 spec PDFs for insulation materials/grades/standards (Nitrile rubber, Rockwool, thermal conductivity, thickness, IS codes) → `data/ontology/` (seed: `prompts/wave4/AGENT-G2_insulation_ontology.md`).
2. D2 Ingest GeM catalog as authoritative gazetteer (seed: `tasks/NW07_ingest_swa_gem_catalog.md`).
3. D3 Wire ontology/gazetteer into NER as reference (no schema changes — `config/constants.py` is locked).
4. D4 Insulation NER reference set for Lane A to evaluate against (seed: `AGENT-G3_ner_retrain_insulation.md` — honest, no synthetic).

**Lane E — Pipeline robustness + 100% fidelity (R1)**
1. E1 Unified unit/qty normalizer shared by pipeline + evaluator (seed: `tasks/NW05_unified_unit_normalizer.md`).
2. E2 Flag-never-drop fidelity: run 11 insulation tenders end-to-end, assert zero silent data loss; flag low-confidence rows.
3. E3 Rate-only row flagging + unit aliases + honest confidence (seeds: `AGENT-F1/F2/F3`).
4. E4 Export validation (seed: `AGENT-F4_export_validation.md`).
5. E5 XLSX gap fixes (seed: `tasks/NW08_fix_zydus_animal_xlsx_gap.md`).

---

## 5. Continuous-week flow (non-stop, hybrid orchestration)

Matches the SWA "hybrid: I steer, agents run autonomously through the day" model.

- **Day 0 (setup, owner):** rebuild venv to 3.12 (currently wrongly 3.14); create 5 worktrees; dispatch Lane A first.
- **Day 0–1:** Lane A produces honest baseline + harness. **Gate:** Srujan reproduces A2 numbers. Only then B–E start in parallel.
- **Day 1–6:** 5 windows run continuously through their backlogs. Each task ends with the 9-section REPORT + real command output. Srujan reproduces the headline number, merges that lane to `phase8-clean-slate`, lane rebases, next task starts.
- **Daily checkpoint:** Lane A (A5) audits all merges against the anti-cheat harness.
- **Day 7:** Integration smoke across all 10 SWA + insulation corpus; honest metrics table; update `docs/wave_status.md` + handoff.

Each lane has ≥5 sequenced tasks → no agent idles. If a lane drains, Srujan pulls the next item from the seed pools in `tasks/`/`prompts/wave4/`.

---

## 6. Anti-cheat gates (every lane inherits — hard rules)

1. **No gold edited to match output.** Gold derives from SOURCE (XLSX cell / PDF text / human). Provenance recorded per row.
2. **No matcher threshold lowering, no `if filename ==` hacks, no hardcoded confidences.**
3. **~100% / sudden perfect score = STOP and investigate, not celebrate.**
4. **Never grade the pipeline against its own output.** Independent gold only.
5. **No "100% COMPLETE" claims in docs/results** (CI greps for it).
6. **HUMAN sign-off on all new gold** (Lane B drafts; Srujan verifies ≥5 random rows vs source).
7. **Report both** synthetic and real metrics, honestly.
8. **Scope guard:** nothing from CLAUDE.md §1 "is NOT" list.
9. **Schema locked:** `config/constants.py` (8 entities / 6 relations / BIOES) — read-only.
10. **No new branches except the 5 lane branches**; no synthetic data in `data/`.

Each 9-section task prompt repeats the relevant subset in CONSTRAINTS + GOTCHAS.

---

## 7. Model → lane mapping (RECOMMENDED — confirm exact model per plan)

Srujan's 4 token plans: **Xamoni**, **MiniMax**, **OpenCode (paid)**, **OpenCode free (4.5-class)**. Assign the strongest model to the integrity + reasoning-heavy lanes:

| Lane | Difficulty | Recommended plan (top model of that plan) |
|------|-----------|-------------------------------------------|
| A (integrity, gates all) | highest reasoning | strongest plan available |
| B (gold/annotation) | high judgement | strong plan |
| C (structure extraction) | strong coding | strong plan |
| E (pipeline/fidelity) | strong coding | strong plan |
| D (ontology mining) | mechanical | free / lighter model |

> ⚠️ Confirm the actual top model in each plan — I can't read your OpenCode account. Tell me the 4 model IDs and I'll pin each lane.

---

## 8. Owner-only (agents cannot do these)

1. **Rebuild venv to 3.12** (charter pins 3.11–3.13; venv is on 3.14): `python3.12 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`.
2. **Create the 5 worktrees** (Day 0).
3. **Reproduce each lane's headline number** before merging.
4. **HUMAN gold sign-off** (Lane B, and the disputed 03 Zydus / 09-10 GeM gold).
5. **Confirm the 4 model IDs** for the mapping.
6. **Chase the ~100 PDFs** (Sales / Jineth / Softnil) — the real F1 lever.

---

## 9. Approval gate

Nothing is dispatched until Srujan approves. On approval, Claude generates the **9-section task prompts** ([prompts/TASK_TEMPLATE.md](../prompts/TASK_TEMPLATE.md)) for the Day-0/Day-1 tasks (A1–A4 first, then B1/C1/D1/E1), one file per task under `tasks/lane_<X>/`, ready to paste into each OpenCode window.
