"""Export routes: SAP, Primavera, IFC, CostX adapters as API endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.api.store import result_store

router = APIRouter(prefix="/v1/export", tags=["export"])


class ExportRequest(BaseModel):
    job_id: str
    format: str


@router.post("/sap")
async def export_sap(req: ExportRequest) -> FileResponse:
    result = result_store.get(req.job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Extraction not found")

    from pathlib import Path

    from src.export.adapters.sap_xml import SAPExporter

    output_path = Path(f"/tmp/boq_{req.job_id}_sap.xml")
    SAPExporter().export(result, str(output_path))

    return FileResponse(
        path=output_path,
        filename=f"boq_{req.job_id}_sap.xml",
        media_type="application/xml",
    )


@router.post("/primavera")
async def export_primavera(req: ExportRequest) -> FileResponse:
    result = result_store.get(req.job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Extraction not found")

    from pathlib import Path

    from src.export.adapters.primavera_xer import PrimaveraExporter

    output_path = Path(f"/tmp/boq_{req.job_id}_primavera.xer")
    PrimaveraExporter().export(result, str(output_path))

    return FileResponse(
        path=output_path,
        filename=f"boq_{req.job_id}_primavera.xer",
        media_type="application/xml",
    )


@router.post("/ifc")
async def export_ifc(req: ExportRequest) -> FileResponse:
    result = result_store.get(req.job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Extraction not found")

    from pathlib import Path

    from src.export.adapters.ifc_export import IFCExporter

    output_path = Path(f"/tmp/boq_{req.job_id}_ifc.json")
    IFCExporter().export(result, str(output_path))

    return FileResponse(
        path=output_path,
        filename=f"boq_{req.job_id}_ifc.json",
        media_type="application/json",
    )


@router.post("/costx")
async def export_costx(req: ExportRequest) -> FileResponse:
    result = result_store.get(req.job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Extraction not found")

    from pathlib import Path

    from src.export.adapters.costx_csv import CostXExporter

    output_path = Path(f"/tmp/boq_{req.job_id}_costx.csv")
    CostXExporter(format="costx").export(result, str(output_path))

    return FileResponse(
        path=output_path,
        filename=f"boq_{req.job_id}_costx.csv",
        media_type="text/csv",
    )


@router.post("/cpwd")
async def export_cpwd(req: ExportRequest) -> FileResponse:
    result = result_store.get(req.job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Extraction not found")

    from pathlib import Path

    from src.export.adapters.excel_templates import export_cpwd

    output_path = Path(f"/tmp/boq_{req.job_id}_cpwd.xlsx")
    export_cpwd(result, str(output_path))

    return FileResponse(
        path=output_path,
        filename=f"boq_{req.job_id}_cpwd.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.post("/dsr")
async def export_dsr(req: ExportRequest) -> FileResponse:
    result = result_store.get(req.job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Extraction not found")

    from pathlib import Path

    from src.export.adapters.excel_templates import export_dsr

    output_path = Path(f"/tmp/boq_{req.job_id}_dsr.xlsx")
    export_dsr(result, str(output_path))

    return FileResponse(
        path=output_path,
        filename=f"boq_{req.job_id}_dsr.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
