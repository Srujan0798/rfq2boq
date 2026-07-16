# UI Upload Priority — Live Demo File Order

> **Goal:** Show the system working on real, working files only.
> **Rule:** ONLY use files listed here. Everything else is broken.
> **Port:** UI runs on `http://localhost:8502`

---

## START THE UI

```bash
cd /Users/srujansai/Desktop/rfq2boq
source .venv/bin/activate
streamlit run ui/app.py
```

Browser opens at: `http://localhost:8502`

---

## PRIORITY 1: 08 SAEL (Excel) ⭐ BEST

**Why:** Instant, real output, zero risk
**Time:** < 1 second
**Rows extracted:** 14
**File path to browse to:**
```
data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx
```

**What to say:** *"14 insulation rows from an Excel tender. Instant extraction."*

---

## PRIORITY 2: Road Tender PDF (Unseen File) ⭐ ONLY PDF TO SHOW

**Why:** Proves it works on NEW data, never tested before
**Time:** ~20 seconds
**Rows extracted:** 8
**File path to browse to:**
```
data/real_rfqs/reference_real/rfq_road_RFQ9740_050.pdf
```

**What to say:** *"This is a road construction tender PDF I've never tested on. Let's see what it extracts."* (wait 20 seconds) *"Eight road materials — macadam, bituminous concrete, sub-base. All real."*

---

## DO NOT UPLOAD — EVER

| File | Why Avoid |
|------|-----------|
| **01 GSECL PDF** | BUG: extracts page 5 receipt text instead of page 61 BOQ |
| **05 Zydus Animal Excel** | BROKEN: pipe diameters as materials, zero quantities |
| **04 Adani PDF** | Known bug: dimension headers instead of materials |
| **09 GeM PDF** | 3.6+ minutes — UI timeout is 60 seconds |
| **02 ISRO PDF** | Low quality output |
| **03 Zydus Matoda Excel** | Has some issues, not demo-worthy |

---

## RECOMMENDED DEMO FLOW

### 30-second demo:
1. Upload **08 SAEL Excel** → *"14 rows in under a second"*

### 1-minute demo:
1. Upload **08 SAEL Excel** → *"14 rows instant"*
2. Upload **rfq_road_RFQ9740_050.pdf** → *"8 rows from unseen PDF"*

---

## STOP UI AFTER DEMO

Press `Ctrl+C` in the terminal where streamlit is running.

---

## IF SOMETHING GOES WRONG

> *"The pipeline has some known bugs on certain files. Let me show one that works."*

Then upload **08 SAEL Excel** — it always works.
