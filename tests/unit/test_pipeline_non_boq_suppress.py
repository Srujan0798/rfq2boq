"""Unit tests for Pipeline non-BOQ PDF suppression and section-chrome drops.

Uses object.__new__(Pipeline) so no PDF runs, torch, or HF model downloads.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

from config.constants import FlagCode
from src.domain.models import BoqRow
from src.pipeline import Pipeline


def _bare_pipeline() -> Pipeline:
    """Instantiate Pipeline without __init__ (avoids heavy component setup)."""
    return object.__new__(Pipeline)


def _row(
    material: str,
    quantity: str | int | float = 0,
    unit: str = "no.",
    *,
    rate_only: bool = False,
    item_no: int = 1,
) -> BoqRow:
    return BoqRow(
        item_no=item_no,
        material=material,
        quantity=Decimal(str(quantity)),
        unit=unit,
        rate_only=rate_only,
    )


class TestSuppressNonBoqPdfItems:
    def test_tech_specs_short_materials_cleared(self):
        p = _bare_pipeline()
        items = [
            _row("Armaflex", 0, "no."),
            _row("plate", 0, "no."),
            _row("Standard Method", 0, "nos"),
        ]
        path = Path("/docs/Tech Specs - Insulation.pdf")

        kept, flags = p._suppress_non_boq_pdf_items(path, items)

        assert kept == []
        assert len(flags) == 1
        assert flags[0].code == FlagCode.TABLE_TYPE_NOT_BOQ
        assert "tech-spec" in flags[0].message.lower() or "datasheet" in flags[0].message.lower()

    def test_boq_named_pdf_keeps_billable_rows(self):
        p = _bare_pipeline()
        items = [
            _row(
                "Closed cell elastomeric NBR insulation 19 mm thick on chilled water pipes",
                250,
                "sqm",
                item_no=1,
            ),
            _row(
                "Underdeck insulation with aluminium foil faced polyurethane foam 50 mm",
                800,
                "sqm",
                item_no=2,
            ),
        ]
        path = Path("/docs/BOQ - Insulation.pdf")

        kept, flags = p._suppress_non_boq_pdf_items(path, items)

        assert len(kept) == 2
        assert flags == []
        assert kept[0].material.startswith("Closed cell")
        assert float(kept[1].quantity) == 800

    def test_empty_items_passthrough(self):
        p = _bare_pipeline()
        kept, flags = p._suppress_non_boq_pdf_items(Path("whatever.pdf"), [])
        assert kept == []
        assert flags == []

    def test_short_zero_qty_noise_without_spec_name(self):
        """Non-spec filename still suppressed when all short, zero-qty chrome."""
        p = _bare_pipeline()
        items = [
            _row("Armaflex", 0, "no."),
            _row("plate", 0, "no."),
            _row("foam", 0, "nos"),
            _row("IS 3346", 0, "no."),
        ]
        path = Path("/docs/drawing-notes.pdf")

        kept, flags = p._suppress_non_boq_pdf_items(path, items)

        assert kept == []
        assert len(flags) == 1
        assert flags[0].code == FlagCode.NO_BOQ_SECTION_FOUND


class TestPostProcessSectionChrome:
    def test_hvac_works_description_dropped(self):
        p = _bare_pipeline()
        # catalog_matcher used after filter step; stub to stay light.
        match = MagicMock()
        match.to_dict.return_value = {"method": "none", "is_unmatched": True}
        p.catalog_matcher = MagicMock()
        p.catalog_matcher.match.return_value = match

        items = [
            _row("HVAC WORKS Description", 0, "no.", item_no=1),
            _row(
                "Supply and install closed cell elastomeric insulation 19mm thick",
                120,
                "sqm",
                item_no=2,
            ),
        ]

        out = p._post_process_items(items)

        materials = [i.material for i in out]
        assert not any("HVAC WORKS" in m for m in materials)
        assert any("elastomeric" in m.lower() for m in materials)

    def test_lone_description_chrome_dropped(self):
        p = _bare_pipeline()
        match = MagicMock()
        match.to_dict.return_value = {"method": "none", "is_unmatched": True}
        p.catalog_matcher = MagicMock()
        p.catalog_matcher.match.return_value = match

        items = [
            _row("Description", 0, "no."),
            _row("Item Description", 0, "nos"),
            _row("Particulars", 0, "no."),
            _row(
                "Rockwool slab insulation density 48 kg/cum for duct external",
                45,
                "sqm",
            ),
        ]

        out = p._post_process_items(items)
        mats_lower = [m.material.lower() for m in out]

        assert "description" not in mats_lower
        assert "item description" not in mats_lower
        assert "particulars" not in mats_lower
        assert any("rockwool" in m for m in mats_lower)

class TestRepairSwappedUnitMaterial:
    """UBS-style column shift: material='Rmt', unit='Dia - 9.5 mm' → swap."""

    def _stub_catalog(self, p: Pipeline) -> None:
        match = MagicMock()
        match.to_dict.return_value = {"method": "none", "is_unmatched": True}
        p.catalog_matcher = MagicMock()
        p.catalog_matcher.match.return_value = match

    def test_swaps_rmt_material_with_dia_unit(self):
        p = _bare_pipeline()
        self._stub_catalog(p)
        items = [
            _row("Rmt", 289, "Dia - 9.5 mm", item_no=1),
            _row("Rmt", 536, "Dia - 12.7 mm", item_no=2),
            _row("32 mm dia", 142, "rmt", item_no=3),
        ]
        out = p._post_process_items(items)
        mats = [(i.material or "").strip() for i in out]
        assert "Dia - 9.5 mm" in mats or any("9.5" in m for m in mats)
        assert "Dia - 12.7 mm" in mats or any("12.7" in m for m in mats)
        assert any("32 mm dia" in m for m in mats)
        # Repaired rows must use a length unit, not a size string as unit.
        for i in out:
            if "9.5" in (i.material or "") or "12.7" in (i.material or ""):
                assert "mm" not in (i.unit or "").lower() or "dia" not in (i.unit or "").lower()
                assert (i.unit or "").lower() in {"rmt", "rm", "mtr", "m"}
        assert len(out) >= 3

    def test_does_not_swap_real_materials(self):
        p = _bare_pipeline()
        self._stub_catalog(p)
        items = [
            _row(
                "Closed cell elastomeric NBR insulation 19 mm thick on chilled water pipes",
                250,
                "sqm",
            ),
        ]
        out = p._post_process_items(items)
        assert len(out) == 1
        assert "elastomeric" in out[0].material.lower()
        assert out[0].unit.lower() == "sqm"


class TestBufferTankDatasheetSuppress:
    """MECH buffer-tank PDF: keep 1.1 SITC + 1.2 tank-spec; drop weld/proviso chrome."""

    def test_keeps_sitc_and_tank_spec_drops_weld_and_proviso(self):
        p = _bare_pipeline()
        items = [
            _row(
                "Supply, installation, testing and commissioning of Horizontal type "
                "chilled water buffer tank complete with carbon steel, Baffles, "
                "designed per ASME SECT. VIII DIV I with SA516 shell",
                0,
                "nos",
                rate_only=True,
                item_no=1,
            ),
            _row(
                "Provide the below provision along with Tank: Detachable Ladder "
                "and Platform arrangement above the Tank suitable for site install",
                1,
                "nos",
                item_no=2,
            ),
            _row(
                "Tank shall be as per below specifications: Buffer Tank dia. Should "
                "be max 2500 mm. Buffer Tank Length should be max 7000 mm.",
                1,
                "nos",
                item_no=3,
            ),
            _row("PIPE TO FLANGE WELD DETAIL", 5, "rmt", item_no=4),
            _row("N9 R PIPE TO FLANGE WELD DETAIL N10 F", 3, "rmt", item_no=5),
            # duplicate SITC tranche reprint
            _row(
                "Supply, installation, testing and commissioning of Horizontal type "
                "chilled water buffer tank complete with carbon steel, Baffles, "
                "designed per ASME SECT. VIII DIV I with SA516 shell",
                0,
                "nos",
                rate_only=True,
                item_no=6,
            ),
        ]
        path = Path("/docs/MECH-EIPL-HVAC-NXTRA-001-R2-BUFFER TANK.pdf")
        kept, flags = p._suppress_non_boq_pdf_items(path, items)
        mats = [(i.material or "").lower() for i in kept]
        assert len(kept) == 2, [m[:60] for m in mats]
        assert any("supply, installation" in m and "buffer tank" in m for m in mats)
        assert any("shall be as per" in m for m in mats)
        assert not any("weld detail" in m for m in mats)
        assert not any("provide the below" in m for m in mats)
        assert flags == []

    def test_sitc_not_killed_by_embedded_asme_marker(self):
        p = _bare_pipeline()
        items = [
            _row(
                "Supply, installation, testing and commissioning of Horizontal type "
                "chilled water buffer tank ASME SECT VIII SA516 design pressure notes",
                0,
                "nos",
                rate_only=True,
            ),
        ]
        path = Path("/docs/equipment-buffer-tank-datasheet.pdf")
        kept, flags = p._suppress_non_boq_pdf_items(path, items)
        assert len(kept) == 1
        assert "buffer tank" in (kept[0].material or "").lower()

