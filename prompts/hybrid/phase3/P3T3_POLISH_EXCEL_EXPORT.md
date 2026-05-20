# TASK: P3T3 — Polish Excel Export (CPWD-Format) — Agent-3

**Phase:** 3 | **Effort:** 2 days | **Priority:** P1

## 1. GOAL
Make the Excel BOQ output look like a quantity surveyor crafted it by hand, following the CPWD/DSR formatting conventions used by every Indian construction estimator. This is the visible deliverable; it must look professional.

## 2. CONTEXT
Read first:
- `src/export/excel_generator.py` — current Excel exporter
- `data/rates/cpwd_dsr_2023.json` — DSR rates from P1T4
- `src/domain/models.py` — BoqRow shape
- [docs/HYBRID_PLAN.md](../../../docs/HYBRID_PLAN.md)
- [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)

CPWD BOQ format (industry standard):
- Header: project name, location, date, RFQ reference, contractor name
- Columns (in order): S.No | DSR Code | Description | Unit | Quantity | Rate (₹) | Amount (₹)
- Sections grouped by trade (Excavation / Concrete / Masonry / Plaster / Painting / Finishing / etc.)
- Subtotals per section
- Grand Total row
- GST and adjustment rows
- Footer: signature blocks, terms reference

## 3. DELIVERABLES
- [ ] `src/export/excel_generator.py` — CPWD-style output
- [ ] `src/export/templates/cpwd_template.xlsx` — Excel template (header, styles, footer)
- [ ] `tests/unit/test_excel_cpwd.py` — ≥6 tests
- [ ] `docs/excel_format.md` — what the output looks like + sample screenshots
- [ ] `data/samples/sample_boq_output.xlsx` — sample for QA

## 4. STEPS
1. Read context.
2. **Design template** `src/export/templates/cpwd_template.xlsx`:
   - Use openpyxl to create the template programmatically (or hand-craft once and load as base)
   - Header block: rows 1–5 with project metadata cells
   - Column headers row 7: S.No, DSR Code, Description, Unit, Quantity, Rate (₹), Amount (₹), Notes
   - Style: bold headers, borders, alternating row shading
3. **Update `excel_generator.py`**:
   ```python
   class CPWDExcelGenerator:
       def export(self, result: ExtractionResult, output_path: str, project_metadata: dict | None = None):
           # Load template
           # Fill header (project name, date, etc.)
           # Group BOQ items by trade (use OmniClass mapping from P1T1)
           # Insert items with DSR code lookup (from P1T4)
           # Subtotal per trade
           # Grand total + GST 18%
           # Save
   ```
4. **Trade grouping**:
   - Use OmniClass mapping to group items: excavation, concrete, masonry, plaster, flooring, painting, plumbing, electrical, finishing
   - Sort within trade alphabetically by description
5. **DSR code lookup**:
   - For each BOQ item, search `data/rates/cpwd_dsr_2023.json` for matching code
   - If found: insert code + use the official rate (override our extracted rate)
   - If not found: blank code, use extracted rate, mark with note "rate estimated"
6. **Styling**:
   - Numbers right-aligned, 2 decimal places, ₹ symbol via number format
   - Description left-aligned, wrap text
   - Header row: bold, blue fill (#1F4E78), white text
   - Subtotal row: bold, light gray fill
   - Grand total row: bold, larger font, dark fill
   - Borders: thin all around, double under grand total
7. **Footer**:
   - Notes section
   - Signature blocks: "Prepared by: ___" / "Checked by: ___" / "Approved by: ___"
8. **Sample output** to QA: generate `data/samples/sample_boq_output.xlsx` from sample PDF
9. Tests verify: template loads, headers correct, totals sum properly, styling applied.

## 5. VERIFICATION
```bash
# Template exists
$ ls src/export/templates/cpwd_template.xlsx
EXPECT: exists

# Sample output generated
$ python3 -c "
from src.pipeline import Pipeline
p = Pipeline()
r = p.run('data/samples/sample_rfq_simple.pdf')
from src.export.excel_generator import CPWDExcelGenerator
g = CPWDExcelGenerator()
g.export(r, '/tmp/test_boq.xlsx', {'project': 'Test Project', 'location': 'Delhi'})
import openpyxl
wb = openpyxl.load_workbook('/tmp/test_boq.xlsx')
ws = wb.active
# Check headers in row 7
headers = [ws.cell(row=7, column=c).value for c in range(1, 9)]
expected = ['S.No', 'DSR Code', 'Description', 'Unit', 'Quantity', 'Rate (₹)', 'Amount (₹)', 'Notes']
for h, e in zip(headers, expected):
    assert h == e, f'header mismatch: {h} vs {e}'
print('headers OK')
"
EXPECT: prints "headers OK"

# Numbers formatted with ₹
$ python3 -c "
import openpyxl
wb = openpyxl.load_workbook('/tmp/test_boq.xlsx')
ws = wb.active
# Look for any cell with ₹ in number format
found = any('₹' in str(ws.cell(row=r, column=6).number_format or '') for r in range(7, 50))
assert found, 'no ₹ formatting'
print('₹ formatting OK')
"
EXPECT: prints "₹ formatting OK"

# Tests
$ python3 -m pytest tests/unit/test_excel_cpwd.py -v
EXPECT: ≥6 passed

# Sample committed for QA
$ ls data/samples/sample_boq_output.xlsx
EXPECT: exists
```

## 6. ACCEPTANCE CRITERIA
- [ ] CPWD template renders with all required sections
- [ ] DSR codes inserted where matches exist
- [ ] Trades grouped + subtotaled correctly
- [ ] Grand total + GST shown
- [ ] Numbers formatted with ₹ + 2 decimals
- [ ] Sample output looks professional (visual QA pass)
- [ ] Coverage ≥ 80%

## 7. CONSTRAINTS
- All imports `src.` prefix
- Use `openpyxl` (already a dependency); no new Excel libraries
- Keep the JSON exporter and simple CSV exporter unchanged — CPWD is one specific format
- Total formula must sum correctly (use Excel SUM formulas, not pre-computed values, so user can edit and totals auto-update)

## 8. DEPENDENCIES
- **Blocked by:** P3T1 (uses final model), P1T1 (OmniClass), P1T4 (DSR rates)
- **Blocks:** None
- **Parallel-safe with:** P3T2, P3T4

## 9. GOTCHAS
- ₹ symbol may not render in some Excel viewers — use `"₹"#,##0.00` format string
- Excel SUM formulas across non-contiguous rows: use SUMIFS or named ranges
- Indian number format: 1,23,456 (lakhs separator), not 123,456 — use `#,##,##0.00`
- DSR codes are strings like "1.1.1" — preserve as text, not parsed as date
- Sample data must be representative — pick a 10–15 item BOQ
- Some trades may be empty for a given PDF; show "No items in this trade" or hide row
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)
