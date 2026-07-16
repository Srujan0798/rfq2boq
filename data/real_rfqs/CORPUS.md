# RFQ2BOQ Real Corpus — sacred-10 TEST subset (see ALL_RFQS_README.md for the full 127)

**⚠️ Corrected 2026-07-05 — this file only ever listed 10 documents and its name ("CORPUS.md") made it look like the whole corpus. It is NOT. It is one subset: the frozen TEST-split anchor. The full corpus is 127 real RFQ documents — see [ALL_RFQS_README.md](ALL_RFQS_README.md) (the actual master index) and [corpus_manifest.json](corpus_manifest.json) (machine-readable, all 127). Do not scope any task to just this file's 10.**

## SWA Enquiries (10 of 127 — the frozen TEST-split anchor, held out for eval/demo, never trained on)
| ID | Client | File(s) | Type | Gold Status |
|----|--------|---------|------|-------------|
| 01_gsecl_wanakbori_tmd8 | GSECL | RFQ-75810 TMD-8.pdf | PDF | swa_01_gsecl...json (pre-cleaned) |
| 02_isro_vssc | ISRO VSSC | VSSC_BOQ_with_qty.xlsx | XLSX | rowgold + swa_02...json |
| 03_zydus_matoda_osd | Zydus Matoda | Zydus_Matoda_Insulation_Enquiry.xlsx | XLSX | rowgold + swa_03...json |
| 04_adani | Adani | BOQ PAGE2adani proj.pdf | PDF | swa_04_adani.json (human_curated) |
| 05_zydus_animal_pharmez | Zydus Animal | Copy of Insulation Enquiry-... .xlsx | XLSX | rowgold + swa_05...json |
| 06_avante_kirloskar_pune | Avante | Insulation Boq_132.pdf | PDF | swa_06...json (human_curated) |
| 07_grew_solar_narmadapuram | Grew | 108, BOQ compliance, Grew Energy.pdf | PDF | swa_07...json (human_curated) |
| 08_sael | SAEL | Copy of Insulation Enquiry - SAEL.xlsx | XLSX | rowgold + swa_08...json |
| 09_gem_bid_7439924 | GeM | GeM-Bidding-9218026.pdf | PDF | swa_09...json (ai-precleaned-needs-human-signoff) |
| 10_gem_bid_7552777 | GeM | GeM-Bidding-9343469.pdf | PDF | swa_10...json (ai-precleaned-needs-human-signoff) |

Sources: 18 files (12 PDF + 6 XLSX) in swa_enquiries/. Ingested JSON: 10 in ingested/. All tracked in git.

## Notes
- NO synthetic or sample data in corpus — all purged to attic/ (2026-06-11).
- Gold: 10/10 enquiries, entity + rowgold for XLSX.
- For eval: use scripts/validate_product.py (honest, independent gold/rowgold preferred).
- Owner: 09/10 human sign-off pending (S5).
