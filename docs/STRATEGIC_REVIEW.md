# Strategic Review — Build vs. Leverage vs. Buy

A decision document for the RFQ2BOQ project after a deep market scan (May 2026).

The question you raised: **"This is common — others are doing it. Why are we building from scratch instead of scraping/reusing what exists?"**

This document answers that honestly, lists every relevant existing resource, and proposes three forward paths so you can choose with full information.

---

## 1. TL;DR

**Yes — most of what we built has an existing equivalent.** The honest answer:

- 10+ commercial BOQ-extraction products already exist (Kreo, BuildVisionAI, QSmaster, Realx, IntoAEC, ProQsmart, Turian).
- 5+ Indian tender-AI products already cover CPWD/NHAI/state PWD tracking (Nexizo, ContraVault, Bid India, Aitenders, Civils.ai).
- A construction-specific BERT (ARCBERT) was already published in 2022.
- Construction ontologies (OmniClass, IFC, MasterFormat, UniClass, ifcOWL) are open ISO standards we could have used instead of inventing one.
- CPWD DSR, state SORs, and Indian e-tenders are all publicly downloadable.

**What we still have that's defensible:**
- Indian-specific focus (IS codes, Hindi/Devanagari, DSR rate integration)
- On-prem / open-source posture (most competitors are SaaS)
- BIOES schema + 8 entity ontology specifically tuned for Indian RFQ language
- End-to-end pipeline (PDF → entities → relations → BOQ → cost → IFC/SAP export) — most competitors only do parts

**The right move depends on which game you're playing:**
- **Internship/portfolio** → finish what you have, frame it as a research contribution
- **Real product / commercial** → pivot to *leverage* mode: use existing ontologies, pretrained models, scraped data; differentiate on niche
- **Hybrid** → leverage where free, scratch-build where it matters for the differentiator

---

## 2. What already exists (deep scan)

### 2.1 Commercial BOQ / takeoff / RFQ extraction (global)

| Product | Capability | Notes |
|---------|------------|-------|
| Kreo Software | AI BoQ from 2D/3D drawings | UK; production-grade |
| BuildVisionAI | Blueprint → BOQ by trade & CSI code | US; CSI integration |
| QSmaster | AI takeoff + BOQ generation | Quantity surveyor focused |
| Realx ERP | DXF/DWG/PDF → BOQ, material estimation, costing | India-based ERP integration |
| IntoAEC | BOQ for QS & contractors | Indian/UK |
| ProQsmart | NLP-driven RFQ intake, 10k+ line items | Email/PDF parsing emphasized |
| Turian | LLM-driven BoQ automation | Sales-team focused |
| FlowSense | 78% time reduction claim | Mid-size projects |
| C-Link | Tender analysis using AI/ML | Quantity surveyor industry |
| Procol | RFQ + BOQ + bid scoring in one platform | Procurement-focused |

### 2.2 Indian tender-AI products

| Product | Specific to | Notes |
|---------|------------|-------|
| Nexizo.ai | CPWD, NHAI, state PWD tracking | Closest to our target |
| ContraVault AI | RFP analysis, auto-fill bid docs | Tender prep automation |
| Bid India | Tender discovery + bid mgmt | Discovery-focused |
| Aitenders | Tender + contract mgmt | Multi-country |
| Civils.ai | Construction tender prep | UK + India |
| Minaions | MSME smart bidding | India MSME focus |
| TendersOnTime | India AI tender alerts | Alert-driven |

### 2.3 Pretrained domain models

| Model | Domain | Availability |
|-------|--------|--------------|
| **ARCBERT** | Architecture / Engineering / Construction | Published 2022 (ScienceDirect); we should have started here |
| SciBERT | Scientific text (biomedical + CS) | Free on HF — `allenai/scibert_scivocab_uncased` |
| BioBERT | Biomedical | Free on HF |
| FinBERT | Finance | Free on HF |
| `bert-base-cased` | General English | What our model actually started from |
| `xlm-roberta-base` | 100 languages incl. Hindi | What our bilingual prompt specifies |
| `microsoft/layoutlmv3-base` | Layout-aware doc understanding | Free; we use it in S1 |
| `microsoft/table-transformer-detection` | Table extraction in docs | Free; we use it in A2 |

### 2.4 Open construction ontologies / standards

| Standard | Authority | What it gives us |
|----------|-----------|------------------|
| **OmniClass** | CSI (US) | 15 hierarchical tables: products, materials, elements, work results, properties |
| **MasterFormat** | CSI | Specification of work results — directly maps to BOQ line items |
| **UniFormat** | CSI | Building elements |
| **UniClass 2015** | NBS (UK) | UK building classification, faceted |
| **IFC** | buildingSMART (ISO 16739) | Building data model |
| **ifcOWL** | W3C/buildingSMART | OWL ontology of IFC — formally reasonable knowledge graph |
| **COBie** | NBIMS | Construction operations building information exchange |

### 2.5 Public data sources (Indian focus)

| Source | URL | Format | Status |
|--------|-----|--------|--------|
| CPWD DSR 2023 | `cpwd.gov.in/Publication/DSR14.pdf` | PDF | Public domain |
| CPWD DAR (rate analysis) | `cpwd.gov.in` | PDF | Public domain |
| Delhi SOR (E&M) | `cpwd.gov.in` | PDF | Public domain |
| State SORs (Maharashtra, Karnataka, Tamil Nadu, etc.) | State PWD sites | PDF | Public domain |
| NSR-Civil aggregator | `nsrcivil.in` | Web/API | Aggregated |
| Indian Railways DSR mirror | Railway engineering dir | PDF | Public domain |
| GeM portal tenders | `gem.gov.in` | Web | Scrapeable with rate-limit |
| etenders.gov.in | Government | PDF | Scrapeable; NDSAP-compliant |
| OCDS (open contracting) | `data.open-contracting.org` | JSON | Standardized procurement data, ~70 countries |

### 2.6 Existing research / academic work

| Paper | Year | Relevance |
|-------|------|-----------|
| Yin et al., Computer-Aided Civil & Infra Eng | 2024 | Deep NLP ontology learning from BIM — directly related |
| Pretrained domain LM for AEC (Auto. in Construction) | 2022 | ARCBERT origin paper |
| Automation in Construction Cost Budgeting (IEOM Dubai) | 2024 | LLM cost estimation |
| State-of-art LLMs for construction cost estimation | 2025 | Modular CoT for cost; very recent |
| Automating Quantity Extraction (Drogemuller & Tucker) | 2003 | Foundational |
| Generative AI for BoQs in cost management | 2024 | Transformer-based BoQ generation |

---

## 3. Honest gap analysis — what we built vs. what exists

| What we built | Existing equivalent | Honest assessment |
|---------------|---------------------|-------------------|
| Our 8-entity schema | OmniClass Tables, MasterFormat | We invented; OmniClass would've been a stronger standard |
| Our knowledge graph (Neo4j, custom JSON) | ifcOWL, OmniClass RDF | We invented; ifcOWL exists as W3C OWL form |
| BERT-BiLSTM-CRF trained from scratch on synthetic | ARCBERT (already exists) | We should have fine-tuned ARCBERT |
| Synthetic RFQ generator (300 docs) | CPWD DSR public PDFs (hundreds) | We synthesized when real existed |
| Cost engine with hardcoded rates | NSR-Civil API, state SOR PDFs | We could have integrated rather than coded |
| Custom annotation pipeline | OCDS standardized procurement schema | Aligning to OCDS would make our data portable |
| Hindi support (A6) | xlm-roberta + already-translated standards | A6 is fine; uses existing multilingual model |
| Layout-aware NER (S1) | Free `microsoft/layoutlmv3-base` | We used the right thing |
| Table extraction (A2) | Camelot + Table Transformer | We used the right thing |
| SpERT joint NER+RE (A1) | Published model | We used the right architecture |
| End-to-end pipeline | No single competitor has all 7 stages open-source | **This is genuine differentiation** |

**Score:** ~60% of what we built duplicates existing work; ~40% is genuine.

---

## 4. Three forward paths

### Path A — "Finish what you have" (internship / portfolio frame)

**When to choose:** You want a defensible internship deliverable; commercial viability isn't the goal.

**Do:**
- Close the 19 audit-identified gaps (esp. C3 Observability, A6 Hindi, C2 Security)
- Collect 50 real RFQ PDFs (A8) — proves real-world performance
- Frame the technical report honestly: "Re-implements established techniques on the Indian construction NER niche; the contribution is the hybrid architecture + the open Indian-specific dataset + the end-to-end pipeline."

**Don't:**
- Try to monetize or compete with existing products
- Hide the fact that 60% of components have prior art

**Pros:** Clean finish line, defendable academically, you control the timeline.
**Cons:** Doesn't position for product/job leverage beyond "I shipped a system."

---

### Path B — "Pivot to leverage" (real product frame)

**When to choose:** You want this to keep going post-internship as a real product or to underpin a job/startup pitch.

**Do these moves IN ORDER:**

1. **Replace synthetic with real corpus (1 week)**
   - Scrape 500–1000 CPWD/NHAI/state-PWD PDFs via `scripts/scrape_etenders.py`
   - Use CPWD DSR PDFs as additional training source
   - Replace `data/synthetic/` as primary training data; keep synthetic as augmentation only

2. **Swap base model to ARCBERT (3 days)**
   - Replace `bert-base-cased` with the published ARCBERT (or, if not freely available, with SciBERT as nearest free analog)
   - Re-train NER on real corpus
   - Expected lift: +5–10 F1 points on real data

3. **Anchor schema to OmniClass + IS codes (1 week)**
   - Map our 8 entity types to OmniClass tables (Materials → Table 23 Products, Standards → Table 41 Materials properties, etc.)
   - Adopt MasterFormat codes for work results
   - Adopt ifcOWL for knowledge graph instead of our custom Neo4j schema
   - Output BOQs can then be exported as standards-compliant IFC

4. **Integrate NSR-Civil / DSR APIs for cost engine (3 days)**
   - Replace our hardcoded rate library with NSR-Civil aggregated data
   - Fall back to CPWD DSR for missing items
   - Document data source per cost estimate

5. **Differentiate on niche (ongoing)**
   - **Indian focus**: IS codes, Hindi/Devanagari, DSR/state SOR integration
   - **On-prem / open-source**: Most competitors are closed SaaS — your model can run air-gapped (huge advantage for defense/PSU clients)
   - **End-to-end**: Most competitors solve one stage — yours covers PDF → cost → IFC export in one pipeline
   - **Pricing**: ₹0 self-hosted vs. ₹X/month SaaS

**Pros:** Strongest positioning. Lower technical risk (standing on standards). Real F1 should jump significantly.
**Cons:** Significant rework. Requires re-doing some Wave 0/1 decisions.

---

### Path C — "Hybrid" (recommended for you specifically)

**When to choose:** You want internship credit AND a credible product path. You have 4–6 more weeks.

**Phase 1 — keep what works (Weeks 1–2):**
- Close A8 (real RFQs) — non-negotiable for credibility
- Close the most important audit gaps (C3 Observability, A6 Hindi, C2 Security)
- Keep our custom BIOES schema + BERT-BiLSTM-CRF — it works, it's your portfolio piece

**Phase 2 — selectively leverage (Weeks 3–4):**
- Adopt OmniClass mapping table (`docs/omniclass_mapping.md`) — links our 8 entities to standard classifications. This adds standards compliance without rewriting code.
- Adopt ifcOWL for IFC export only (we already have `src/export/adapters/ifc_export.py`) — just point it at the standard ontology
- Use CPWD DSR PDFs as additional training corpus alongside synthetic (best of both worlds)
- Try fine-tuning from SciBERT or any freely-available domain model as A3 alternative — A/B against your current model

**Phase 3 — position (Weeks 5–6):**
- Rewrite README + report to acknowledge prior art transparently
- Frame contribution as: *"End-to-end open-source pipeline for Indian construction RFQ→BOQ with Hindi support, BIOES 8-entity schema for the Indian sub-domain, fine-tuned on real CPWD/NHAI corpus, exporting to standards-compliant IFC."*
- Patent provisional filing only if there's a genuinely novel sub-system (probably the hybrid ML+rules conflict resolution algorithm — that's defensibly novel)

**Pros:** Honest framing. Builds on standards. Keeps your existing work credit. Realistic timeline.
**Cons:** Requires honest re-framing of what's novel vs. derivative.

---

## 5. Specific reuse decisions to make

Decide each of these, then I'll generate the relevant task prompts.

| Question | Option A | Option B | Recommendation |
|----------|----------|----------|----------------|
| Base NER model | Keep custom BERT-BiLSTM-CRF | Fine-tune from ARCBERT/SciBERT | B if ARCBERT obtainable; A otherwise |
| Training data | Synthetic + real (mixed) | Real only (CPWD scraped) | Mixed (best F1) |
| Entity schema | Keep our 8-entity BIOES | Adopt OmniClass tables | Keep ours; map TO OmniClass for export |
| Knowledge graph | Custom Neo4j | ifcOWL | ifcOWL — it's W3C standard |
| Cost rate library | Hardcoded JSON | Scrape CPWD DSR | Scrape DSR; fall back to JSON |
| Ontology source | Our `data/ontology/*.json` | OmniClass + MasterFormat | Map ours to both — bidirectional |
| Output format | Our schema/boq.v1.json | IFC + OmniClass codes | Both — JSON internally, IFC for export |
| Frontend | Streamlit + Next.js | Use existing (Kreo plugin model) | Keep ours (open-source moat) |
| Real RFQ collection | Skip (internship demo) | Scrape 500+ from etenders.gov.in | Scrape — credibility-critical |
| Hindi support | Keep A6 as planned | Use existing Indic NLP (IndicBERT/IndicNER) | Use IndicBERT as base model |

---

## 6. What to do RIGHT NOW

Three actions, all parallel-safe, no decision required yet:

1. **Scrape CPWD DSR PDFs** — cost is zero, value is huge for both training corpus and rate library. Take 1 day.
2. **Map our 8 entities to OmniClass** — produces `docs/omniclass_mapping.md`. Pure documentation. Takes 2 hours. Locks in standards compliance with no code change.
3. **Test ARCBERT availability** — if it's downloadable, fine-tuning on top is a low-risk experiment that may unlock significant F1 gains.

These three don't commit you to any of paths A/B/C. They give you optionality.

---

## 7. Where to NOT reuse

A few places we should keep building, not borrowing:

- **The hybrid ML + rule conflict resolution algorithm** — genuinely novel; defensible IP
- **BIOES-tagged Indian construction NER dataset** — there is no public equivalent; this is academic contribution
- **Synthetic RFQ generator** — the templates encode domain knowledge that's hard to reproduce
- **Indian-specific entity ontology (IS codes, DSR units, regional materials)** — no off-the-shelf replacement

These are your defensible moat.

---

## 8. Verdict

**You over-built in places where standards/products already exist** (ontology, base model, cost engine, knowledge graph format). **You under-built in places where you have unique angles** (real Indian corpus, Hindi support, end-to-end open-source positioning).

The fix is **not** to throw work away. The fix is to **re-anchor the existing work to open standards** (so it gains credibility from being interoperable) and **swap a few foundational pieces** (base model, training data) to drastically improve real-world performance.

This is a 2–3 week rework, not a rewrite. And it makes the project legitimately competitive with the commercial products listed in §2.1–2.2.

---

## Decision needed from you

Pick one:

- **A** — Finish as-is, submit, move on
- **B** — Full pivot: rip out duplicates, leverage standards & pretrained models
- **C** — Hybrid (recommended): keep work, anchor to standards, swap key foundations

Once you decide, I'll generate the exact task prompts for whichever path.

---

## Sources

This document was assembled from a deep web scan in May 2026. Key sources cited:

- [ProQsmart — Automated RFQ creation tool](https://proqsmart.com/blog/how-an-automated-rfq-creation-tool-builds-complex-tenders-in-under-20-minutes/)
- [BuildVisionAI BoQ Generation](https://www.buildvisionai.com/features/boq-generation)
- [Kreo — AI in Bills of Quantities](https://www.kreo.net/news-2d-takeoff/ai-in-bills-of-quantities)
- [Realx ERP — BOQ software for construction](https://realxerp.com/construction-boq-software.php)
- [IntoAEC — BOQ for Quantity Surveyors](https://intoaec.ai/boq/)
- [DesignDrafter — Quantity extraction in construction 2026](https://designdrafter.com/quantity-extraction-in-construction-how-ai-is-replacing-manual-boq-with-smart-automation-in-2026/)
- [Turian — BoQ AI automation](https://www.turian.ai/use-cases/bill-of-quantities)
- [Nexizo — AI for Indian construction tenders (CPWD/NHAI/PWD)](https://nexizo.ai/blogs/ai-for-construction-tenders-how-to-win-more-cpwd-nhai-and-state-pwd-contracts)
- [ContraVault AI — RFP analysis](https://www.contravault.com/)
- [C-Link — Tender analysis using AI/ML](https://c-link.com/blog/the-future-of-quantity-surveying-tender-analysis-using-ai-ml/)
- [ARCBERT / Pretrained domain language model for AEC](https://www.sciencedirect.com/science/article/abs/pii/S0166361522001300)
- [SciBERT (allenai)](https://github.com/allenai/scibert)
- [OmniClass — Construction Specifications Institute](https://www.csiresources.org/standards/omniclass)
- [ifcOWL — buildingSMART](https://technical.buildingsmart.org/standards/ifc/ifc-formats/ifcowl/)
- [Yin et al. — Deep NLP ontology learning from BIM](https://onlinelibrary.wiley.com/doi/full/10.1111/mice.13013)
- [State-of-art LLMs for construction cost estimation (Preprints.org 2025)](https://www.preprints.org/manuscript/202510.1060)
- [CPWD Delhi Schedule of Rates 2014 PDF](https://cpwd.gov.in/Publication/DSR14.pdf)
- [NSR-Civil — Indian state rates aggregator](https://nsrcivil.in/)
- [State-wise SOR India 2026 (Infralens)](https://infralens.in/knowledge/state-wise-sor-india-2026)
- [Actowiz — Scraping Government Portals in India (compliance)](https://www.actowizsolutions.com/government-data-scraping-india-compliance-guide.php)
- [OCDS — Open Contracting Data Registry](https://data.open-contracting.org/en/search/)
- [Open Building Information Modeling Standards (COBIE, OMNICLASS)](https://buildinginformationmanagement.wordpress.com/2013/02/18/open-bim-standards-cobie-omniclass-ifc-cobie-report-2012/)
