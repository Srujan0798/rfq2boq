"""LLM Assistant routes - Claude/GPT integration for entity resolution, summaries, Q&A."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.api.store import result_store

router = APIRouter(prefix="/v1/llm", tags=["llm"])


class ResolveRequest(BaseModel):
    job_id: str
    entity_text: str
    context: str = ""
    current_type: str = "MATERIAL"
    provider: str = "claude"


class ResolveResponse(BaseModel):
    entity_text: str
    resolved_type: str
    confidence: float
    reasoning: str
    source: str


class SummaryRequest(BaseModel):
    job_id: str
    include_risk: bool = True


class SummaryResponse(BaseModel):
    total_items: int
    total_quantity: float
    materials_by_category: dict[str, list[str]]
    risk_items: list[dict]
    recommendations: list[str]


class AskRequest(BaseModel):
    job_id: str
    question: str


class AskResponse(BaseModel):
    answer: str


@router.post("/resolve", response_model=ResolveResponse)
async def resolve_entity(req: ResolveRequest):
    from src.llm.assistant import LLMAssistant

    assistant = LLMAssistant(provider=req.provider)
    resolution = assistant.resolve_entity(req.entity_text, req.context, req.current_type)

    if resolution is None:
        raise HTTPException(status_code=503, detail="LLM service unavailable")

    return ResolveResponse(
        entity_text=resolution.entity_text,
        resolved_type=resolution.resolved_type,
        confidence=resolution.confidence,
        reasoning=resolution.reasoning,
        source=resolution.source,
    )


@router.post("/summary", response_model=SummaryResponse)
async def summarize_boq(req: SummaryRequest):
    result = result_store.get(req.job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Extraction not found")

    from src.llm.assistant import LLMAssistant

    boq_items = [
        {
            "material": item.material,
            "quantity": str(item.quantity),
            "unit": item.unit,
            "grade": item.grade,
            "location": item.location,
        }
        for item in result.boq_items
    ]

    risk_report = None
    if req.include_risk:
        from src.risk.engine import RiskEngine
        engine = RiskEngine()
        risk_report = engine.analyze(result.boq_items)

    assistant = LLMAssistant()
    summary = assistant.summarize_boq(boq_items, risk_report)

    return SummaryResponse(
        total_items=summary.total_items,
        total_quantity=summary.total_quantity,
        materials_by_category=summary.materials_by_category,
        risk_items=summary.risk_items,
        recommendations=summary.recommendations,
    )


@router.post("/ask", response_model=AskResponse)
async def ask_question(req: AskRequest):
    result = result_store.get(req.job_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Extraction not found")

    from src.llm.assistant import LLMAssistant

    boq_items = [
        {
            "material": item.material,
            "quantity": str(item.quantity),
            "unit": item.unit,
            "grade": item.grade,
            "location": item.location,
        }
        for item in result.boq_items
    ]

    assistant = LLMAssistant()
    answer = assistant.answer_question(req.question, boq_items)

    return AskResponse(answer=answer)
