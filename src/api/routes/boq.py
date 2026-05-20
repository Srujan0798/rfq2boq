"""BOQ/job retrieval routes."""

from fastapi import APIRouter, HTTPException
from src.api.schemas import ExtractResponse
from src.api.store import result_store

router = APIRouter(tags=["boq"])


@router.get("/api/boq/{extraction_id}", response_model=ExtractResponse)
@router.get("/v1/jobs/{extraction_id}", response_model=ExtractResponse)
async def get_boq(extraction_id: str):
    result = result_store.get(extraction_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Extraction not found")
    return ExtractResponse(extraction_id=extraction_id, result=result)
