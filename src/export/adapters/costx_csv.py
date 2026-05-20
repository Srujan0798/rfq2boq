"""CostX/Buildsoft CSV exporter.

CostX-compatible CSV with specific column ordering for cost estimation software.
"""

from __future__ import annotations

from pathlib import Path

from src.domain.models import BoqRow, ExtractionResult


class CostXExporter:
    def __init__(self, format: str = "costx"):
        self.format = format

    def export(self, result: ExtractionResult, output_path: str) -> None:
        path = Path(output_path)
        csv_lines = self._generate_csv(result.boq_items)
        path.write_text(csv_lines, encoding="utf-8")

    def _generate_csv(self, boq_items: list[BoqRow]) -> str:
        if self.format == "costx":
            headers = ["Item No", "Description", "Quantity", "Unit", "Rate", "Amount", "Remarks"]
        elif self.format == "buildsoft":
            headers = ["Line", "Code", "Description", "Qty", "Unit", "Price", "Total", "Alt"]
        else:
            headers = ["Item No", "Description", "Material", "Grade", "Quantity", "Unit", "Location", "Action"]

        lines = [",".join(f'"{h}"' for h in headers)]

        for idx, item in enumerate(boq_items, start=1):
            if self.format == "costx":
                row = [
                    str(idx),
                    f'"{item.description_raw or item.material}"',
                    str(float(item.quantity or 0)),
                    f'"{item.unit or "no."}"',
                    "",
                    "",
                    f'"{", ".join(item.standard) if item.standard else ""}"',
                ]
            elif self.format == "buildsoft":
                row = [
                    str(idx),
                    f"BOQ-{idx:04d}",
                    f'"{item.material}"',
                    str(float(item.quantity or 0)),
                    f'"{item.unit or "EA"}"',
                    "",
                    "",
                    "",
                ]
            else:
                row = [
                    str(idx),
                    f'"{item.description_raw or item.material}"',
                    f'"{item.material}"',
                    f'"{item.grade}"',
                    str(float(item.quantity or 0)),
                    f'"{item.unit or "no."}"',
                    f'"{item.location}"',
                    f'"{item.action}"',
                ]
            lines.append(",".join(row))

        return "\n".join(lines) + "\n"


class BuildsoftExporter(CostXExporter):
    def __init__(self):
        super().__init__(format="buildsoft")


def export_costx(result: ExtractionResult, output_path: str) -> None:
    CostXExporter(format="costx").export(result, output_path)


def export_buildsoft(result: ExtractionResult, output_path: str) -> None:
    CostXExporter(format="buildsoft").export(result, output_path)
