#!/usr/bin/env python3
"""Generate synthetic RFQ documents for NER training.

Produces 300-500 diverse RFQ documents with:
- Scope of Work (free-text paragraphs)
- Technical Specifications (structured with standards)
- Bill of Materials (table format)
- General Terms (boilerplate)

Each document has text + metadata JSON with ground truth entities.
"""

import json
import random
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.constants import CANONICAL_UNITS

random.seed(42)

MATERIALS_DATA = {
    "concrete": ["M20 concrete", "M25 concrete", "M30 concrete", "M35 concrete", "PCC", "RCC"],
    "steel": ["TMT steel", "MS plate", "structural steel", "GI sheet", "rebar"],
    "brickwork": ["brick masonry", "AAC block", "fly ash brick", "hollow block"],
    "finishes": ["cement plaster", "POP", "tile", "paint", "putty"],
    "piping": ["GI pipe", "PVC pipe", "HDPE pipe", "CI pipe", "SWR pipe"],
    "doors_windows": ["flush door", "aluminum window", "MS door", "glass"],
    "waterproofing": ["brickbat coba", "membrane", "integral waterproofing", "DPC"],
    "electrical": ["cable", "GI conduit", "switch", "light fixture", "DB"],
}

GRADES = {
    "concrete": ["M20", "M25", "M30", "M35", "M40"],
    "steel": ["Fe415", "Fe500", "Fe550"],
    "brickwork": ["Class A", "Class B", "Class C"],
    "finishes": ["Class 1", "Class 2"],
}

DIMENSIONS = [
    "100mm thick", "150mm thick", "200mm thick", "230mm thick", "300mm thick",
    "12mm thick", "16mm thick", "20mm thick", "25mm thick",
    "100 x 100mm", "150 x 150mm", "200 x 200mm",
    "6mm diameter", "8mm diameter", "10mm diameter", "12mm diameter", "16mm diameter",
]

UNITS = ["cum", "sqm", "rmt", "kg", "nos", "ls", "ltr", "set"]

ACTIONS = [
    "Supply and install", "Supply and lay", "Supply and fix",
    "Provide and install", "Provide and lay", "Provide and fix",
    "Erect", "Fabricate and erect", "Lay", "Cast", "Plaster",
    "Apply", "Fix", "Install", "Supply"
]

LOCATIONS = [
    "ground floor", "first floor", "second floor", "roof level",
    "basement", "exterior walls", "interior walls", "balcony",
    "bathroom", "kitchen", "terrace", "compound wall",
]

STANDARDS = {
    "concrete": ["IS 456", "IS 383", "IS 269"],
    "steel": ["IS 2062", "IS 1786", "IS 1139"],
    "brickwork": ["IS 1077", "IS 2185", "IS 12894"],
    "finishes": ["IS 1661", "IS 101", "IS 15622"],
    "piping": ["IS 1239", "IS 4985", "IS 4984"],
    "waterproofing": ["IS 3144", "IS 1322", "IS 1582"],
    "electrical": ["IS 694", "IS 9537", "IS 3043"],
}

PROJECT_NAMES = [
    "Residential Complex at Whitefield", "Commercial Building at MG Road",
    "IT Park Phase 2", "Hospital Building at Hebbal",
    "School Building at Electronic City", "Warehouse at Peenya",
    "Apartment Block at HSR Layout", "Office Building at Manyata Tech Park",
    "Shopping Mall at Outer Ring Road", "Hotel at Airport Road",
]

CONTRACTORS = [
    "ABC Constructions Pvt Ltd", "XYZ Builders & Developers",
    "DEF Infrastructure Ltd", "GHI Projects LLP",
    "JKL Engineering Services", "MNO Realty Corp",
]

SCOPE_TEMPLATES = [
    "The scope of work includes {items} for the {project_name} project located at {location}. The contractor shall supply all materials and execute the works as per the specifications given below.",
    "Supply and installation of {items} for {project_name} as per the drawings and specifications. All works to be completed as per IS codes and good practice.",
    "The work comprises {items} for the proposed {project_name}. Materials to be of best quality conforming to relevant Indian Standards.",
    "Items described in the Bill of Quantities are to be supplied and installed at {location} for the {project_name} project. All work to be carried out as per specifications.",
]

ITEM_TEMPLATES = [
    "{action} {grade} {material} {dimension} as per {standard} for {location}",
    "{action} {material} of {grade} {dimension} at {location}",
    "{action} {material} {quantity} {unit} for {location}",
    "{action} {grade} {material} {quantity} {unit} {dimension}",
    "{material} {grade} {action} at {location}",
    "{action} {material} {quantity} {unit} conforming to {standard}",
]


def generate_scope(project_name: str, category: str) -> str:
    template = random.choice(SCOPE_TEMPLATES)
    category_materials = MATERIALS_DATA.get(category, ["concrete"])
    items = ", ".join(random.sample(category_materials, min(3, len(category_materials))))
    loc = random.choice(LOCATIONS)

    text = template.format(
        items=items,
        project_name=project_name,
        location=loc,
    )
    return text


def generate_boq_table(num_items: int = 8) -> tuple[list[list[str]], list[dict]]:
    header = ["S.No", "Description", "Qty", "Unit", "Rate", "Amount"]
    rows = [header]
    ground_truth = []

    materials_list = list(MATERIALS_DATA.keys())
    random.shuffle(materials_list)

    for i in range(num_items):
        sno = str(i + 1)
        cat = materials_list[i % len(materials_list)]
        mat_list = MATERIALS_DATA[cat]
        material = random.choice(mat_list)
        grade = random.choice(GRADES.get(cat, [""]))
        grade_str = f"{grade} " if grade else ""

        action = random.choice(ACTIONS)
        qty = str(random.randint(10, 500))
        unit = random.choice(UNITS)
        dim = random.choice(DIMENSIONS) if random.random() > 0.3 else ""
        std = random.choice(STANDARDS.get(cat, ["IS 456"]))

        desc = f"{action} {grade_str}{material} {dim}" if dim else f"{action} {grade_str}{material}"

        rows.append([sno, desc, qty, unit, str(random.randint(100, 5000)), str(random.randint(1000, 100000))])

        item_gt = {
            "item_no": i + 1,
            "action": action,
            "material": material,
            "grade": grade,
            "dimension": dim,
            "quantity": int(qty),
            "unit": CANONICAL_UNITS.get(unit, unit),
            "standard": [std],
        }
        ground_truth.append(item_gt)

    return rows, ground_truth


def generate_specifications() -> str:
    specs = []
    specs.append("TECHNICAL SPECIFICATIONS")
    specs.append("")
    specs.append("1. MATERIALS")
    specs.append("   All materials shall be of best quality conforming to relevant Indian Standards.")
    specs.append("   The contractor shall submit samples of all materials for approval before use.")
    specs.append("")
    specs.append("2. WORKMANSHIP")
    specs.append("   All works shall be carried out as per IS codes and good construction practice.")
    specs.append("   The engineer-in-charge shall have the right to reject any defective material or workmanship.")
    specs.append("")
    specs.append("3. TESTING")
    specs.append("   All materials shall be tested as per relevant IS codes.")
    specs.append("   Test certificates from NABL accredited labs shall be submitted.")
    specs.append("")
    return "\n".join(specs)


def generate_general_terms() -> str:
    terms = []
    terms.append("GENERAL TERMS AND CONDITIONS")
    terms.append("")
    terms.append("1. Payment: 80% advance on materials at site, balance within 15 days of completion.")
    terms.append("2. Completion: Within 60 days from date of work order.")
    terms.append("3. Validity: Quotation valid for 90 days from submission date.")
    terms.append("4. Warranty: Defects arising within 12 months from completion shall be rectified free of cost.")
    terms.append("5. Taxes: GST extra as applicable.")
    terms.append("")
    return "\n".join(terms)


def generate_document(doc_id: int) -> dict[str, Any]:
    project_name = random.choice(PROJECT_NAMES)
    category = random.choice(list(MATERIALS_DATA.keys()))

    scope = generate_scope(project_name, category)
    boq_table, boq_ground_truth = generate_boq_table(random.randint(5, 12))
    specs = generate_specifications()
    terms = generate_general_terms()

    full_text = scope + "\n\n" + "BILL OF QUANTITIES\n\n" + table_to_text(boq_table) + "\n\n" + specs + "\n\n" + terms

    text_for_ner = scope + " " + " ".join(row[1] for row in boq_table[1:])

    doc = {
        "id": f"syn_{doc_id:04d}",
        "project_name": project_name,
        "category": category,
        "text": full_text,
        "text_for_ner": text_for_ner,
        "sections": {
            "scope": scope,
            "boq_table": boq_table,
            "specifications": specs,
            "terms": terms,
        },
        "metadata": {
            "boq_ground_truth": boq_ground_truth,
            "num_items": len(boq_ground_truth),
        }
    }

    return doc


def table_to_text(table: list[list[str]]) -> str:
    lines = []
    for row in table:
        lines.append("  ".join(row))
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic RFQ documents")
    parser.add_argument("--output-dir", type=str, default="data/synthetic")
    parser.add_argument("--num-docs", type=int, default=300)
    parser.add_argument("--format", type=str, default="all", choices=["json", "txt", "pdf", "all"])
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.num_docs} synthetic RFQ documents...")
    docs = []

    for i in range(args.num_docs):
        doc = generate_document(i + 1)
        docs.append(doc)

        if (i + 1) % 50 == 0:
            print(f"  Generated {i + 1}/{args.num_docs}")

    for doc in docs:
        if args.format in {"json", "all"}:
            doc_path = output_dir / f"{doc['id']}.json"
            with open(doc_path, "w", encoding="utf-8") as f:
                json.dump(doc, f, indent=2, ensure_ascii=False)

        if args.format in {"txt", "json", "all"}:
            text_path = output_dir / f"{doc['id']}.txt"
            with open(text_path, "w", encoding="utf-8") as f:
                f.write(doc["text"])

        if args.format in {"pdf", "all"}:
            write_text_pdf(doc["text"], output_dir / f"{doc['id']}.pdf")

    print(f"\nGenerated {args.num_docs} documents in {output_dir}")
    if args.format in {"json", "all"}:
        print(f"  {args.num_docs} JSON files with ground truth")
    if args.format in {"txt", "json", "all"}:
        print(f"  {args.num_docs} TXT files with plain text")
    if args.format in {"pdf", "all"}:
        print(f"  {args.num_docs} PDF files")

    return 0


def write_text_pdf(text: str, output_path: Path) -> None:
    """Write a small valid text PDF without third-party PDF dependencies."""
    safe_lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        while len(line) > 95:
            safe_lines.append(line[:95])
            line = line[95:]
        safe_lines.append(line)

    pages = [safe_lines[i:i + 52] for i in range(0, len(safe_lines), 52)] or [[]]
    objects: list[bytes] = []

    def add_object(payload: str) -> int:
        objects.append(payload.encode("latin-1", errors="replace"))
        return len(objects)

    catalog_id = add_object("<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object("")
    page_ids = []
    for page_lines in pages:
        commands = ["BT", "/F1 10 Tf", "50 790 Td", "14 TL"]
        for line in page_lines:
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            commands.append(f"({escaped}) Tj")
            commands.append("T*")
        commands.append("ET")
        stream = "\n".join(commands)
        stream_len = len(stream.encode("latin-1", errors="replace"))
        content_id = add_object(f"<< /Length {stream_len} >>\nstream\n{stream}\nendstream")
        page_id = add_object(
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            "/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> "
            f"/Contents {content_id} 0 R >>"
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("latin-1")

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj_id, payload in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{obj_id} 0 obj\n".encode("ascii"))
        output.extend(payload)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    trailer = f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    output.extend(trailer.encode("ascii"))
    output_path.write_bytes(output)


if __name__ == "__main__":
    import sys
    sys.exit(main())
