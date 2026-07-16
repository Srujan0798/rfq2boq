# FINAL PREP CHECKLIST — Presentation at 11:10 AM

## Time Remaining: ~4 hours

---

## ✅ READY — Open Browser and Test

### 1. Presentation Slides
```bash
open deliverables/slides/Internship_Review_Presentation.html
```
- 12 slides, dark theme
- Navigate with → arrow key or space
- F11 for fullscreen

### 2. Speaker Notes
```bash
open deliverables/slides/SPEAKER_NOTES.md
```
- What to say on each slide
- Q&A answers pre-loaded
- Demo commands included

### 3. Demo Script
```bash
open deliverables/slides/DEMO_SCRIPT.md
```
- Copy-paste commands only
- Expected output shown
- Emergency fallbacks included

---

## ✅ WHAT WORKS (Verified This Session)

| File | Type | Time | Output | Status |
|------|------|------|--------|--------|
| 08 SAEL | Excel | <1 sec | 14 rows | ✅ Demo-ready |
| 01 GSECL | PDF | ~27 sec | 4 items (Mineral Wool, Aluminum) | ✅ Demo-ready |
| Road RFQ9740 | PDF (unseen) | ~20 sec | 8 items | ✅ Demo-ready |
| 03 Zydus Matoda | Excel | <1 sec | 33 rows | ✅ Fixed |
| 04 Adani | PDF | ~3 sec | 16 items | ⚠️ Improved, not demo-worthy |

---

## ⚠️ SLOW BUT WORKING

| File | Type | Time | Output |
|------|------|------|--------|
| 09 GeM | PDF | ~40 sec | 22 items |
| 10 GeM | PDF | ~23 sec | 10 items |

## ❌ DO NOT DEMO

| File | Why |
|------|-----|
| 04 Adani PDF | Still has pipe diameters and 1 zero-qty item |
| 05 Zydus Animal Excel | Pipe diameters as materials |

---

## 🎯 RECOMMENDED 90-SECOND DEMO

**Part 1 — Excel (5 seconds):**
```bash
cd /Users/srujansai/Desktop/rfq2boq && source .venv/bin/activate && time python3 -c "from src.pipeline_xlsx import XLSXRowPipeline; p=XLSXRowPipeline(); items=p.run('data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx'); print(f'=== {len(items)} ROWS ==='); [print(f'{i+1}. {r.material[:55]} | {r.quantity} {r.unit}') for i,r in enumerate(items[:5])]; print(f'Total: {len(items)} rows')"
```

**Part 2 — GSECL PDF (30 seconds):**
```bash
cd /Users/srujansai/Desktop/rfq2boq && time python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf'); print(f'=== GSECL: {len(r.boq_items)} items from 62 pages ==='); [print(f'{i+1}. {row.material[:50]}\n   Qty: {row.quantity} {row.unit}') for i,row in enumerate(r.boq_items)]"
```

**Part 3 — Unseen Road PDF (20 seconds):**
```bash
cd /Users/srujansai/Desktop/rfq2boq && time python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/reference_real/rfq_road_RFQ9740_050.pdf'); print(f'=== ROAD: {len(r.boq_items)} items ==='); [print(f'{i+1}. {row.material[:45]} | {row.quantity} {row.unit}') for i,row in enumerate(r.boq_items)]"
```

---

## 🗣️ KEY TALKING POINTS

> **Opening:** "I have two numbers: 44% and 100%. Entity F1 is 44%. Row-level F1 on the same files is 100%. The pipeline was correct; the metric was wrong."

> **GSECL:** "This 62-page PDF had its BOQ on page 61. Our old classifier only looked at the first 30 pages and found a receipt on page 5. We fixed it — now it extracts all pages for large PDFs and finds the real BOQ."

> **Closing:** "Excel: instant. PDF: works on 62-page files and unseen road tenders. Structure-aware extraction and GeM catalog integration are next. The foundation is solid."

---

## 📋 PRE-PRESENTATION CHECKLIST

- [ ] `cd /Users/srujansai/Desktop/rfq2boq && source .venv/bin/activate`
- [ ] Run sanity check commands (above)
- [ ] Open presentation HTML in browser
- [ ] Copy demo commands to a text file on desktop
- [ ] Close all other browser tabs / notifications
- [ ] Have speaker notes open on second screen or phone

---

## 🚨 IF SOMETHING BREAKS DURING DEMO

> *"Let me show the pre-validated results instead."*

Then click to Slide 5 (Honest Metrics) or Slide 6 (10 Files table).

---

## 📊 CURRENT PROJECT STATUS

| Metric | Value |
|--------|-------|
| Tests | 97/97 passed |
| Lint | Clean |
| Git | Clean (all committed) |
| CI Gate | `make verify` passes |
| Critical Bugs Fixed This Session | GSECL page classifier, Adani dedup, UI routing |
| Remaining Bugs | 09 GeM speed, 04 Adani pipe diameters |
| Next Big Feature | Structure-aware PDF extraction |

---

**You're ready. The product works on real files. Go show them.**
