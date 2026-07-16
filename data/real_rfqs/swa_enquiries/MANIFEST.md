# SWA Real Tender Enquiries — Manifest

**Received from SWA Consultancy:** 22 May 2026 (8 enquiries) + 22 May 2026 evening (2 GeM bids)
**Source:** internal SWA estimator forwarded live insulation tender enquiries (mix of PDF + XLSX + DOCX) + public GeM portal bids
**License / Privacy:** internal SWA work, NOT for redistribution; GeM bids are public-portal sourced; gold annotations may be shared but not the source PDFs

---

## 10 Enquiries

| # | Client / Project | Domain | Source files | BOQ format | Use as |
|---|---|---|---|---|---|
| 01 | **GSECL Wanakbori** — Thermal Power Station, TMD-8 | Power · thermal | `RFQ-75810 TMD-8.pdf` (62 pp, text-based) | embedded inside PDF | **PDF→BOQ extraction test** |
| 02 | **ISRO VSSC** — incremental qty BOQ | Aerospace facility | `VSSC_BOQ_with_qty.xlsx` | XLSX (already structured) | **Ground-truth BOQ** for validation |
| 03 | **Zydus Pharma Matoda** — OSD facility insulation | Pharma facility | `Zydus_Matoda_Insulation_Enquiry.xlsx` | XLSX | **Ground-truth BOQ** |
| 04 | **Adani** — CHW pipe + acoustic insulation | Industrial | `BOQ PAGE*.pdf` ×2 + `TENDER SPECIFICATION*.pdf` ×2 | PDF (BOQ + spec separate) | **PDF→BOQ extraction test + spec parsing** |
| 05 | **Zydus Animal Health** — Pharmez Ahmedabad expansion | Pharma facility | `Insulation Enquiry*.xlsx` + `TDS*.xlsx` + `INSULATION-TECHNICAL SPECIFICATION.docx` | XLSX + DOCX | **Ground-truth BOQ + DOCX spec test** |
| 06 | **Avante Spaces / Kirloskar Pune** — Plot A+C | Real-estate / industrial | `Insulation Boq_132.pdf` + `Insulation Specs_132.pdf` (6.7 MB) | PDF | **PDF→BOQ extraction test (large doc)** |
| 07 | **Grew Solar Narmadapuram** — energy project | Renewables | `108, BOQ compliance*.pdf` + `108, Specification compliance*.pdf` + `108, TDS Fill up*.pdf` | PDF (3 separate sheets) | **PDF→BOQ + spec + TDS multi-format test** |
| 08 | **SAEL** — insulation enquiry | Industrial | `Insulation Enquiry - SAEL.xlsx` + `TDS - Insulation - SAEL (1).xlsx` | XLSX | **Ground-truth BOQ** |
| 09 | **GeM Bid 7439924** — Dept of Heavy Industry · Item: wire netting 13mm×0.56mm stitched 0.4mm · Qty 231,900 · Dated 22-Apr-2026 | Public-sector / GeM | `GeM-Bidding-9218026.pdf` (23 pp, bilingual Hindi/English) | embedded inside PDF | **PDF→BOQ extraction test + bilingual handling** |
| 10 | **GeM Bid 7552777** — Dept of Heavy Industry · Item: SS wire netting 150-75, Bonded mineral Rock wool · Qty 49,643 · Dated 19-May-2026 | Public-sector / GeM | `GeM-Bidding-9343469.pdf` (14 pp, bilingual Hindi/English) | embedded inside PDF | **PDF→BOQ extraction test + bilingual handling** |

**Total:** 10 enquiries · 19 files · ~10.1 MB

---

## What this changes (vs prior corpus)

| Prior corpus | New SWA corpus |
|---|---|
| 4 real PDFs + 113 synthetic (auto-archived) | 8 real enquiries, all SWA-live |
| Mostly construction/civil tenders | Insulation-specific (SWA's actual specialty) |
| Manual gold annotation needed | 7 of 8 have XLSX = **ground-truth BOQ already exists** |
| PDF-only | Mixed PDF + XLSX + DOCX |

The XLSX files are **already-completed BOQs** by SWA's own estimators — that means the system's job is to reproduce what the estimator did from the corresponding RFQ/spec document. This is a much stronger evaluation signal than synthetic data.

---

## SCOPE GUARD

- Per SWA's instruction (22 May 2026): **stop training on dummy/synthetic data.** Synthetic corpus moves to `attic/synthetic_corpus_archived/` for reference only.
- All future eval, fine-tuning, and gold annotations work off `data/real_rfqs/swa_enquiries/` only.
- Source PDFs from this folder are internal SWA work — do not commit to public mirrors. `.gitignore` should exclude `data/real_rfqs/swa_enquiries/*.pdf` if repo goes public.
