"""Risk Analysis API - /v1/risk/analyze endpoint."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from src.domain.risk_engine import RiskEngine
from src.export.risk_report import generate_risk_excel

router = APIRouter(prefix="/v1/risk", tags=["risk"])

_engine = RiskEngine()


class RiskAnalysisRequest(BaseModel):
    job_id: str | None = None
    include_recommendations: bool = True


@router.post("/analyze")
async def analyze_risk(boq: list[dict]) -> dict[str, Any]:
    """Analyze BOQ items for risk."""
    result = _engine.score_project(boq)
    result["coverage"] = _engine.coverage_analysis(boq)
    result["recommendations"] = _engine.generate_recommendations(boq)
    return result


@router.post("/report")
async def generate_risk_report(boq: list[dict], format: str = "json") -> dict[str, Any]:
    """Generate risk report in specified format."""
    if format == "excel":
        path = "/tmp/risk_report.xlsx"
        generate_risk_excel(boq, path)
        return {"path": path}
    else:
        return _engine.score_project(boq)
