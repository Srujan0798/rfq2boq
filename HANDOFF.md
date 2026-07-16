# HANDOFF.md — RFQ2BOQ Project

**Last updated:** 2026-07-16 (fidelity restore: UBS + short-BOQ pages; measured audit)

---

## Where to start

| Audience | Start here |
|----------|------------|
| **SWA / client closeout** | [`deliverables/PROJECT_CLOSEOUT_HANDOFF.md`](deliverables/PROJECT_CLOSEOUT_HANDOFF.md) + [`deliverables/SWA_HANDOFF_GUIDE.md`](deliverables/SWA_HANDOFF_GUIDE.md) |
| **Maintainers / agents** | [`tasks/phase9/00_README.md`](tasks/phase9/00_README.md) (engineering plan) + this file |

GitHub **`main`** is the submission branch. Local long history is for developers only.

---

## Project at a glance

RFQ2BOQ converts construction tender RFQs (PDF/XLSX) into structured Bill of Quantities (unpriced Excel + JSON). Built for SWA Consultancy (insulation contractor).

**Pipeline:** `PDF/OCR → preprocess → NER → relation extraction → rules/ontology → BOQ assembly → export`

**Honest metrics (re-measured 2026-07-16 via `scripts/audit_fidelity_per_doc.py --all`):**
- Sacred-10 **independent fidelity auditor** (`results/fidelity/summary.json`): **10/10 PASS** (incl. `08_sael` 16/16)
- Broader BOQ-bearing corpus (same auditor): **33/33 PASS** (re-verified full `--all` 2026-07-16)
- Residual FAILs (missing rows, hard multi-column compliance PDFs): `BOQ- Insulation_Compliance` (9/13), `Copy of BOQ` (11/19), `Insulation Boq (2)` (20/29)
- Notable restore: `Copy of UBS_Hyderabad_Project_BOQ(1)` **25/25 PASS** (was 9/25 after over-filter)
- Gold/completeness report (`results/FIDELITY_REPORT.md`, `measure_fidelity.py`): sacred-10 **0 silent drops** when low-confidence rows count as flagged — **completeness ≠ content F1**
- Product row-match (`results/PRODUCT_EVAL.md`, 2026-07-16): **82.5%** (66/80) on four XLSX enquiries
- Real NER F1: ~0.43 (pattern-based; needs human-annotated training data)
- Owner-verified BIOES sentences: **0** for the retrain gate (Desktop-repo “198 verified” stamps were forged; not trusted)

**The core problem:** NER was trained on regex-auto-generated labels from academic papers, not real tenders. Fix = real human-annotated tender gold (Phase 2 tasks).

---

## Repo layout

| Path | What |
|------|------|
| `tasks/phase9/` | **Active plan** — the only dispatch source |
| `src/` | Production code (pipeline, NER, BOQ assembly, export) |
| `config/` | Settings + constants (entities, relations, BIOES) — locked |
| `data/real_rfqs/` | 127 real RFQ documents (corpus) |
| `data/real_rfqs/gold/` | Gold annotations (owner-only) |
| `tests/` | Unit, integration, regression, e2e tests |
| `scripts/` | Train, evaluate, audit, intake scripts |
| `ui/` | Streamlit UI |
| `docs/` | Architecture, conventions, SWA requirements |
| `results/` | Current evaluation outputs and fidelity reports |
| `archive/` | Legacy files (moved via git mv, history preserved) |
| `deliverables/` | Internship report + handoff docs |
| `resources/` | **SACRED** — SWA-provided materials, never move |

---

## Quick commands

```bash
make verify          # CI gate: lint + typecheck + tests
make test            # Run test suite
make lint            # Ruff lint
PYTHONPATH=. python3.12 scripts/measure_fidelity.py --all   # Fidelity numbers
```

---

## Anti-cheat rules

See `tasks/phase9/02_ANTI_CHEAT_PROTOCOL.md` — distilled from 13+ integrity incidents. Non-negotiable. Key points:
1. Numbers come from commands, not reports
2. Never grade the pipeline against its own output
3. Gold is owner-only (no agent stamps)
4. Eval scripts and thresholds are frozen (P0_03)

---

## History

All superseded docs, tasks, prompts, and reports are in `archive/` — see `archive/README.md` for the full mapping of what was archived and what replaced it.
