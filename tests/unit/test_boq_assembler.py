"""Tests for BOQ assembler."""

from decimal import Decimal

from config.constants import EntityType
from src.domain.boq_assembler import BOQAssembler
from src.domain.models import EntitySpan


class TestBOQAssembler:
    def test_initialization(self):
        assembler = BOQAssembler()
        assert assembler._item_counter == 0

    def test_assemble_empty(self):
        assembler = BOQAssembler()
        result = assembler.assemble([], [], "test text")
        assert len(result) == 1
        assert result[0].material == ""

    def test_assemble_with_material_only(self):
        assembler = BOQAssembler()
        entities = [
            EntitySpan(
                text="cement",
                type=EntityType.MATERIAL,
                start=0,
                end=6,
                page=1,
                conf=0.9,
            )
        ]
        result = assembler.assemble(entities, [], "cement")
        assert len(result) == 1
        assert result[0].material == "cement"

    def test_assemble_with_quantity_and_unit(self):
        assembler = BOQAssembler()
        entities = [
            EntitySpan(text="cement", type=EntityType.MATERIAL, start=0, end=6, page=1, conf=0.9),
            EntitySpan(text="150", type=EntityType.QUANTITY, start=7, end=10, page=1, conf=0.95),
            EntitySpan(text="bags", type=EntityType.UNIT, start=11, end=15, page=1, conf=0.9),
        ]
        result = assembler.assemble(entities, [], "cement 150 bags")
        assert len(result) == 1
        assert result[0].quantity == Decimal("150")
        assert result[0].unit == "bags"

    def test_assemble_with_grade(self):
        assembler = BOQAssembler()
        entities = [
            EntitySpan(text="concrete", type=EntityType.MATERIAL, start=0, end=8, page=1, conf=0.9),
            EntitySpan(text="M20", type=EntityType.GRADE, start=9, end=12, page=1, conf=0.85),
        ]
        result = assembler.assemble(entities, [], "concrete M20")
        assert len(result) == 1
        assert result[0].grade == "M20"

    def test_assemble_quantity_before_material(self):
        assembler = BOQAssembler()
        entities = [
            EntitySpan(text="concrete", type=EntityType.MATERIAL, start=10, end=18, page=1, conf=0.9),
            EntitySpan(text="150", type=EntityType.QUANTITY, start=0, end=3, page=1, conf=0.95),
            EntitySpan(text="cu.m", type=EntityType.UNIT, start=4, end=8, page=1, conf=0.9),
        ]
        result = assembler.assemble(entities, [], "150 cu.m concrete")
        assert len(result) == 1
        assert result[0].quantity == Decimal("150")
        assert result[0].unit == "m³"

    def test_assemble_full_realistic(self):
        assembler = BOQAssembler()
        entities = [
            EntitySpan(text='concrete', type=EntityType.MATERIAL, start=7, end=15, page=1, conf=0.9),
            EntitySpan(text='M20', type=EntityType.GRADE, start=0, end=3, page=1, conf=0.85),
            EntitySpan(text='150', type=EntityType.QUANTITY, start=20, end=23, page=1, conf=0.95),
            EntitySpan(text='cu.m', type=EntityType.UNIT, start=24, end=28, page=1, conf=0.9),
            EntitySpan(text='ground floor', type=EntityType.LOCATION, start=35, end=46, page=1, conf=0.85),
            EntitySpan(text='IS 456', type=EntityType.STANDARD, start=55, end=61, page=1, conf=0.95),
            EntitySpan(text='Supply', type=EntityType.ACTION, start=0, end=6, page=1, conf=0.8),
        ]
        result = assembler.assemble(
            entities, [],
            'Supply M20 concrete 150 cu.m in ground floor slab conforming to IS 456',
            [1]
        )
        assert len(result) == 1
        assert result[0].material == "concrete"
        assert result[0].action == "Supply"
        assert result[0].grade == "M20"
        assert result[0].quantity == Decimal("150")
        assert result[0].unit == "m³"
        assert result[0].location == "ground floor"
        assert result[0].standard == ["IS 456"]

    def test_deduplicate_same_items(self):
        from src.domain.models import BoqRow

        item1 = BoqRow(
            item_no=1,
            material="cement",
            quantity=Decimal("100"),
            unit="bags",
            confidence=0.9,
        )
        item2 = BoqRow(
            item_no=2,
            material="cement",
            quantity=Decimal("50"),
            unit="bags",
            confidence=0.85,
        )

        items = [item1, item2]
        assembler = BOQAssembler()
        result = assembler.deduplicate(items)
        assert len(result) == 1
        assert result[0].quantity == Decimal("150")
