# TASK: P3T2 — Polish Streamlit UI for Non-Technical Estimators — Agent-3

**Phase:** 3 | **Effort:** 2 days | **Priority:** P1

## 1. GOAL
Make `ui/app.py` usable by a construction estimator who has never touched ML, with the simplest possible flow: drag PDF → click button → see BOQ table → download Excel. Strip everything that confuses a non-technical user.

## 2. CONTEXT
Read first:
- `ui/app.py` — current Streamlit UI
- `src/pipeline.py` — top-level Pipeline
- `src/domain/models.py` — BoqRow shape (what to display)
- `src/export/excel_generator.py` — Excel output
- [docs/HYBRID_PLAN.md](../../../docs/HYBRID_PLAN.md) § "What the company actually sees"
- [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)

Current UI has tabs, charts, debug info, technical jargon. Target user: a quantity surveyor or junior estimator. They want: upload, extract, edit, export.

## 3. DELIVERABLES
- [ ] `ui/app.py` — rewritten / polished Streamlit app
- [ ] `ui/assets/logo.png` — small RFQ2BOQ logo (or placeholder)
- [ ] `ui/assets/sample_rfq.pdf` — one bundled sample so users can try without their own PDF
- [ ] `ui/help.md` — short user help (3 paragraphs max)
- [ ] `docs/user_guide.md` — updated walkthrough with screenshots placeholder
- [ ] Smoke verification by running locally

## 4. STEPS
1. Read context.
2. **Strip jargon**:
   - No mentions of: "NER", "BIOES", "BERT", "CRF", "ontology", "confidence threshold", "F1"
   - Replace with: "extraction", "tagging", "model", "quality score", "accuracy"
3. **Simplify layout**:
   - Single-page (no tabs unless absolutely necessary)
   - Top: Title + 1-line description
   - Main area:
     1. Drag-and-drop PDF uploader (with "Try sample" button)
     2. Progress bar during extraction
     3. BOQ table (editable cells)
     4. Download buttons: "Download Excel", "Download JSON", "Download CSV"
   - Sidebar: project name, region selector (Delhi/Mumbai/Bangalore/etc.), reset button
4. **BOQ table polish**:
   - Columns: # | Description | Quantity | Unit | Rate (₹) | Amount (₹) | Standard | Grade | Confidence
   - Inline-edit support
   - Color-code Confidence: green (>0.8), yellow (0.5–0.8), red (<0.5) — labeled "Quality"
   - Show grand total at bottom
   - Show warnings panel (scope gaps) collapsed by default
5. **Sample PDF**:
   - Use one of `data/samples/sample_rfq_simple.pdf` (already exists)
   - "Try sample" button loads it
6. **Error handling**:
   - If extraction fails: show friendly message "Could not read this PDF. Try a different file or contact support."
   - Never show stack traces
7. **Help**:
   - `ui/help.md` is 3 paragraphs: what it does, how to use, who to contact for support
   - Accessible via a "?" icon in the sidebar
8. **Test the UI manually**:
   - Start with `streamlit run ui/app.py --server.port 8501`
   - Upload sample PDF
   - Verify table renders, download works

## 5. VERIFICATION
```bash
# UI files exist
$ ls ui/app.py ui/help.md ui/assets/sample_rfq.pdf
EXPECT: all three exist

# UI starts without error (background test)
$ timeout 10 python3 -m streamlit run ui/app.py --server.port 8502 --server.headless true 2>&1 | grep -E "You can now view|already in use|Streamlit"
EXPECT: "You can now view" appears (UI is up)

# No technical jargon (basic check)
$ grep -i "BIOES\|BERT-BiLSTM\|CRF\|micro-F1\|ontology loader\|conflict resolution" ui/app.py
EXPECT: no output (or only in comments)

# Pipeline integration smoke
$ python3 -c "
from src.pipeline import Pipeline
p = Pipeline()
print('pipeline ready')
"
EXPECT: "pipeline ready"

# Help doc concise
$ wc -w ui/help.md | awk '{print $1}'
EXPECT: ≤300 words
```

## 6. ACCEPTANCE CRITERIA
- [ ] UI starts cleanly on port 8501
- [ ] Drag-drop upload works
- [ ] "Try sample" works
- [ ] BOQ table renders with all required columns
- [ ] Confidence column color-codes correctly
- [ ] Excel/JSON/CSV downloads work
- [ ] No technical jargon visible to user
- [ ] Errors handled gracefully (no stack traces)
- [ ] Help available and concise

## 7. CONSTRAINTS
- All imports `src.` prefix
- DO NOT add new dependencies beyond what's already in pyproject
- Keep file size: `ui/app.py` ≤ 500 lines
- Streamlit version pinned via existing pyproject
- DO NOT show internal model names, confidence math, or technical details

## 8. DEPENDENCIES
- **Blocked by:** P3T1 (uses the final model)
- **Blocks:** None
- **Parallel-safe with:** P3T3, P3T4

## 9. GOTCHAS
- Streamlit reruns on every interaction — cache the pipeline (`@st.cache_resource`)
- Large PDFs (>10MB) freeze the UI — show progress + spinner
- Color-coding may not be obvious to colorblind users — also add a text label ("Good", "Check", "Verify")
- Sample PDF must be small (<2MB) so it loads fast
- Streamlit's file-uploader has a 200MB default limit — keep
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)
