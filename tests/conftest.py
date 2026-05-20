from datetime import datetime
from decimal import Decimal

import pytest
from config.constants import EntityType, RelationType
from src.domain import BoqRow, EntitySpan, ExtractionMetadata, ExtractionResult, Relation
from src.domain.models import EntitySourceType


@pytest.fixture
def sample_rfq_text():
    return """
    SCOPE OF WORK
    Supply and install 2mm galvanized steel cladding to exterior walls
    as per IS 2062 Grade 43. Quantity: 500 sqm.

    Provide and lay M25 grade concrete for ground floor slab as per
    IS 456. Quantity: 200 cum.

    Supply, fabricate and erect structural steel members using Fe 500
    TMT bars conforming to IS 1786 for basement columns. Quantity: 15000 kg.
    """


@pytest.fixture
def sample_entities():
    bert = EntitySourceType.BERT
    return [
        EntitySpan(
            text="galvanized steel", type=EntityType.MATERIAL,
            start=17, end=34, page=1, conf=0.92, source=bert
        ),
        EntitySpan(
            text="2mm", type=EntityType.DIMENSION,
            start=11, end=16, page=1, conf=0.95, source=bert
        ),
        EntitySpan(
            text="500", type=EntityType.QUANTITY,
            start=72, end=75, page=1, conf=0.98, source=bert
        ),
        EntitySpan(
            text="sqm", type=EntityType.UNIT,
            start=76, end=79, page=1, conf=0.95, source=bert
        ),
        EntitySpan(
            text="exterior walls", type=EntityType.LOCATION,
            start=47, end=60, page=1, conf=0.88, source=bert
        ),
        EntitySpan(
            text="IS 2062", type=EntityType.STANDARD,
            start=62, end=69, page=1, conf=0.90, source=bert
        ),
        EntitySpan(
            text="Grade 43", type=EntityType.GRADE,
            start=70, end=78, page=1, conf=0.85, source=bert
        ),
        EntitySpan(
            text="M25", type=EntityType.GRADE,
            start=107, end=109, page=1, conf=0.95, source=bert
        ),
        EntitySpan(
            text="concrete", type=EntityType.MATERIAL,
            start=111, end=119, page=1, conf=0.92, source=bert
        ),
        EntitySpan(
            text="200", type=EntityType.QUANTITY,
            start=137, end=140, page=1, conf=0.98, source=bert
        ),
        EntitySpan(
            text="cum", type=EntityType.UNIT,
            start=141, end=144, page=1, conf=0.95, source=bert
        ),
        EntitySpan(
            text="ground floor slab", type=EntityType.LOCATION,
            start=122, end=137, page=1, conf=0.88, source=bert
        ),
        EntitySpan(
            text="IS 456", type=EntityType.STANDARD,
            start=145, end=151, page=1, conf=0.90, source=bert
        ),
        EntitySpan(
            text="Fe 500", type=EntityType.GRADE,
            start=174, end=179, page=1, conf=0.95, source=bert
        ),
        EntitySpan(
            text="steel", type=EntityType.MATERIAL,
            start=180, end=185, page=1, conf=0.92, source=bert
        ),
        EntitySpan(
            text="IS 1786", type=EntityType.STANDARD,
            start=200, end=207, page=1, conf=0.90, source=bert
        ),
        EntitySpan(
            text="15000", type=EntityType.QUANTITY,
            start=220, end=225, page=1, conf=0.98, source=bert
        ),
        EntitySpan(
            text="kg", type=EntityType.UNIT,
            start=226, end=228, page=1, conf=0.95, source=bert
        ),
        EntitySpan(
            text="basement columns", type=EntityType.LOCATION,
            start=208, end=220, page=1, conf=0.88, source=bert
        ),
    ]


@pytest.fixture
def sample_relations():
    return [
        Relation(head_id="0", tail_id="1", type=RelationType.HAS_DIMENSION, conf=0.90),
        Relation(head_id="0", tail_id="2", type=RelationType.HAS_QUANTITY, conf=0.90),
        Relation(head_id="2", tail_id="3", type=RelationType.HAS_UNIT, conf=0.90),
        Relation(head_id="0", tail_id="4", type=RelationType.AT_LOCATION, conf=0.90),
        Relation(head_id="8", tail_id="7", type=RelationType.OF_GRADE, conf=0.90),
        Relation(head_id="8", tail_id="9", type=RelationType.HAS_QUANTITY, conf=0.90),
    ]


@pytest.fixture
def sample_boq_rows():
    return [
        BoqRow(
            item_no=1,
            material="galvanized steel",
            quantity=Decimal("500"),
            unit="m²",
            action="install",
            grade="Grade 43",
            standard=["IS 2062"],
            location="exterior walls",
            confidence=0.88,
            description_raw="2mm galvanized steel cladding to exterior walls",
            source_pages=[1],
        ),
        BoqRow(
            item_no=2,
            material="concrete",
            quantity=Decimal("200"),
            unit="m³",
            action="lay",
            grade="M25",
            standard=["IS 456"],
            location="ground floor slab",
            confidence=0.90,
            description_raw="M25 concrete to ground floor slab",
            source_pages=[1],
        ),
        BoqRow(
            item_no=3,
            material="steel",
            quantity=Decimal("15000"),
            unit="kg",
            action="erect",
            grade="Fe 500",
            standard=["IS 1786"],
            location="basement columns",
            confidence=0.87,
            description_raw="Fe 500 steel to basement columns",
            source_pages=[1],
        ),
    ]


@pytest.fixture
def sample_extraction_result(sample_entities, sample_relations, sample_boq_rows):
    return ExtractionResult(
        doc_id="test-doc-001",
        project_name="Test Project",
        extraction_date=datetime.now(),
        source_file="sample_rfq.pdf",
        entities=sample_entities,
        relations=sample_relations,
        boq_items=sample_boq_rows,
        metadata=ExtractionMetadata(
            total_items=3,
            avg_confidence=0.88,
            processing_time_sec=5.2,
            pages_processed=1,
            entity_counts={"MATERIAL": 2, "QUANTITY": 3, "UNIT": 3, "LOCATION": 3},
            warnings=[],
        ),
    )


@pytest.fixture
def api_client():
    from httpx import AsyncClient
    from src.api.main import app
    return AsyncClient(app=app, base_url="http://test")


@pytest.fixture
def tmp_output_dir(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    return output
