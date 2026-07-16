"""IFC (Industry Foundation Classes) export adapter.

Exports BOQ items to IFC format for BIM (Building Information Modeling)
integration with tools like Revit, ArchiCAD, Navisworks.

IFC schema: http://www.buildingsmart-tech.org/ifc
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass
class IFCProduct:
    name: str
    type: str
    quantity: float
    unit: str
    material: str
    global_id: str


class IFCExporter:
    def __init__(self):
        self.products: list[IFCProduct] = []
        self._next_id = 1

    def add_boq_item(
        self,
        material: str,
        quantity: float,
        unit: str,
        grade: str = "",
        location: str = "",
    ) -> None:
        import uuid

        product = IFCProduct(
            name=material,
            type=self._map_unit_to_ifc_type(unit),
            quantity=quantity,
            unit=unit,
            material=material,
            global_id=str(uuid.uuid4())[:22],
        )
        self.products.append(product)

    def _map_unit_to_ifc_type(self, unit: str) -> str:
        unit_map = {
            "cu.m": "IfcVolumeMeasure",
            "m3": "IfcVolumeMeasure",
            "sq.m": "IfcAreaMeasure",
            "m2": "IfcAreaMeasure",
            "rmt": "IfcLengthMeasure",
            "m": "IfcLengthMeasure",
            "kg": "IfcMassMeasure",
            "tonne": "IfcMassMeasure",
            "nos": "IfcCountMeasure",
            "no.": "IfcCountMeasure",
        }
        return unit_map.get(unit, "IfcQuantityCount")

    def export_ifc(self, output_path: Path) -> None:
        root = ET.Element("ifcXML")
        root.set("xmlns", "http://www.ifc.org/IFC4")
        root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

        header = ET.SubElement(root, "file_header")
        ET.SubElement(header, "name").text = "RFQ2BOQ Exporter"
        ET.SubElement(header, "time_stamp").text = "2024-01-01T00:00:00"

        product_def = ET.SubElement(root, "product_definition")

        for prod in self.products:
            element = ET.SubElement(product_def, "IfcBuildingElement")
            element.set("GlobalId", prod.global_id)
            ET.SubElement(element, "Name").text = prod.name
            ET.SubElement(element, "ObjectType").text = prod.type
            ET.SubElement(element, "Description").text = f"{prod.material} - {prod.quantity} {prod.unit}"

            quantity_set = ET.SubElement(element, "QuantitySet")
            ET.SubElement(quantity_set, "Name").text = "QTO_Data"

            quantity = ET.SubElement(quantity_set, "IfcQuantityCount")
            ET.SubElement(quantity, "Name").text = "Count"
            ET.SubElement(quantity, "CountValue").text = str(int(prod.quantity))

        tree = ET.ElementTree(root)
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

    def export_ifc_simple(self, output_path: Path) -> str:
        lines = [
            "ISO-10303-21;",
            "HEADER;",
            "FILE_DESCRIPTION(('RFQ2BOQ IFC Export'),'2;1');",
            "FILE_NAME('rfq2boq_export.ifc','2024-01-01',('RFQ2BOQ'),('RFQ2BOQ'),'','','');",
            "FILE_SCHEMA(('IFC4'));",
            "ENDSEC;",
            "DATA;",
        ]

        for prod in self.products:
            entity = f"PRODUCT(#{self._next_id},' {prod.name}',$,{prod.type},$,$,*,*,*,$);"
            lines.append(entity)
            self._next_id += 1

        lines.extend(
            [
                "ENDSEC;",
                "END-ISO-10303-21;",
            ]
        )

        content = "\n".join(lines)
        output_path.write_text(content, encoding="utf-8")
        return content


def boq_to_ifc(boq_items: list[dict], output_path: Path) -> None:
    exporter = IFCExporter()
    for item in boq_items:
        exporter.add_boq_item(
            material=item.get("material", ""),
            quantity=float(item.get("quantity", 0)),
            unit=item.get("unit", "nos"),
            grade=item.get("grade", ""),
            location=item.get("location", ""),
        )
    exporter.export_ifc_simple(output_path)
    print(f"Exported {len(boq_items)} items to IFC: {output_path}")
