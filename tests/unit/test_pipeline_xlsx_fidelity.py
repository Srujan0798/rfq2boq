"""Fidelity tests for XLSXRowPipeline (E2: flag-never-drop).

Verifies that every source row is accounted for in the fidelity report:
no silent data loss. Low-confidence and rate-only rows are flagged, not
dropped.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from src.pipeline_xlsx import XLSXRowPipeline


def make_xlsx(rows: list[list[Any]], sheet_name: str = "Sheet1") -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    for row in rows:
        ws.append(row)
    path = Path(tempfile.gettempdir()) / f"test_fidelity_{sheet_name}.xlsx"
    wb.save(path)
    return path


class TestFidelityReport:
    def test_empty_xlsx_returns_empty_fidelity(self) -> None:
        rows = [["A", "B"]]
        path = make_xlsx(rows)
        pipeline = XLSXRowPipeline()
        result = pipeline.run(path)
        assert len(result) == 0
        report = pipeline.fidelity_report
        assert report["source_rows"] == 0

    def test_all_rows_accounted_for(self) -> None:
        """Every source row must appear in exactly one fidelity category."""
        rows = [
            ["SR. NO.", "DESCRIPTION", "UNIT", "QTY"],
            ["1", "20 mm thick insulation", "Sqm.", 500],
            ["2", "25 mm thick insulation", "Sqm.", 750],
            [None, None, None, None],  # empty
            ["", "Sub-Total", None, None],  # total
        ]
        path = make_xlsx(rows)
        pipeline = XLSXRowPipeline()
        result = pipeline.run(path)
        report = pipeline.fidelity_report

        assert report["source_rows"] == 4  # 4 data rows after header
        accounted = (
            report["empty_rows"]
            + report["total_rows"]
            + report["header_rows"]
            + report["spec_rows"]
            + report["section_header_rows"]
            + report["extracted_rows"]
            + report.get("wrapped_continuation_rows", 0)
            + report.get("non_boq_rows", 0)
        )
        assert accounted == report["source_rows"], (
            f"source_rows={report['source_rows']} but accounted={accounted}; breakdown: {report}"
        )
        assert len(result) == 2

    def test_zero_qty_rows_are_flagged_not_dropped(self) -> None:
        """Rows with zero quantity must be in the output and counted."""
        rows = [
            ["DESCRIPTION", "UNIT", "QTY"],
            ["20 mm thick insulation", "Sqm.", 500],
            ["A rate-only item", "Sqm.", 0],
        ]
        path = make_xlsx(rows)
        pipeline = XLSXRowPipeline()
        result = pipeline.run(path)
        report = pipeline.fidelity_report

        assert report["extracted_rows"] == 2
        # The zero-qty row should still be in the output (not silently dropped)
        zero_qty_rows = [r for r in result if r.quantity == 0]
        assert len(zero_qty_rows) == 1

    def test_rate_only_marker_sets_flag(self) -> None:
        """R/O marker in quantity column must set rate_only=True."""
        rows = [
            ["SR. NO.", "DESCRIPTION", "UNIT", "QUANTITY"],
            ["1", "Real item", "Sqm.", 500],
            ["2", "Rate-only item", "Sqm.", "R0"],
        ]
        path = make_xlsx(rows)
        pipeline = XLSXRowPipeline()
        result = pipeline.run(path)

        rate_only_rows = [r for r in result if r.rate_only]
        assert len(rate_only_rows) == 1
        assert rate_only_rows[0].material == "Rate-only item"
        assert rate_only_rows[0].quantity == 0

    def test_fidelity_report_is_independent_of_pipeline_state(self) -> None:
        """Running pipeline twice resets fidelity report."""
        rows = [
            ["DESCRIPTION", "UNIT", "QTY"],
            ["Cement", "bags", 100],
        ]
        path = make_xlsx(rows)
        pipeline = XLSXRowPipeline()
        pipeline.run(path)
        report1 = pipeline.fidelity_report.copy()

        pipeline.run(path)
        report2 = pipeline.fidelity_report.copy()

        assert report1 == report2


class TestFidelityOnSWAFiles:
    """Integration test: verify fidelity on existing SWA XLSX files."""

    def test_03_zydus_matoda_fidelity(self) -> None:
        xlsx = Path("data/real_rfqs/swa_enquiries/03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx")
        if not xlsx.exists():
            return
        pipeline = XLSXRowPipeline()
        result = pipeline.run(xlsx)
        report = pipeline.fidelity_report

        assert report["source_rows"] > 0
        accounted = (
            report["empty_rows"]
            + report["total_rows"]
            + report["header_rows"]
            + report["spec_rows"]
            + report["section_header_rows"]
            + report["extracted_rows"]
            + report.get("wrapped_continuation_rows", 0)
            + report.get("non_boq_rows", 0)
        )
        assert accounted == report["source_rows"], (
            f"03 Zydus: source_rows={report['source_rows']} but accounted={accounted}; breakdown: {report}"
        )
        assert len(result) == 33, f"expected 33 rows, got {len(result)}"

    def test_08_sael_fidelity(self) -> None:
        xlsx_candidates = list(Path("data/real_rfqs/swa_enquiries/08_sael").glob("*.xlsx"))
        if not xlsx_candidates:
            return
        pipeline = XLSXRowPipeline()
        for xlsx in xlsx_candidates:
            pipeline.run(xlsx)
            report = pipeline.fidelity_report
            assert report["source_rows"] > 0
            accounted = (
                report["empty_rows"]
                + report["total_rows"]
                + report["header_rows"]
                + report["spec_rows"]
                + report["section_header_rows"]
                + report["extracted_rows"]
                + report.get("wrapped_continuation_rows", 0)
                + report.get("non_boq_rows", 0)
            )
            assert accounted == report["source_rows"], (
                f"08 Sael {xlsx.name}: source_rows={report['source_rows']} but accounted={accounted}; breakdown: {report}"
            )
