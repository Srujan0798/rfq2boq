# Source-Truth Worksheets — manual transcription evidence (P1_01)

> **Purpose:** human-readable row listings transcribed from SOURCE documents
> (never from pipeline output — Rule 2). The owner can spot-check any doc
> against the source file in <5 minutes. D4 exclusions are recorded separately.

---

## 06_avante_kirloskar_pune (36 rows)

**Source:** `data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Boq_132.pdf`
**Method:** manual transcription via pdfplumber (p1-p2 BOQ table)
**D4 exclusions (5 section-title parents):** 76, 79, 80, 81, 82 (title-only, no qty/unit)

| # | item_no | description (first 60 chars) | qty | unit |
|---|---------|------------------------------|-----|------|
| 1 | #REF! | 13 mm thick insulation for supply air ducts in return air | 6163 | sq.m |
| 2 | #REF! | 19 mm thick insulation for return air ducts. | 576 | sq.m |
| 3 | #REF! | 25 mm thick insulation for supply duct (not in RA path). | RO | sq.m |
| 4 | #REF! | 25 mm thick insulation for supply & return air ducts exp | RO | sq.m |
| 5 | 75 | 25 mm thick insulation for ducts exposed to atmosphere wi | 3443 | sq.m |
| 6 | 76.1 | 15 mm thick | 2664 | sq.m |
| 7 | 77 | Supplyandinstallationof acousticliningofwallsofmechani | RO | Nos. |
| 8 | 77.1 | 15 mm thick acoustic lining with Nitrile Rubber | 9351 | Sq.m. |
| 9 | 78 | Supply, installation of acoustic enclosure for Axial flow | RO | Nos. |
| 10-14 | 79.1-79.5 | 25/20/15/50/25 mm dia condensate drain pipes | various | RM |
| 15-20 | 80.1-80.6 | 100/80/65/50/40/32 mm dia pipes | various | RM |
| 21-30 | 81.1-81.10 | 400/300/250/200/150/125/600/500/450/350 mm dia pipes | various | RM |
| 31-36 | 82.1-82.6 | 300/250/200/150/600/500 mm dia pipes | various | RM |

**NOTE:** P0_01 fidelity baseline used 31 source rows (from gold). Independent transcription finds 36. This discrepancy is OWNER-DECISION-NEEDED: the gold rowgold may undercount by 5 (the #REF! parent items), or the independent count includes rows that gold deliberately excludes. Both counts recorded.

---

## 07_grew_solar_narmadapuram (11 rows)

**Source:** `data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf`
**Method:** manual transcription via pdfplumber (p1)
**D4 exclusions (3 section titles):** 11 THERMAL INSULATION, 12 ACOUSTIC LINING header, 8 S.I.T.C. header

| # | item_no | description (first 60 chars) | qty | unit |
|---|---------|------------------------------|-----|------|
| 1 | 11.1 | 32 mm thick for Clean Room SA Duct | 15000 | Sqm. |
| 2 | 11.2 | 25 mm thick for Clean Room SA Duct | 23750 | Sqm. |
| 3 | 11.3 | 19 mm thick for Comfort SA Duct | 8500 | Sqm. |
| 4 | 11.4 | 13 mm thick for Comfort RA Duct | 5000 | Sqm. |
| 5 | 12 | Supply, Installation and Testing of Accoustic lining... | 500 | Sqm. |
| 6 | 8.1 | 75 mm thick Insulation on 1200NB to 1000NB | 1976 | Sq. Mtr. |
| 7 | 8.2 | 51 mm thick Insulation on 950NB to 500NB | 3600 | Sq. Mtr. |
| 8 | 8.3 | 38 mm thick Insulation on 450NB to 80NB | 14800 | Sq. Mtr. |
| 9 | 8.4 | 19 mm thick Insulation on 65NB / 50NB / 40NB / 32NB / 25NB / 20NB / 15NB | 7400 | Sq. Mtr. |
| 10 | 6 | Supply & Installation of underfloor insulation... | R/O | Sqm |
| 11 | 7 | Supply & Installation of underdeck insulation... | R/O | Sqm |

**NOTE:** P0_01 baseline used 9 source rows; independent transcription finds 11 (includes items 6 and 7 which have R/O qty but real unit). OWNER-DECISION-NEEDED.

---

## 08_sael (19 rows — TDS file, possible misclassification)

**Source:** `data/real_rfqs/swa_enquiries/08_sael/Copy of TDS - Insulation - SAEL (1).xlsx`
**Method:** manual transcription via openpyxl (Sheet1, rows 8-37)
**D4 exclusions (3 section titles):** 11 DUCT THERMAL INSULATION, 11.2 FINISHING MATERIALS, 12.01 INSULATION MATERIALS

**⚠️ OWNER-DECISION-NEEDED:** This file is a **Technical Data Sheet (TDS)**, NOT a BOQ enquiry. It has no qty/unit columns in the BOQ sense — it's a spec-compliance data sheet. The manifest classifies it as `boq_bearing`, but it may be `spec_only`. The separate SAEL BOQ enquiry file (`Copy of Insulation Enquiry - SAEL.xlsx`, NOT in the boq_bearing manifest list) has 16 rows per P0_02 D4. **Question for owner: is the TDS file boq_bearing or spec_only?**

19 numbered spec rows transcribed (11.1, 11.1.1-4, 11.2.1-4, 12, 12.02-04, 1-10) — these are TDS spec items, not BOQ line items with qty/unit.

---

## 09_gem_bid_7439924 (22 rows)

**Source:** `data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf`
**Method:** manual transcription via pdfplumber (p1 item category + p6-7 consolidated BOQ)
**D4 exclusions:** none
**Verification:** sum of 22 quantities = 231,900 = exact match to page 1 stated total.

22 rows: Bonded Mineral Rock Wool Mattresses variants (11 products × 2 projects TALCHER+LARA). All with Sq.Mtr unit + numeric qty.

---

## 10_gem_bid_7552777 (10 rows)

**Source:** `data/real_rfqs/swa_enquiries/10_gem_bid_7552777/GeM-Bidding-9343469.pdf`
**Method:** manual transcription via pdfplumber (p5-11 form-field tables)
**D4 exclusions:** none

10 rows: Bonded Mineral Rock Wool Mattresses variants (150-40/50/60/75, 100-25/40/50/60/75). Quantities: 208, 892, 5838, 10061, 3795, 1080, 3405, 5504, 8893, 9967. (730 = Delivery Days, not qty.)

---

## OWNER-DECISION-NEEDED summary

| Doc | Issue | Candidate counts |
|-----|-------|-------------------|
| 06_avante | independent=36 vs gold=31 | 36 (5 #REF! parents included) or 31 (gold) |
| 07_grew | independent=11 vs gold=9 | 11 (items 6,7 with R/O qty included) or 9 (gold) |
| 08_sael (TDS) | TDS file may be spec_only, not boq_bearing | 19 (TDS spec items) or 0 (reclassify as spec_only) or use the BOQ enquiry file's 16 |
| 05_zydus_animal | multi-qty-column (D5 open from P0_02) | 48 (all source rows) or 20 (one-per-item) |

All other docs have a single confident count. The owner rules on these 4.