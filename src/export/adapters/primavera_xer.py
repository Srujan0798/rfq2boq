"""Primavera P6 XER export adapter.

Exports BOQ items to Oracle Primavera P6 XER format
for project scheduling integration.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


class PrimaveraXERExporter:
    def __init__(self, project_name: str = "RFQ2BOQ Project"):
        self.project_name = project_name
        self.activities: list[dict] = []
        self.wbs_elements: list[dict] = []
        self._next_id = 1

    def add_wbs(self, name: str, parent_id: int | None = None) -> int:
        wbs_id = self._next_id
        self._next_id += 1
        self.wbs_elements.append(
            {
                "wbs_id": wbs_id,
                "wbs_name": name,
                "parent_id": parent_id,
            }
        )
        return wbs_id

    def add_activity(
        self,
        name: str,
        wbs_id: int,
        duration: int = 1,
        unit: str = "day",
    ) -> int:
        act_id = self._next_id
        self._next_id += 1
        self.activities.append(
            {
                "activity_id": act_id,
                "wbs_id": wbs_id,
                "name": name,
                "duration": duration,
                "unit": unit,
            }
        )
        return act_id

    def add_boq_as_activity(
        self,
        material: str,
        quantity: float,
        unit: str,
        wbs_id: int,
    ) -> int:
        duration_days = max(1, int(quantity / 10))
        return self.add_activity(
            name=f"{material} ({quantity} {unit})",
            wbs_id=wbs_id,
            duration=duration_days,
        )

    def export_xer(self, output_path: Path) -> None:
        lines = [
            "ERMHDR",
            "PRTGLB",
            "ACT",
            "WBS",
        ]

        for wbs in self.wbs_elements:
            wbs_line = f"WBS\t{self._escape_xer(wbs['wbs_name'])}\t{wbs.get('parent_id', '')}"
            lines.append(wbs_line)

        for act in self.activities:
            act_line = (
                f"ACT\t{act['activity_id']}\t"
                f"{self._escape_xer(act['name'])}\t"
                f"{act['wbs_id']}\t"
                f"{act['duration']}\t"
                f"{act['unit']}"
            )
            lines.append(act_line)

        lines.append("ENDHDR")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"Exported {len(self.activities)} activities to XER: {output_path}")

    @staticmethod
    def _escape_xer(s: str) -> str:
        return s.replace("\t", " ").replace("\n", " ")


class PrimaveraXMLExporter:
    def __init__(self, project_name: str = "RFQ2BOQ Project"):
        self.project_name = project_name
        self.activities: list[dict] = []

    def add_boq_item(
        self,
        material: str,
        quantity: float,
        unit: str,
        activity_id: str | None = None,
    ) -> None:
        self.activities.append(
            {
                "id": activity_id or f"ACT_{len(self.activities) + 1}",
                "name": material,
                "quantity": quantity,
                "unit": unit,
            }
        )

    def export_xml(self, output_path: Path) -> None:
        root = ET.Element("PrimaveraData")
        project = ET.SubElement(root, "Project", name=self.project_name)

        activities_elem = ET.SubElement(project, "Activities")
        for act in self.activities:
            act_elem = ET.SubElement(activities_elem, "Activity")
            ET.SubElement(act_elem, "Id").text = act["id"]
            ET.SubElement(act_elem, "Name").text = act["name"]
            ET.SubElement(act_elem, "Quantity").text = str(act["quantity"])
            ET.SubElement(act_elem, "Unit").text = act["unit"]

        ET.indent(root)
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        print(f"Exported {len(self.activities)} activities to XML: {output_path}")


def boq_to_primavera(boq_items: list[dict], output_path: Path, format: str = "xer") -> None:
    exporter: Any = PrimaveraXERExporter() if format == "xer" else PrimaveraXMLExporter()
    root_wbs = exporter.add_wbs(exporter.project_name)

    for item in boq_items:
        exporter.add_boq_as_activity(
            material=item.get("material", "Unknown"),
            quantity=float(item.get("quantity", 1)),
            unit=item.get("unit", "nos"),
            wbs_id=root_wbs,
        )

    if format == "xer":
        exporter.export_xer(output_path)
    else:
        exporter.export_xml(output_path)
