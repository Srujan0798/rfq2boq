"""Generic Excel BOQ templates for CPWD and DSR formats.

CPWD format: Central Public Works Department standard
DSR format: Delhi Schedule of Rates format
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from src.domain.models import ExtractionResult


class CPWDTemplate:
    @staticmethod
    def generate(result: ExtractionResult, output_path: str) -> None:
        wb = Workbook()
        ws = wb.active
        ws.title = "BOQ-CPWD"

        header_fill = PatternFill("solid", fgColor="1F4E78")
        header_font = Font(bold=True, color="FFFFFF", size=11)

        headers = [
            "SI No",
            "Item Code",
            "Description of Item",
            "Material",
            "Grade",
            "Quantity",
            "Unit",
            "Rate (Rs)",
            "Amount (Rs)",
            "Location",
        ]

        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for row_idx, item in enumerate(result.boq_items, start=2):
            ws.cell(row=row_idx, column=1, value=row_idx - 1)
            ws.cell(row=row_idx, column=2, value=f"BOQ-{row_idx - 1:04d}")
            ws.cell(row=row_idx, column=3, value=item.description_raw or item.material)
            ws.cell(row=row_idx, column=4, value=item.material)
            ws.cell(row=row_idx, column=5, value=item.grade or "")
            ws.cell(row=row_idx, column=6, value=float(item.quantity or 0))
            ws.cell(row=row_idx, column=7, value=item.unit or "no.")
            ws.cell(row=row_idx, column=8, value="")
            ws.cell(row=row_idx, column=9, value="")
            ws.cell(row=row_idx, column=10, value=item.location or "")

        for col_idx in range(1, len(headers) + 1):
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = 18

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(path)


class DSRTemplate:
    @staticmethod
    def generate(result: ExtractionResult, output_path: str) -> None:
        wb = Workbook()
        ws = wb.active
        ws.title = "BOQ-DSR"

        header_fill = PatternFill("solid", fgColor="2E7D32")
        header_font = Font(bold=True, color="FFFFFF", size=11)

        headers = [
            "Item No",
            "DSR Code",
            "Description",
            "Material",
            "Specification",
            "Quantity",
            "Unit",
            "Base Rate",
            "Total",
            "Sub-Head",
        ]

        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for row_idx, item in enumerate(result.boq_items, start=2):
            ws.cell(row=row_idx, column=1, value=row_idx - 1)
            ws.cell(row=row_idx, column=2, value="")
            ws.cell(row=row_idx, column=3, value=item.description_raw or item.material)
            ws.cell(row=row_idx, column=4, value=item.material)
            ws.cell(row=row_idx, column=5, value=item.grade or "")
            ws.cell(row=row_idx, column=6, value=float(item.quantity or 0))
            ws.cell(row=row_idx, column=7, value=item.unit or "no.")
            ws.cell(row=row_idx, column=8, value="")
            ws.cell(row=row_idx, column=9, value="")
            ws.cell(row=row_idx, column=10, value="")

        for col_idx in range(1, len(headers) + 1):
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = 18

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(path)


class GenericTemplate:
    @staticmethod
    def generate(result: ExtractionResult, output_path: str, template_name: str = "standard") -> None:
        wb = Workbook()
        ws = wb.active
        ws.title = f"BOQ-{template_name.upper()}"

        header_fill = PatternFill("solid", fgColor="1565C0")
        header_font = Font(bold=True, color="FFFFFF", size=11)

        headers = [
            "Item No",
            "Description",
            "Material",
            "Grade",
            "Dimensions",
            "Location",
            "Quantity",
            "Unit",
            "Action",
            "Confidence",
        ]

        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for row_idx, item in enumerate(result.boq_items, start=2):
            ws.cell(row=row_idx, column=1, value=row_idx - 1)
            ws.cell(row=row_idx, column=2, value=item.description_raw or item.material)
            ws.cell(row=row_idx, column=3, value=item.material)
            ws.cell(row=row_idx, column=4, value=item.grade or "")
            ws.cell(row=row_idx, column=5, value=", ".join(item.dimensions) if item.dimensions else "")
            ws.cell(row=row_idx, column=6, value=item.location or "")
            ws.cell(row=row_idx, column=7, value=float(item.quantity or 0))
            ws.cell(row=row_idx, column=8, value=item.unit or "no.")
            ws.cell(row=row_idx, column=9, value=item.action or "supply")
            ws.cell(row=row_idx, column=10, value=round(item.confidence * 100, 1) if item.confidence else 0)

        for col_idx in range(1, len(headers) + 1):
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = 16

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(path)


def export_cpwd(result: ExtractionResult, output_path: str) -> None:
    CPWDTemplate.generate(result, output_path)


def export_dsr(result: ExtractionResult, output_path: str) -> None:
    DSRTemplate.generate(result, output_path)


def export_generic(result: ExtractionResult, output_path: str, template: str = "standard") -> None:
    GenericTemplate.generate(result, output_path, template)
