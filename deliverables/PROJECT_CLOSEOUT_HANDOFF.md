# RFQ2BOQ — Full Project Closeout Handoff

**Date:** 2026-07-16  
**Author:** Choda Srujan Sai (IIT Gandhinagar · Roll No. 23110081)  
**Mentor:** Dr. Sudish Mishra  
**Organization:** SWA Consultancy Pvt. Ltd.  
**Status:** Internship / project **closing** — product + documentation handed over

---

## 1. What this is

**RFQ2BOQ** turns construction tender **RFQ** documents (PDF / Excel) into structured **unpriced BOQ** (Excel + JSON).

Built for SWA’s insulation / mechanical tender workflow.

**Pipeline:**

```text
PDF/Excel → structure routing → extraction (rules + gazetteer + optional NER assist)
  → GeM catalog checks → BOQ assembly → fidelity flags → Excel/JSON export
```

**Scope (locked):** unpriced BOQ only — no rate/amount lookup, no pricing engine.

---

## 2. Where the code lives (submit / continue from here only)

| Item | Value |
|------|--------|
| **GitHub** | https://github.com/Srujan0798/rfq2boq |
| **Branch to use** | **`main`** |
| **Latest release tag** | `v0.1.1-final-closeout` |
| **Latest release commit** | `2b5b237` |
| **Clone** | `git clone https://github.com/Srujan0798/rfq2boq.git && cd rfq2boq` |

Do **not** use empty Desktop folders or ad-hoc zip packs. Everything required is in this repository under `deliverables/` and the app sources.

---

## 3. Deliverables checklist (in-repo)

All under `deliverables/`:

| File | Purpose |
|------|---------|
| `Internship_Project_Report.pdf` | Main internship report (also `.md` / `.docx`) |
| `SWA_HANDOFF_GUIDE.md` | Day-to-day runbook for SWA (setup, run, fidelity, annotation) |
| `PROJECT_CLOSEOUT_HANDOFF.md` | **This file** — full closeout summary |
| `internship_certificate.jpg` | Offer / acceptance image |
| `signature.jpg` / `signature_clean.png` / `buddy_signature.png` | Signature assets |
| `demo_live.py` | CLI demo without UI |
| `generate_docx.py` | Rebuild report DOCX from Markdown (maintainer) |

Also read:

- `docs/CORE_UNDERSTANDING.md` — grounded problem statement  
- `docs/SWA_REQUIREMENTS_2026-06-11.md` — requirements  
- Root `README.md` — metrics + quick start  
- Root `HANDOFF.md` — engineering notes for maintainers  

---

## 4. How to run (quick)

```bash
git clone https://github.com/Srujan0798/rfq2boq.git
cd rfq2boq
python3.12 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
PYTHONPATH=. python3.12 -c "from src.pipeline import Pipeline; print('OK')"
PYTHONPATH=. python3.12 -m streamlit run ui/app.py
# → http://localhost:8501
```

CLI:

```bash
PYTHONPATH=. python3.12 deliverables/demo_live.py "path/to/tender.pdf"
```

**Python:** 3.11–3.13 only (not 3.14).

---

## 5. What works well / what does not (honest)

### Strong today
- Table-driven **XLSX** and structured **PDF** BOQs  
- End-to-end UI: upload → extract → review flags → export  
- GeM catalog validation (flag non-catalog materials)  
- Fidelity audit tooling (`scripts/audit_fidelity_per_doc.py`)  
- Anti-cheat / integrity rules for evaluation  

### Weaker / open
- Hard free-text / multi-layout insulation PDFs still need human review of flags  
- **Production NER = pattern + gazetteer**; ML NER is experimental and **not** production  
- Domain NER F1 on real free-text ~**0.43** until real human gold exists  
- **Owner-verified BIOES training set for retrain gate: still effectively 0 trusted stamps**  

### Honest metrics (do not invent “100% NER”)
- Product row-match sample (XLSX): ~**82%** (`results/PRODUCT_EVAL.md`)  
- Completeness harness can report 0 **silent drops** when uncertain rows are **flagged** — that is **not** the same as perfect description match  
- Re-run audits after any code change; never grade the pipeline against its own output  

---

## 6. What SWA should do next (priority order)

1. **Day-to-day:** run Streamlit UI; always check **Flag Review** panel.  
2. **Accuracy path:** human-review annotation queue → 1000+ verified sentences → retrain NER (`SWA_HANDOFF_GUIDE.md` §5).  
3. **Quality gate:** after changes, `PYTHONPATH=. python3.12 scripts/audit_fidelity_per_doc.py --all`.  
4. **Intake:** new RFQs into `data/` per `docs/INTAKE_PROTOCOL.md` when used.  

Without human-verified training data, **code churn will not unlock literature-level NER**.

---

## 7. Repository map (short)

| Path | Role |
|------|------|
| `src/` | Pipeline, PDF/XLSX extractors, BOQ assembly, export |
| `ui/` | Streamlit app |
| `config/` | Locked entity/relation schema |
| `data/real_rfqs/` | Real tender corpus |
| `data/ontology/` | GeM + materials/units gazetteers |
| `scripts/` | Audit, train, annotation factory |
| `tests/` | Unit / integration / regression |
| `results/` | Fidelity and eval artifacts |
| `resources/` | **Sacred** SWA materials — do not move/delete |
| `deliverables/` | Reports, handoff, this closeout |

---

## 8. Integrity rules (non-negotiable)

1. Numbers come from **commands**, not marketing claims.  
2. Never evaluate against gold the pipeline itself produced.  
3. Only humans stamp training gold as verified.  
4. Unpriced BOQ only — no invented rates.  

Details: `tasks/phase9/02_ANTI_CHEAT_PROTOCOL.md`, `docs/CORE_UNDERSTANDING.md`.

---

## 9. Contacts

| Role | Name |
|------|------|
| Author | Choda Srujan Sai |
| Mentor | Dr. Sudish Mishra |
| Org | SWA Consultancy Pvt. Ltd. |

---

## 10. Closeout statement

This project is **handed over** as:

- A **working RFQ→BOQ tool** (UI + CLI + exports)  
- **Documented** setup, limits, and next steps  
- **Internship deliverables** in `deliverables/`  
- **Canonical source** on GitHub **`main`**

Further accuracy work is **data-led** (annotation + retrain), not a greenfield rebuild.

**End of closeout handoff.**
