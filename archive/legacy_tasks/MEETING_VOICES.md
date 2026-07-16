# Meeting Voices — All Points (June 11, 2026)

Give this file to your agents. Every point is brief and actionable.

---

## 1. Training / Agent Orchestration

**Voice:** "It's a hybrid approach — high-level human guidance with heavy automation. I give strategic direction to the orchestration agent. It assigns tasks to worker agents that run autonomously throughout the day. Training starts automatically when the laptop is active. I steer, I don't micromanage."

**Key requirement:** Agents must run autonomously. Human only intervenes at the orchestration level.

---

## 2. Large PDF Handling — Structure-Aware Extraction

**Voice:** "For big PDFs (50-100+ pages), first extract document structure — titles, subtitles, sections, subsections, annexures. Then run extraction only on relevant BOQ sections instead of the full document. Government formats are consistent, so this works well and saves time."

**Technical detail:** Parse document outline (headings, subheadings, section numbers, annexure references). Route NER and table extraction only to sections that historically contain BOQ data. This reduces context length and improves speed/precision on 60-100 page files.

**Action for agents:** Implement structure-aware extraction as a preprocessing step before the existing pipeline.

---

## 3. Data Accuracy Requirement

**Voice:** "100% accuracy required. Zero tolerance for missing information, incorrect mappings, or data loss. Every detail in the source document must be captured correctly."

**Current status:** Only 1 document available. More documents requested and will be shared soon.

---

## 4. GeM Portal + NER Reference

**Voice:** "GeM uses standardized product catalogs. No paraphrasing or spelling variations because buyers and sellers both use the same predefined list. We can provide the product list already submitted in GeM as a reliable reference dataset for NER entity extraction and validation."

**Action for agents:** Integrate GeM product catalog as a gazetteer/dictionary for the NER pipeline. This should boost MATERIAL entity recognition significantly.

---

## 5. Document Collection

**Voice:** "Coordinate with Sales team, Jineth, and Softnil archive to collect historical RFQs and procurement documents. Target: approximately 100 PDF documents as initial dataset for training and validation."

**Action for agents:** This is a human coordination task. Not an agent task.

---

## 6. Parallel Project

**Voice:** "Started 2 days ago. ZIP downloaded and work in progress. This project is mainly business logic implementation — far fewer edge cases and data issues than document processing, so it should move faster."

**Note:** Separate from RFQ2BOQ. Agents should not touch it unless explicitly assigned.

---

## 7. Product Demo Feedback

**Insight from meeting:** The product must be demo-ready with real, working files. No broken demos. The interviewer suggested structure-aware extraction as a clear optimization path.

---

# Agent Task Priority (Post-Meeting)

### P0 — Before Next Demo
1. Fix 01 GSECL PDF page classification (extracts page 5 instead of page 61)
2. Fix 04 Adani PDF output quality (remove duplicates, fix 0 quantities)
3. Commit all changes to git
4. Update demo script with only working files

### P1 — This Week
5. Implement structure-aware PDF extraction (titles/subtitles → BOQ section routing)
6. Fix 09 GeM PDF speed (3.6+ min hang)
7. Integrate GeM product catalog as NER gazetteer

### P2 — Next 2 Weeks
8. Collect and annotate 100 PDF dataset
9. Retrain NER model with real data + GeM catalog
10. Achieve 100% data accuracy on all extracted fields
