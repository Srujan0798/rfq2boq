# Q&A Preparation

## Likely Questions & How to Answer

### Q: "Why is the F1 only 43%? That seems low."
**A:** "Two reasons. First, PDF extraction is genuinely hard — tables with merged cells and complex layouts. Second, there's an evaluation mismatch: our gold data expects short material names like 'Mineral Wool,' but the pipeline outputs full descriptions. Row-level evaluation shows much better alignment. The XLSX files, which are easier, perform significantly better."

### Q: "When will this be production-ready?"
**A:** "For Excel-based tenders, it's usable now. For PDFs, we need two things: fix the known bugs I mentioned, and get human annotations on 20 to 40 real tenders to retrain the NER model. With real data, we can realistically hit 70 to 80% F1. Timeline depends on annotation pace."

### Q: "What was your biggest mistake?"
**A:** "Early on, we used synthetic training data and believed the 99% F1 score. It took real evaluation on actual tenders to see the gap. The lesson: always validate on real data, never trust synthetic metrics. We fixed this by implementing honest, independent evaluation."

### Q: "Why pattern-based NER instead of deep learning?"
**A:** "With only 20 real annotated documents, deep learning overfits. Our LoRA model scored 75% on validation but only 19% on held-out real documents. Pattern-based NER — regex plus gazetteer — is more reliable with limited data. Once we have 50-plus real annotations, we can switch to ML."

### Q: "What would you do differently?"
**A:** "Start with real data collection on day one, not synthetic generation. And enforce one-agent-at-a-time from the start — parallel agents on one repo caused file deletions and conflicting changes that cost us time."

### Q: "What's the business value?"
**A:** "An estimator currently spends 2 to 4 hours per tender manually extracting BOQ. This system does it in under 30 seconds for Excel files. Even at 43% F1, it provides a strong starting point that an estimator can review and correct, saving significant time. As accuracy improves with more training data, the value increases."

### Q: "How do you know the evaluation is honest?"
**A:** "Three safeguards. One: gold files are human-verified, not auto-generated from pipeline output. Two: we check git diffs to ensure gold wasn't modified. Three: we run independent row-level evaluation that matches complete BOQ rows, not just material names."

### Q: "What about scanned PDFs?"
**A:** "We have OCR fallback with pytesseract. It works for scans above 300 DPI. Below that, accuracy drops. This is a known limitation documented in our scope."

### Q: "Can it handle Hindi tenders?"
**A:** "We built an IndicBERT module and integration, but model download was blocked by network restrictions at the time. The architecture supports it — we'd need to download the model and annotate Hindi-specific training data."

### Q: "What's the cost of running this?"
**A:** "On a MacBook with MPS, cold start is 8 to 12 seconds, then under 30 seconds per Excel file. Memory usage is about 2 GB with the model loaded. For production deployment, a single CPU instance with 4 GB RAM would handle the load."

### Q: "How does this compare to manual extraction?"
**A:** "Manual extraction by an estimator takes 2 to 4 hours per tender. Our system takes 30 seconds for Excel, 1 to 2 minutes for PDF. The trade-off is accuracy: manual is near-perfect but slow; automated is fast but needs review. The sweet spot is using automation as a first draft that an estimator validates."

---

## If You Don't Know the Answer

**Never guess.** Say one of these:

- "That's a great question. I haven't tested that specifically, but my hypothesis is..."
- "I'd need to run an experiment to confirm. I can follow up with the results."
- "That's outside my current scope, but it's a valuable direction for future work."
- "Let me check my notes and get back to you on that."

**Never:**
- Make up numbers
- Claim something works if you haven't tested it
- Promise timelines you can't deliver
