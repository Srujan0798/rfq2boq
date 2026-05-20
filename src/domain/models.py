"""Domain models for RFQ2BOQ."""

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from config.constants import EntityType, RelationType
from pydantic import BaseModel, Field


class EntitySourceType(StrEnum):
    BERT = "BERT"
    GAZETTEER = "GAZETTEER"
    REGEX = "REGEX"
    MANUAL = "MANUAL"


class EntitySpan(BaseModel):
    text: str
    type: EntityType
    start: int
    end: int
    page: int = 1
    conf: float = Field(default=0.5, ge=0.0, le=1.0)
    source: EntitySourceType = EntitySourceType.BERT


class Relation(BaseModel):
    head_id: str
    tail_id: str
    type: RelationType
    conf: float = Field(default=0.5, ge=0.0, le=1.0)


class BoqRow(BaseModel):
    item_no: int = Field(default=1, gt=0)
    material: str = ""
    quantity: Decimal = Decimal("0")
    unit: str = "no."
    action: str = "supply"
    grade: str = ""
    dimensions: list[str] = Field(default_factory=list)
    standard: list[str] = Field(default_factory=list)
    location: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    description_raw: str = ""
    source_pages: list[int] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    rate: Decimal | None = None
    amount: Decimal | None = None
    rate_source: str | None = None
    rate_confidence: float | None = None


class WarningType(StrEnum):
    SCOPE_GAP = "SCOPE_GAP_WARNING"
    UNIT_AMBIGUOUS = "UNIT_AMBIGUOUS"
    STANDARD_UNKNOWN = "STANDARD_UNKNOWN"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    QUANTITY_MISSING = "QUANTITY_MISSING"
    OCR_LOW_QUALITY = "OCR_LOW_QUALITY"


class ExtractionMetadata(BaseModel):
    total_items: int = 0
    avg_confidence: float = 0.0
    processing_time_sec: float = 0.0
    pages_processed: int = 0
    entity_counts: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    doc_id: str
    project_name: str = "Untitled"
    extraction_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_file: str = ""
    entities: list[EntitySpan] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    boq_items: list[BoqRow] = Field(default_factory=list)
    metadata: ExtractionMetadata = Field(default_factory=ExtractionMetadata)
    risk_report: dict | None = Field(default=None)
    low_confidence_entities: list[dict] = Field(default_factory=list)


class IngestedDoc(BaseModel):
    doc_id: str
    source_file: str
    pages: list[str] = Field(default_factory=list)
    tables: list[list[list[str]]] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    is_scanned: bool = False
    ocr_confidence: float | None = None
