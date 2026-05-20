# Hybrid Plan — The Practical Way Forward

A plain-language plan for a non-technical audience.
The goal: best of both worlds — keep what we built that works, plug in proven free tools where they exist, drop what we don't need. No over-engineering. No academic flexing. Just a solid working product.

---

## The Big Idea (in one line)

> **Stop building from scratch what already exists for free. Keep what's uniquely ours. Combine the two cleanly.**

The previous strategic review (`STRATEGIC_REVIEW.md`) was correct but a bit advanced. This document is the practical, decision-ready version.

---

## What we already have that's worth keeping (DON'T touch these)

| What we built | Why keep it |
|---------------|-------------|
| **Full end-to-end pipeline** (PDF → entities → BOQ → Excel/JSON/CSV) | Works today. Tested. 245+ tests pass. |
| **8-entity Indian construction schema** (MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE) | Specific to Indian RFQs. Nothing better exists. |
| **BIOES tagging** (more precise than basic BIO tagging) | Already trained the model on this. Better quality. |
| **Hybrid ML + rules approach** | Genuinely smart — handles ambiguity better than pure ML or pure rules. |
| **The Streamlit UI** | Non-technical people can actually use it. |
| **The synthetic data generator (300 RFQs)** | Useful for training when real data is sparse. |
| **All the API/CLI/exports** (FastAPI, Typer, Excel, JSON, CSV) | Standard stuff, already working. |

**Verdict:** ~40% of our work is genuinely valuable. We keep it.

---

## What we should REPLACE (plug in free official versions)

Each row below is a thing we built ourselves that has a better, free, official alternative we can just *download and use*.

### 1. Hindi support → use **IndicBERT** (from IIT Madras / AI4Bharat)

| | |
|--|--|
| **What it is** | Free pretrained model from IIT Madras that already understands Hindi + 11 other Indian languages. |
| **Why use it** | Trained on billions of Indian words. Better than us training from scratch. MIT license — free for commercial use. |
| **How to use** | Download from HuggingFace: `ai4bharat/indic-bert`. One line of code change. |
| **Effort** | 1 day to swap in. |
| **What we cut from our plan** | A6 prompt to train a custom bilingual model from scratch. We don't need to. |

### 2. Construction language understanding → use **ARCBERT** (Tsinghua University, 2022)

| | |
|--|--|
| **What it is** | A BERT model already trained on millions of construction documents. Published research, free download. |
| **Why use it** | Already understands construction vocabulary (IS codes, materials, units). Our model has to learn this from scratch. |
| **How to use** | Download from the authors' GitHub. Fine-tune on our Indian data. |
| **Effort** | 2–3 days. |
| **What we cut from our plan** | A3 prompt to pre-train ConstructionBERT from a 50,000-document corpus we'd have to scrape. We skip that step entirely. |

### 3. Construction rates → use **CPWD DSR 2023 PDFs** + **NSR-Civil aggregator**

| | |
|--|--|
| **What it is** | The official government rate book for construction in India. Free PDF download. NSR-Civil aggregates state SORs too. |
| **Why use it** | Our cost estimator currently has ~200 hardcoded rates. CPWD DSR has thousands, official, accepted by every Indian PSU/government client. |
| **How to use** | Download PDFs from `cpwd.gov.in/Publication/`, parse with our existing PDF pipeline, populate rate library. |
| **Effort** | 3 days. |
| **What we cut from our plan** | Maintaining our own rate JSON files manually. |

### 4. Knowledge graph → use **OmniClass** + **ifcOWL** (free open standards)

| | |
|--|--|
| **What it is** | International standards used by every BIM tool on the planet. Free. Maintained by industry bodies. |
| **Why use it** | Anyone our exports go to (Revit, AutoCAD, SAP) already speaks these standards. Today they have to manually map our format → their format. |
| **How to use** | Add a mapping table: our 8 entities ↔ OmniClass codes. Just a JSON file. |
| **Effort** | 2 hours (it's just a lookup table). |
| **What we cut from our plan** | Inventing our own knowledge-graph schema from zero. |

### 5. Real RFQ data → **CPWD/MES/state PWD public tender portals**

| | |
|--|--|
| **What it is** | Government tender PDFs are public domain in India (NDSAP/RTI policy). Hundreds available. |
| **Why use it** | We trained on synthetic data; real F1 is only 67%. Real training data will push it to 80%+. |
| **How to use** | Manual download (slow but legal) OR controlled scraping with rate-limit + robots.txt compliance. |
| **Effort** | 1 week (collection + cleanup + annotation of 50). |
| **What we cut from our plan** | Pretending synthetic data is good enough. |

### 6. Pre-existing BOQ matching code → look at **BOQ-Matching** (GitHub, MIT-licensed)

| | |
|--|--|
| **What it is** | Open-source Python project that matches Master BOQ items to Project BOQ items using TF-IDF + SpaCy. |
| **Why use it** | Useful as a sanity-check / inspiration. Their LDA topic modeling approach for grouping similar items is a good idea we could borrow. |
| **How to use** | Read the code, optionally borrow the matching idea for our deduplication module. |
| **Effort** | 1 day to evaluate. |
| **What we cut from our plan** | N/A — this is additive insight, not a replacement. |

---

## What we should CUT entirely (over-built, not needed for company use)

These are things we (or our agents) built that don't pull weight for a non-technical audience and add maintenance burden.

| Item | Why cut |
|------|---------|
| **Neo4j knowledge graph** (S2) | Overkill. JSON ontology + simple lookups is enough for our scale. Neo4j adds a database to maintain. |
| **SpERT joint NER+RE model** (A1) | Adds complexity for marginal accuracy. Our current model + rule-based RE works fine. |
| **MLflow tracking server** (A5) | Pro-level MLOps. Not needed when we train a model once a month. Plain folder + metrics.json is fine. |
| **Voice input** (B3) | Cool, but no construction estimator uses voice. They want PDFs in, Excel out. |
| **Drawing analysis** (B4) | Massive effort (YOLO training, symbol detection), small win. Skip for v1. |
| **Sub-domain models** (B5) | Train 5 separate models for buildings/roads/electrical/plumbing? Maintenance nightmare. One good model is better. |
| **Multi-tenant SaaS billing** (C4) | We're not running a SaaS. We're delivering a tool to one company. Drop Stripe + tenant DB. |
| **Public benchmark + leaderboard** (D3) | Academic ego project. Adds nothing for company users. |
| **Patent filing** (D4) | Talk to SWA Consultancy first. If they say no, drop it. |
| **Mutation testing, chaos engineering, load testing** (C5 pieces) | Way too much for a small/medium product. Keep regular tests, drop the rest. |

**Verdict:** Cutting these saves weeks of work + significantly less code to maintain.

---

## What we keep building / improving (the unique-to-us 30%)

This is the work that's worth doing because no off-the-shelf alternative exists.

| Item | Why keep building |
|------|-------------------|
| **Real Indian RFQ corpus + annotations** (A8) | No public dataset exists; this becomes our moat. |
| **Hybrid ML + rules conflict resolution** | Genuinely novel; defensible IP. |
| **Indian-specific entity behaviors** (M20 grade detection, IS code parsing, DSR unit normalization) | No off-the-shelf model knows these patterns. |
| **End-to-end pipeline gluing everything together** | Each commercial competitor does one part; we do them all. |
| **Risk engine** (B1) | Catches scope gaps + outliers; differentiator for tender reviewers. |
| **LLM ambiguity resolver** (B2) | Calls Claude/GPT only when our model is unsure. Practical. |
| **Excel/IFC/SAP export** | Tangible deliverable for the user. |

---

## The simple 3-phase plan (no academic flexing)

### Phase 1 — Plug in the free official stuff (1 week)

**Goal:** Get the easy wins. No risk, all upside.

1. **Download IndicBERT** → swap into the Hindi-detection path. (1 day)
2. **Download CPWD DSR PDFs** → populate the rate library. (2 days)
3. **Create OmniClass mapping table** → just a JSON file in `data/ontology/omniclass_map.json`. (2 hours)
4. **Manually download 50 real RFQ PDFs** → drop into `data/real_rfqs/raw/`. No fancy scraping. (2 days)

End of Phase 1: project is using official Indian government data and a real Indian-language model.

### Phase 2 — Cut the over-engineering (1 week)

**Goal:** Make the codebase smaller and easier to maintain.

1. Remove Neo4j from `docker-compose.yml`; keep the JSON ontology only.
2. Remove SpERT, MLflow, Voice, Drawing analysis, Sub-domain models, Multi-tenant, Benchmark code from the build (move to `attic/` if you want to preserve, or delete).
3. Slim down the test suite — keep unit/integration/golden, drop mutation/chaos/load.
4. Update CLAUDE.md + README to reflect the slimmed scope.

End of Phase 2: codebase is ~40% smaller, easier to onboard a new developer.

### Phase 3 — Improve the unique 30% (2 weeks)

**Goal:** Make the parts only we can build genuinely great.

1. Fine-tune our NER on ARCBERT + real Indian RFQs. Target real-world F1 ≥ 75%.
2. Strengthen the hybrid ML+rules conflict resolution (Section 7 logic in `src/rules/conflict.py`).
3. Polish the Streamlit UI for non-technical estimators (clearer buttons, simpler workflow).
4. Better Excel export (CPWD-format template, BOQ that looks like an estimator made it).
5. Demo video showing one PDF → BOQ → Excel in 2 minutes.

End of Phase 3: a polished product the company can show clients.

---

## What the company actually sees / uses (the user-facing parts)

The non-technical audience only sees three things:

1. **A web page** — upload PDF, get BOQ. (Streamlit UI — already built.)
2. **An Excel file** — looks like what an estimator hand-crafts. (Excel exporter — already built, can be polished.)
3. **A summary report** — what was extracted, confidence levels, any flagged risks. (Report generator — already built.)

Everything else (the BERT model, the patterns, the rules, the ontology, the API) is plumbing they never see.

**Insight:** We should optimize for *those three visible things*, not for the impressive-looking internals.

---

## Comparison: before vs. after this plan

| Aspect | Today | After this plan |
|--------|-------|----------------|
| Pre-trained base model | `bert-base-cased` (generic English) | `ARCBERT` (construction) + `IndicBERT` (Hindi) |
| Training data | 300 synthetic + 10 pseudo-real | Real CPWD/state PWD tender corpus |
| Rate library | ~200 hardcoded items | Full CPWD DSR + state SORs |
| Ontology | Custom JSON | Mapped to OmniClass/IFC standards |
| Real-world F1 | 67% | Target 80%+ |
| Codebase size | ~213 Python files | ~120 files (after cutting over-engineering) |
| Components to maintain | NLP, KG, MLflow, voice, drawing, billing, benchmark, etc. | NLP, rules, ontology, pipeline, API, UI, export (focused) |
| Audience fit | Built for ML researchers | Built for construction estimators |

---

## What to do RIGHT NOW (your next message decides)

Pick **one** of these to start with. Each is small, low-risk, and unblocks the rest.

- **(a) Phase 1 — Plug in free official stuff** (recommended start; 1 week effort, 0 risk)
- **(b) Phase 2 — Cut over-engineering first** (good if you want to clean before adding)
- **(c) Start by mapping OmniClass** (smallest commit; 2 hours; produces a deliverable today)
- **(d) Start by downloading IndicBERT + ARCBERT** (sets up technical foundation)
- **(e) Start by manually downloading 20 real RFQ PDFs** (immediate credibility win)

Tell me which one and I'll generate the exact instructions for your agent to execute.

---

## Sources (deep-scan May 2026)

### Pretrained models (free, MIT/Apache licensed)

- [IndicBERT v2 — AI4Bharat / IIT Madras (HuggingFace)](https://huggingface.co/ai4bharat/indic-bert)
- [IndicBERT GitHub repo](https://github.com/AI4Bharat/IndicBERT)
- [ARCBERT — Pretrained Language Model for AEC (Lin et al., 2022)](https://linjiarui.net/en/portfolio/2022-04-02-ARCBERT-largescale-dataset-and-pretrained-model-for-AEC-domain)
- [ARCBERT paper on ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0166361522001300)
- [Domain-specific LMs on construction management corpora (Auto. in Construction 2024)](https://www.sciencedirect.com/science/article/pii/S0926580524000529)

### Indian government data (public domain)

- [CPWD DSR 2023 Vol 1 + 2 download link (helptheengineer.com mirror)](https://helptheengineer.com/cpwd-publication/)
- [CPWD DSR Vol 1 Civil PDF (Scribd)](https://www.scribd.com/document/777526980/DSR-Vol-1-Civil-2023-Compressed-2)
- [Civil Engineering Ascent — CPWD SOR 2023 download page](https://civilenggascent.com/cpwd-sor-schedule-of-rates-2023-pdf-download/)
- [NSR-Civil — state SOR aggregator + DSR 2023 corrections](https://nsrcivil.in/cpwd-dsr-2023-corrections/)
- [State-wise SOR India 2026 (Infralens)](https://infralens.in/knowledge/state-wise-sor-india-2026)
- [Open Contracting Data Standard (OCDS) registry](https://data.open-contracting.org/en/search/)
- [Scraping Government Portals in India — compliance guide (Actowiz)](https://www.actowizsolutions.com/government-data-scraping-india-compliance-guide.php)

### Construction standards (free, open ISO/W3C)

- [OmniClass — Construction Specifications Institute](https://www.csiresources.org/standards/omniclass)
- [ifcOWL — W3C OWL ontology of IFC (buildingSMART)](https://technical.buildingsmart.org/standards/ifc/ifc-formats/ifcowl/)
- [Open BIM Standards — COBie + OMNICLASS + IFC overview](https://buildinginformationmanagement.wordpress.com/2013/02/18/open-bim-standards-cobie-omniclass-ifc-cobie-report-2012/)

### Existing open-source BOQ projects (GitHub)

- [BOQ-Matching — TF-IDF + SpaCy BOQ matcher (kondakrindirahul)](https://github.com/kondakrindirahul/BOQ-Matching)
- [BOQ for tender — material calculation tool (surya9teja)](https://github.com/surya9teja/BOQ)
- [BOQ topic on GitHub (all related projects)](https://github.com/topics/boq)
- [OpenNRE — Neural Relation Extraction (Tsinghua)](https://github.com/thunlp/OpenNRE)

### Commercial competitive landscape

- [Nexizo — Indian construction tender AI](https://nexizo.ai/blogs/ai-for-construction-tenders-how-to-win-more-cpwd-nhai-and-state-pwd-contracts)
- [ContraVault AI](https://www.contravault.com/)
- [Kreo Software — AI in BoQ](https://www.kreo.net/news-2d-takeoff/ai-in-bills-of-quantities)
- [BuildVisionAI — BoQ Generator](https://www.buildvisionai.com/features/boq-generation)
- [Realx ERP — Construction BOQ](https://realxerp.com/construction-boq-software.php)
- [IntoAEC — BOQ for QS & contractors](https://intoaec.ai/boq/)

### Research / academic context

- [Yin et al. — Deep NLP for ontology learning from BIM (Wiley/MICE 2024)](https://onlinelibrary.wiley.com/doi/full/10.1111/mice.13013)
- [State-of-art LLMs for construction cost estimation (Preprints 2025)](https://www.preprints.org/manuscript/202510.1060)
- [Generative AI for BoQ generation in cost management (IEOM Dubai 2024)](https://ieomsociety.org/proceedings/2024dubai/466.pdf)
