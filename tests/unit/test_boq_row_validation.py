"""Tests for BoqRow.validate() and export filtering."""

import json
from decimal import Decimal

from src.domain.models import BoqRow


class TestBoqRowValidate:
    def test_valid_row(self):
        r = BoqRow(material="Cement", quantity=Decimal("100"), unit="kg")
        assert r.validate() == []

    def test_empty_material(self):
        r = BoqRow(material="", quantity=Decimal("10"), unit="kg")
        errs = r.validate()
        assert any("material" in e for e in errs)

    def test_whitespace_material(self):
        r = BoqRow(material="   ", quantity=Decimal("10"), unit="kg")
        errs = r.validate()
        assert any("material" in e for e in errs)

    def test_zero_quantity_valid(self):
        # Zero quantity is valid for BOQ rows (e.g. rate-only items, pending qty)
        r = BoqRow(material="Cement", quantity=Decimal("0"), unit="kg")
        errs = r.validate()
        assert not any("quantity" in e for e in errs)

    def test_negative_quantity(self):
        r = BoqRow(material="Cement", quantity=Decimal("-5"), unit="kg")
        errs = r.validate()
        assert any("quantity" in e for e in errs)

    def test_empty_unit(self):
        r = BoqRow(material="Cement", quantity=Decimal("10"), unit="")
        errs = r.validate()
        assert any("unit" in e for e in errs)

    def test_whitespace_unit(self):
        r = BoqRow(material="Cement", quantity=Decimal("10"), unit="  ")
        errs = r.validate()
        assert any("unit" in e for e in errs)

    def test_multiple_errors(self):
        r = BoqRow(material="", quantity=Decimal("-1"), unit="")
        errs = r.validate()
        assert len(errs) >= 3

    def test_rate_only_zero_quantity_valid(self):
        r = BoqRow(material="Cement", quantity=Decimal("0"), unit="kg", rate_only=True)
        errs = r.validate()
        assert errs == []

    def test_rate_only_with_quantity_valid(self):
        r = BoqRow(material="Cement", quantity=Decimal("100"), unit="kg", rate_only=True)
        assert r.validate() == []

    def test_none_quantity(self):
        r = BoqRow(material="Cement", quantity=Decimal("0"), unit="kg")
        r.quantity = None
        errs = r.validate()
        assert any("quantity" in e for e in errs)


class TestExcelExportSkipsInvalid:
    def test_invalid_rows_skipped(self, tmp_path):
        from src.export.excel_generator import CPWDExcelGenerator

        gen = CPWDExcelGenerator()
        items = [
            BoqRow(material="Cement", quantity=Decimal("100"), unit="kg"),
            BoqRow(material="", quantity=Decimal("0"), unit=""),
            BoqRow(material="Steel", quantity=Decimal("50"), unit="kg"),
        ]
        out = tmp_path / "test.xlsx"
        gen.export(items, str(out))
        assert out.exists()

    def test_dict_items_not_crashed(self, tmp_path):
        from src.export.excel_generator import CPWDExcelGenerator

        gen = CPWDExcelGenerator()
        items = [
            {"material": "Cement", "quantity": 100, "unit": "kg"},
            {"material": "Steel", "quantity": 50, "unit": "kg"},
        ]
        out = tmp_path / "test.xlsx"
        gen.export(items, str(out))
        assert out.exists()

    def test_empty_items(self, tmp_path):
        from src.export.excel_generator import CPWDExcelGenerator

        gen = CPWDExcelGenerator()
        out = tmp_path / "test.xlsx"
        gen.export([], str(out))
        assert out.exists()


class TestJsonExportSkipsInvalid:
    def test_invalid_rows_skipped(self):
        from src.domain.models import ExtractionResult
        from src.export.json_formatter import JSONFormatter

        result = ExtractionResult(
            doc_id="test",
            boq_items=[
                BoqRow(material="Cement", quantity=Decimal("100"), unit="kg"),
                BoqRow(material="", quantity=Decimal("0"), unit=""),
            ],
        )
        formatter = JSONFormatter()
        output = formatter.format(result)
        parsed = json.loads(output)
        materials = [it["material"] for it in parsed["boq_items"]]
        assert "Cement" in materials
        assert "" not in materials


class TestAlphanumericItemNoGoldLoad:
    """Regression: 05_zydus row-gold uses hierarchical item_no like 'A.6'."""

    def test_row_gold_zydus_item_nos_construct_boqrow(self):
        gold_path = (
            __import__("pathlib").Path(__file__).resolve().parents[2]
            / "data"
            / "real_rfqs"
            / "gold"
            / "rows"
            / "05_zydus_animal_pharmez.rowgold.json"
        )
        if not gold_path.exists():
            return  # skip quietly if gold not present in this checkout
        with open(gold_path) as fh:
            data = json.load(fh)
        rows = []
        for e in data.get("entries", []):
            rows.append(
                BoqRow(
                    item_no=e.get("item_no", 1),
                    material=e.get("material", ""),
                    quantity=Decimal(str(e.get("quantity", "0"))),
                    unit=e.get("unit", "no."),
                )
            )
        assert len(rows) > 0
        assert any(isinstance(r.item_no, str) for r in rows)
        assert any(r.item_no == "A.6" for r in rows)
