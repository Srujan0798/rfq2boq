"""Tests for XLSXColumnMapper."""

from src.domain.xlsx_column_mapper import XLSXColumnMapper


class TestXLSXColumnMapper:
    def test_header_description_maps_to_material(self) -> None:
        mapper = XLSXColumnMapper()
        headers = ["Item No.", "Description", "Unit", "Quantity", "Rate"]
        sample_rows = [
            ["1", "Supply of cement", "kg", "500", "100"],
            ["2", "M20 concrete", "m³", "10", "5000"],
        ]
        result = mapper.map_columns(headers, sample_rows)
        assert result.material_col == 1
        assert result.unit_col == 2
        assert result.quantity_col == 3

    def test_header_qty_quantity_maps_to_quantity(self) -> None:
        mapper = XLSXColumnMapper()
        headers = ["Sr. No.", "Item", "Qty", "Unit"]
        sample_rows = [
            ["1", "Steel bars", "100", "kg"],
            ["2", "Plywood", "50", "sqm"],
        ]
        result = mapper.map_columns(headers, sample_rows)
        assert result.quantity_col == 2

    def test_header_unit_uom_maps_to_unit(self) -> None:
        mapper = XLSXColumnMapper()
        headers = ["No.", "Material", "UoM", "Amount"]
        sample_rows = [
            ["1", "Mineral wool", "kg", "5000"],
            ["2", "Glass wool", "m³", "3000"],
        ]
        result = mapper.map_columns(headers, sample_rows)
        assert result.unit_col == 2

    def test_header_Unit_with_capital_U_maps_to_unit(self) -> None:
        mapper = XLSXColumnMapper()
        headers = ["No.", "Description", "Unit", "Qty"]
        sample_rows = [
            ["1", "Steel bars", "kg", "100"],
            ["2", "Plywood", "sqm", "50"],
        ]
        result = mapper.map_columns(headers, sample_rows)
        assert result.unit_col == 2

    def test_header_item_no_ignored(self) -> None:
        mapper = XLSXColumnMapper()
        headers = ["Item No.", "Description", "Unit", "Quantity", "Rate"]
        sample_rows = [
            ["1", "Pipe insulation", "RMT", "100", "50"],
        ]
        result = mapper.map_columns(headers, sample_rows)
        assert result.material_col == 1
        assert result.quantity_col == 3
        assert result.unit_col == 2

    def test_header_rate_ignored(self) -> None:
        mapper = XLSXColumnMapper()
        headers = ["No.", "Description", "Unit", "Qty", "Rate", "Amount"]
        sample_rows = [
            ["1", "Duct insulation", "sqm", "500", "200", "100000"],
        ]
        result = mapper.map_columns(headers, sample_rows)
        assert result.material_col == 1
        assert result.quantity_col == 3
        assert result.unit_col == 2

    def test_numeric_content_infers_quantity(self) -> None:
        mapper = XLSXColumnMapper()
        headers = ["A", "B", "C", "D"]
        sample_rows = [
            ["X", "Material description here", "kg", "2500"],
            ["Y", "Another description", "RMT", "1800"],
        ]
        result = mapper.map_columns(headers, sample_rows)
        assert result.quantity_col == 3

    def test_unit_content_infers_unit(self) -> None:
        mapper = XLSXColumnMapper()
        headers = ["Col1", "Col2", "Col3", "Col4"]
        sample_rows = [
            ["A", "Some material", "SQM", "2500"],
            ["B", "Another material", "RMT", "1800"],
        ]
        result = mapper.map_columns(headers, sample_rows)
        assert result.unit_col == 2
