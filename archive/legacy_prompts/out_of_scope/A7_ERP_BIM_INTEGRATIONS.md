# TASK: ERP/BIM Integration Adapters — Agent-3

**Wave:** 2 | **Tier:** A | **Priority:** P1

## 1. GOAL
Build export adapters so extracted BOQs feed directly into major construction/ERP/BIM tools. This is the commercial differentiator — turns the system from "extractor" into "estimator's daily tool."

## 2. CONTEXT
Read first:
- `src/domain/models.py` — `BoqRow`, `ExtractionResult` schemas
- `src/export/excel_generator.py` — existing Excel exporter (pattern to follow)
- `src/export/json_formatter.py` — JSON exporter
- `src/api/routes/upload.py` — pattern for new API endpoints
- [docs/conventions.md](../../../docs/conventions.md)

Target tools:
- SAP MM (Material Management) — IDoc XML
- Primavera P6 — XER file (Activity/Resource/Cost)
- IFC (BIM standard) — IfcCostItem entities
- CostX/Buildsoft — CSV with specific column order
- CPWD / DSR templates — Excel formats

Current state: only generic Excel, JSON, CSV exports exist.

## 3. DELIVERABLES
- [ ] `src/export/sap_xml.py` — `SAPExporter` (IDoc XML format)
- [ ] `src/export/primavera_xer.py` — `PrimaveraExporter` (XER for P6)
- [ ] `src/export/ifc_export.py` — IFC export via `ifcopenshell`
- [ ] `src/export/costx_csv.py` — CostX-compatible CSV
- [ ] `src/export/excel_templates.py` — CPWD/DSR templated Excel
- [ ] `src/api/routes/export.py` — endpoints for each format
- [ ] `integrations/revit/` — Revit plugin scaffold (C#) calling `/v1/extract`
- [ ] `src/export/templates/` — XML/XER templates as starting point (NEVER a top-level `templates/` — see docs/WAVE_GOTCHAS.md)
- [ ] `tests/unit/test_exporters.py` — minimum 12 tests (2 per exporter)
- [ ] `docs/integrations.md` — per-tool integration guide

## 4. STEPS
1. Read pattern from existing `src/export/excel_generator.py`
2. Add to `pyproject.toml` deps: `ifcopenshell`, `lxml`
3. Implement each exporter:
   - **SAP**: Use lxml to build SAP IDoc structure (PURCHREQ message type for purchase requisitions)
   - **Primavera**: Construct XER format (tab-delimited with specific RSRC/ACTV/COST sections)
   - **IFC**: Use `ifcopenshell` API — create IfcCostItem per BoqRow, link to IfcBuildingElement if location resolved
   - **CostX**: Map BoqRow → CSV with columns: ItemCode, Description, Unit, Quantity, Rate, Amount, Location
   - **CPWD Excel**: Use openpyxl with the CPWD-published BOQ format
4. Add API endpoints:
   - `POST /v1/export/sap` (takes job_id or BOQ JSON)
   - `POST /v1/export/primavera`
   - `POST /v1/export/ifc`
   - `POST /v1/export/costx`
   - `POST /v1/export/cpwd-excel`
   - Each returns the file binary with appropriate Content-Type
5. Revit plugin scaffold:
   - `integrations/revit/RfqBoqRevitPlugin/` — minimal C# project
   - Calls `/v1/extract`, parses response, creates schedule in Revit
   - README with build instructions (Visual Studio + Revit SDK)
6. Per-tool docs in `docs/integrations.md`
7. Verification

## 5. VERIFICATION
```bash
# Each exporter produces valid output
$ python3 -c "
from src.export.sap_xml import SAPExporter
from src.domain.models import BoqRow, ExtractionResult, ExtractionMetadata
from datetime import datetime
result = ExtractionResult(
    doc_id='test', source_file='t.pdf', extraction_date=datetime.utcnow(),
    entities=[], relations=[],
    boq_items=[BoqRow(item_no=1, material='cement', quantity=500, unit='kg', confidence=0.9)],
    metadata=ExtractionMetadata(total_items=1, avg_confidence=0.9, processing_time_sec=1.0, pages_processed=1)
)
SAPExporter().export(result, '/tmp/test_sap.xml')
import xml.etree.ElementTree as ET
ET.parse('/tmp/test_sap.xml')
print('SAP XML valid')
"
EXPECT: "SAP XML valid"

# Primavera
$ python3 -c "from src.export.primavera_xer import PrimaveraExporter; PrimaveraExporter().export(__import__('tests.fixtures', fromlist=['sample_result']).sample_result(), '/tmp/test.xer'); print('XER OK')"
EXPECT: "XER OK"

# IFC
$ python3 -c "from src.export.ifc_export import IFCExporter; IFCExporter().export(__import__('tests.fixtures', fromlist=['sample_result']).sample_result(), '/tmp/test.ifc'); import ifcopenshell; f = ifcopenshell.open('/tmp/test.ifc'); assert len(f.by_type('IfcCostItem')) > 0"
EXPECT: no AssertionError

# CostX CSV
$ python3 -c "from src.export.costx_csv import CostXExporter; CostXExporter().export(__import__('tests.fixtures', fromlist=['sample_result']).sample_result(), '/tmp/test.csv'); import csv; rows = list(csv.reader(open('/tmp/test.csv'))); assert len(rows) > 1"
EXPECT: no AssertionError

# CPWD Excel
$ python3 -c "from src.export.excel_templates import CPWDExporter; CPWDExporter().export(__import__('tests.fixtures', fromlist=['sample_result']).sample_result(), '/tmp/cpwd.xlsx'); import openpyxl; openpyxl.load_workbook('/tmp/cpwd.xlsx')"
EXPECT: no exception

# API endpoints registered
$ python3 -c "from src.api.main import app; paths = [r.path for r in app.routes]; assert '/v1/export/sap' in paths and '/v1/export/ifc' in paths"
EXPECT: no AssertionError

# Tests
$ python3 -m pytest tests/unit/test_exporters.py -v
EXPECT: ≥12 passed

# Lint
$ python3 -m ruff check src/export src/api/routes/export.py
EXPECT: clean
```

## 6. ACCEPTANCE CRITERIA
- [ ] All Section 5 commands succeed
- [ ] Each exporter produces a file parseable by its target tool's standard parser
- [ ] API endpoints functional (with curl tests in `docs/integrations.md`)
- [ ] Revit plugin scaffold builds (or has documented build steps)
- [ ] Coverage of new code ≥ 80%
- [ ] No regression in tests

## 7. CONSTRAINTS
- All imports use `src.` prefix
- DO NOT modify existing `src/export/excel_generator.py` or `json_formatter.py`
- IFC export: use `ifcopenshell.api` only, do not raw-write IFC
- SAP IDoc: use IDoc 4.6C+ format (most widely supported)
- Primavera XER format must be the documented field structure (don't invent)
- CostX columns must match their import template exactly (verify against current CostX docs)

## 8. DEPENDENCIES
- **Blocked by:** A0 (test fix)
- **Blocks:** C4 (multi-tenancy may scope these per tenant)
- **Parallel-safe with:** A1, A2, A3, A4, A5, A6
- **Shared files:** `src/api/main.py` (only adds router, low conflict risk)

## 9. GOTCHAS
- `ifcopenshell` install: needs `pip install ifcopenshell` — wheels exist for Python 3.11
- SAP IDoc: many subformats — pick PURCHREQ04 unless instructed otherwise
- Primavera XER: tab-delimited, NOT comma — easy mistake
- CostX rate column expects unit price; ensure BOQ rows include rates from S3 cost engine
- Revit plugin: only stub; full plugin needs Revit license + Visual Studio. Document this clearly
- IFC entities need GUID (use `ifcopenshell.guid.new()`)
- Large IFC files: stream write, don't accumulate in memory
