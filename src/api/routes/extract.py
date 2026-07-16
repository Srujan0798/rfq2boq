"""Text extraction route with rate limiting."""

import uuid
from datetime import UTC, datetime

from config.constants import EntityType
from fastapi import APIRouter, Request
from src.api.dependencies import get_pipeline_container
from src.api.schemas import ExtractRequest, ExtractResponse
from src.api.store import result_store
from src.domain.models import BoqRow, EntitySpan, ExtractionMetadata, ExtractionResult
from src.logging_config import TimingLogger, get_logger

router = APIRouter(tags=["extract"])
logger = get_logger(__name__)


@router.post("/api/extract", response_model=ExtractResponse)
@router.post("/v1/extract", response_model=ExtractResponse)
async def extract_text(
    request: Request,
    extract_request: ExtractRequest,
    include_cost: bool = False,  # deprecated (pricing removed - unpriced BOQ only)
    region: str = "cpwd_delhi",
    return_uncertainty: bool = False,
):
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        f"Extract request received | client_ip={client_ip} | project={extract_request.project_name} | region={region} (include_cost ignored)"
    )

    extraction_id = str(uuid.uuid4())
    entity_spans: list[EntitySpan] = []
    boq_items: list[BoqRow] = []
    warnings: list[str] = []

    container = get_pipeline_container()

    if container.assembler and extract_request.text:
        try:
            with TimingLogger(logger, "nlp_extraction"):
                from src.nlp.pipeline import NLPPipeline

                pipeline = NLPPipeline()
                nlp_result = pipeline.process(extract_request.text)
                entity_types = [e.value for e in EntityType]
                for ent_dict in getattr(nlp_result, "entities", []):
                    ent_type = ent_dict.get("type", "MATERIAL")
                    type_enum = EntityType[ent_type.upper()] if ent_type in entity_types else EntityType.MATERIAL
                    entity_spans.append(
                        EntitySpan(
                            text=ent_dict.get("text", ""),
                            type=type_enum,
                            start=ent_dict.get("start", 0),
                            end=ent_dict.get("end", 0),
                            page=1,
                            conf=ent_dict.get("confidence", 0.5),
                        )
                    )

            if entity_spans:
                with TimingLogger(logger, "boq_assembly"):
                    boq_items = container.assembler.assemble(entity_spans, [], extract_request.text)

            # include_cost / cost_estimation / variance removed (unpriced BOQ scope - Step 1)

        except Exception as e:
            logger.error(f"Extraction failed | error={str(e)}")
            warnings.append(f"EXTRACTION_ERROR: {str(e)}")

    logger.info(f"Entities found | count={len(entity_spans)} | boq_items={len(boq_items)}")

    result = ExtractionResult(
        doc_id=extraction_id,
        project_name=extract_request.project_name,
        extraction_date=datetime.now(UTC),
        source_file="text-input",
        entities=entity_spans,
        boq_items=boq_items,
        metadata=ExtractionMetadata(
            total_items=len(boq_items),
            avg_confidence=(sum(i.confidence for i in boq_items) / len(boq_items) if boq_items else 0.0),
            processing_time_sec=0.0,
            pages_processed=0,
            entity_counts={et.value: sum(1 for e in entity_spans if e.type == et) for et in EntityType},
            warnings=warnings,
        ),
    )
    result_store.save(result)

    return ExtractResponse(extraction_id=extraction_id, result=result)
