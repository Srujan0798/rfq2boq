# CORE UNDERSTANDING — RFQ2BOQ (read this before working on the project)

**Locked:** 2026-06-05 · **Source:** derived directly from `resources/` (SWA project brief, implementation guide, academic papers, domain videos, the NER training-data generator).
**Purpose:** the single grounded explanation of *what this project is, what the goal is, what the core problem is, and why our numbers are what they are.* Every agent reads this so we stop re-deriving it and stop repeating the same mistake.

**⚠️ CORPUS SCOPE CORRECTION (2026-07-05):** every "10 SWA enquiries" reference below describes the *frozen TEST-split anchor*, not the whole corpus. **The RFQ corpus is 127 real documents** — see [CORPUS_DEFINITION.md](CORPUS_DEFINITION.md) and `data/real_rfqs/ALL_RFQS_README.md`. This was the single most repeated scoping mistake across agent sessions; read the correction doc before scoping any fidelity/training/eval task.

---

## 1. What the project is (from the SWA brief)
Turn an unstructured **construction tender (RFQ)** — Indian government/private PDFs/Excels — into a structured **Bill of Quantities (BOQ)** in Excel + JSON.
**Pipeline (matches the SWA implementation guide 1:1):**
`PDF/OCR → preprocess → NER → relation extraction → rules/ontology → BOQ assembly → export`
**Schema (locked in `config/constants.py`, confirmed by the source):**
- 8 entities: MATERIAL, QUANTITY, UNIT, LOCATION, DIMENSION, STANDARD, ACTION, GRADE
- 6 relations: HAS_QUANTITY, HAS_UNIT, AT_LOCATION, OF_GRADE, COMPLIES_WITH, HAS_DIMENSION
- BIOES tagging.

**The architecture is correct and faithful to the brief. There is no architecture problem.**

---

## 2. The honest target (from the implementation guide's own benchmarks)
| Metric | Literature target | Requires |
|---|---|---|
| NER F1 (BERT-BiLSTM-CRF) | **0.88** | **1,000+ annotated sentences + 50+ real PDFs** (its Phase 1) |
| End-to-end line-item match | **>85%** | same |
| Processing time | <60s | (we meet this) |

**Where we actually are (honest, re-checked 2026-07-16 with a full `audit_fidelity_per_doc.py --all` run):** NER ~**0.43 F1** on real free text. **Do not claim 100% row F1 or 100% content-match on the sacred-10.** The independent row-capture auditor (`results/fidelity/summary.json`) now shows sacred-10 **10/10 PASS** and the broader BOQ-bearing corpus **33/33 PASS** — every source-truth row captured with zero missing and zero extra under the locked ruler (`08_sael` now passes 16/16). That is a *row-capture* bar, **not** the same as domain NER F1 or content-match accuracy. A separate completeness harness (`results/FIDELITY_REPORT.md` / `measure_fidelity.py`) can report **0 silent drops** when low-confidence output is counted as *flagged* rather than matched content — again **not** the same as 100% row-match F1. Independent product row-match: **82.5%** on four XLSX enquiries (`results/PRODUCT_EVAL.md`). The gap to the NER target is still **data volume** (owner-verified BIOES), and the source says so explicitly.

---

## 3. 🔴 THE CORE PROBLEM (root cause — do not forget this)
**The original NER training data was auto-generated, not human-annotated.**
`resources/ner_training_data.py` is a **script that regex-matches the academic papers and video transcripts** (`COMPLETE_PDF_CONTENTS.md` + `VIDEO_TRANSCRIPTS.md`) and calls the output "training data." So the model was trained on:
1. **Wrong text** — papers/videos *about* construction NLP, not real tender BOQs, and
2. **Circular labels** — the same regex patterns the pipeline already applies.

**Consequence:** the model memorized regex on research-style text → **synthetic/eval F1 ~99% but real F1 ~0.43**, because real Indian tenders look nothing like academic prose. **Every retrain has failed for this one reason: there is no real human-labeled tender data underneath it.**

**Corollary — the anti-cheat rule this project enforces:** never grade the pipeline against gold the pipeline produced (the fake-100% "self-comparison" incidents). Gold must be **independent + human-verified**. A sudden ~100%/perfect score is a red flag, not a win.

---

## 4. Scope note (S1+S2 purges)
Per project scope corrections:
- **S1_STRIP_RATES**: unpriced BOQ only (no Rate/Amount/cost/DSR fields or columns in output/exports/models/schema). Rate lookup out of scope.
- **S2_PURGE_DEMO_SAMPLE**: no data/samples/, data/synthetic/ (purged to attic/ where needed); UI has no "Try Sample", only real tender upload. Generators removed/attic'ed. .gitignore blocks return. Only real_rfqs/ (the 10 SWA + more) and gold/annotations for training.

The core is faithful extraction of quantities and specs from real tenders.

---

## 5. The honest fix path (what actually moves 0.43 → 0.88)
Not more code, not another retrain on the same auto-data. The guide's own **Phase 1**:
1. **Real RFQ PDFs** (target 50+) and
2. **Genuine human BIOES annotation** (target 1,000+ sentences).

Our **10 SWA gold enquiries are the first real instance of this** — the right direction. Replace regex-auto-data with real human-labeled tenders, then retrain. Secondary levers: Zhang & El-Gohary's rule+semantic IE (precision 0.969) for the rule layer; LayoutLMv3 for table/layout.

---

## 6. So, plainly, what we are doing and where we are
- **Doing:** building one honest RFQ→BOQ extraction tool (correct architecture), and replacing its weak auto-generated data foundation with real human-annotated tender data.
- **Where:** tool runs end-to-end on sacred-10 and a wider real corpus; honest numbers are **10/10 sacred-10 auditor PASS / 33/33 broader BOQ-bearing corpus PASS (row capture, zero miss/extra) / ~0.43 NER F1 / 82.5% product row-match**, with a separate completeness report that counts flags toward “no silent drop.” Row capture on the current corpus is demonstrable today; R1 row-capture is met on that corpus, but content-match F1 and neural NER accuracy remain blocked on owner-verified annotated data.
- **Next:** close real fidelity gaps under the independent auditor → real gold (owner-verified) → retrain → the literature's 0.88/85% becomes reachable *if* measured honestly on the frozen TEST split.

**Do not:** chase fake 100%s, train on `data/synthetic/` or regex-auto-data as if it were real, grade the pipeline against its own output, or "re-create" `data/real_rfqs/swa_enquiries/` (it has been deleted 3× by resets — restore from git, never regenerate).

---
*If any number here drifts from reality, re-verify with `scripts/validate_product.py --enquiry all` and update this doc. This is the project's grounded truth — keep it honest. (Durable copy also in Claude's cross-session memory, which survives repo resets.)*
