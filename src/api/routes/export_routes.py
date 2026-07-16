"""Export routes — ERP/BIM integrations are out of scope for unpriced BOQ.

The unpriced BOQ scope (Step 1) only supports JSON/Excel/CSV output. SAP,
Primavera, IFC, CostX, CPWD pricing, and DSR adapters were removed.
Core exports live on the upload/extract/boq routes and the CLI.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/v1/export", tags=["export"])


class ExportRequest(BaseModel):
    job_id: str
    format: str


@router.post("/sap")
async def export_sap(req: ExportRequest) -> None:
    raise HTTPException(
        status_code=410,
        detail="SAP export is out of scope for the unpriced BOQ milestone. Use /v1/upload or /v1/boq/{id}?format=excel instead.",
    )


@router.post("/primavera")
async def export_primavera(req: ExportRequest) -> None:
    raise HTTPException(
        status_code=410,
        detail="Primavera export is out of scope for the unpriced BOQ milestone. Use /v1/upload or /v1/boq/{id}?format=excel instead.",
    )


@router.post("/ifc")
async def export_ifc(req: ExportRequest) -> None:
    raise HTTPException(
        status_code=410,
        detail="IFC export is out of scope for the unpriced BOQ milestone. Use /v1/upload or /v1/boq/{id}?format=excel instead.",
    )
