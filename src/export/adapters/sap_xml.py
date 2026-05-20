"""SAP XML export adapter.

Exports BOQ items to SAP-compatible XML format
for integration with SAP MM (Materials Management) and SAP PS (Project Systems).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


class SAPXMLExporter:
    def __init__(
        self,
        company_code: str = "1000",
        plant: str = "P001",
        purchase_org: str = "PO01",
    ):
        self.company_code = company_code
        self.plant = plant
        self.purchase_org = purchase_org
        self.items: list[dict] = []

    def add_boq_item(
        self,
        material: str,
        quantity: float,
        unit: str,
        description: str = "",
        material_group: str = "MG01",
    ) -> None:
        item_num = len(self.items) + 1
        self.items.append({
            "item_num": str(item_num * 10).zfill(5),
            "material": self._map_material_to_sap(material),
            "quantity": quantity,
            "unit": self._map_unit_to_sap(unit),
            "description": description or material,
            "material_group": material_group,
            "plant": self.plant,
            "purchase_org": self.purchase_org,
            "company_code": self.company_code,
        })

    @staticmethod
    def _map_material_to_sap(material: str) -> str:
        material_map = {
            "cement": "CEM-001",
            "steel": "STL-001",
            "sand": "SND-001",
            "aggregate": "AGG-001",
            "brick": "BRK-001",
            "concrete": "CNT-001",
            "timber": "TMB-001",
            "glass": "GLS-001",
        }
        material_lower = material.lower()
        return material_map.get(material_lower, f"MAT-{material[:8].upper()}")

    @staticmethod
    def _map_unit_to_sap(unit: str) -> str:
        unit_map = {
            "nos": "PC",
            "cu.m": "MTQ",
            "m3": "MTQ",
            "sq.m": "MTK",
            "m2": "MTK",
            "rmt": "MTR",
            "m": "MTR",
            "kg": "KGM",
            "tonne": "TNE",
        }
        return unit_map.get(unit.lower(), "PC")

    def export_xml(self, output_path: Path) -> None:
        root = ET.Element("SAP_BOQ_EXPORT")
        root.set("export_date", datetime.now().isoformat())
        root.set("company_code", self.company_code)
        root.set("plant", self.plant)

        header = ET.SubElement(root, "HEADER")
        ET.SubElement(header, "DOC_TYPE").text = "PR"
        ET.SubElement(header, "PURCH_ORG").text = self.purchase_org
        ET.SubElement(header, "PUR_GROUP").text = "PG01"
        ET.SubElement(header, "CO_CODE").text = self.company_code

        items_elem = ET.SubElement(root, "ITEMS")
        for item in self.items:
            item_elem = ET.SubElement(items_elem, "ITEM")
            ET.SubElement(item_elem, "PO_ITEM").text = item["item_num"]
            ET.SubElement(item_elem, "MATERIAL").text = item["material"]
            ET.SubElement(item_elem, "SHORT_TEXT").text = item["description"]
            ET.SubElement(item_elem, "PLANT").text = item["plant"]
            ET.SubElement(item_elem, "STORE_LOC").text = "SL01"
            ET.SubElement(item_elem, "QUANTITY").text = str(item["quantity"])
            ET.SubElement(item_elem, "UNIT").text = item["unit"]
            ET.SubElement(item_elem, "MAT_GRP").text = item["material_group"]

        ET.indent(root)
        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)
        print(f"Exported {len(self.items)} items to SAP XML: {output_path}")


def boq_to_sap_xml(boq_items: list[dict], output_path: Path, **kwargs) -> None:
    exporter = SAPXMLExporter(**kwargs)
    for item in boq_items:
        exporter.add_boq_item(
            material=item.get("material", "Unknown"),
            quantity=float(item.get("quantity", 1)),
            unit=item.get("unit", "nos"),
            description=item.get("description_raw", ""),
        )
    exporter.export_xml(output_path)
