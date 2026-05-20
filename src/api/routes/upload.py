"""Upload route — PDF upload + full extraction with background job support."""

import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

from config.settings import settings
from fastapi import APIRouter, BackgroundTasks, File, Query, Request, UploadFile
from fastapi.responses import FileResponse
from src.api.dependencies import get_pipeline_container
from src.api.schemas import UploadResponse
from src.api.store import result_store
from src.domain.models import EntitySpan, ExtractionMetadata, ExtractionResult
from src.export import ExcelGenerator
from src.logging_config import TimingLogger, get_logger

router = APIRouter(tags=["upload"])
logger = get_logger(__name__)

MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024
LARGE_FILE_THRESHOLD_MB = 5
LARGE_PAGE_COUNT = 10


def _sanitize_filename(filename: str) -> str:
    safe = re.sub(r"[^\w\s.-]", "", filename)
    safe = re.sub(r"\s+", "_", safe)
    return safe[:100]


def _get_file_size_mb(content: bytes) -> float:
    return len(content) / (1024 * 1024)


def _process_upload_sync(
    job_id: str,
    contents: bytes,
    filename: str,
    project_name: str,
) -> None:
    from src.domain.boq_assembler import BOQAssembler
    from src.ingest.pdf_extractor import PDFExtractor
    from src.nlp.pipeline import NLPPipeline

    result_store.save_job_status(job_id, "processing")

    try:
        sanitized = _sanitize_filename(filename)
        temp_path = Path(f"/tmp/{uuid.uuid4()}_{sanitized}")
        temp_path.write_bytes(contents)

        extractor = PDFExtractor()
        pages = extractor.extract_text(str(temp_path))
        text = "\n".join(p.text for p in pages)
        temp_path.unlink()

        container = get_pipeline_container()
        if hasattr(container, "pipeline") and container.pipeline:
            nlp_result = container.pipeline.process(text)
        else:
            pipeline = NLPPipeline(ontology_dir=str(Path("data/ontology")))
            nlp_result = pipeline.process(text)

        entities = []
        for e in getattr(nlp_result, "entities", []):
            entities.append(EntitySpan(
                text=e.get("text", ""),
                type=e.get("type", "MATERIAL"),
                start=e.get("start", 0),
                end=e.get("end", 0),
                page=e.get("page", 1),
                conf=e.get("confidence", 0.5),
            ))

        if hasattr(container, "assembler") and container.assembler:
            boq_items = container.assembler.assemble(entities, getattr(nlp_result, "relations", []), text)
        else:
            assembler = BOQAssembler()
            boq_items = assembler.assemble(entities, getattr(nlp_result, "relations", []), text)

        entity_counts = {}
        for e in entities:
            t = e.type.value if hasattr(e.type, "value") else str(e.type)
            entity_counts[t] = entity_counts.get(t, 0) + 1

        result = ExtractionResult(
            doc_id=job_id,
            project_name=project_name,
            extraction_date=datetime.now(UTC),
            source_file=sanitized,
            entities=entities,
            boq_items=boq_items,
            metadata=ExtractionMetadata(
                total_items=len(boq_items),
                avg_confidence=sum(i.confidence for i in boq_items) / len(boq_items) if boq_items else 0.0,
                processing_time_sec=0.0,
                pages_processed=len(pages),
                entity_counts=entity_counts,
                warnings=[],
            ),
        )

        result_store.save(result)
        result_store.save_job_status(job_id, "complete", result)
        logger.info(f"Background job completed | job_id={job_id} | items={len(boq_items)}")

    except Exception as e:
        logger.error(f"Background job failed | job_id={job_id} | error={str(e)}")
        result_store.save_job_status(job_id, "failed")


@router.post("/api/upload", response_model=UploadResponse)
@router.post("/v1/extract/upload", response_model=UploadResponse)
async def upload_pdf(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),  # noqa: B008
    project_name: str = Query(default="Untitled"),
    format: str = Query(default="json"),
):
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Upload request received | client_ip={client_ip} | filename={file.filename}")

    try:
        contents = await file.read()
        file_size_mb = _get_file_size_mb(contents)
        logger.debug(f"File size: {file_size_mb:.2f} MB")

        if len(contents) > MAX_FILE_SIZE:
            logger.warning(f"File too large rejected | size={file_size_mb:.2f}MB | limit={settings.MAX_FILE_SIZE_MB}MB")
            return UploadResponse(
                extraction_id=str(uuid.uuid4()),
                result=ExtractionResult(
                    doc_id=str(uuid.uuid4()),
                    project_name=project_name,
                    extraction_date=datetime.now(UTC),
                    source_file=_sanitize_filename(file.filename or "unknown.pdf"),
                    entities=[],
                    boq_items=[],
                    metadata=ExtractionMetadata(
                        total_items=0,
                        avg_confidence=0.0,
                        processing_time_sec=0.0,
                        pages_processed=0,
                        warnings=[f"FILE_TOO_LARGE: Maximum {settings.MAX_FILE_SIZE_MB}MB allowed"],
                    ),
                ),
            )

        sanitized = _sanitize_filename(file.filename or "unknown.pdf")
        temp_path = Path(f"/tmp/{uuid.uuid4()}_{sanitized}")
        temp_path.write_bytes(contents)

        from src.ingest.pdf_extractor import PDFExtractor
        extractor = PDFExtractor()
        pages = extractor.extract_text(str(temp_path))
        text = "\n".join(p.text for p in pages)
        temp_path.unlink()

        page_count = len(pages)
        needs_background = file_size_mb > LARGE_FILE_THRESHOLD_MB or page_count > LARGE_PAGE_COUNT

        if needs_background:
            job_id = str(uuid.uuid4())
            result_store.save_job_status(job_id, "pending")
            background_tasks.add_task(
                _process_upload_sync,
                job_id,
                contents,
                file.filename or "unknown.pdf",
                project_name,
            )
            logger.info(f"Large file queued for background processing | job_id={job_id} | size={file_size_mb:.2f}MB | pages={page_count}")
            return UploadResponse(
                extraction_id=job_id,
                result=ExtractionResult(
                    doc_id=job_id,
                    project_name=project_name,
                    extraction_date=datetime.now(UTC),
                    source_file=sanitized,
                    entities=[],
                    boq_items=[],
                    metadata=ExtractionMetadata(
                        total_items=0,
                        avg_confidence=0.0,
                        processing_time_sec=0.0,
                        pages_processed=page_count,
                        warnings=["QUEUED_FOR_BACKGROUND: Large file queued for processing"],
                    ),
                ),
            )

        with TimingLogger(logger, "nlp_processing"):
            container = get_pipeline_container()
            if hasattr(container, "pipeline") and container.pipeline:
                nlp_result = container.pipeline.process(text)
                entities = []
                for e in getattr(nlp_result, "entities", []):
                    entities.append(EntitySpan(
                        text=e.get("text", ""),
                        type=e.get("type", "MATERIAL"),
                        start=e.get("start", 0),
                        end=e.get("end", 0),
                        page=e.get("page", 1),
                        conf=e.get("confidence", 0.5),
                    ))
                relations = getattr(nlp_result, "relations", [])
            else:
                from src.nlp.pipeline import NLPPipeline
                pipeline = NLPPipeline(ontology_dir=str(Path("data/ontology")))
                nlp_result = pipeline.process(text)
                entities = []
                for e in getattr(nlp_result, "entities", []):
                    entities.append(EntitySpan(
                        text=e.get("text", ""),
                        type=e.get("type", "MATERIAL"),
                        start=e.get("start", 0),
                        end=e.get("end", 0),
                        page=e.get("page", 1),
                        conf=e.get("confidence", 0.5),
                    ))
                relations = getattr(nlp_result, "relations", [])

        with TimingLogger(logger, "boq_assembly"):
            if hasattr(container, "assembler") and container.assembler:
                boq_items = container.assembler.assemble(entities, relations, text)
            else:
                from src.domain.boq_assembler import BOQAssembler
                assembler = BOQAssembler()
                boq_items = assembler.assemble(entities, relations, text)

        entity_counts = {}
        for e in entities:
            t = e.type.value if hasattr(e.type, "value") else str(e.type)
            entity_counts[t] = entity_counts.get(t, 0) + 1

        logger.info(f"Extraction complete | entities={len(entities)} | boq_items={len(boq_items)}")

        extraction_id = str(uuid.uuid4())
        result = ExtractionResult(
            doc_id=extraction_id,
            project_name=project_name,
            extraction_date=datetime.now(UTC),
            source_file=sanitized,
            entities=entities,
            boq_items=boq_items,
            metadata=ExtractionMetadata(
                total_items=len(boq_items),
                avg_confidence=sum(i.confidence for i in boq_items) / len(boq_items) if boq_items else 0.0,
                processing_time_sec=0.0,
                pages_processed=page_count,
                entity_counts=entity_counts,
                warnings=[],
            ),
        )
        result_store.save(result)

        return UploadResponse(extraction_id=extraction_id, result=result)

    except Exception as e:
        logger.error(f"Upload processing error | error={str(e)}")
        return UploadResponse(
            extraction_id=str(uuid.uuid4()),
            result=ExtractionResult(
                doc_id=str(uuid.uuid4()),
                project_name=project_name,
                extraction_date=datetime.now(UTC),
                source_file=_sanitize_filename(file.filename or "unknown.pdf"),
                entities=[],
                boq_items=[],
                metadata=ExtractionMetadata(
                    total_items=0,
                    avg_confidence=0.0,
                    processing_time_sec=0.0,
                    pages_processed=0,
                    warnings=[f"PROCESSING_ERROR: {str(e)}"],
                ),
            ),
        )


@router.post("/api/upload/download-excel")
@router.post("/v1/extract/download-excel")
async def upload_for_excel(
    request: Request,
    file: UploadFile = File(...),  # noqa: B008
    project_name: str = Query(default="Untitled"),
):
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Excel export request | client_ip={client_ip} | filename={file.filename}")

    try:
        contents = await file.read()

        if len(contents) > MAX_FILE_SIZE:
            return FileResponse(
                path="/tmp/error.xlsx",
                filename="error.xlsx",
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        sanitized = _sanitize_filename(file.filename or "unknown.pdf")
        temp_path = Path(f"/tmp/{uuid.uuid4()}_{sanitized}")
        temp_path.write_bytes(contents)

        from src.ingest.pdf_extractor import PDFExtractor
        extractor = PDFExtractor()
        pages = extractor.extract_text(str(temp_path))
        text = "\n".join(p.text for p in pages)
        temp_path.unlink()

        container = get_pipeline_container()
        if hasattr(container, "pipeline") and container.pipeline:
            nlp_result = container.pipeline.process(text)
            entities = []
            for e in getattr(nlp_result, "entities", []):
                entities.append(EntitySpan(
                    text=e.get("text", ""),
                    type=e.get("type", "MATERIAL"),
                    start=e.get("start", 0),
                    end=e.get("end", 0),
                    page=e.get("page", 1),
                    conf=e.get("confidence", 0.5),
                ))
            relations = getattr(nlp_result, "relations", [])
        else:
            from src.nlp.pipeline import NLPPipeline
            pipeline = NLPPipeline(ontology_dir=str(Path("data/ontology")))
            nlp_result = pipeline.process(text)
            entities = []
            for e in getattr(nlp_result, "entities", []):
                entities.append(EntitySpan(
                    text=e.get("text", ""),
                    type=e.get("type", "MATERIAL"),
                    start=e.get("start", 0),
                    end=e.get("end", 0),
                    page=e.get("page", 1),
                    conf=e.get("confidence", 0.5),
                ))
            relations = getattr(nlp_result, "relations", [])

        if hasattr(container, "assembler") and container.assembler:
            boq_items = container.assembler.assemble(entities, relations, text)
        else:
            from src.domain.boq_assembler import BOQAssembler
            assembler = BOQAssembler()
            boq_items = assembler.assemble(entities, relations, text)

        extraction_id = str(uuid.uuid4())
        result = ExtractionResult(
            doc_id=extraction_id,
            project_name=project_name,
            extraction_date=datetime.now(UTC),
            source_file=sanitized,
            entities=entities,
            boq_items=boq_items,
        )

    except Exception:
        result = ExtractionResult(
            doc_id=str(uuid.uuid4()),
            project_name=project_name,
            extraction_date=datetime.now(UTC),
            source_file=_sanitize_filename(file.filename or "unknown.pdf"),
            entities=[],
            boq_items=[],
        )

    output_path = f"/tmp/{extraction_id}.xlsx"
    ExcelGenerator().generate(result, output_path)

    return FileResponse(
        path=output_path,
        filename=f"{project_name}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
