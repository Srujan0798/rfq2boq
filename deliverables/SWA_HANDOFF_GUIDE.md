# RFQ2BOQ — Project Handoff Guide for SWA Consultancy

**Prepared by:** Choda Srujan Sai (Internship Project)
**Date:** 14-07-2026
**Purpose:** Complete setup, architecture, and continuation guide so SWA's team can run, maintain, and extend this project after the internship ends.

---

## 1. What This Project Does

Converts construction tender RFQ documents (PDF/Excel) into structured, unpriced Bills of Quantities (BOQ) — output as Excel + JSON. Built specifically for SWA's tender-processing workflow (insulation/mechanical contracting).

**Pipeline:** `PDF/Excel → structure-first section routing → entity extraction (rule-based + pretrained NER assist) → GeM catalog validation → BOQ assembly → fidelity audit → Excel/JSON export`

---

## 2. One-Time Setup (New Machine)

This runs on Windows, macOS, or Linux — plain Python, no OS-specific dependencies. Development happened on macOS, but nothing here requires it.

**Windows (Command Prompt or PowerShell):**
```bat
:: 1. Clone the repository (default branch: main)
git clone https://github.com/Srujan0798/rfq2boq.git
cd rfq2boq

:: 2. Install Python 3.11-3.13 from python.org (NOT 3.14 -- known typer/click bug)
py -3.12 -m venv venv
venv\Scripts\activate

:: 3. Install dependencies
pip install -r requirements.txt
:: If requirements.txt is absent, minimum needed:
pip install streamlit pandas pdfplumber openpyxl transformers torch pydantic

:: 4. Verify install
set PYTHONPATH=.
python -c "from src.pipeline import Pipeline; print('OK')"
```

**macOS / Linux:**
```bash
# 1. Clone the repository (default branch: main)
git clone https://github.com/Srujan0798/rfq2boq.git
cd rfq2boq

# 2. Install Python 3.11–3.13 (NOT 3.14 — known typer/click bug)
python3.12 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
# If requirements.txt is absent, minimum needed:
pip install streamlit pandas pdfplumber openpyxl transformers torch pydantic

# 4. Verify install
PYTHONPATH=. python3.12 -c "from src.pipeline import Pipeline; print('OK')"
```

---

## 3. Running the App (Daily Use)

**Windows:**
```bat
cd rfq2boq
venv\Scripts\activate
set PYTHONPATH=.
python -m streamlit run ui/app.py
```

**macOS / Linux:**
```bash
cd rfq2boq
source venv/bin/activate
PYTHONPATH=. python3.12 -m streamlit run ui/app.py
```

Either way, this opens at `http://localhost:8501`. Upload any tender PDF/Excel → get BOQ output (Excel/JSON/CSV) + a Flag Review panel showing every uncertain row.

**Command-line alternative** (no UI):
```bash
# Windows: set PYTHONPATH=. first, then run
python deliverables/demo_live.py "path/to/your/tender.pdf"

# macOS/Linux:
PYTHONPATH=. python3.12 deliverables/demo_live.py "path/to/your/tender.pdf"
```

---

## 4. Checking Extraction Quality (Fidelity Audit)

This is the tool that PROVES nothing gets silently dropped — compares pipeline output against a verified source row count per document.

```bash
# Windows (after venv\Scripts\activate and set PYTHONPATH=.):
python scripts/audit_fidelity_per_doc.py --all

# macOS/Linux (after source venv/bin/activate):
PYTHONPATH=. python3.12 scripts/audit_fidelity_per_doc.py --all
```
Output: `results/fidelity/summary.json` + per-document `.audit.md` reports.

**Current honest status (closeout 2026-07-16):** independent fidelity auditor reports in `results/fidelity/` show strong coverage on the BOQ-bearing set (see `summary.json` after `audit_fidelity_per_doc.py --all`). Sacred-10 is aligned including `08_sael` (16/16). Product row-match on sample XLSX enquiries is ~82% (see `results/PRODUCT_EVAL.md`). A separate completeness report (`results/FIDELITY_REPORT.md`) can show 0 silent drops when low-confidence rows count as **flagged** — treat that as completeness accounting, **not** perfect content F1. NER is still pattern-based (~0.43 F1 on real free-text); large NER gains need human-verified training data (§5). Always re-measure after changes — never invent scores.

---

## 5. The Data Foundation — What SWA's Team Needs to Do Next

**This is the single most important next step.** The pipeline currently uses rule-based extraction (regex + dictionary) plus a generic (non-domain-trained) pretrained NER assist. To reach higher accuracy, it needs a domain-trained model — which requires **human-verified annotated data**.

### What's already prepared:
- 127 real tender documents collected and organized (`data/real_rfqs/`)
- 32,933 candidate training sentences already auto-drafted, waiting for human review
- A review tool built specifically for this:

```bash
# Windows (after venv\Scripts\activate and set PYTHONPATH=.):
python scripts/annotation_factory.py review --queue

# macOS/Linux (after source venv/bin/activate):
PYTHONPATH=. python3.12 scripts/annotation_factory.py review --queue
```

### What SWA's team does:
1. Run the review command above (or ask a developer to wire it into a simpler review UI if preferred)
2. For each candidate sentence, a domain expert (someone who knows what a correct BOQ looks like) confirms or corrects the suggested entity tags (MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE)
3. Target: 1,000+ verified sentences minimum for a first real training pass
4. Once verified data crosses that threshold, retrain:
```bash
# Windows:
python scripts/train_ner.py --data data/annotations/verified/

# macOS/Linux:
PYTHONPATH=. python3.12 scripts/train_ner.py --data data/annotations/verified/
```
5. Re-run the fidelity audit to measure real improvement — compare honestly against the current baseline, never against the pipeline's own prior output (see `docs/CORE_UNDERSTANDING.md` for why this matters).

**Without this step, accuracy will not improve — this is a data problem, not a code problem.**

---

## 6. Repository Map

| Path | What it is |
|---|---|
| `src/` | Production pipeline code |
| `config/` | Locked schema (entities, relations, tagging scheme) — do not change without understanding downstream impact |
| `data/real_rfqs/` | 127 real tender documents — the corpus |
| `data/ontology/` | GeM catalog + materials/standards/units gazetteers |
| `data/annotations/` | Training data (draft + verified) |
| `scripts/` | All CLI tools — audit, training, annotation review |
| `ui/` | Streamlit app (what you interact with daily) |
| `tests/` | Automated test suite — run before trusting any change |
| `docs/` | Architecture and requirements documentation — **read `docs/CORE_UNDERSTANDING.md` first** |
| `deliverables/` | This guide, the internship report, and presentation materials |
| `resources/` | SWA-provided source materials — never move or delete |

---

## 7. GitHub / Branch Status (as of 16-07-2026)

- **Use branch `main`:** this is the submission package on GitHub — clone, run, and hand over from `main`.
- **Contents on `main`:** application code, tests, docs, corpus/metadata that is tracked in git, and the full `deliverables/` pack (report PDF/MD, handoff guides, certificate image, signatures).
- **Note:** Local developer machines may keep longer experimental history. That does not affect SWA day-to-day use: **clone `main`, follow §2–§3 above.**

---

## 8. Key Documents to Read (in order)

1. `docs/CORE_UNDERSTANDING.md` — the grounded truth about where this project stands
2. `docs/SWA_REQUIREMENTS_2026-06-11.md` — the locked client requirements this was built against
3. `CLAUDE.md` (repo root) — full project charter and scope boundaries
4. This document, for day-to-day operation

---

## 9. Contacts / Ownership

- **Project author:** Choda Srujan Sai (IIT Gandhinagar, Roll No. 23110081)
- **Mentor:** Dr. Sudish Mishra
- **Organization:** SWA Consultancy Pvt. Ltd.

For technical continuation, any Python developer familiar with NLP pipelines can pick this up using this guide + the docs listed above. The codebase has full test coverage and inline documentation to support a smooth handover.
