# Meeting Voices — COMPLETE (June 11, 2026)

> All insights from the SWA Consultancy internship review meeting. Give this to your agents.

---

## 1. Training / Agent Orchestration

**Question asked:** "Unsupervised or are you actively supervising and guiding the training?"

**Answer:**
> "It's a hybrid approach — high-level human guidance with heavy automation. I give strategic direction and protocols to the orchestration agent. It breaks that down into concrete tasks and assigns them to specialized agents that run throughout the day. The actual training and execution happen automatically. As soon as I open my laptop or it becomes active, the agents pick up where they left off and continue working. So I'm steering the system at the orchestration level while the agents handle the day-to-day execution autonomously."

**Key point:** Not micromanaging. Human steers at orchestration level. Agents execute autonomously.

---

## 2. Large PDF Handling — Structure-Aware Extraction

**Insight:**
> "For larger PDFs — especially 50 to 100+ page government tenders — we can make the system much more efficient by first extracting the document structure. Government formats are quite consistent. They rarely change the overall layout because estimators manually go through titles, subtitles, sections, and subsections to locate the BOQ. So instead of processing the entire document, we can: extract the hierarchical structure (main titles → subtitles → sections → subsections → annexures), identify which sections are most likely to contain BOQ content, then run the extraction pipeline only on those relevant parts. This mirrors how a human estimator works and significantly reduces noise and processing time on very large files."

**Action for agents:** Implement structure-aware extraction as a preprocessing step before the existing pipeline.

---

## 3. Data Accuracy Requirement

**Requirement:**
> "Whatever data is present in the document must be converted with 100% accuracy. There is zero tolerance for missing information, incorrect mappings, or data loss. Every field, value, and detail available in the source document should be captured correctly during processing."

**Current status:** Only 1 document available. More documents requested and will be shared soon.

---

## 4. GeM Portal + NER Reference

**Insight:**
> "In the GeM (Government e-Marketplace) portal, tenders and procurement requirements are based on predefined product catalogs. Buyers select products directly from an existing standardized list. This eliminates any possibility of paraphrasing, spelling variations, or inconsistencies in product descriptions. Sellers also choose from the same catalog. This creates a highly structured marketplace with common product definitions. To support the NER process, we can provide the product list that has already been submitted in the GeM portal. This list contains all relevant materials and products for this category and can serve as a reliable reference dataset for entity extraction and validation."

**Action for agents:** Integrate GeM product catalog as a gazetteer/dictionary for the NER pipeline.

---

## 5. Additional Document Collection

**Plan:**
> "We should collect additional documents for training and validation. Coordinate internally with the Sales team, Jineth, or Softnil's archive, which contains historical RFQs, quotations, and related procurement documents. Our target should be around 100 PDF documents as an initial dataset. This will provide a strong foundation for development, testing, and validation."

**Action:** Human coordination task. Contact Sales team, Jineth, and Softnil archive.

---

## 6. Parallel Project

**Update:**
> "Started working on another project a couple of days ago. ZIP file downloaded and reviewed. Work is in progress. This parallel project is primarily focused on implementing business logic in code. It has significantly fewer edge cases, data inconsistencies, and debugging efforts compared to the RFQ/document-processing project. Therefore, it should be relatively straightforward and faster to develop."

**Note:** Separate from RFQ2BOQ. Agents should not touch unless explicitly assigned.

---

# Agent Task Priority (Post-Meeting)

## P0 — Before Next Demo
1. ~~Fix 01 GSECL PDF page classification~~ ✅ DONE
2. ~~Fix 04 Adani PDF output quality~~ ✅ DONE (partial)
3. Commit all changes ✅ DONE

## P1 — This Week
4. Fix 09 GeM PDF speed (3.6+ min hang)
5. Implement structure-aware PDF extraction (titles/subtitles → BOQ section routing)
6. Integrate GeM product catalog as NER gazetteer

## P2 — Next 2 Weeks
7. Collect and annotate 100 PDF dataset (coordinate with Sales/Jineth/Softnil)
8. Retrain NER model with real data + GeM catalog
9. Achieve 100% data accuracy on all extracted fields
