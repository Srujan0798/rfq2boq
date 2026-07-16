"""API schemas."""

from pydantic import BaseModel
from src.domain.models import ExtractionResult


class ExtractRequest(BaseModel):
    text: str = ""
    project_name: str = "Untitled"


class ExtractResponse(BaseModel):
    extraction_id: str
    result: ExtractionResult


class UploadResponse(BaseModel):
    extraction_id: str
    result: ExtractionResult


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: ExtractionResult | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    model_loaded: bool = False
    ontology_loaded: bool = False
    disk_space_gb: float | None = None
    memory_mb: float | None = None
    memory_percent: float | None = None
