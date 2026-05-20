# User Guide

## Getting Started

### Access the System

**Web UI (recommended)**:
```
Open browser → http://localhost:8501 (local) or your deployed URL
```

### Upload a PDF

1. Open the web UI
2. Click **Upload Tender PDF** or drag-and-drop
3. Click **Try Sample Now** to test with a sample document
4. Wait for processing (progress bar shown)
5. View extracted BOQ in editable table format
6. Click **Download Excel** to get the BOQ spreadsheet

### Interpret Results

Each extracted BOQ row contains:

| Field | Description | Example |
|-------|-------------|---------|
| Description | Construction material type | M25 concrete, GI pipe, brick masonry |
| Quantity | Numeric amount | 450, 200, 75 |
| Unit | Measurement unit | m³, kg, sqm, running meter |
| Rate (₹) | Item rate in rupees | 1200, 450 |
| Amount (₹) | Total amount | 540000, 90000 |
| Standard | Relevant standard | IS 456, IS 4923 |
| Grade | Material grade | M25, Fe500D, Class A |
| Quality | Confidence label | Good, Check, Verify |

### Quality Labels

| Label | Meaning | Action |
|-------|---------|--------|
| 🟢 Good | High confidence (≥80%) | Items look correct |
| 🟡 Check | Medium confidence (50-79%) | Review before use |
| 🔴 Verify | Low confidence (<50%) | Manual verification needed |

### Fix Wrong Extractions

- Click any cell in the BOQ table to edit the value
- Changes are saved when you download

### Export Options

**Excel Export** (recommended):
1. Click **Download Excel** in UI
2. Open in Excel/Google Sheets
3. Use as-is or copy into your BOQ template

**JSON Export** (for developers):
Structured data format for integration with other systems.

**CSV Export**:
Simple comma-separated format for import into any tool.

## Tips for Better Accuracy

### PDF Quality
- Use born-digital PDFs (not scanned)
- Minimum 300 DPI for scanned documents
- Avoid photographs of documents

### Document Format
- Works best with CPWD-style tender format
- Standard BOQ table formats extract most reliably
- May need manual review for non-standard phrasing

## Troubleshooting

**"Could not read this PDF"**
→ Try a different file. The PDF may be corrupted or use an unsupported format.

**"No BOQ items found"**
→ The document may not contain standard tender data. Try the sample PDF first.

**"Low confidence items"**
→ Complex phrasing or unusual material names. Verify each flagged item manually.

**"Processing takes too long"**
→ PDF too large. Try compressing the PDF or splitting into smaller files.

## Support

For issues, contact your system administrator with the document name and description of the problem.