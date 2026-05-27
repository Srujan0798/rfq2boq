"""Generate 50 realistic synthetic RFQ PDFs for testing.

Creates diverse construction RFQ PDFs across different domains:
building, road, bridge, electrical, plumbing, water supply, etc.

Usage:
    python scripts/generate_realistic_rfqs.py --output data/real_rfqs/raw --count 50
"""

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.lib.enums import TA_CENTER  # noqa: F401
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle  # noqa: F401
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle  # noqa: F401
except ImportError:
    print("Installing reportlab...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab", "-q"])
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


BLUE = HexColor("#1a3c5e")
LIGHT_BLUE = HexColor("#e8f0f7")
HEADER_BG = HexColor("#2e7d32")
GRAY = HexColor("#f5f5f5")

MATERIALS = {
    "building": [
        ("M20 concrete for foundation", "50", "m³", "IS 456"),
        ("M25 concrete for columns", "75", "m³", "IS 456"),
        ("M30 concrete for slabs", "100", "m³", "IS 456"),
        ("Fe500 TMT bars 10mm dia", "3000", "kg", "IS 1786"),
        ("Fe500 TMT bars 8mm dia", "2500", "kg", "IS 1786"),
        ("Fe415 bars 12mm dia", "2000", "kg", "IS 1786"),
        ("First class brickwork", "150", "m³", "IS 1077"),
        ("20mm thick external plaster", "800", "m²", "IS 1661"),
        ("12mm thick internal plaster", "600", "m²", "IS 1661"),
        ("Granite flooring 18mm", "200", "m²", "IS 13630"),
        ("Ceramic floor tiles 600x600", "400", "m²", "IS 15622"),
        ("Plywood flush door 35mm", "20", "nos", "IS 2191"),
        ("Aluminum windows", "50", "nos", "IS 10450"),
        ("CPVC pipes 25mm dia", "300", "rm", "IS 15778"),
        ("PVC conduit 25mm", "400", "rm", "IS 9537"),
        ("Electric wire 2.5mm FR", "2000", "rm", "IS 694"),
        ("MS structural steel", "1500", "kg", "IS 2062"),
    ],
    "road": [
        ("Granular sub-base (GSB)", "5000", "m³", "IRC 37"),
        ("Wet mix macadam", "4000", "m³", "IRC 37"),
        ("Dense bituminous macadam", "3000", "m³", "IRC 85"),
        ("Bituminous concrete (BC)", "2500", "m³", "IRC 85"),
        ("Prime coat", "8000", "m²", "IRC 85"),
        ("Tack coat", "8000", "m²", "IRC 85"),
        ("Cement stabilized subgrade", "2000", "m³", "IRC 37"),
        ("Granular sub-base type B", "3500", "m³", "MORT&H"),
        ("Aggregate base course", "3000", "m³", "IRC 29"),
        ("DLC (dry lean concrete)", "1500", "m³", "IS 456"),
    ],
    "bridge": [
        ("M35 concrete for piers", "200", "m³", "IS 456"),
        ("M40 concrete for deck", "300", "m³", "IS 456"),
        ("Pre-stressed steel strands", "5000", "kg", "IS 14268"),
        ("Reinforcement steel Fe500", "15000", "kg", "IS 1786"),
        ("Elastomeric bearings", "40", "nos", "IS 13478"),
        ("Expansion joints", "4", "nos", "IRC 34"),
        ("Shotcrete M30", "100", "m³", "IS 9013"),
        ("Rock anchor 25mm dia", "200", "nos", "IS 11382"),
    ],
    "electrical": [
        ("Aluminum cable 3.5 core 400sqmm", "500", "m", "IS 9968"),
        ("Copper cable 4 core 16sqmm", "1000", "m", "IS 3961"),
        ("GI conduit 25mm", "600", "m", "IS 9537"),
        ("Light point wiring", "200", "pts", "IS 694"),
        ("Air breaker 63A TP", "20", "nos", "IS 8828"),
        ("DB box 24 way flush", "10", "nos", "IS 8623"),
        ("Earth electrode plate 600x600", "8", "nos", "IS 3043"),
        ("LED panel light 40W", "100", "nos", "IS 10322"),
        ("Ceiling fan 1200mm", "50", "nos", "IS 374"),
        ("Fire alarm call point", "30", "nos", "IS 2188"),
    ],
    "plumbing": [
        ("CPVC pipes 25mm class 4", "400", "m", "IS 15778"),
        ("UPVC pipes 110mm SWV", "300", "m", "IS 13592"),
        ("GI pipes 25mm heavy", "250", "m", "IS 1239"),
        ("Ball valve 25mm brass", "40", "nos", "IS 1702"),
        ("Water meter 25mm", "20", "nos", "IS 779"),
        ("Sewage pump 2HP", "4", "nos", "IS 805"),
        ("FRP tank 5000L", "2", "nos", "IS 12785"),
        ("Pressure boosting set", "1", "set", "Hydraulic"),
        ("Sanitary ware complete set", "40", "set", "CPWD"),
        ("RCC pipe 600mm NP3", "100", "m", "IS 458"),
    ],
}

LOCATIONS = [
    "ground floor", "first floor", "second floor", "third floor",
    "basement level", "roof level", "plinth level", "+5.0m level",
    "all floors", "stilt level", "parking level", "terrace",
]

CONTRACTORS = [
    "ABC Construction Pvt Ltd", "XYZ Builders", "National Infraprojects",
    "Prime Structures Pvt Ltd", "Metro Buildcon", "Supreme Contractors",
    "Apex Engineering Corp", "Rajat Infrastructure", "Sharma & Associates",
]

DEPARTMENTS = [
    "Central Public Works Department", "CPWD", "State PWD",
    "Municipal Corporation", "Housing Board", "CPWD Lucknow",
    "CPWD Mumbai", "Delhi PWD", "Public Works Department",
]


def generate_rfq_id() -> str:
    return f"RFQ{random.randint(1000, 9999)}"


def create_simple_table(data, col_widths):
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [GRAY, white]),
    ]))
    return table


def generate_rfq_pdf(domain: str, output_path: Path, rfq_id: str) -> dict:
    normal = ParagraphStyle("normal", fontSize=9, leading=12)
    title = ParagraphStyle("title", fontSize=14, textColor=BLUE, alignment=TA_CENTER, spaceAfter=15)
    heading2 = ParagraphStyle("heading2", fontSize=11, textColor=BLUE, spaceAfter=8)
    ParagraphStyle("small", fontSize=8, leading=10, textColor=HexColor("#555555"))

    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)

    story = []
    dept = random.choice(DEPARTMENTS)
    date = datetime.now() - timedelta(days=random.randint(1, 90))
    location = f"{random.choice(['New Delhi', 'Mumbai', 'Chennai', 'Kolkata', 'Bangalore', 'Hyderabad', 'Pune'])}, {random.choice(['Delhi', 'Maharashtra', 'Tamil Nadu', 'Karnataka', 'West Bengal', 'Telangana', 'Gujarat'])}"

    story.append(Paragraph("REQUEST FOR QUOTATION", title))
    story.append(Paragraph(f"<b>RFQ No:</b> {rfq_id}", normal))
    story.append(Paragraph(f"<b>Department:</b> {dept}", normal))
    story.append(Paragraph(f"<b>Date:</b> {date.strftime('%d %B %Y')}", normal))
    story.append(Paragraph(f"<b>Location:</b> {location}", normal))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Scope:</b> {domain.replace('_', ' ').title()} Construction Work", normal))
    story.append(Spacer(1, 15))

    story.append(Paragraph("BILL OF QUANTITIES", heading2))
    story.append(Spacer(1, 5))

    header = ["Item", "Description", "Qty", "Unit", "Specification"]
    items_data = random.sample(MATERIALS.get(domain, MATERIALS["building"]), min(random.randint(8, 15), len(MATERIALS.get(domain, MATERIALS["building"]))))
    boq_data = [[str(i+1), desc, qty, unit, spec] for i, (desc, qty, unit, spec) in enumerate(items_data)]

    table = create_simple_table([header] + boq_data, [20, 100, 30, 25, 55])
    story.append(table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("TERMS AND CONDITIONS", heading2))
    story.append(Paragraph("• Prices should include all taxes, duties, and delivery to site.", normal))
    story.append(Paragraph("• Delivery period: 30-45 days from purchase order.", normal))
    story.append(Paragraph("• Payment: 30% advance, balance on delivery and verification.", normal))
    story.append(Paragraph("• Materials should conform to relevant Indian Standards.", normal))
    story.append(Spacer(1, 15))

    story.append(Paragraph("INSTRUCTIONS TO BIDDERS", heading2))
    story.append(Paragraph("1. Quotes should be submitted in sealed covers by the due date.", normal))
    story.append(Paragraph("2. Late quotations will not be entertained.", normal))
    story.append(Paragraph("3. The department reserves the right to accept or reject any quotation.", normal))
    story.append(Paragraph("4. Quality certificates and test reports to be furnished with supply.", normal))

    doc.build(story)

    sha = hashlib.sha256(output_path.read_bytes()).hexdigest()
    return {
        "filename": output_path.name,
        "source_url": f"generated://{domain}/{rfq_id}",
        "title": f"{domain.replace('_', ' ').title()} RFQ - {rfq_id}",
        "date_downloaded": datetime.now().strftime("%Y-%m-%d"),
        "organization": dept,
        "file_size_bytes": output_path.stat().st_size,
        "sha256": sha,
        "domain": domain,
        "item_count": len(items_data),
    }


def main():
    parser = argparse.ArgumentParser(description="Generate realistic synthetic RFQ PDFs")
    parser.add_argument("--output", type=str, default="data/real_rfqs/raw", help="Output directory")
    parser.add_argument("--count", type=int, default=50, help="Number of PDFs to generate")
    parser.add_argument("--domain", type=str, default=None, help="Specific domain")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    domains = list(MATERIALS.keys())

    manifest = []
    generated = 0

    while generated < args.count:
        domain = args.domain or random.choice(domains)
        rfq_id = generate_rfq_id()
        filename = f"rfq_{domain}_{rfq_id}_{generated+1:03d}.pdf"
        output_path = output_dir / filename

        try:
            meta = generate_rfq_pdf(domain, output_path, rfq_id)
            manifest.append(meta)
            generated += 1
            print(f"[{generated}/{args.count}] {filename} ({meta['file_size_bytes']/1024:.1f} KB, {meta['item_count']} items)")
        except Exception as e:
            print(f"Failed to generate {filename}: {e}")
            continue

    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print("\n=== Complete ===")
    print(f"Generated: {len(manifest)} PDFs")
    print(f"Saved to: {output_dir}")
    print(f"Manifest: {manifest_path}")

    by_domain = {}
    for m in manifest:
        by_domain[m["domain"]] = by_domain.get(m["domain"], 0) + 1
    print("\nBy domain:")
    for d, c in sorted(by_domain.items()):
        print(f"  {d}: {c}")


if __name__ == "__main__":
    main()
