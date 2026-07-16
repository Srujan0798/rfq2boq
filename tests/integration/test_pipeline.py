"""Integration tests for full pipeline."""

from decimal import Decimal

from config.constants import EntityType
from src.domain.boq_assembler import BOQAssembler
from src.domain.confidence import ConfidenceScorer
from src.domain.models import BoqRow, EntitySpan


class TestPipelineIntegration:
    def test_assemble_simple_material(self):
        assembler = BOQAssembler()
        entities = [
            EntitySpan(text="cement", type=EntityType.MATERIAL, start=0, end=6, page=1, conf=0.9),
        ]
        relations = []
        items = assembler.assemble(entities, relations, "cement", [1])
        assert len(items) >= 1
        assert items[0].material == "cement"

    def test_assemble_with_quantity_and_unit(self):
        assembler = BOQAssembler()
        entities = [
            EntitySpan(text="cement", type=EntityType.MATERIAL, start=0, end=6, page=1, conf=0.9),
            EntitySpan(text="150", type=EntityType.QUANTITY, start=7, end=10, page=1, conf=0.95),
            EntitySpan(text="bags", type=EntityType.UNIT, start=11, end=15, page=1, conf=0.9),
        ]
        items = assembler.assemble(entities, relations=[], source_text="cement 150 bags", pages=[1])
        assert len(items) == 1
        assert items[0].quantity == Decimal("150")
        # P3_04 (commit 8f649f6): "bags" normalizes to the canonical "bag"
        # via the shared alias table (src/rules/units.py). The old behavior
        # (returning "bags" as a non-canonical form) was the source of
        # subtle row-match mismatches in fidelity audits. This mirrors the
        # already-updated sibling assertion in
        # tests/unit/test_boq_assembler.py::test_assemble_with_quantity_and_unit,
        # which this integration test duplicates but was missed when P3_04 landed.
        assert items[0].unit == "bag"

    def test_assemble_full_realistic_text(self):
        assembler = BOQAssembler()
        entities = [
            EntitySpan(text="concrete", type=EntityType.MATERIAL, start=7, end=15, page=1, conf=0.9),
            EntitySpan(text="M20", type=EntityType.GRADE, start=0, end=3, page=1, conf=0.85),
            EntitySpan(text="150", type=EntityType.QUANTITY, start=20, end=23, page=1, conf=0.95),
            EntitySpan(text="cu.m", type=EntityType.UNIT, start=24, end=28, page=1, conf=0.9),
            EntitySpan(text="ground floor", type=EntityType.LOCATION, start=35, end=46, page=1, conf=0.85),
            EntitySpan(text="IS 456", type=EntityType.STANDARD, start=55, end=61, page=1, conf=0.95),
            EntitySpan(text="Supply", type=EntityType.ACTION, start=0, end=6, page=1, conf=0.8),
        ]
        items = assembler.assemble(
            entities, [], "Supply M20 concrete 150 cu.m in ground floor slab conforming to IS 456", [1]
        )
        assert len(items) == 1
        assert items[0].material == "concrete"
        assert items[0].action == "Supply"
        assert items[0].grade == "M20"
        assert items[0].quantity == Decimal("150")
        assert items[0].location == "ground floor"

    def test_confidence_scoring_complete_item(self):
        scorer = ConfidenceScorer()
        item = BoqRow(
            item_no=1,
            material="cement",
            quantity=Decimal("100"),
            unit="bags",
            confidence=0.9,
        )
        score = scorer.score_item(item)
        assert 0.0 <= score <= 1.0
        assert score >= 0.5

    def test_confidence_scoring_minimal_item(self):
        scorer = ConfidenceScorer()
        item = BoqRow(
            item_no=1,
            material="cement",
            quantity=Decimal("50"),
            unit="bags",
            confidence=0.5,
        )
        score = scorer.score_item(item)
        assert 0.0 <= score <= 1.0

    def test_pipeline_consistency(self):
        assembler = BOQAssembler()
        entities = [
            EntitySpan(text="cement", type=EntityType.MATERIAL, start=0, end=6, page=1, conf=0.9),
            EntitySpan(text="100", type=EntityType.QUANTITY, start=7, end=10, page=1, conf=0.95),
            EntitySpan(text="bags", type=EntityType.UNIT, start=11, end=15, page=1, conf=0.9),
        ]

        result1 = assembler.assemble(entities, [], "test", [1])
        result2 = assembler.assemble(entities, [], "test", [1])

        assert len(result1) == len(result2)
        for r1, r2 in zip(result1, result2, strict=True):
            assert r1.material == r2.material
            assert r1.quantity == r2.quantity

    def test_pipeline_multiple_materials(self):
        assembler = BOQAssembler()
        entities = [
            EntitySpan(text="cement", type=EntityType.MATERIAL, start=0, end=6, page=1, conf=0.9),
            EntitySpan(text="100", type=EntityType.QUANTITY, start=7, end=10, page=1, conf=0.95),
            EntitySpan(text="bags", type=EntityType.UNIT, start=11, end=15, page=1, conf=0.9),
            EntitySpan(text="steel", type=EntityType.MATERIAL, start=50, end=55, page=1, conf=0.9),
            EntitySpan(text="200", type=EntityType.QUANTITY, start=56, end=59, page=1, conf=0.95),
            EntitySpan(text="kg", type=EntityType.UNIT, start=60, end=62, page=1, conf=0.9),
        ]

        items = assembler.assemble(entities, [], "cement 100 bags steel 200 kg", [1])
        assert len(items) == 2
        materials = [item.material for item in items]
        assert "cement" in materials
        assert "steel" in materials


class TestBOQGenerator:
    def test_generate_boq_output(self):
        from src.boq_generator import BOQGenerator

        generator = BOQGenerator()
        items = [
            BoqRow(
                item_no=1,
                material="cement",
                quantity=Decimal("100"),
                unit="bags",
                confidence=0.9,
            )
        ]
        output = generator.generate(items)
        assert "metadata" in output
        assert "boq" in output
        assert output["boq"]["summary"]["total_items"] == 1

    def test_boq_format_item(self):
        from src.boq_generator import BOQGenerator

        generator = BOQGenerator()
        item = BoqRow(
            item_no=1,
            material="concrete",
            quantity=Decimal("150"),
            unit="m³",
            confidence=0.85,
        )
        formatted = generator._format_item(item)
        assert formatted["item_code"] == "BOQ-001"
        assert formatted["material"] == "concrete"
        assert formatted["quantity"] == Decimal("150")


class TestUnitNormalization:
    def test_normalize_unit_cubic_meters(self):
        from src.unit_normalization import normalize_unit

        assert normalize_unit("cu.m") == "cum"
        assert normalize_unit("cum") == "cum"
        assert normalize_unit("cubic meter") == "cum"

    def test_normalize_unit_square_meters(self):
        from src.unit_normalization import normalize_unit

        assert normalize_unit("sq.m") == "sqm"
        assert normalize_unit("sqm") == "sqm"

    def test_normalize_unit_kg(self):
        from src.unit_normalization import normalize_unit

        assert normalize_unit("kg") == "kg"
        assert normalize_unit("KG") == "kg"
        assert normalize_unit("Kg") == "kg"

    def test_normalize_dimension(self):
        from src.unit_normalization import normalize_dimension

        assert normalize_dimension("20mm thick") == "20mm"
        assert normalize_dimension("3m x 2m") == "3m x 2m"

    def test_parse_dimension(self):
        from src.unit_normalization import parse_dimension

        result = parse_dimension("230mm")
        assert result is not None
        assert result["thickness"] == 0.23

        result = parse_dimension("3m x 2m")
        assert result is not None
        assert result["length"] == 3.0
        assert result["width"] == 2.0
