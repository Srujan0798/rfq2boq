# UI Guide — RFQ2BOQ Streamlit Interface

RFQ2BOQ is a document extraction tool that converts construction tender PDFs (RFQs) into structured Bill of Quantities (BOQ) data. Upload a PDF, review the extracted items, and download results in Excel, JSON, or CSV format.

## Uploading a PDF

Drag and drop your PDF into the upload area, or click to browse. The tool accepts files up to 50MB. If your file is larger, try compressing it or splitting it into smaller files.

## Understanding the BOQ Table

The extracted items appear in a sortable table with columns: S.No, Description, Quantity, Unit, Rate (₹), Amount (₹), Confidence, and Quality.

- **Good** (green): High confidence ≥80% — reliable extraction
- **Check** (yellow): Medium confidence 50–79% — review recommended
- **Verify** (red): Low confidence <50% — manual verification needed

Click column headers to sort. Hover over confidence bars to see exact percentages.

## Downloading Results

Use the three download buttons to export:
- **Excel (CPWD)**: Formatted spreadsheet matching CPWD standards
- **JSON**: Full structured data with metadata
- **CSV**: Spreadsheet-compatible comma-separated values

## Interpreting Confidence Scores

Confidence scores reflect how certain the model is about each extraction. Higher values mean more reliable data. Items marked "Verify" should be checked against the original PDF before finalizing your BOQ.

## Troubleshooting

- **No items extracted**: The PDF may not contain standard tender format. Try the sample PDF.
- **Missing text**: The PDF may be scanned (image-based). OCR processing is planned.
- **Slow extraction**: Large PDFs with many pages take 30–60 seconds. Please wait.