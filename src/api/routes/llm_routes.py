"""LLM Assistant routes - Claude/GPT/OpenRouter integration for entity resolution, summaries, Q&A."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.api.store import result_store

router = APIRouter(prefix="/v1/llm", tags=["llm"])
logger = logging.getLogger(__name__)

_ALLOWED_PROVIDERS = {"claude", "openai", "openrouter", "gpt-4", "gpt-3.5-turbo"}
_MAX_ENTITY_TEXT_LEN = 500
_MAX_CONTEXT_LEN = 2000
_MAX_QUESTION_LEN = 500


class ResolveRequest(BaseModel):
    job_id: str
    entity_text: str
    context: str = ""
    current_type: str = "MATERIAL"
    provider: str = "claude"
    model: str | None = None  # Optional model override (e.g., for OpenRouter free models)


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


def _sanitize_error(exc: Exception) -> str:
    """Return a sanitized error message safe to expose via HTTP."""
    return f"{type(exc).__name__}: {str(exc)[:200]}"


@router.post("/resolve", response_model=ResolveResponse)
async def resolve_entity(req: ResolveRequest):
    logger.info("LLM resolve request | job_id=%s | provider=%s", req.job_id, req.provider)

    if req.provider.lower() not in _ALLOWED_PROVIDERS:
        logger.warning("Invalid provider rejected | provider=%s", req.provider)
        raise HTTPException(status_code=400, detail=f"Provider '{req.provider}' not supported")
    if len(req.entity_text) > _MAX_ENTITY_TEXT_LEN:
        logger.warning("Entity text too long | len=%s", len(req.entity_text))
        raise HTTPException(status_code=400, detail="entity_text exceeds maximum length")
    if len(req.context) > _MAX_CONTEXT_LEN:
        logger.warning("Context too long | len=%s", len(req.context))
        raise HTTPException(status_code=400, detail="context exceeds maximum length")

    try:
        from src.llm.assistant import LLMAssistant

        assistant = LLMAssistant(provider=req.provider, model=req.model)
        resolution = assistant.resolve_entity(req.entity_text, req.context, req.current_type)
    except Exception as exc:
        logger.exception("LLM resolve failed | job_id=%s", req.job_id)
        raise HTTPException(status_code=500, detail=_sanitize_error(exc)) from exc

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
    logger.info("LLM summary request | job_id=%s | include_risk=%s", req.job_id, req.include_risk)

    result = result_store.get(req.job_id)
    if result is None:
        logger.warning("Summary request for missing job_id=%s", req.job_id)
        raise HTTPException(status_code=404, detail="Extraction not found")

    try:
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

        risk_report: dict | None = None
        if req.include_risk:
            from dataclasses import asdict

            from src.risk.engine import BoqRiskAnalyzer

            engine = BoqRiskAnalyzer()
            risk_report = asdict(engine.analyze(result.boq_items))

        assistant = LLMAssistant()
        summary = assistant.summarize_boq(boq_items, risk_report)
    except Exception as exc:
        logger.exception("LLM summary failed | job_id=%s", req.job_id)
        raise HTTPException(status_code=500, detail=_sanitize_error(exc)) from exc

    return SummaryResponse(
        total_items=summary.total_items,
        total_quantity=summary.total_quantity,
        materials_by_category=summary.materials_by_category,
        risk_items=summary.risk_items,
        recommendations=summary.recommendations,
    )


@router.post("/ask", response_model=AskResponse)
async def ask_question(req: AskRequest):
    logger.info("LLM ask request | job_id=%s", req.job_id)

    result = result_store.get(req.job_id)
    if result is None:
        logger.warning("Ask request for missing job_id=%s", req.job_id)
        raise HTTPException(status_code=404, detail="Extraction not found")
    if len(req.question) > _MAX_QUESTION_LEN:
        logger.warning("Question too long | len=%s", len(req.question))
        raise HTTPException(status_code=400, detail="question exceeds maximum length")

    try:
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
    except Exception as exc:
        logger.exception("LLM ask failed | job_id=%s", req.job_id)
        raise HTTPException(status_code=500, detail=_sanitize_error(exc)) from exc

    return AskResponse(answer=answer)
