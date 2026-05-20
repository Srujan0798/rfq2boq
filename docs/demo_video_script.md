# Demo Video Script — RFQ2BOQ

**Duration:** 3–5 minutes | **Audience:** Construction estimators, project managers, SWA Consultancy clients

---

## Scene 1 — Intro (30 seconds)

**[On screen: RFQ2BOQ UI with logo, clean dark theme]**

**Narration:**
> "Every construction project starts with a tender document — a PDF full of specifications, quantities, and material requirements. Extracting all of that into a usable Bill of Quantities manually takes hours and is error-prone.
>
> RFQ2BOQ automates this. You upload a tender PDF, and within seconds you get a structured BOQ ready for review and export."

**[B-roll: slow pan over a sample tender PDF]**

---

## Scene 2 — Upload & Extract (60 seconds)

**[On screen: Streamlit UI — drag-drop zone highlighted]**

**Narration:**
> "Let's walk through it. Here is a real CPWD tender — a residential building project with foundation, RCC, masonry, and finishing items."

**[Click: upload PDF]**

> "We upload the PDF. The system reads every page, extracts text and tables, then runs our NLP pipeline to identify entities — materials, quantities, units, grades, standards — all labeled and normalized."

**[Show: extracted entities list appearing]**

> "In under a minute, we have 47 items extracted with confidence scores. Green means high confidence — these look right. Yellow means review recommended. Red means manual verification needed."

---

## Scene 3 — Review & Edit (60 seconds)

**[On screen: Editable BOQ table — click to edit a cell]**

**Narration:**
> "The extracted BOQ is fully editable. If the estimator wants to correct a quantity or change a unit, they click the cell and type. No separate tool needed."

**[Click: edit quantity from "500" to "480"]**

> "Here, a quantity was slightly off — we correct it inline. The changes are reflected in the Excel export automatically."

**[Show: edit confirmed, amount recalculates]**

> "And notice — we match each item against official CPWD DSR rates wherever possible. So if this cement matches DSR item 1.1.1, the official rate is used instead of an estimate."

---

## Scene 4 — Export (45 seconds)

**[On screen: Download buttons — Excel, JSON, CSV highlighted]**

**Narration:**
> "When the review is done, export in one click. The Excel export follows CPWD format — grouped by trade, with subtotals, grand total, and GST calculated. Ready to submit."

**[Click: Download Excel → file saves]**

> "The exported BOQ has everything an estimator needs: DSR codes, descriptions, units, quantities, rates, and amounts — all formatted professionally."

---

## Scene 5 — Conflict Resolution (60 seconds)

**[On screen: Side-by-side comparison — old vs new resolution]**

**Narration:**
> "Now let me show you something that makes our approach different from generic NER tools. When our BERT model and our rule-based patterns both find an entity — like this dimension — they sometimes disagree on what's correct."

**[Show: BERT says "12", pattern says "12mm"]**

> "Our conflict resolution system handles this. For dimensions and grades, it picks whichever source has higher confidence. For quantities, units, and standards — rules win if confidence is above 0.7. For materials, locations, and actions — the BERT model wins if confidence is above 0.6."

**[Show: resolution decision explained with color coding]**

> "This hybrid approach is what makes our system work well on real Indian construction documents — where pure ML models struggle with domain-specific terminology like 'cum', 'sqm', 'IS 2062', or 'Fe500D'."

---

## Scene 6 — Closing (30 seconds)

**[On screen: Summary — 47 items extracted, 3 exports ready, 2 flagged for review]**

**Narration:**
> "RFQ2BOQ turns hours of manual extraction into a 2-minute automated process. It handles real Indian construction documents — CPWD tenders, MES schedules, state PWD RFQs.
>
> Built with hybrid ML + rules, calibrated for Indian construction language. Export to Excel in CPWD format, or JSON for further processing."

**[Show: final dashboard view]**

> "Try it at rfq2boq.swa-consultancy.com — or contact SWA Consultancy for a demo."

**[End card: SWA Consultancy logo + contact]**

---

## Filming Notes

| Scene | Duration | Key UI Elements | Notes |
|-------|----------|-----------------|-------|
| 1 | 30s | Logo, dark theme | Keep minimal |
| 2 | 60s | Upload zone, extraction progress | Real PDF recommended |
| 3 | 60s | Editable table, cells | Show actual correction |
| 4 | 45s | Download buttons | Show file save |
| 5 | 60s | Conflict resolution overlay | Show before/after |
| 6 | 30s | Summary dashboard | Clear CTA |

**Total: ~4–5 minutes**

**Tips:**
- Use a real (not synthetic) tender PDF for authenticity
- Keep camera steady — no zooms during narration
- Record narration separately (better audio quality)
- Export first, then re-record scenes that feel slow