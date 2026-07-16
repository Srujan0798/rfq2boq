# Integration Guides — RFQ2BOQ

 guides for exporting BOQ data into external construction/ERP tools.

---

## SAP MM Integration

**Format:** SAP IDoc XML (PURCHCHREQ04 message type)

**Endpoint:** `POST /v1/export/sap`

```bash
# Export extraction result to SAP XML
curl -X POST http://localhost:8000/v1/export/sap \
  -H "Content-Type: application/json" \
  -d '{"job_id": "abc123", "format": "sap"}' \
  -o boq_sap.xml
```

**XML Structure:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<SAP_BOQ_EXPORT export_date="2024-01-15" company_code="1000" plant="P001">
  <HEADER>
    <DOC_TYPE>PR</DOC_TYPE>
    <PURCH_ORG>PO01</PURCH_ORG>
    <PUR_GROUP>PG01</PUR_GROUP>
    <CO_CODE>1000</CO_CODE>
  </HEADER>
  <ITEMS>
    <ITEM>
      <PO_ITEM>00010</PO_ITEM>
      <MATERIAL>CEM-001</MATERIAL>
      <SHORT_TEXT>Cement OPC 53 grade</SHORT_TEXT>
      <PLANT>P001</PLANT>
      <QUANTITY>500</QUANTITY>
      <UNIT>KG</UNIT>
      <MAT_GRP>MG01</MAT_GRP>
    </ITEM>
  </ITEMS>
</SAP_BOQ_EXPORT>
```

**Material Number Mapping:** (configured in `src/export/adapters/sap_xml.py`)
| Material | SAP Number |
|----------|------------|
| cement | CEM-001 |
| steel | STL-001 |
| sand | SND-001 |
| aggregate | AGG-001 |
| brick | BRK-001 |
| concrete | CNT-001 |
| timber | TMB-001 |
| glass | GLS-001 |

---

## Oracle Primavera P6 Integration

**Format:** XER (Exchange File)

**Endpoint:** `POST /v1/export/primavera`

```bash
curl -X POST http://localhost:8000/v1/export/primavera \
  -H "Content-Type: application/json" \
  -d '{"job_id": "abc123", "format": "xer"}' \
  -o boq.xer
```

**XER Format:** Tab-delimited with sections: `ERMHDR`, `PRTGLB`, `ACT`, `WBS`

Activity naming: `{material} ({quantity} {unit})`

---

## IFC (BIM) Integration

**Format:** IFC4 via ifcopenshell

**Endpoint:** `POST /v1/export/ifc`

```bash
curl -X POST http://localhost:8000/v1/export/ifc \
  -H "Content-Type: application/json" \
  -d '{"job_id": "abc123"}' \
  -o boq.ifc
```

**Entities Created:**
- `IfcCostItem` per BOQ row
- `IfcConstructionMaterial` with material type
- Linked to `IfcBuildingElement` if location resolved

**Python Usage:**
```python
from src.export.adapters.ifc_export import boq_to_ifc
from pathlib import Path

boq_items = [
    {"material": "cement", "quantity": 500, "unit": "kg", "grade": "M25"},
]
boq_to_ifc(boq_items, Path("/tmp/boq.ifc"))
```

---

## CostX / Buildsoft Integration

**Format:** CSV with CostX-specific column order

**Endpoint:** `POST /v1/export/costx`

```bash
curl -X POST http://localhost:8000/v1/export/costx \
  -H "Content-Type: application/json" \
  -d '{"job_id": "abc123", "format": "costx"}' \
  -o boq_costx.csv
```

**Columns:** `Item No, Description, Quantity, Unit, Rate, Amount, Remarks`

---

## CPWD / DSR Excel Templates

**Format:** Excel (.xlsx) in CPWD or DSR format

**Endpoint:** `POST /v1/export/cpwd-excel`

```bash
curl -X POST http://localhost:8000/v1/export/cpwd-excel \
  -H "Content-Type: application/json" \
  -d '{"job_id": "abc123", "template": "cpwd"}' \
  -o boq_cpwd.xlsx
```

**Python Usage:**
```python
from src.export.adapters.excel_templates import export_cpwd, export_dsr

export_cpwd(result, "/tmp/boq_cpwd.xlsx")
export_dsr(result, "/tmp/boq_dsr.xlsx")
```

---

## Revit Plugin (Scaffold)

**Location:** `integrations/revit/RfqBoqRevitPlugin/`

**Setup:**
1. Open `RfqBoqRevitPlugin.sln` in Visual Studio
2. Install Revit SDK 2024+
3. Build solution
4. In Revit: Add-Ins → External Tools → RFQ2BOQ

**Functionality:**
- Calls `/v1/extract` on selected PDF
- Parses response JSON
- Creates schedule in active Revit project

**Build Requirements:**
- Visual Studio 2022+
- Revit SDK 2024
- .NET Framework 4.8

---

## Quick Test

```bash
# Test all export formats
python -c "
from src.export.adapters.sap_xml import SAPExporter
from src.export.adapters.primavera_xer import PrimaveraXERExporter
from src.export.adapters.ifc_export import IFCExporter
from src.export.adapters.costx_csv import CostXExporter
from src.export.adapters.excel_templates import export_cpwd
from src.domain.models import BoqRow, ExtractionResult, ExtractionMetadata
from datetime import datetime

result = ExtractionResult(
    doc_id='test', source_file='test.pdf', extraction_date=datetime.utcnow(),
    entities=[], relations=[],
    boq_items=[BoqRow(item_no=1, material='cement', quantity=500, unit='kg', confidence=0.9)],
    metadata=ExtractionMetadata(total_items=1, avg_confidence=0.9, processing_time_sec=1.0, pages_processed=1)
)

import tempfile, os
for Exporter, name in [(SAPExporter, 'sap'), (PrimaveraXERExporter, 'xer'), (IFCExporter, 'ifc'), (CostXExporter, 'costx')]:
    path = f'/tmp/test_boq.{name}'
    Exporter().export(result, path)
    print(f'{name}: {os.path.exists(path)} (size: {os.path.getsize(path)} bytes)')
"
```
