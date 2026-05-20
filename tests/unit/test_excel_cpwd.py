"""Tests for CPWD Excel BOQ generator."""


import openpyxl
import pytest
from src.export.excel_generator import CPWDExcelGenerator


@pytest.fixture
def dsr_rates():
    return {
        "earthwork in excavation by mechanical means in ordinary soil": {
            "code": "2.1.1",
            "description": "Earthwork in excavation by mechanical means in ordinary soil",
            "rate_inr": 245.5,
            "unit": "cum",
        },
        "m20 grade concrete in foundation": {
            "code": "2.2.1",
            "description": "M20 grade concrete in foundation",
            "rate_inr": 5800.0,
            "unit": "cum",
        },
        "brickwork in cement mortar 1:6": {
            "code": "3.1.1",
            "description": "Brickwork in cement mortar 1:6",
            "rate_inr": 6200.0,
            "unit": "cum",
        },
    }


@pytest.fixture
def sample_boq_items():
    return [
        {
            "material": "Earthwork in excavation by mechanical means",
            "quantity": 100,
            "unit": "cum",
            "rate": 245.5,
            "description": "Earthwork in excavation by mechanical means",
        },
        {
            "material": "M20 grade concrete in foundation",
            "quantity": 50,
            "unit": "cum",
            "rate": 5800.0,
            "description": "M20 grade concrete in foundation",
        },
        {
            "material": "Brickwork in cement mortar 1:6",
            "quantity": 200,
            "unit": "cum",
            "rate": 6200.0,
            "description": "Brickwork in cement mortar 1:6",
        },
    ]


class TestCPWDExcelGenerator:
    def test_export_creates_file(self, dsr_rates, sample_boq_items, tmp_path):
        gen = CPWDExcelGenerator()
        out = tmp_path / "test_boq.xlsx"
        gen.export(sample_boq_items, str(out), {"project": "Test Project", "location": "Delhi"})
        assert out.exists()
        assert out.stat().st_size > 1024

    def test_column_headers_correct(self, dsr_rates, sample_boq_items, tmp_path):
        gen = CPWDExcelGenerator()
        out = tmp_path / "test_boq.xlsx"
        gen.export(sample_boq_items, str(out))
        wb = openpyxl.load_workbook(str(out))
        ws = wb.active
        headers = [ws.cell(row=9, column=c).value for c in range(1, 9)]
        expected = ["S.No", "DSR Code", "Description", "Unit", "Quantity", "Rate (₹)", "Amount (₹)", "Notes"]
        assert headers == expected

    def test_rupee_formatting_present(self, dsr_rates, sample_boq_items, tmp_path):
        gen = CPWDExcelGenerator()
        out = tmp_path / "test_boq.xlsx"
        gen.export(sample_boq_items, str(out))
        wb = openpyxl.load_workbook(str(out))
        ws = wb.active
        found = False
        for row in range(10, 50):
            cell = ws.cell(row=row, column=6)
            if cell.value is not None:
                fmt = str(cell.number_format or "")
                if "₹" in fmt:
                    found = True
                    break
        assert found, "No ₹ formatting found in rate column"

    def test_trade_grouping(self, dsr_rates, sample_boq_items, tmp_path):
        gen = CPWDExcelGenerator()
        out = tmp_path / "test_boq.xlsx"
        gen.export(sample_boq_items, str(out))
        wb = openpyxl.load_workbook(str(out))
        ws = wb.active
        cell_values = [ws.cell(row=r, column=1).value for r in range(1, 60)]
        assert any("excavation" in str(v).lower() for v in cell_values if v)
        assert any("concrete" in str(v).lower() for v in cell_values if v)
        assert any("brickwork" in str(v).lower() for v in cell_values if v)

    def test_subtotal_formula_sum(self, dsr_rates, sample_boq_items, tmp_path):
        gen = CPWDExcelGenerator()
        out = tmp_path / "test_boq.xlsx"
        gen.export(sample_boq_items, str(out))
        wb = openpyxl.load_workbook(str(out))
        ws = wb.active
        formulas = []
        for row in range(1, 60):
            cell = ws.cell(row=row, column=7)
            if cell.value and isinstance(cell.value, str) and cell.value.startswith("=SUM"):
                formulas.append(cell.value)
        assert len(formulas) >= 1, "No SUM formulas found"

    def test_grand_total_formula(self, dsr_rates, sample_boq_items, tmp_path):
        gen = CPWDExcelGenerator()
        out = tmp_path / "test_boq.xlsx"
        gen.export(sample_boq_items, str(out))
        wb = openpyxl.load_workbook(str(out))
        ws = wb.active
        found = False
        for row in range(1, 60):
            cell = ws.cell(row=row, column=1)
            if cell.value == "GRAND TOTAL":
                amt_cell = ws.cell(row=row, column=7)
                assert amt_cell.value and str(amt_cell.value).startswith("=SUM")
                found = True
                break
        assert found, "GRAND TOTAL row not found"

    def test_gst_row_present(self, dsr_rates, sample_boq_items, tmp_path):
        gen = CPWDExcelGenerator()
        out = tmp_path / "test_boq.xlsx"
        gen.export(sample_boq_items, str(out))
        wb = openpyxl.load_workbook(str(out))
        ws = wb.active
        cell_values = [ws.cell(row=r, column=6).value for r in range(1, 60)]
        assert any("gst" in str(v).lower() for v in cell_values if v)

    def test_project_metadata_in_header(self, dsr_rates, sample_boq_items, tmp_path):
        gen = CPWDExcelGenerator()
        out = tmp_path / "test_boq.xlsx"
        gen.export(
            sample_boq_items,
            str(out),
            {"project": "Test Project", "location": "Delhi", "reference": "REF/001", "contractor": "ABC Corp"},
        )
        wb = openpyxl.load_workbook(str(out))
        ws = wb.active
        assert ws.cell(row=2, column=2).value == "Test Project"
        assert ws.cell(row=3, column=2).value == "Delhi"
        assert ws.cell(row=5, column=2).value == "REF/001"

    def test_boq_row_model_compatible(self):
        from src.domain.models import BoqRow
        row = BoqRow(material="Test", quantity=10, unit="nos", rate=100)
        gen = CPWDExcelGenerator()
        d = gen._as_dict(row)
        assert d["material"] == "Test"
        assert d["quantity"] == 10

    def test_dsr_lookup(self, dsr_rates, sample_boq_items):
        gen = CPWDExcelGenerator(dsr_rates_path=None)
        gen.dsr_rates = dsr_rates
        code, rate = gen._lookup_dsr("Earthwork in excavation by mechanical means in ordinary soil")
        assert code == "2.1.1"
        assert rate == 245.5

    def test_empty_boq_export(self, dsr_rates, tmp_path):
        gen = CPWDExcelGenerator()
        out = tmp_path / "empty_boq.xlsx"
        gen.export([], str(out), {"project": "Empty Test"})
        wb = openpyxl.load_workbook(str(out))
        ws = wb.active
        assert ws.cell(row=1, column=1).value == "BILL OF QUANTITIES (CPWD FORMAT)"

    def test_trade_detection(self, dsr_rates, sample_boq_items):
        gen = CPWDExcelGenerator()
        gen.dsr_rates = dsr_rates
        assert gen._detect_trade("earthwork in excavation") == "excavation"
        assert gen._detect_trade("M20 concrete") == "concrete"
        assert gen._detect_trade("random material") == "general"

    def test_amount_calculation(self, dsr_rates, sample_boq_items):
        gen = CPWDExcelGenerator()
        item = {"quantity": 10, "rate": 500}
        assert gen._get_amount(item) == 5000.0

    def test_dsrmatched_rate_used(self, dsr_rates, sample_boq_items):
        gen = CPWDExcelGenerator()
        gen.dsr_rates = dsr_rates
        item = {"material": "Earthwork in excavation", "quantity": 100, "unit": "cum"}
        code, rate = gen._lookup_dsr(item["material"])
        assert rate == 245.5
