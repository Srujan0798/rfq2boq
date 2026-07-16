"""Domain models for RFQ2BOQ."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from config.constants import EntityType, RelationType
from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from src.domain.flags import Flag


class EntitySourceType(StrEnum):
    BERT = "BERT"
    GAZETTEER = "GAZETTEER"
    REGEX = "REGEX"
    MANUAL = "MANUAL"
    GOLD = "GOLD"


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
    # Construction BOQs use hierarchical / alphanumeric item codes
    # (e.g. "A.6", "1.2.3", "B.drain.1") as well as sequential ints.
    item_no: int | str = Field(default=1)
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
    rate_only: bool = False
    source_pages: list[int] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    parent_context: list[str] = Field(
        default_factory=list,
        description=(
            "P3_03 hierarchy inheritance: ordered list of ancestor material "
            "descriptions (outermost parent first, item's own material last). "
            "Empty list for top-level items with no parent. Always contains "
            "at least the item's own material."
        ),
    )
    catalog_match: dict | None = Field(
        default=None,
        description=(
            "GeM catalog match result from CatalogMatcher. "
            "Keys: input_text, gem_id, gem_name, matched_alias, confidence, "
            "method (exact/alias_exact/token_overlap/substring/edit_distance/none), "
            "is_unmatched, material, standards."
        ),
    )
    flags: list[Flag] = Field(
        default_factory=list,
        description=(
            "P3_04 typed flags attached to this row.  Surfaces every "
            "uncertainty (low confidence, unknown unit, non-catalog "
            "material, dropped source row reference) as a typed "
            "Flag.  JSON exporter writes these as 'flags' array.  "
            "The legacy 'warnings' list[str] is also populated for "
            "backward compatibility (each flag.to_legacy_warning())."
        ),
    )

    @field_validator("item_no", mode="before")
    @classmethod
    def _normalize_item_no(cls, v: object) -> int | str:
        """Accept sequential ints and hierarchical codes; reject empty/non-positive ints."""
        if v is None:
            raise ValueError("item_no is required")
        if isinstance(v, bool):
            # bool is a subclass of int; reject explicitly before the int branch.
            raise ValueError("item_no must not be a boolean")
        if isinstance(v, int):
            if v <= 0:
                raise ValueError("item_no must be > 0 when integer")
            return v
        if isinstance(v, float):
            if v != int(v) or int(v) <= 0:
                raise ValueError("item_no must be a positive whole number or hierarchical code")
            return int(v)
        s = str(v).strip()
        if not s:
            raise ValueError("item_no must not be empty")
        # Pure digit strings stay int for backward compatibility with numeric BOQs.
        if s.isdigit():
            n = int(s)
            if n <= 0:
                raise ValueError("item_no must be > 0 when integer")
            return n
        return s

    def validate(self) -> list[str]:  # type: ignore[override]
        """Return list of validation error messages. Empty list = valid."""
        errors: list[str] = []
        if not self.material or not self.material.strip():
            errors.append("material is empty")
        if (self.quantity is None or self.quantity < 0) and not self.rate_only:
            errors.append(f"quantity is invalid: {self.quantity}")
        if not self.unit or not self.unit.strip():
            errors.append("unit is empty")
        return errors


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
    flags: list[Flag] = Field(
        default_factory=list,
        description=(
            "P3_04 typed document-level flags.  Surfaces every "
            "uncertainty at the document scope (e.g. STRUCTURE_FALLBACK, "
            "TABLE_TYPE_NOT_BOQ, PIPELINE_ERROR).  Row-attached flags "
            "live in BoqRow.flags.  JSON exporter writes these as "
            "metadata.flags; legacy string-form warnings are "
            "preserved in metadata.warnings."
        ),
    )


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


# P3_04: resolve the Flag forward-refs in BoqRow / ExtractionMetadata
# after the flags module is importable.  Imports are deferred to here
# (after the BoqRow + ExtractionMetadata classes are defined) so the
# flags module can import from config/constants without a cycle.
# Use ``importlib`` + direct module path to avoid triggering
# ``src.domain.__init__`` (which would re-enter this module while
# it's still being loaded).
import importlib as _il  # noqa: E402  (deferred to here deliberately)

try:
    _flags_mod = _il.import_module("src.domain.flags")
    Flag = _flags_mod.Flag  # type: ignore[no-redef,misc]  # noqa: F401  (re-exported for callers)
    BoqRow.model_rebuild()
    ExtractionMetadata.model_rebuild()
    del _flags_mod
    __all__ = [
        "EntitySourceType",
        "EntitySpan",
        "Relation",
        "BoqRow",
        "WarningType",
        "ExtractionMetadata",
        "ExtractionResult",
        "IngestedDoc",
        "Flag",
    ]
except Exception:
    # src.domain.flags not importable (very early bootstrap); the
    # type-checker-only annotation in BoqRow.flags is fine.  When
    # the flags module is imported later, the caller should
    # ``BoqRow.model_rebuild()`` explicitly.
    pass
