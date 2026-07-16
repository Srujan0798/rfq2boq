# CORPUS SWEEP REPORT — reconciliation with sha256 evidence

**Generated:** 2026-07-06T14:23:33.391331+00:00
**Manifest:** data/real_rfqs/corpus_manifest.json (127 entries)

## Summary

| Category | Count |
|----------|-------|
| Manifest entries | 127 |
| On-disk doc files found | 219 |
| Manifested (path match) | 19 |
| Duplicate of manifest entry (hash match, different path) | 182 |
| **UNMANIFESTED** (hash not in manifest) | **18** |

> **UNMANIFESTED = 0** means the corpus is complete: every on-disk document
> is either a manifest entry or a duplicate of one. Non-zero UNMANIFESTED
> requires owner disposition per file (P1_00 owner gate).

## Section 1 — Manifested (path match)

19 on-disk files whose path exactly matches a manifest entry.

- `data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/INSULATION-TECHNICAL SPECIFICATION.docx` (.docx, 31641 bytes)
- `data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/Copy of TDS TO BE FILLED BY VENDOR-INSULATION.xlsx` (.xlsx, 10120 bytes)
- `data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx` (.xlsx, 16844 bytes)
- `data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx` (.xlsx, 12738 bytes)
- `data/real_rfqs/swa_enquiries/08_sael/Copy of TDS - Insulation - SAEL (1).xlsx` (.xlsx, 11961 bytes)
- `data/real_rfqs/swa_enquiries/03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx` (.xlsx, 439816 bytes)
- `data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf` (.pdf, 249564 bytes)
- `data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Boq_132.pdf` (.pdf, 121733 bytes)
- `data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Specs_132.pdf` (.pdf, 6726298 bytes)
- `data/real_rfqs/swa_enquiries/10_gem_bid_7552777/GeM-Bidding-9343469.pdf` (.pdf, 165232 bytes)
- `data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, TDS Fill up, Grew Energy.pdf` (.pdf, 105030 bytes)
- `data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, Specification compliance, Grew Energy.pdf` (.pdf, 397780 bytes)
- `data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf` (.pdf, 77160 bytes)
- `data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf` (.pdf, 1390487 bytes)
- `data/real_rfqs/swa_enquiries/04_adani/BOQ PAGEadani proj.pdf` (.pdf, 224615 bytes)
- `data/real_rfqs/swa_enquiries/04_adani/TENDER SPECIFICATION-ACCOUSTIC INSULATIONadani proj.pdf` (.pdf, 231029 bytes)
- `data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf` (.pdf, 169609 bytes)
- `data/real_rfqs/swa_enquiries/04_adani/TENDER SPECIFICATION- CHW PIPE INSULATIONadani proj.pdf` (.pdf, 232609 bytes)
- `data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx` (.xlsx, 11807 bytes)

## Section 2 — Duplicates of manifest entries (hash match, different path)

182 on-disk files whose sha256 matches a manifest entry but whose path differs.
These are copies (e.g. ALL_RFQS flat aggregation, resources/ archive, swa_enquiries/ originals) — not new docs.

- hash `095ae8491256…` — manifest path(s): ['data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, TDS Fill up, Grew Energy.pdf', 'data/specifications/Re_ Required technical data - Avant - Grew Solar, Narmadapuram/108, TDS Fill up, Grew Energy.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__108, TDS Fill up, Grew Energy.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_grew_solar__108, TDS Fill up, Grew Energy.pdf`
- hash `0a5875ea10df…` — manifest path(s): ['data/specifications/Specifications/162_HVAC SPECIFICATIONS-156-158.pdf']
  - duplicate at `resources/Specifications/162_HVAC SPECIFICATIONS-156-158.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__162_HVAC SPECIFICATIONS-156-158.pdf`
- hash `0bd974a2fa2c…` — manifest path(s): ['data/specifications/Specifications/MECHANICAL DATA SHEET FOR INSULATION - RIL INGOT WAFER JAMNAGAR.pdf']
  - duplicate at `resources/Specifications/MECHANICAL DATA SHEET FOR INSULATION - RIL INGOT WAFER JAMNAGAR.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__MECHANICAL DATA SHEET FOR INSULATION - RIL INGOT WAFER JAMNAGAR.pdf`
- hash `0c499354613d…` — manifest path(s): ['data/specifications/Specification 2/Tendor Specs - Wall Accoustic.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Tendor Specs - Wall Accoustic.pdf`
- hash `0ee95d8268e6…` — manifest path(s): ['data/specifications/Specification 2/Adani Pune, Compliance FIle Updated.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Adani Pune, Compliance FIle Updated.pdf`
- hash `11c69d5d74a4…` — manifest path(s): ['data/real_rfqs/swa_enquiries/08_sael/Copy of TDS - Insulation - SAEL (1).xlsx', 'data/specifications/Require Technical data/Copy of TDS - Insulation - SAEL (1).xlsx']
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_sael__Copy of TDS - Insulation - SAEL (1).xlsx`
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__Copy of TDS - Insulation - SAEL (1).xlsx`
- hash `1245a6cc0e97…` — manifest path(s): ['data/specifications/Specification 2/boq.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__boq.pdf`
- hash `141e2181da92…` — manifest path(s): ['data/specifications/Specification 2/Make list - Gopin.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Make list - Gopin.pdf`
- hash `16b6437399f8…` — manifest path(s): ['data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Boq_132.pdf', 'data/specifications/Re_ Enquiry for Insulation for AVANTE SPACES LIMITED PLOT – A+C , Kirloskar Pune. (1)/Insulation Boq_132.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_avante__Insulation Boq_132.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__Insulation Boq_132.pdf`
- hash `1b48b0fd2413…` — manifest path(s): ['data/specifications/Specifications/Insulation Boq (1).pdf']
  - duplicate at `resources/Specifications/Insulation Boq (1).pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Insulation Boq (1).pdf`
- hash `1cc59379b7c2…` — manifest path(s): ['data/specifications/Specifications/Insulation Specs.pdf']
  - duplicate at `resources/Specifications/Insulation Specs.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Insulation Specs.pdf`
- hash `1ceaa36e97d3…` — manifest path(s): ['data/specifications/Specifications/Nitrile insulation - Revised.pdf']
  - duplicate at `resources/Specifications/Nitrile insulation - Revised.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Nitrile insulation - Revised.pdf`
- hash `1dbf2ffe365c…` — manifest path(s): ['data/specifications/Specification 2/Response to Prebid Queries - 20241228.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Response to Prebid Queries - 20241228.pdf`
- hash `246b76410039…` — manifest path(s): ['data/specifications/Specification 2/DC-90 (DC 37801 )INSULATION - (Sample).pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__DC-90 (DC 37801 )INSULATION - (Sample).pdf`
- hash `25a26cc627bc…` — manifest path(s): ['data/specifications/Specification 2/INSULATION..pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__INSULATION..pdf`
- hash `263990a36656…` — manifest path(s): ['data/specifications/Specification 2/Copy of Inquiry for Duct Insulation of Proj-1017 Bioltus Valsad(56642).pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Copy of Inquiry for Duct Insulation of Proj-1017 Bioltus Valsad(56642).pdf`
- hash `26c85e5b1df4…` — manifest path(s): ['data/specifications/Specification 2/INSULATION TECHNICAL TO BE FILLED BY VENDOR.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__INSULATION TECHNICAL TO BE FILLED BY VENDOR.pdf`
- hash `2912cc62cb9b…` — manifest path(s): ['data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, Specification compliance, Grew Energy.pdf', 'data/specifications/Re_ Required technical data - Avant - Grew Solar, Narmadapuram/108, Specification compliance, Grew Energy.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_grew_solar__108, Specification compliance, Grew Energy.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__108, Specification compliance, Grew Energy.pdf`
- hash `2b875fed2634…` — manifest path(s): ['data/specifications/Specification 2/INSULATION TENDER SPECIFICATION.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__INSULATION TENDER SPECIFICATION.pdf`
- hash `2c6f4c2f660f…` — manifest path(s): ['data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx']
  - duplicate at `data/incoming/40_vssc_acoustic_boq.xlsx`
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__VSSC_BOQ_with_qty.xlsx`
- hash `2cb5ce9d943e…` — manifest path(s): ['data/specifications/Specifications/insulation-cmrl.pdf']
  - duplicate at `resources/Specifications/insulation-cmrl.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__insulation-cmrl.pdf`
- hash `2e9212ec1088…` — manifest path(s): ['data/specifications/Specification 2/Copy of UBS_Hyderabad_Project_BOQ(1).pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Copy of UBS_Hyderabad_Project_BOQ(1).pdf`
- hash `2ecbadc6bd89…` — manifest path(s): ['data/specifications/Specifications/23 07 13.01 Ductwork Insulation, Schedule.r0.pdf']
  - duplicate at `resources/Specifications/23 07 13.01 Ductwork Insulation, Schedule.r0.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__23 07 13.01 Ductwork Insulation, Schedule.r0.pdf`
- hash `2f0294d2c1d6…` — manifest path(s): ['data/specifications/Specification 2/Insulation ARFF.xlsx']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Insulation ARFF.xlsx`
- hash `2f3010bf783c…` — manifest path(s): ['data/specifications/Specifications/BOQ- Insulation_Compliance.pdf']
  - duplicate at `resources/Specifications/BOQ- Insulation_Compliance.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__BOQ- Insulation_Compliance.pdf`
- hash `32801aa0df7c…` — manifest path(s): ['data/specifications/Specifications/Copy of Insulation Enquiry - SAEL.pdf']
  - duplicate at `resources/Specifications/Copy of Insulation Enquiry - SAEL.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Copy of Insulation Enquiry - SAEL.pdf`
- hash `35d9612ebc20…` — manifest path(s): ['data/specifications/Specifications/BOQ - INSULATION.pdf']
  - duplicate at `resources/Specifications/BOQ - INSULATION.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__BOQ - INSULATION.pdf`
- hash `36920c5c9176…` — manifest path(s): ['data/specifications/Specification 2/Insulation.xlsx']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Insulation.xlsx`
- hash `37693c5e2952…` — manifest path(s): ['data/specifications/Specifications/Insulation (1).pdf']
  - duplicate at `resources/Specifications/Insulation (1).pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Insulation (1).pdf`
- hash `3f607148ab74…` — manifest path(s): ['data/specifications/Specifications/Insulation TS.pdf']
  - duplicate at `resources/Specifications/Insulation TS.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Insulation TS.pdf`
- hash `40f7aeb730cd…` — manifest path(s): ['data/specifications/Specification 2/BOQ_Thermal Insulation.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__BOQ_Thermal Insulation.pdf`
- hash `4172608f5666…` — manifest path(s): ['data/real_rfqs/swa_enquiries/10_gem_bid_7552777/GeM-Bidding-9343469.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__GeM-Bidding-9343469.pdf`
- hash `44f4603ebd67…` — manifest path(s): ['data/specifications/Specifications/Tender (2).pdf']
  - duplicate at `resources/Specifications/Tender (2).pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Tender (2).pdf`
- hash `462e507a2cf2…` — manifest path(s): ['data/specifications/Specifications/Compliance Sheet.pdf']
  - duplicate at `resources/Specifications/Compliance Sheet.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Compliance Sheet.pdf`
- hash `470944efb80d…` — manifest path(s): ['data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/INSULATION-TECHNICAL SPECIFICATION.docx', 'data/specifications/RE_ Provide Technical data - Avant , Zydus Animal Health Expansion Project - Pharmez-Ahmedabad/INSULATION-TECHNICAL SPECIFICATION.docx']
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_zydus_animal_health__INSULATION-TECHNICAL SPECIFICATION.docx`
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__INSULATION-TECHNICAL SPECIFICATION.docx`
- hash `4bd73074ccc6…` — manifest path(s): ['data/specifications/Specification 2/MECH-EIPL-HVAC-NXTRA-001-R2-BUFFER TANK.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__MECH-EIPL-HVAC-NXTRA-001-R2-BUFFER TANK.pdf`
- hash `500720c6cb17…` — manifest path(s): ['data/real_rfqs/swa_enquiries/04_adani/TENDER SPECIFICATION- CHW PIPE INSULATIONadani proj.pdf', 'data/specifications/Specs and boq/TENDER SPECIFICATION- CHW PIPE INSULATIONadani proj.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_adani__TENDER SPECIFICATION- CHW PIPE INSULATIONadani proj.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__TENDER SPECIFICATION- CHW PIPE INSULATIONadani proj.pdf`
- hash `55d4d8996200…` — manifest path(s): ['data/specifications/Specifications/Tender (4) (1).pdf']
  - duplicate at `resources/Specifications/Tender (4) (1).pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Tender (4) (1).pdf`
- hash `5976cf047a60…` — manifest path(s): ['data/specifications/Specifications/Annexure-K7-B-GCC for Indigenous Supplies-R3.pdf']
  - duplicate at `resources/Specifications/Annexure-K7-B-GCC for Indigenous Supplies-R3.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Annexure-K7-B-GCC for Indigenous Supplies-R3.pdf`
- hash `5f8dfe8efae3…` — manifest path(s): ['data/specifications/Specification 2/1_Specification Compliance.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__1_Specification Compliance.pdf`
- hash `61d7817e11b2…` — manifest path(s): ['data/specifications/Specifications/HVAC Duct - Insulation Specification Imphal (1).pdf']
  - duplicate at `resources/Specifications/HVAC Duct - Insulation Specification Imphal (1).pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__HVAC Duct - Insulation Specification Imphal (1).pdf`
- hash `66ea9b83e9ca…` — manifest path(s): ['data/real_rfqs/swa_enquiries/03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx']
  - duplicate at `data/incoming/R3_zydus_matoda_osd.xlsx`
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__Zydus_Matoda_Insulation_Enquiry.xlsx`
- hash `6a0f1b25d4af…` — manifest path(s): ['data/specifications/Specification 2/Specification_Insulation_GBRC.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Specification_Insulation_GBRC.pdf`
- hash `6b4dfa18012f…` — manifest path(s): ['data/specifications/rar_extra/TENDER SPECIFICATION- CHW PIPE INSULATION.pdf']
  - duplicate at `resources/Specifications/TENDER SPECIFICATION- CHW PIPE INSULATION.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/rar__TENDER SPECIFICATION- CHW PIPE INSULATION.pdf`
- hash `6cb55f25944a…` — manifest path(s): ['data/specifications/Specifications/23 07 13 Ductwork Insulation.rA.pdf']
  - duplicate at `resources/Specifications/23 07 13 Ductwork Insulation.rA.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__23 07 13 Ductwork Insulation.rA.pdf`
- hash `6dbc0aca1e93…` — manifest path(s): ['data/specifications/Specification 2/D 1.1.11-THERMAL INSULATION FOR COLD SURFACES.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__D 1.1.11-THERMAL INSULATION FOR COLD SURFACES.pdf`
- hash `6e95a211fdb2…` — manifest path(s): ['data/specifications/Specifications/Copy of BOQ.pdf']
  - duplicate at `resources/Specifications/Copy of BOQ.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Copy of BOQ.pdf`
- hash `6f52c5459f1d…` — manifest path(s): ['data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__GeM-Bidding-9218026.pdf`
- hash `71da064afd92…` — manifest path(s): ['data/real_rfqs/swa_enquiries/04_adani/TENDER SPECIFICATION-ACCOUSTIC INSULATIONadani proj.pdf', 'data/specifications/Specs and boq/TENDER SPECIFICATION-ACCOUSTIC INSULATIONadani proj.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__TENDER SPECIFICATION-ACCOUSTIC INSULATIONadani proj.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_adani__TENDER SPECIFICATION-ACCOUSTIC INSULATIONadani proj.pdf`
- hash `7261003c9507…` — manifest path(s): ['data/specifications/Specification 2/1.Thermal Insulation - Tender Specs_Bajaj_Colaba House.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__1.Thermal Insulation - Tender Specs_Bajaj_Colaba House.pdf`
- hash `7791e22e4959…` — manifest path(s): ['data/specifications/Specification 2/TDS - Insulation Piping.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__TDS - Insulation Piping.pdf`
- hash `7e03bbae1966…` — manifest path(s): ['data/specifications/Specification 2/TDS - Insulation Ducting.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__TDS - Insulation Ducting.pdf`
- hash `8043f8e1ed3e…` — manifest path(s): ['data/specifications/Specifications/rockwool-acu..pdf']
  - duplicate at `resources/Specifications/rockwool-acu..pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__rockwool-acu..pdf`
- hash `813e39280ca9…` — manifest path(s): ['data/specifications/Specification 2/Accoustic Wall Insulation for DCS High Side Project.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Accoustic Wall Insulation for DCS High Side Project.pdf`
- hash `84b11065976e…` — manifest path(s): ['data/specifications/Specification 2/2. HVAC SPECIFICATION.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__2. HVAC SPECIFICATION.pdf`
- hash `9708d501e018…` — manifest path(s): ['data/specifications/Specifications/SWPL-PER-HVAC-RFQ-02 (Thermal & Acoustic Insulation).pdf']
  - duplicate at `resources/Specifications/SWPL-PER-HVAC-RFQ-02 (Thermal & Acoustic Insulation).pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__SWPL-PER-HVAC-RFQ-02 (Thermal & Acoustic Insulation).pdf`
- hash `9814b68b3a69…` — manifest path(s): ['data/specifications/Specifications/Tech Specs  - Insulation.pdf']
  - duplicate at `resources/Specifications/Tech Specs  - Insulation.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Tech Specs  - Insulation.pdf`
- hash `996f9ef90b79…` — manifest path(s): ['data/specifications/Specification 2/Tender Specs.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Tender Specs.pdf`
- hash `9d25e03555fe…` — manifest path(s): ['data/specifications/Specification 2/Tender Specs (1).pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Tender Specs (1).pdf`
- hash `9db7a982ea39…` — manifest path(s): ['data/real_rfqs/swa_enquiries/04_adani/BOQ PAGEadani proj.pdf', 'data/specifications/Specs and boq/BOQ PAGEadani proj.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__BOQ PAGEadani proj.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_adani__BOQ PAGEadani proj.pdf`
- hash `a247b965bae1…` — manifest path(s): ['data/specifications/Specifications/1_HVAC SPECIFICATIONS-156-158.pdf']
  - duplicate at `resources/Specifications/1_HVAC SPECIFICATIONS-156-158.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__1_HVAC SPECIFICATIONS-156-158.pdf`
- hash `a37bbf766a6b…` — manifest path(s): ['data/specifications/Specifications/Specs_.pdf']
  - duplicate at `resources/Specifications/Specs_.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Specs_.pdf`
- hash `a3e8495fda02…` — manifest path(s): ['data/specifications/Specifications/Annexure-3 DS-CHW-Insulation-Nitrile-Rubber.pdf']
  - duplicate at `resources/Specifications/Annexure-3 DS-CHW-Insulation-Nitrile-Rubber.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Annexure-3 DS-CHW-Insulation-Nitrile-Rubber.pdf`
- hash `a786e1d21a0f…` — manifest path(s): ['data/specifications/Specifications/Tender (3).pdf']
  - duplicate at `resources/Specifications/Tender (3).pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Tender (3).pdf`
- hash `ac2f7e247c8b…` — manifest path(s): ['data/specifications/rar_extra/TENDER.pdf']
  - duplicate at `resources/Specifications/TENDER.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/rar__TENDER.pdf`
- hash `adea765b0f8c…` — manifest path(s): ['data/specifications/rar_extra/TENDER SPECIFICATION-ACCOUSTIC INSULATION.pdf']
  - duplicate at `resources/Specifications/TENDER SPECIFICATION-ACCOUSTIC INSULATION.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/rar__TENDER SPECIFICATION-ACCOUSTIC INSULATION.pdf`
- hash `aec1e72f5b61…` — manifest path(s): ['data/specifications/Specification 2/ADANI_KARNAVATI - INSULATION - SPECIFICATION COMPLIANCE.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__ADANI_KARNAVATI - INSULATION - SPECIFICATION COMPLIANCE.pdf`
- hash `af3daf0c71c0…` — manifest path(s): ['data/specifications/Specifications/TENDER (1) (1).pdf']
  - duplicate at `resources/Specifications/TENDER (1) (1).pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__TENDER (1) (1).pdf`
- hash `af820a10b350…` — manifest path(s): ['data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf', 'data/specifications/Specs and boq/BOQ PAGE2adani proj.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_adani__BOQ PAGE2adani proj.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__BOQ PAGE2adani proj.pdf`
- hash `b28507449718…` — manifest path(s): ['data/specifications/Specifications/KRC Cignus 2 Phase 4 Powai.pdf']
  - duplicate at `resources/Specifications/KRC Cignus 2 Phase 4 Powai.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__KRC Cignus 2 Phase 4 Powai.pdf`
- hash `b29a5a9a9b10…` — manifest path(s): ['data/specifications/Specification 2/Specs_Thermal Insulation_Bajaj House.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Specs_Thermal Insulation_Bajaj House.pdf`
- hash `b2ef11b8e437…` — manifest path(s): ['data/specifications/Specifications/SPECS - INSULATION.pdf']
  - duplicate at `resources/Specifications/SPECS - INSULATION.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__SPECS - INSULATION.pdf`
- hash `b69fafd66921…` — manifest path(s): ['data/specifications/Specifications/OEPMC-EQS-0000-EC-00008_R05_ thermal insulation TS.pdf']
  - duplicate at `resources/Specifications/OEPMC-EQS-0000-EC-00008_R05_ thermal insulation TS.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__OEPMC-EQS-0000-EC-00008_R05_ thermal insulation TS.pdf`
- hash `b844a51c39c6…` — manifest path(s): ['data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf', 'data/specifications/Re_ Required technical data - Avant - Grew Solar, Narmadapuram/108, BOQ compliance, Grew Energy.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_grew_solar__108, BOQ compliance, Grew Energy.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__108, BOQ compliance, Grew Energy.pdf`
- hash `b8ba7b3c13ed…` — manifest path(s): ['data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Specs_132.pdf', 'data/specifications/Re_ Enquiry for Insulation for AVANTE SPACES LIMITED PLOT – A+C , Kirloskar Pune. (1)/Insulation Specs_132.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__Insulation Specs_132.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_avante__Insulation Specs_132.pdf`
- hash `b9438783d79e…` — manifest path(s): ['data/specifications/Specification 2/Copy of Insulation 13-12-24 Inner(58795).pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Copy of Insulation 13-12-24 Inner(58795).pdf`
- hash `bd6515f925ca…` — manifest path(s): ['data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx', 'data/specifications/Require Technical data/Copy of Insulation Enquiry - SAEL.xlsx']
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__Copy of Insulation Enquiry - SAEL.xlsx`
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_sael__Copy of Insulation Enquiry - SAEL.xlsx`
- hash `c320f6bc5075…` — manifest path(s): ['data/specifications/Specification 2/Technical Compliance- Aquachill =CEAT, Halol dt 09.06.2025.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Technical Compliance- Aquachill =CEAT, Halol dt 09.06.2025.pdf`
- hash `c3fb9f12ed1e…` — manifest path(s): ['data/specifications/Specifications/TDS - to be filled by vendor.pdf']
  - duplicate at `resources/Specifications/TDS - to be filled by vendor.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__TDS - to be filled by vendor.pdf`
- hash `c483e34a6dc1…` — manifest path(s): ['data/specifications/Specifications/181_Insulation Excel.pdf']
  - duplicate at `resources/Specifications/181_Insulation Excel.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__181_Insulation Excel.pdf`
- hash `c6b44882ca75…` — manifest path(s): ['data/specifications/Specifications/COMPLIANCE REPORT SHEET- Sleeve Ref Copper Pipe.pdf']
  - duplicate at `resources/Specifications/COMPLIANCE REPORT SHEET- Sleeve Ref Copper Pipe.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__COMPLIANCE REPORT SHEET- Sleeve Ref Copper Pipe.pdf`
- hash `c6bf2192c2a4…` — manifest path(s): ['data/specifications/Specification 2/TECHNICAL SPECIFICATION OF INSULATION.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__TECHNICAL SPECIFICATION OF INSULATION.pdf`
- hash `c7d35a312e28…` — manifest path(s): ['data/specifications/Specification 2/Gopin - Insulation TDS.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Gopin - Insulation TDS.pdf`
- hash `c8e7fc466f94…` — manifest path(s): ['data/specifications/Specification 2/INSULATION.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__INSULATION.pdf`
- hash `ca1ced11d19b…` — manifest path(s): ['data/specifications/Specification 2/INSULATION TENDER SPECIFICATION..pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__INSULATION TENDER SPECIFICATION..pdf`
- hash `cb779faa0429…` — manifest path(s): ['data/specifications/Specification 2/2.Copper & Drain Pipe Insulation _Tender Specs_Bajaj_Colaba House.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__2.Copper & Drain Pipe Insulation _Tender Specs_Bajaj_Colaba House.pdf`
- hash `cce6a6fcbc80…` — manifest path(s): ['data/specifications/Specification 2/INSULATION_BOQ_BLUEGRASS.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__INSULATION_BOQ_BLUEGRASS.pdf`
- hash `d28c1b8a8255…` — manifest path(s): ['data/specifications/Specification 2/BOQ - Insulation.xlsx']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__BOQ - Insulation.xlsx`
- hash `d2e02778c99f…` — manifest path(s): ['data/specifications/Specification 2/Copy of SWPL-ADANI-HVAC-PR-RFQ-18_Wall Acountic Insulation(53047).pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Copy of SWPL-ADANI-HVAC-PR-RFQ-18_Wall Acountic Insulation(53047).pdf`
- hash `d3cdda52290b…` — manifest path(s): ['data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/Copy of TDS TO BE FILLED BY VENDOR-INSULATION.xlsx', 'data/specifications/RE_ Provide Technical data - Avant , Zydus Animal Health Expansion Project - Pharmez-Ahmedabad/Copy of TDS TO BE FILLED BY VENDOR-INSULATION.xlsx']
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_zydus_animal_health__Copy of TDS TO BE FILLED BY VENDOR-INSULATION.xlsx`
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__Copy of TDS TO BE FILLED BY VENDOR-INSULATION.xlsx`
- hash `d3f44225ae6e…` — manifest path(s): ['data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__RFQ-75810 TMD-8.pdf`
- hash `d50f777b2e81…` — manifest path(s): ['data/specifications/Specifications/BOQ.pdf']
  - duplicate at `resources/Specifications/BOQ.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__BOQ.pdf`
- hash `d6fdb733a823…` — manifest path(s): ['data/specifications/Specification 2/Enquiry for Thermal Insulation for CHW Pipe.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Enquiry for Thermal Insulation for CHW Pipe.pdf`
- hash `dad94977cf50…` — manifest path(s): ['data/specifications/Specifications/183_.INSULATION.pdf']
  - duplicate at `resources/Specifications/183_.INSULATION.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__183_.INSULATION.pdf`
- hash `dba2c94fb256…` — manifest path(s): ['data/specifications/Specifications/INSULATION TECH SPEC.pdf']
  - duplicate at `resources/Specifications/INSULATION TECH SPEC.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__INSULATION TECH SPEC.pdf`
- hash `dbea10ff027d…` — manifest path(s): ['data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx', 'data/specifications/RE_ Provide Technical data - Avant , Zydus Animal Health Expansion Project - Pharmez-Ahmedabad/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx']
  - duplicate at `data/real_rfqs/ALL_RFQS/sacred10__Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx`
  - duplicate at `data/real_rfqs/ALL_RFQS/bundle_zydus_animal_health__Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx`
- hash `dc80837cdfad…` — manifest path(s): ['data/specifications/Specifications/23 07 13 Ductwork Insulation.r0.pdf']
  - duplicate at `resources/Specifications/23 07 13 Ductwork Insulation.r0.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__23 07 13 Ductwork Insulation.r0.pdf`
- hash `e2e4076781e4…` — manifest path(s): ['data/specifications/Specifications/Technical specifciation_ Thermal & acoustic insulation.pdf']
  - duplicate at `resources/Specifications/Technical specifciation_ Thermal & acoustic insulation.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Technical specifciation_ Thermal & acoustic insulation.pdf`
- hash `e34629174c56…` — manifest path(s): ['data/specifications/Specifications/37. RPMS-ENGG-SPC-HV-019-Thermal insulation.pdf']
  - duplicate at `resources/Specifications/37. RPMS-ENGG-SPC-HV-019-Thermal insulation.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__37. RPMS-ENGG-SPC-HV-019-Thermal insulation.pdf`
- hash `e4e14607bba5…` — manifest path(s): ['data/specifications/Specifications/Copy of Duct Insulation Compliance Sheet_.pdf']
  - duplicate at `resources/Specifications/Copy of Duct Insulation Compliance Sheet_.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Copy of Duct Insulation Compliance Sheet_.pdf`
- hash `e5ebcefd0c08…` — manifest path(s): ['data/specifications/Specifications/Insulation For Pipes-Spects - CHW Pipes - 20-11-205.pdf']
  - duplicate at `resources/Specifications/Insulation For Pipes-Spects - CHW Pipes - 20-11-205.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Insulation For Pipes-Spects - CHW Pipes - 20-11-205.pdf`
- hash `e66b2b37042b…` — manifest path(s): ['data/specifications/Specifications/LGE - Technical specification-45-51.pdf']
  - duplicate at `resources/Specifications/LGE - Technical specification-45-51.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__LGE - Technical specification-45-51.pdf`
- hash `e6994f1f82ed…` — manifest path(s): ['data/specifications/Specifications/BOQ PAGE (003).pdf']
  - duplicate at `resources/Specifications/BOQ PAGE (003).pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__BOQ PAGE (003).pdf`
- hash `ebcca679d0c8…` — manifest path(s): ['data/specifications/Specifications/BOQ PAGE.pdf']
  - duplicate at `resources/Specifications/BOQ PAGE.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__BOQ PAGE.pdf`
- hash `ecfd0cc3f7d9…` — manifest path(s): ['data/specifications/Specification 2/CISF EXTENSION -HVAC- PC-TS.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__CISF EXTENSION -HVAC- PC-TS.pdf`
- hash `ef9f86342ae7…` — manifest path(s): ['data/specifications/Specification 2/Insulation Medical.xlsx']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__Insulation Medical.xlsx`
- hash `f15b2c3fa638…` — manifest path(s): ['data/specifications/Specifications/TENDER - INSULATION.pdf']
  - duplicate at `resources/Specifications/TENDER - INSULATION.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__TENDER - INSULATION.pdf`
- hash `f6e21bae22c5…` — manifest path(s): ['data/specifications/Specifications/Technical Specification- Insulatiom.pdf']
  - duplicate at `resources/Specifications/Technical Specification- Insulatiom.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Technical Specification- Insulatiom.pdf`
- hash `f9deda63bd79…` — manifest path(s): ['data/specifications/Specifications/Tender (5).pdf']
  - duplicate at `resources/Specifications/Tender (5).pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Tender (5).pdf`
- hash `fc084048a3ea…` — manifest path(s): ['data/specifications/Specification 2/SWPL-MPL-GPVC-CAC2-HVAC-RFQ-10.pdf']
  - duplicate at `data/real_rfqs/ALL_RFQS/spec2__SWPL-MPL-GPVC-CAC2-HVAC-RFQ-10.pdf`
- hash `fcbc08099f03…` — manifest path(s): ['data/specifications/Specifications/Insulation Boq (2).pdf']
  - duplicate at `resources/Specifications/Insulation Boq (2).pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__Insulation Boq (2).pdf`
- hash `fcbf1e46f91b…` — manifest path(s): ['data/specifications/Specifications/47_Pipe Insulation_BOQ Compliance.pdf']
  - duplicate at `resources/Specifications/47_Pipe Insulation_BOQ Compliance.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__47_Pipe Insulation_BOQ Compliance.pdf`
- hash `fe288d17b125…` — manifest path(s): ['data/specifications/Specifications/01. JN3102-H31-EWE305-815-001 Technical Specifications for HVAC Low Side System.pdf']
  - duplicate at `resources/Specifications/01. JN3102-H31-EWE305-815-001 Technical Specifications for HVAC Low Side System.pdf`
  - duplicate at `data/real_rfqs/ALL_RFQS/spec1__01. JN3102-H31-EWE305-815-001 Technical Specifications for HVAC Low Side System.pdf`

## Section 3 — UNMANIFESTED (hash not in manifest)

**18 file(s) require owner disposition.** Recommended categories: `client-doc-ingest` / `non-client-quarantine` / `delete`.

- `ui/assets/sample_rfq.pdf` (.pdf, 3786 bytes, mtime 2026-07-06T11:03:01.112752+00:00)
  - provenance guess: path under ui/assets — review
  - sha256: `38d97cc018fcd3d80ac75a10eca885030d49f754ce46d9fb75afcca098506376`
- `resources/RFQ to BOQ Scope Extraction using NLP system.pdf` (.pdf, 331479 bytes, mtime 2026-07-06T11:03:00.643796+00:00)
  - provenance guess: resources/ — original client delivery archive (SACRED, read-only)
  - sha256: `a67af1420d71ba6a694bf9efb7456eb3e84182a3109cc3ff0e63fcdb674929b2`
- `resources/PUBLISH PRODUCT.xlsx` (.xlsx, 11159 bytes, mtime 2026-07-06T11:03:00.642156+00:00)
  - provenance guess: resources/ — original client delivery archive (SACRED, read-only)
  - sha256: `b2e01b14b083bbe791fda162208f1720242f0f43508daa428ed73a813b0f2871`
- `resources/resources/RFQ to BOQ Scope Extraction using NLP system.pdf` (.pdf, 331479 bytes, mtime 2026-07-06T11:03:00.909500+00:00)
  - provenance guess: resources/ — original client delivery archive (SACRED, read-only)
  - sha256: `a67af1420d71ba6a694bf9efb7456eb3e84182a3109cc3ff0e63fcdb674929b2`
- `resources/resources/Academic Papers/2023_13-ITcon-Nabavi.pdf` (.pdf, 810747 bytes, mtime 2026-07-06T11:03:00.896665+00:00)
  - provenance guess: resources/ — original client delivery archive (SACRED, read-only)
  - sha256: `e0c1d91e4fb88a94438cd79139abfe5c0d9fb56a4b543ef0ac48f18611514cf0`
- `resources/resources/Academic Papers/Semantic-NLP-Based-Information-Extraction-from-Construction-Regulatory-Documents-for-Automated-Compliance-Checking.pdf` (.pdf, 1327411 bytes, mtime 2026-07-06T11:03:00.899908+00:00)
  - provenance guess: resources/ — original client delivery archive (SACRED, read-only)
  - sha256: `96273825877e65f992ec44428c65992896cded0c1a88558f4c4a47c64b77db41`
- `resources/resources/Academic Papers/ci-12-2022-0315.pdf` (.pdf, 1043611 bytes, mtime 2026-07-06T11:03:00.902722+00:00)
  - provenance guess: resources/ — original client delivery archive (SACRED, read-only)
  - sha256: `bf7da81ae0e0296001f8a7d0ea98d4834a67b0a6a4a85115fdd4faccf40e5b93`
- `resources/resources/Industry Studies & Insights/Overview_and_analysis_of_the_text_mining_applicati.pdf` (.pdf, 2285635 bytes, mtime 2026-07-06T11:03:00.908546+00:00)
  - provenance guess: resources/ — original client delivery archive (SACRED, read-only)
  - sha256: `123831fb07a75f8ec09c4d0083e9faa5b0b9d2cb0d8c0fcbdf3a75b4630caf53`
- `resources/1/Academic Papers/2023_13-ITcon-Nabavi.pdf` (.pdf, 810747 bytes, mtime 2026-07-06T11:03:00.607061+00:00)
  - provenance guess: resources/ — original client delivery archive (SACRED, read-only)
  - sha256: `e0c1d91e4fb88a94438cd79139abfe5c0d9fb56a4b543ef0ac48f18611514cf0`
- `resources/1/Academic Papers/Semantic-NLP-Based-Information-Extraction-from-Construction-Regulatory-Documents-for-Automated-Compliance-Checking.pdf` (.pdf, 1327411 bytes, mtime 2026-07-06T11:03:00.617370+00:00)
  - provenance guess: resources/ — original client delivery archive (SACRED, read-only)
  - sha256: `96273825877e65f992ec44428c65992896cded0c1a88558f4c4a47c64b77db41`
- `resources/1/Academic Papers/ci-12-2022-0315.pdf` (.pdf, 1043611 bytes, mtime 2026-07-06T11:03:00.622281+00:00)
  - provenance guess: resources/ — original client delivery archive (SACRED, read-only)
  - sha256: `bf7da81ae0e0296001f8a7d0ea98d4834a67b0a6a4a85115fdd4faccf40e5b93`
- `resources/1/Surveys & Reviews/arXiv-2309.13249-Survey-Document-Level-IE.pdf` (.pdf, 696659 bytes, mtime 2026-07-06T11:03:00.638598+00:00)
  - provenance guess: resources/ — original client delivery archive (SACRED, read-only)
  - sha256: `8b00e6c116fcd4969afd3e7b03eddb74deac8e5e25fa1ee217e69c6cc2513efa`
- `resources/1/Industry Studies & Insights/Overview_and_analysis_of_the_text_mining_applicati.pdf` (.pdf, 2285635 bytes, mtime 2026-07-06T11:03:00.634375+00:00)
  - provenance guess: resources/ — original client delivery archive (SACRED, read-only)
  - sha256: `123831fb07a75f8ec09c4d0083e9faa5b0b9d2cb0d8c0fcbdf3a75b4630caf53`
- `data/real_rfqs/swa_gem_catalog.xlsx` (.xlsx, 11159 bytes, mtime 2026-07-06T11:03:00.574114+00:00)
  - provenance guess: path under data/real_rfqs — review
  - sha256: `b2e01b14b083bbe791fda162208f1720242f0f43508daa428ed73a813b0f2871`
- `data/real_rfqs/reference_real/ireps_bc341034058b.pdf` (.pdf, 2608557 bytes, mtime 2026-07-06T11:03:00.519288+00:00)
  - provenance guess: path under data/real_rfqs — review
  - sha256: `bc341034058b4fdbcb0caad80e15c92d12cacc4751edcb95f9b1ecfa02982bc1`
- `data/real_rfqs/reference_real/cpwd_Guidelines_for_Hassle_Free_Bid_Submission_1778959268.pdf` (.pdf, 35053 bytes, mtime 2026-07-06T11:03:00.504480+00:00)
  - provenance guess: path under data/real_rfqs — review
  - sha256: `bb4c5edcda4b7b436e67a624fccdabab8a5a2db7cdae392d3891a124e72456ac`
- `data/real_rfqs/reference_real/ireps_2724bb1eff78.pdf` (.pdf, 1261301 bytes, mtime 2026-07-06T11:03:00.507726+00:00)
  - provenance guess: path under data/real_rfqs — review
  - sha256: `2724bb1eff7867032053313af2562c389df2893f534ac083c10c2c20321fb700`
- `src/export/templates/cpwd_template.xlsx` (.xlsx, 5366 bytes, mtime 2026-07-06T11:03:01.072617+00:00)
  - provenance guess: path under src/export — review
  - sha256: `39071f2b2b7db666c4ba127d0275ec11b2c114d891abdc4a04a873eb6095b333`

## Path-drift finding (P1_00)

The manifest records 108 of 127 entries under `data/specifications/...` paths that do
not exist in this clone. All 108 files exist on disk with matching sha256 under
`resources/Specifications/` (spec1, rar) and `data/real_rfqs/ALL_RFQS/` (all batches).
This is path drift, not missing data — the sweep classifies them as 'manifested (hash match)'
because it compares by sha256 per the §9 gotcha. The orchestrator may re-pin manifest paths
to the on-disk locations in a future gate; no data is lost.

## OWNER GATE — disposition summary (P1_00 §3)

**18 unmanifested files / 12 unique hashes. Owner (Srujan) must rule per file/group.**
Agent recommendation per group (agent recommends; owner rules):

| Group | Unique hashes | Files | Recommendation | Reason |
|-------|--------------|-------|----------------|--------|
| Academic papers / surveys / industry studies | 4 | 8 (2 copies each) | **non-client-quarantine** | Research literature under `resources/*/Academic Papers/`, `Surveys & Reviews/`, `Industry Studies & Insights/` — NOT client RFQs. NER training reference material. Leave in `resources/` (SACRED, read-only). |
| Project brief / SOW | 1 | 2 (2 copies) | **non-client-quarantine** | `resources/RFQ to BOQ Scope Extraction using NLP system.pdf` — the SWA project brief, NOT a tender. Leave in `resources/`. |
| GeM product catalog | 1 | 2 (2 copies) | **non-client-quarantine** (P2_01 ingests as NER reference) | `resources/PUBLISH PRODUCT.xlsx` = `data/real_rfqs/swa_gem_catalog.xlsx` — GeM catalog, NOT a tender. P2_01 ingests as authoritative NER reference. |
| UI demo sample | 1 | 1 | **non-client-quarantine** | `ui/assets/sample_rfq.pdf` (3.8 KB) — UI demo file, NOT a real client doc. Leave in place. |
| Export template | 1 | 1 | **non-client-quarantine** | `src/export/templates/cpwd_template.xlsx` — Excel export template, NOT an RFQ. Leave in place. |
| IREPS / CPWD reference docs | 3 | 3 | **OWNER RULING NEEDED** | `data/real_rfqs/reference_real/{ireps_2724bb1eff78,ireps_bc341034058b,cpwd_Guidelines_*}.pdf` — look like real Indian government tender reference docs (IREPS/CPWD platforms). Could be `client-doc-ingest` or `non-client-quarantine`. **Only files that genuinely need the owner's call.** |

**Bottom line:** 9 of 12 unique hashes are clearly non-client material — recommend `non-client-quarantine` (leave in place, no manifest entry). **3 unique hashes (IREPS/CPWD) need the owner's ruling.** If owner rules all 3 as non-client, UNMANIFESTED = 0 and corpus is confirmed at 127 client docs. If any are client docs, they get ingested and the count rises.

**Path-drift note (separate from the gate):** 108 manifest entries reference `data/specifications/...` paths absent from this clone; all 108 exist with matching sha256 under `resources/Specifications/` + `data/real_rfqs/ALL_RFQS/`. Path drift, not missing data. Orchestrator may re-pin manifest paths to on-disk locations in a future gate.

**Agent recommendation: do NOT delete anything.**

## OWNER RULING APPLIED (2026-07-06)

**Owner (Srujan) ruled: non-client quarantine for all 18 unmanifested files.**
None are SWA documents. Disposition recorded in `attic/non_client_data/DISPOSITION.md`.
Corpus confirmed at **127 client docs**. UNMANIFESTED effectively = 0 after ruling.
No files moved or deleted (resources/ is SACRED; reference docs stay in place).
