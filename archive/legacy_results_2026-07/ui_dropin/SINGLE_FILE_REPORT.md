# UI Drop-in: Single-File Pass

Every one of the 127 real corpus documents uploaded to `ui/app.py` via `streamlit.testing.v1.AppTest.from_file` and observed for crash, row count, and UI-level errors.

- Generated: 2026-07-07 06:21:50 UTC
- Per-doc timeout: 120s

## Summary

| Status | Count |
|---|---|
| ok | 76 |
| no_items | 7 |
| ui_error | 0 |
| timeout | 42 |
| crash | 2 |
| **completed (ok + no_items + ui_error)** | **83** |
| **TOTAL** | **127** |

- Docs with BOQ rows > 0: **76 / 127**
- Total BOQ rows extracted: 948
- Wall-clock total: 4143.1s (avg 32.6s, max 399.4s)

## By format

| Format | Count |
|---|---|
| docx | 2 |
| pdf | 111 |
| xlsx | 14 |

## By doc_type

| doc_type | Count |
|---|---|
| boq_bearing | 33 |
| non_training | 16 |
| spec_only | 78 |

## By source_batch

| source_batch | Count |
|---|---|
| bundle:adani | 4 |
| bundle:avante | 2 |
| bundle:grew_solar | 3 |
| bundle:sael | 2 |
| bundle:zydus_animal_health | 3 |
| rar | 3 |
| sacred10 | 19 |
| spec1 | 50 |
| spec2 | 41 |

## Crashes, timeouts, and UI errors (verbatim)

| # | doc_id | status | rows | duration | detail |
|---|---|---|---|---|---|
| 1 | data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf | timeout | - | 98.0s | second at.run() timed out: AppTest script run timed out after 7.91379358300037(s) |
| 2 | data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/INSULATION-TECHNICAL SPECIFICATION.docx | crash | - | 1.2s | str: Invalid file extension: `.docx`. Allowed: ['.pdf', '.xlsx', '.xls'] |
| 3 | data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Specs_132.pdf | timeout | - | 203.4s | second at.run() timed out: AppTest script run timed out after 14.353885625001567(s) |
| 4 | data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf | timeout | - | 23.7s | second at.run() timed out: AppTest script run timed out after 14.84633129100257(s) |
| 5 | data/real_rfqs/swa_enquiries/10_gem_bid_7552777/GeM-Bidding-9343469.pdf | timeout | - | 23.0s | second at.run() timed out: AppTest script run timed out after 14.810293209004158(s) |
| 6 | data/real_rfqs/ALL_RFQS/spec1__Annexure-K7-B-GCC for Indigenous Supplies-R3.pdf | timeout | - | 19.7s | second at.run() timed out: AppTest script run timed out after 14.404002167000726(s) |
| 7 | data/real_rfqs/ALL_RFQS/spec1__BOQ.pdf | timeout | - | 24.7s | second at.run() timed out: AppTest script run timed out after 13.247459332997096(s) |
| 8 | data/real_rfqs/ALL_RFQS/spec1__Copy of BOQ.pdf | timeout | - | 16.2s | second at.run() timed out: AppTest script run timed out after 13.452011958004732(s) |
| 9 | data/real_rfqs/ALL_RFQS/spec1__Copy of Insulation Enquiry - SAEL.pdf | timeout | - | 16.4s | second at.run() timed out: AppTest script run timed out after 14.077541958999063(s) |
| 10 | data/real_rfqs/ALL_RFQS/spec1__HVAC Duct - Insulation Specification Imphal (1).pdf | timeout | - | 21.2s | second at.run() timed out: AppTest script run timed out after 14.19571816700045(s) |
| 11 | data/real_rfqs/ALL_RFQS/spec1__INSULATION TECH SPEC.pdf | timeout | - | 125.4s | second at.run() timed out: AppTest script run timed out after 13.927837208997516(s) |
| 12 | data/real_rfqs/ALL_RFQS/spec1__Insulation (1).pdf | timeout | - | 22.7s | second at.run() timed out: AppTest script run timed out after 14.130639667004289(s) |
| 13 | data/real_rfqs/ALL_RFQS/spec1__Insulation Specs.pdf | timeout | - | 56.9s | second at.run() timed out: AppTest script run timed out after 14.405466958000034(s) |
| 14 | data/real_rfqs/ALL_RFQS/spec1__Insulation TS.pdf | timeout | - | 29.5s | second at.run() timed out: AppTest script run timed out after 14.334687125003256(s) |
| 15 | data/real_rfqs/ALL_RFQS/spec1__OEPMC-EQS-0000-EC-00008_R05_ thermal insulation TS.pdf | timeout | - | 50.5s | second at.run() timed out: AppTest script run timed out after 14.402649333002046(s) |
| 16 | data/real_rfqs/ALL_RFQS/spec1__SPECS - INSULATION.pdf | timeout | - | 312.3s | second at.run() timed out: AppTest script run timed out after 14.315522707998753(s) |
| 17 | data/real_rfqs/ALL_RFQS/spec1__Specs_.pdf | timeout | - | 40.4s | second at.run() timed out: AppTest script run timed out after 14.4281606250006(s) |
| 18 | data/real_rfqs/ALL_RFQS/spec1__TENDER (1) (1).pdf | timeout | - | 169.1s | second at.run() timed out: AppTest script run timed out after 14.22436820800067(s) |
| 19 | data/real_rfqs/ALL_RFQS/spec1__TENDER - INSULATION.pdf | timeout | - | 25.3s | second at.run() timed out: AppTest script run timed out after 14.344797833000484(s) |
| 20 | data/real_rfqs/ALL_RFQS/spec1__Tech Specs  - Insulation.pdf | timeout | - | 19.1s | second at.run() timed out: AppTest script run timed out after 13.919048957999621(s) |
| 21 | data/real_rfqs/ALL_RFQS/spec1__Technical Specification- Insulatiom.pdf | timeout | - | 31.6s | second at.run() timed out: AppTest script run timed out after 14.093193459004397(s) |
| 22 | data/real_rfqs/ALL_RFQS/spec1__Technical specifciation_ Thermal & acoustic insulation.pdf | timeout | - | 125.6s | second at.run() timed out: AppTest script run timed out after 14.241057957995508(s) |
| 23 | data/real_rfqs/ALL_RFQS/spec1__Tender (2).pdf | timeout | - | 176.5s | second at.run() timed out: AppTest script run timed out after 14.51282424999954(s) |
| 24 | data/real_rfqs/ALL_RFQS/spec1__Tender (3).pdf | timeout | - | 48.3s | second at.run() timed out: AppTest script run timed out after 14.446911916995305(s) |
| 25 | data/real_rfqs/ALL_RFQS/spec1__Tender (4) (1).pdf | timeout | - | 181.7s | second at.run() timed out: AppTest script run timed out after 14.624195707998297(s) |
| 26 | data/real_rfqs/ALL_RFQS/spec1__Tender (5).pdf | timeout | - | 49.5s | second at.run() timed out: AppTest script run timed out after 14.395894875000522(s) |
| 27 | data/real_rfqs/ALL_RFQS/spec1__insulation-cmrl.pdf | timeout | - | 146.7s | second at.run() timed out: AppTest script run timed out after 14.597937999998976(s) |
| 28 | data/real_rfqs/ALL_RFQS/spec2__1.Thermal Insulation - Tender Specs_Bajaj_Colaba House.pdf | timeout | - | 196.1s | second at.run() timed out: AppTest script run timed out after 14.417052958000568(s) |
| 29 | data/real_rfqs/ALL_RFQS/spec2__1_Specification Compliance.pdf | timeout | - | 22.5s | second at.run() timed out: AppTest script run timed out after 14.324563207999745(s) |
| 30 | data/real_rfqs/ALL_RFQS/spec2__2. HVAC SPECIFICATION.pdf | timeout | - | 28.1s | second at.run() timed out: AppTest script run timed out after 14.332073792000301(s) |
| 31 | data/real_rfqs/ALL_RFQS/spec2__2.Copper & Drain Pipe Insulation _Tender Specs_Bajaj_Colaba House.pdf | timeout | - | 153.8s | second at.run() timed out: AppTest script run timed out after 13.751814916999137(s) |
| 32 | data/real_rfqs/ALL_RFQS/spec2__ADANI_KARNAVATI - INSULATION - SPECIFICATION COMPLIANCE.pdf | timeout | - | 26.9s | second at.run() timed out: AppTest script run timed out after 13.885778541000036(s) |
| 33 | data/real_rfqs/ALL_RFQS/spec2__Adani Pune, Compliance FIle Updated.pdf | timeout | - | 53.9s | second at.run() timed out: AppTest script run timed out after 12.779200500001025(s) |
| 34 | data/real_rfqs/ALL_RFQS/spec2__CISF EXTENSION -HVAC- PC-TS.pdf | timeout | - | 60.4s | second at.run() timed out: AppTest script run timed out after 14.22619766700518(s) |
| 35 | data/real_rfqs/ALL_RFQS/spec2__DC-90 (DC 37801 )INSULATION - (Sample).pdf | timeout | - | 29.0s | second at.run() timed out: AppTest script run timed out after 14.479579624996404(s) |
| 36 | data/real_rfqs/ALL_RFQS/spec2__INSULATION..pdf | timeout | - | 31.7s | second at.run() timed out: AppTest script run timed out after 14.417487958999118(s) |
| 37 | data/real_rfqs/ALL_RFQS/spec2__INSULATION.pdf | timeout | - | 43.0s | second at.run() timed out: AppTest script run timed out after 14.273478333998355(s) |
| 38 | data/real_rfqs/ALL_RFQS/spec2__MECH-EIPL-HVAC-NXTRA-001-R2-BUFFER TANK.pdf | timeout | - | 69.4s | second at.run() timed out: AppTest script run timed out after 14.324653291994764(s) |
| 39 | data/real_rfqs/ALL_RFQS/spec2__Response to Prebid Queries - 20241228.pdf | timeout | - | 215.1s | second at.run() timed out: AppTest script run timed out after 14.266041709001001(s) |
| 40 | data/real_rfqs/ALL_RFQS/spec2__Specs_Thermal Insulation_Bajaj House.pdf | timeout | - | 88.0s | second at.run() timed out: AppTest script run timed out after 14.22852970900567(s) |
| 41 | data/real_rfqs/ALL_RFQS/spec2__Tender Specs.pdf | timeout | - | 121.7s | second at.run() timed out: AppTest script run timed out after 14.3353984580026(s) |
| 42 | data/real_rfqs/ALL_RFQS/sacred10__Insulation Specs_132.pdf | timeout | - | 399.4s | second at.run() timed out: AppTest script run timed out after 14.342585665996012(s) |
| 43 | data/real_rfqs/ALL_RFQS/bundle_zydus_animal_health__INSULATION-TECHNICAL SPECIFICATION.docx | crash | - | 0.5s | str: Invalid file extension: `.docx`. Allowed: ['.pdf', '.xlsx', '.xls'] |
| 44 | data/real_rfqs/ALL_RFQS/rar__TENDER.pdf | timeout | - | 150.4s | second at.run() timed out: AppTest script run timed out after 14.438837458001217(s) |

## Per-doc results (all 127)

| # | doc_id | format | doc_type | status | rows | duration |
|---|---|---|---|---|---|---|
| 1 | data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf | pdf | spec_only | timeout | - | 98.0s |
| 2 | data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx | xlsx | boq_bearing | ok | 4 | 0.9s |
| 3 | data/real_rfqs/swa_enquiries/03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx | xlsx | boq_bearing | ok | 33 | 1.2s |
| 4 | data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf | pdf | boq_bearing | ok | 2 | 2.2s |
| 5 | data/real_rfqs/swa_enquiries/04_adani/BOQ PAGEadani proj.pdf | pdf | boq_bearing | ok | 43 | 5.9s |
| 6 | data/real_rfqs/swa_enquiries/04_adani/TENDER SPECIFICATION- CHW PIPE INSULATIONadani proj.pdf | pdf | spec_only | ok | 8 | 4.4s |
| 7 | data/real_rfqs/swa_enquiries/04_adani/TENDER SPECIFICATION-ACCOUSTIC INSULATIONadani proj.pdf | pdf | spec_only | ok | 5 | 4.2s |
| 8 | data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx | xlsx | spec_only | ok | 20 | 1.0s |
| 9 | data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/Copy of TDS TO BE FILLED BY VENDOR-INSULATION.xlsx | xlsx | boq_bearing | no_items | 0 | 0.8s |
| 10 | data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/INSULATION-TECHNICAL SPECIFICATION.docx | docx | spec_only | crash | - | 1.2s |
| 11 | data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Boq_132.pdf | pdf | boq_bearing | ok | 31 | 6.5s |
| 12 | data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Specs_132.pdf | pdf | spec_only | timeout | - | 203.4s |
| 13 | data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf | pdf | boq_bearing | ok | 9 | 1.3s |
| 14 | data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, Specification compliance, Grew Energy.pdf | pdf | spec_only | ok | 13 | 5.3s |
| 15 | data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, TDS Fill up, Grew Energy.pdf | pdf | spec_only | ok | 11 | 1.1s |
| 16 | data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx | xlsx | spec_only | ok | 16 | 0.2s |
| 17 | data/real_rfqs/swa_enquiries/08_sael/Copy of TDS - Insulation - SAEL (1).xlsx | xlsx | boq_bearing | ok | 25 | 0.2s |
| 18 | data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf | pdf | spec_only | timeout | - | 23.7s |
| 19 | data/real_rfqs/swa_enquiries/10_gem_bid_7552777/GeM-Bidding-9343469.pdf | pdf | spec_only | timeout | - | 23.0s |
| 20 | data/real_rfqs/ALL_RFQS/spec1__01. JN3102-H31-EWE305-815-001 Technical Specifications for HVAC Low Side System.pdf | pdf | spec_only | ok | 11 | 7.9s |
| 21 | data/real_rfqs/ALL_RFQS/spec1__162_HVAC SPECIFICATIONS-156-158.pdf | pdf | spec_only | ok | 13 | 4.8s |
| 22 | data/real_rfqs/ALL_RFQS/spec1__181_Insulation Excel.pdf | pdf | spec_only | ok | 24 | 1.4s |
| 23 | data/real_rfqs/ALL_RFQS/spec1__183_.INSULATION.pdf | pdf | spec_only | ok | 19 | 6.5s |
| 24 | data/real_rfqs/ALL_RFQS/spec1__1_HVAC SPECIFICATIONS-156-158.pdf | pdf | spec_only | ok | 13 | 3.6s |
| 25 | data/real_rfqs/ALL_RFQS/spec1__23 07 13 Ductwork Insulation.r0.pdf | pdf | spec_only | ok | 9 | 8.8s |
| 26 | data/real_rfqs/ALL_RFQS/spec1__23 07 13 Ductwork Insulation.rA.pdf | pdf | spec_only | ok | 13 | 9.7s |
| 27 | data/real_rfqs/ALL_RFQS/spec1__23 07 13.01 Ductwork Insulation, Schedule.r0.pdf | pdf | spec_only | ok | 6 | 4.1s |
| 28 | data/real_rfqs/ALL_RFQS/spec1__37. RPMS-ENGG-SPC-HV-019-Thermal insulation.pdf | pdf | spec_only | ok | 5 | 4.4s |
| 29 | data/real_rfqs/ALL_RFQS/spec1__47_Pipe Insulation_BOQ Compliance.pdf | pdf | boq_bearing | ok | 5 | 5.9s |
| 30 | data/real_rfqs/ALL_RFQS/spec1__Annexure-3 DS-CHW-Insulation-Nitrile-Rubber.pdf | pdf | spec_only | ok | 1 | 2.6s |
| 31 | data/real_rfqs/ALL_RFQS/spec1__Annexure-K7-B-GCC for Indigenous Supplies-R3.pdf | pdf | non_training | timeout | - | 19.7s |
| 32 | data/real_rfqs/ALL_RFQS/spec1__BOQ - INSULATION.pdf | pdf | boq_bearing | ok | 2 | 4.7s |
| 33 | data/real_rfqs/ALL_RFQS/spec1__BOQ PAGE (003).pdf | pdf | boq_bearing | ok | 2 | 1.0s |
| 34 | data/real_rfqs/ALL_RFQS/spec1__BOQ PAGE.pdf | pdf | boq_bearing | ok | 43 | 2.9s |
| 35 | data/real_rfqs/ALL_RFQS/spec1__BOQ- Insulation_Compliance.pdf | pdf | boq_bearing | ok | 13 | 6.7s |
| 36 | data/real_rfqs/ALL_RFQS/spec1__BOQ.pdf | pdf | boq_bearing | timeout | - | 24.7s |
| 37 | data/real_rfqs/ALL_RFQS/spec1__COMPLIANCE REPORT SHEET- Sleeve Ref Copper Pipe.pdf | pdf | spec_only | ok | 7 | 7.2s |
| 38 | data/real_rfqs/ALL_RFQS/spec1__Compliance Sheet.pdf | pdf | spec_only | ok | 14 | 11.3s |
| 39 | data/real_rfqs/ALL_RFQS/spec1__Copy of BOQ.pdf | pdf | boq_bearing | timeout | - | 16.2s |
| 40 | data/real_rfqs/ALL_RFQS/spec1__Copy of Duct Insulation Compliance Sheet_.pdf | pdf | spec_only | ok | 13 | 12.5s |
| 41 | data/real_rfqs/ALL_RFQS/spec1__Copy of Insulation Enquiry - SAEL.pdf | pdf | spec_only | timeout | - | 16.4s |
| 42 | data/real_rfqs/ALL_RFQS/spec1__HVAC Duct - Insulation Specification Imphal (1).pdf | pdf | spec_only | timeout | - | 21.2s |
| 43 | data/real_rfqs/ALL_RFQS/spec1__INSULATION TECH SPEC.pdf | pdf | non_training | timeout | - | 125.4s |
| 44 | data/real_rfqs/ALL_RFQS/spec1__Insulation (1).pdf | pdf | spec_only | timeout | - | 22.7s |
| 45 | data/real_rfqs/ALL_RFQS/spec1__Insulation Boq (1).pdf | pdf | boq_bearing | ok | 1 | 2.4s |
| 46 | data/real_rfqs/ALL_RFQS/spec1__Insulation Boq (2).pdf | pdf | boq_bearing | ok | 11 | 8.3s |
| 47 | data/real_rfqs/ALL_RFQS/spec1__Insulation For Pipes-Spects - CHW Pipes - 20-11-205.pdf | pdf | spec_only | ok | 3 | 5.2s |
| 48 | data/real_rfqs/ALL_RFQS/spec1__Insulation Specs.pdf | pdf | spec_only | timeout | - | 56.9s |
| 49 | data/real_rfqs/ALL_RFQS/spec1__Insulation TS.pdf | pdf | spec_only | timeout | - | 29.5s |
| 50 | data/real_rfqs/ALL_RFQS/spec1__KRC Cignus 2 Phase 4 Powai.pdf | pdf | spec_only | ok | 11 | 8.3s |
| 51 | data/real_rfqs/ALL_RFQS/spec1__LGE - Technical specification-45-51.pdf | pdf | spec_only | ok | 6 | 10.7s |
| 52 | data/real_rfqs/ALL_RFQS/spec1__MECHANICAL DATA SHEET FOR INSULATION - RIL INGOT WAFER JAMNAGAR.pdf | pdf | spec_only | ok | 5 | 2.7s |
| 53 | data/real_rfqs/ALL_RFQS/spec1__Nitrile insulation - Revised.pdf | pdf | spec_only | ok | 9 | 4.2s |
| 54 | data/real_rfqs/ALL_RFQS/spec1__OEPMC-EQS-0000-EC-00008_R05_ thermal insulation TS.pdf | pdf | spec_only | timeout | - | 50.5s |
| 55 | data/real_rfqs/ALL_RFQS/spec1__SPECS - INSULATION.pdf | pdf | spec_only | timeout | - | 312.3s |
| 56 | data/real_rfqs/ALL_RFQS/spec1__SWPL-PER-HVAC-RFQ-02 (Thermal & Acoustic Insulation).pdf | pdf | spec_only | ok | 1 | 5.7s |
| 57 | data/real_rfqs/ALL_RFQS/spec1__Specs_.pdf | pdf | spec_only | timeout | - | 40.4s |
| 58 | data/real_rfqs/ALL_RFQS/spec1__TDS - to be filled by vendor.pdf | pdf | spec_only | ok | 1 | 3.2s |
| 59 | data/real_rfqs/ALL_RFQS/spec1__TENDER (1) (1).pdf | pdf | non_training | timeout | - | 169.1s |
| 60 | data/real_rfqs/ALL_RFQS/spec1__TENDER - INSULATION.pdf | pdf | spec_only | timeout | - | 25.3s |
| 61 | data/real_rfqs/ALL_RFQS/spec1__Tech Specs  - Insulation.pdf | pdf | boq_bearing | timeout | - | 19.1s |
| 62 | data/real_rfqs/ALL_RFQS/spec1__Technical Specification- Insulatiom.pdf | pdf | spec_only | timeout | - | 31.6s |
| 63 | data/real_rfqs/ALL_RFQS/spec1__Technical specifciation_ Thermal & acoustic insulation.pdf | pdf | spec_only | timeout | - | 125.6s |
| 64 | data/real_rfqs/ALL_RFQS/spec1__Tender (2).pdf | pdf | non_training | timeout | - | 176.5s |
| 65 | data/real_rfqs/ALL_RFQS/spec1__Tender (3).pdf | pdf | non_training | timeout | - | 48.3s |
| 66 | data/real_rfqs/ALL_RFQS/spec1__Tender (4) (1).pdf | pdf | non_training | timeout | - | 181.7s |
| 67 | data/real_rfqs/ALL_RFQS/spec1__Tender (5).pdf | pdf | non_training | timeout | - | 49.5s |
| 68 | data/real_rfqs/ALL_RFQS/spec1__insulation-cmrl.pdf | pdf | non_training | timeout | - | 146.7s |
| 69 | data/real_rfqs/ALL_RFQS/spec1__rockwool-acu..pdf | pdf | spec_only | ok | 2 | 9.3s |
| 70 | data/real_rfqs/ALL_RFQS/spec2__1.Thermal Insulation - Tender Specs_Bajaj_Colaba House.pdf | pdf | non_training | timeout | - | 196.1s |
| 71 | data/real_rfqs/ALL_RFQS/spec2__1_Specification Compliance.pdf | pdf | spec_only | timeout | - | 22.5s |
| 72 | data/real_rfqs/ALL_RFQS/spec2__2. HVAC SPECIFICATION.pdf | pdf | spec_only | timeout | - | 28.1s |
| 73 | data/real_rfqs/ALL_RFQS/spec2__2.Copper & Drain Pipe Insulation _Tender Specs_Bajaj_Colaba House.pdf | pdf | non_training | timeout | - | 153.8s |
| 74 | data/real_rfqs/ALL_RFQS/spec2__ADANI_KARNAVATI - INSULATION - SPECIFICATION COMPLIANCE.pdf | pdf | spec_only | timeout | - | 26.9s |
| 75 | data/real_rfqs/ALL_RFQS/spec2__Accoustic Wall Insulation for DCS High Side Project.pdf | pdf | spec_only | ok | 4 | 7.9s |
| 76 | data/real_rfqs/ALL_RFQS/spec2__Adani Pune, Compliance FIle Updated.pdf | pdf | spec_only | timeout | - | 53.9s |
| 77 | data/real_rfqs/ALL_RFQS/spec2__BOQ - Insulation.xlsx | xlsx | boq_bearing | ok | 47 | 4.5s |
| 78 | data/real_rfqs/ALL_RFQS/spec2__BOQ_Thermal Insulation.pdf | pdf | boq_bearing | ok | 1 | 2.6s |
| 79 | data/real_rfqs/ALL_RFQS/spec2__CISF EXTENSION -HVAC- PC-TS.pdf | pdf | spec_only | timeout | - | 60.4s |
| 80 | data/real_rfqs/ALL_RFQS/spec2__Copy of Inquiry for Duct Insulation of Proj-1017 Bioltus Valsad(56642).pdf | pdf | spec_only | ok | 2 | 1.9s |
| 81 | data/real_rfqs/ALL_RFQS/spec2__Copy of Insulation 13-12-24 Inner(58795).pdf | pdf | spec_only | ok | 14 | 5.1s |
| 82 | data/real_rfqs/ALL_RFQS/spec2__Copy of SWPL-ADANI-HVAC-PR-RFQ-18_Wall Acountic Insulation(53047).pdf | pdf | spec_only | ok | 1 | 4.0s |
| 83 | data/real_rfqs/ALL_RFQS/spec2__Copy of UBS_Hyderabad_Project_BOQ(1).pdf | pdf | boq_bearing | ok | 20 | 3.4s |
| 84 | data/real_rfqs/ALL_RFQS/spec2__D 1.1.11-THERMAL INSULATION FOR COLD SURFACES.pdf | pdf | spec_only | no_items | 0 | 5.1s |
| 85 | data/real_rfqs/ALL_RFQS/spec2__DC-90 (DC 37801 )INSULATION - (Sample).pdf | pdf | non_training | timeout | - | 29.0s |
| 86 | data/real_rfqs/ALL_RFQS/spec2__Enquiry for Thermal Insulation for CHW Pipe.pdf | pdf | spec_only | ok | 13 | 10.3s |
| 87 | data/real_rfqs/ALL_RFQS/spec2__Gopin - Insulation TDS.pdf | pdf | spec_only | ok | 17 | 3.7s |
| 88 | data/real_rfqs/ALL_RFQS/spec2__INSULATION TECHNICAL TO BE FILLED BY VENDOR.pdf | pdf | spec_only | ok | 7 | 2.1s |
| 89 | data/real_rfqs/ALL_RFQS/spec2__INSULATION TENDER SPECIFICATION..pdf | pdf | spec_only | ok | 12 | 4.4s |
| 90 | data/real_rfqs/ALL_RFQS/spec2__INSULATION TENDER SPECIFICATION.pdf | pdf | spec_only | ok | 12 | 4.0s |
| 91 | data/real_rfqs/ALL_RFQS/spec2__INSULATION..pdf | pdf | spec_only | timeout | - | 31.7s |
| 92 | data/real_rfqs/ALL_RFQS/spec2__INSULATION.pdf | pdf | spec_only | timeout | - | 43.0s |
| 93 | data/real_rfqs/ALL_RFQS/spec2__INSULATION_BOQ_BLUEGRASS.pdf | pdf | boq_bearing | ok | 5 | 6.0s |
| 94 | data/real_rfqs/ALL_RFQS/spec2__Insulation ARFF.xlsx | xlsx | boq_bearing | no_items | 0 | 1.0s |
| 95 | data/real_rfqs/ALL_RFQS/spec2__Insulation Medical.xlsx | xlsx | boq_bearing | ok | 15 | 1.0s |
| 96 | data/real_rfqs/ALL_RFQS/spec2__Insulation.xlsx | xlsx | boq_bearing | no_items | 0 | 0.8s |
| 97 | data/real_rfqs/ALL_RFQS/spec2__MECH-EIPL-HVAC-NXTRA-001-R2-BUFFER TANK.pdf | pdf | boq_bearing | timeout | - | 69.4s |
| 98 | data/real_rfqs/ALL_RFQS/spec2__Make list - Gopin.pdf | pdf | non_training | ok | 31 | 12.8s |
| 99 | data/real_rfqs/ALL_RFQS/spec2__Response to Prebid Queries - 20241228.pdf | pdf | non_training | timeout | - | 215.1s |
| 100 | data/real_rfqs/ALL_RFQS/spec2__SWPL-MPL-GPVC-CAC2-HVAC-RFQ-10.pdf | pdf | spec_only | ok | 15 | 7.2s |
| 101 | data/real_rfqs/ALL_RFQS/spec2__Specification_Insulation_GBRC.pdf | pdf | spec_only | ok | 9 | 7.4s |
| 102 | data/real_rfqs/ALL_RFQS/spec2__Specs_Thermal Insulation_Bajaj House.pdf | pdf | non_training | timeout | - | 88.0s |
| 103 | data/real_rfqs/ALL_RFQS/spec2__TDS - Insulation Ducting.pdf | pdf | spec_only | ok | 6 | 4.3s |
| 104 | data/real_rfqs/ALL_RFQS/spec2__TDS - Insulation Piping.pdf | pdf | spec_only | ok | 6 | 3.9s |
| 105 | data/real_rfqs/ALL_RFQS/spec2__TECHNICAL SPECIFICATION OF INSULATION.pdf | pdf | spec_only | no_items | 0 | 7.2s |
| 106 | data/real_rfqs/ALL_RFQS/spec2__Technical Compliance- Aquachill =CEAT, Halol dt 09.06.2025.pdf | pdf | spec_only | ok | 23 | 7.0s |
| 107 | data/real_rfqs/ALL_RFQS/spec2__Tender Specs (1).pdf | pdf | spec_only | ok | 7 | 4.6s |
| 108 | data/real_rfqs/ALL_RFQS/spec2__Tender Specs.pdf | pdf | spec_only | timeout | - | 121.7s |
| 109 | data/real_rfqs/ALL_RFQS/spec2__Tendor Specs - Wall Accoustic.pdf | pdf | non_training | no_items | 0 | 1.9s |
| 110 | data/real_rfqs/ALL_RFQS/spec2__boq.pdf | pdf | boq_bearing | ok | 2 | 1.7s |
| 111 | data/real_rfqs/ALL_RFQS/bundle_grew_solar__108, BOQ compliance, Grew Energy.pdf | pdf | boq_bearing | ok | 9 | 9.3s |
| 112 | data/real_rfqs/ALL_RFQS/sacred10__108, Specification compliance, Grew Energy.pdf | pdf | spec_only | ok | 13 | 12.0s |
| 113 | data/real_rfqs/ALL_RFQS/sacred10__108, TDS Fill up, Grew Energy.pdf | pdf | spec_only | ok | 11 | 4.2s |
| 114 | data/real_rfqs/ALL_RFQS/sacred10__Copy of Insulation Enquiry - SAEL.xlsx | xlsx | spec_only | ok | 16 | 0.9s |
| 115 | data/real_rfqs/ALL_RFQS/bundle_sael__Copy of TDS - Insulation - SAEL (1).xlsx | xlsx | boq_bearing | ok | 25 | 0.9s |
| 116 | data/real_rfqs/ALL_RFQS/sacred10__Insulation Boq_132.pdf | pdf | boq_bearing | ok | 31 | 7.4s |
| 117 | data/real_rfqs/ALL_RFQS/sacred10__Insulation Specs_132.pdf | pdf | spec_only | timeout | - | 399.4s |
| 118 | data/real_rfqs/ALL_RFQS/sacred10__BOQ PAGE2adani proj.pdf | pdf | boq_bearing | ok | 2 | 1.5s |
| 119 | data/real_rfqs/ALL_RFQS/sacred10__BOQ PAGEadani proj.pdf | pdf | boq_bearing | ok | 43 | 5.3s |
| 120 | data/real_rfqs/ALL_RFQS/sacred10__TENDER SPECIFICATION- CHW PIPE INSULATIONadani proj.pdf | pdf | spec_only | ok | 8 | 13.7s |
| 121 | data/real_rfqs/ALL_RFQS/bundle_adani__TENDER SPECIFICATION-ACCOUSTIC INSULATIONadani proj.pdf | pdf | spec_only | ok | 5 | 3.2s |
| 122 | data/real_rfqs/ALL_RFQS/bundle_zydus_animal_health__Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx | xlsx | spec_only | ok | 20 | 0.7s |
| 123 | data/real_rfqs/ALL_RFQS/bundle_zydus_animal_health__Copy of TDS TO BE FILLED BY VENDOR-INSULATION.xlsx | xlsx | boq_bearing | no_items | 0 | 0.6s |
| 124 | data/real_rfqs/ALL_RFQS/bundle_zydus_animal_health__INSULATION-TECHNICAL SPECIFICATION.docx | docx | spec_only | crash | - | 0.5s |
| 125 | data/real_rfqs/ALL_RFQS/rar__TENDER SPECIFICATION- CHW PIPE INSULATION.pdf | pdf | spec_only | ok | 8 | 4.2s |
| 126 | data/real_rfqs/ALL_RFQS/rar__TENDER SPECIFICATION-ACCOUSTIC INSULATION.pdf | pdf | spec_only | ok | 5 | 3.5s |
| 127 | data/real_rfqs/ALL_RFQS/rar__TENDER.pdf | pdf | non_training | timeout | - | 150.4s |

