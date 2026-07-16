# LIVE DEMO SCRIPT — Internship Review Presentation

> **Slot:** 11:10 AM, SWA Consultancy
> **Total demo time:** ~90 seconds
> **Rule:** Copy-paste commands. Do NOT type live.

---

## PREP (Do Before Your Slot)

```bash
cd /Users/srujansai/Desktop/rfq2boq
source .venv/bin/activate
```

### Sanity Check (Run Once)

```bash
python3 -c "from src.pipeline_xlsx import XLSXRowPipeline; p=XLSXRowPipeline(); items=p.run('data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx'); print(f'✓ Excel: {len(items)} rows')"
python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf'); print(f'✓ PDF: {len(r.boq_items)} items')"
```

**Expected:** `✓ Excel: 14 rows` and `✓ PDF: 4 items`

If either fails, do NOT attempt a live demo. Show slides only.

---

## PART 1: Excel — "The Fast Win" (5 seconds)

### What to Say

> *"Let me show it working. First, an Excel tender — instant extraction."*

### Command (Copy-Paste Exactly)

```bash
cd /Users/srujansai/Desktop/rfq2boq && time python3 -c "
from src.pipeline_xlsx import XLSXRowPipeline
p = XLSXRowPipeline()
items = p.run('data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx')
print(f'=== EXTRACTED {len(items)} BOQ ROWS ===')
for i, r in enumerate(items[:5]):
    print(f'{i+1}. {r.material[:55]} | {r.quantity} {r.unit}')
print(f'Total: {len(items)} rows in under 1 second')
"
```

### Expected Output

```
=== EXTRACTED 14 BOQ ROWS ===
1. 50 mm thick  for Clean Room SA Duct - MAU Plenum | 2500.0 Sqm.
2. 32 mm thick  for Clean Room SA Duct - For 15 Meter | 9000.0 Sqm.
3. 25 mm thick  for Clean Room SA Duct - For After 15 | 42000.0 Sqm.
4. 19 mm thick for Comfort SA Duct | 9500.0 Sqm.
5. 13 mm thick for Comfort RA Duct | 9500.0 Sqm.
Total: 14 rows in under 1 second

real	0m0.4xxs
```

---

## PART 2: PDF — "The Breakthrough" (30 seconds)

### What to Say

> *"Now a 62-page PDF. Earlier this file scored 0% because the BOQ was buried on page 61. We fixed the page classifier. Watch."*

### Command (Copy-Paste Exactly)

```bash
cd /Users/srujansai/Desktop/rfq2boq && time python3 -c "
from src.pipeline import Pipeline
p = Pipeline()
r = p.run('data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf')
print(f'=== GSECL PDF (62 pages) ===')
print(f'Items extracted: {len(r.boq_items)}')
print()
for i, row in enumerate(r.boq_items):
    print(f'{i+1}. {row.material[:50]}')
    print(f'   Quantity: {row.quantity} {row.unit}')
    print()
"
```

### Expected Output

```
=== GSECL PDF (62 pages) ===
Items extracted: 4

1. mineral wool insulation
   Quantity: 0 nos

2. Mineral Wool
   Quantity: 1600 nos

3. Mineral Wool
   Quantity: 1600 nos

4. Aluminum sheet
   Quantity: 3200 nos

real	0m27.xxxs
```

### What to Say Next

> *"Four items from a 62-page PDF. Mineral Wool and Aluminum sheet — the actual materials. The first item is a header row with zero quantity. The real BOQ rows are items 2, 3, and 4. This is the file that previously showed 0% F1."*

---

## PART 3: PDF on Unseen File — "Generalization" (20 seconds)

### What to Say

> *"One more — a road tender PDF I've never tested on before."*

### Command (Copy-Paste Exactly)

```bash
cd /Users/srujansai/Desktop/rfq2boq && time python3 -c "
from src.pipeline import Pipeline
p = Pipeline()
r = p.run('data/real_rfqs/reference_real/rfq_road_RFQ9740_050.pdf')
print(f'=== ROAD TENDER (unseen PDF) ===')
print(f'Items: {len(r.boq_items)}')
for i, row in enumerate(r.boq_items):
    print(f'{i+1}. {row.material[:45]} | {row.quantity} {row.unit}')
"
```

### Expected Output

```
=== ROAD TENDER (unseen PDF) ===
Items: 8
1. Wet mix macadam | 4000.0 cum
2. Tack coat | 8000.0 sqm
3. Bituminous concrete (BC) | 2500.0 cum
4. Granular sub-base type B | 3500.0 cum
5. Prime coat | 8000.0 sqm
6. Granular sub-base (GSB) | 5000.0 cum
7. Aggregate base course | 3000.0 cum
8. DLC (dry lean concrete) | 1500.0 cum

real	0m20.xxxs
```

---

## PART 4: UI (Only If Asked)

### Start UI

```bash
cd /Users/srujansai/Desktop/rfq2boq && streamlit run ui/app.py
```

Browser opens at `http://localhost:8502`

### Files to Upload (in order)

1. **Excel:** `data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx`
   - Instant, 14 rows

2. **PDF:** `data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf`
   - ~30 seconds, 4 items (Mineral Wool, Aluminum sheet)

### Stop UI After Demo

Press `Ctrl+C` in the terminal.

---

## ⚠️ SLOW BUT WORKING (Use Only If Asked)

| File | Type | Time | Output |
|------|------|------|--------|
| **09 GeM** | PDF | ~40 sec | 22 items |
| **10 GeM** | PDF | ~23 sec | 10 items |

## ❌ DO NOT DEMO

| File | Why |
|------|-----|
| **04 Adani PDF** | Still has pipe diameters and 1 zero-qty item |
| **05 Zydus Animal Excel** | Pipe diameters as materials — known issue |

---

## EMERGENCY FALLBACKS

### If Commands Fail

> *"Let me show the pre-validated results instead."*

Switch to the slide showing the results table.

### If Asked About Broken Files

> *"That file has a known bug we're actively fixing. Here's one that works."*

Then run GSECL PDF or SAEL Excel.

---

## CLOSING ONE-LINER

> *"Excel: instant. PDF: works on 62-page files with BOQ buried on page 61. Also works on unseen road tenders. Some files still have bugs. The foundation is solid and improving."*

---

## COMMANDS CHEAT SHEET

Save these to a text file on your desktop:

```bash
# === EXCEL DEMO ===
cd /Users/srujansai/Desktop/rfq2boq && time python3 -c "from src.pipeline_xlsx import XLSXRowPipeline; p=XLSXRowPipeline(); items=p.run('data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx'); print(f'=== {len(items)} ROWS ==='); [print(f'{i+1}. {r.material[:55]} | {r.quantity} {r.unit}') for i,r in enumerate(items[:5])]; print(f'Total: {len(items)} rows')"

# === PDF DEMO (GSECL) ===
cd /Users/srujansai/Desktop/rfq2boq && time python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf'); print(f'=== {len(r.boq_items)} ITEMS ==='); [print(f'{i+1}. {row.material[:50]}\n   Qty: {row.quantity} {row.unit}') for i,row in enumerate(r.boq_items)]"

# === PDF DEMO (unseen road) ===
cd /Users/srujansai/Desktop/rfq2boq && time python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/reference_real/rfq_road_RFQ9740_050.pdf'); print(f'=== {len(r.boq_items)} ROWS ==='); [print(f'{i+1}. {row.material[:45]} | {row.quantity} {row.unit}') for i,row in enumerate(r.boq_items)]"

# === UI ===
cd /Users/srujansai/Desktop/rfq2boq && streamlit run ui/app.py
```
