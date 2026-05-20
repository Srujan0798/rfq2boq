"""Generate sample RFQ PDF documents for demo purposes."""

from pathlib import Path

from reportlab.lib.colors import HexColor, black
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUTPUT_DIR = Path("data/samples")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()
normal = styles["Normal"]
heading1 = styles["Heading1"]
heading2 = styles["Heading2"]

BLUE = HexColor("#1a3c5e")
LIGHT_BLUE = HexColor("#e8f0f7")


def create_simple_rfq():
    """Simple 2-page RFQ with 5-6 BOQ items."""
    doc = SimpleDocTemplate(
        str(OUTPUT_DIR / "sample_rfq_simple.pdf"),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    story = []

    story.append(Paragraph("REQUEST FOR QUOTATION", ParagraphStyle("Title", parent=normal, fontSize=18, textColor=BLUE, alignment=TA_CENTER, spaceAfter=20)))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Project:</b> Sample Building Construction - Phase 1", normal))
    story.append(Paragraph("<b>Location:</b> New Delhi", normal))
    story.append(Paragraph("<b>Date:</b> January 15, 2026", normal))
    story.append(Spacer(1, 20))

    story.append(Paragraph("1. SCOPE OF WORK", heading2))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "The contractor shall supply and install the following items as per relevant Indian Standards:",
        normal
    ))
    story.append(Spacer(1, 15))

    story.append(Paragraph("2. BILL OF QUANTITIES", heading2))
    story.append(Spacer(1, 10))

    boq_data = [
        ["Item No", "Description", "Quantity", "Unit", "Remarks"],
        ["1", "M20 grade concrete for foundation", "50", "m³", "As per IS 456"],
        ["2", "M25 grade concrete for columns", "30", "m³", "As per IS 456"],
        ["3", "Fe500 TMT steel bars 10mm dia", "2500", "kg", "As per IS 1786"],
        ["4", "Fe500 TMT steel bars 8mm dia", "1500", "kg", "As per IS 1786"],
        ["5", "First class brickwork for walls", "200", "m³", "As per IS 1077"],
        ["6", "External plastering with CPVC", "500", "m²", "20mm thick"],
    ]

    table = Table(boq_data, colWidths=[25, 120, 40, 30, 50])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f5f5f5"), white]),
    ]))
    story.append(table)

    story.append(Spacer(1, 20))
    story.append(Paragraph("3. TECHNICAL SPECIFICATIONS", heading2))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Concrete:</b> All concrete shall be design mix as per IS 456. Minimum compressive strength at 28 days shall be as specified.", normal))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Steel:</b> TMT bars shall conform to IS 1786. All reinforcement shall be tied with 1mm annealed wire.", normal))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Brickwork:</b> First class bricks shall be used. Mortar ratio 1:4 (cement:sand).", normal))

    story.append(PageBreak())

    story.append(Paragraph("4. NOTES", heading2))
    story.append(Spacer(1, 10))
    story.append(Paragraph("• Rates should include all taxes, duties, and delivery to site.", normal))
    story.append(Paragraph("• Measurement will be based on actual quantities executed.", normal))
    story.append(Paragraph("• Payment terms: 30 days after delivery and verification.", normal))
    story.append(Spacer(1, 20))

    story.append(Paragraph("5. DELIVERY SCHEDULE", heading2))
    story.append(Spacer(1, 10))
    story.append(Paragraph("All items to be delivered within 30 days from purchase order.", normal))

    doc.build(story)
    print(f"Created: {OUTPUT_DIR / 'sample_rfq_simple.pdf'}")


def create_medium_rfq():
    """Medium 5-page RFQ with 10-15 items."""
    doc = SimpleDocTemplate(
        str(OUTPUT_DIR / "sample_rfq_medium.pdf"),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    story = []

    story.append(Paragraph("REQUEST FOR QUOTATION", ParagraphStyle("Title", parent=normal, fontSize=18, textColor=BLUE, alignment=TA_CENTER, spaceAfter=20)))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Project:</b> Commercial Complex - Interior Works", normal))
    story.append(Paragraph("<b>Location:</b> Mumbai, Maharashtra", normal))
    story.append(Paragraph("<b>Date:</b> February 10, 2026", normal))
    story.append(Spacer(1, 20))

    story.append(Paragraph("1. SCOPE OF SUPPLY", heading2))
    story.append(Spacer(1, 5))
    story.append(Paragraph("Complete supply and delivery of materials for interior construction works as per specifications below.", normal))
    story.append(Spacer(1, 15))

    story.append(Paragraph("2. ITEMS REQUIRED", heading2))
    story.append(Spacer(1, 10))

    boq_data = [
        ["Item", "Description", "Qty", "Unit", "Spec"],
        ["1", "Ceramic floor tiles 600x600mm", "800", "m²", "IS 13630"],
        ["2", "Granite flooring 18mm thick", "150", "m²", "Black Galaxy"],
        ["3", "Aluminum false ceiling", "400", "m²", "Powder coated"],
        ["4", "Gypsum board ceiling 12mm", "350", "m²", "Moisture resistant"],
        ["5", "Emulsion paint 2 coats", "1200", "m²", "Asian/Berger"],
        ["6", "Enamel paint for woodwork", "200", "m²", "IS 133"],
        ["7", "Electrical conduit 25mm PVC", "500", "rm", "IS 9537"],
        ["8", "CPVC pipes 25mm dia", "300", "rm", "Ashirvad/Supreme"],
        ["9", "PVC door frames 750x2000mm", "15", "nos", "WPC frame"],
        ["10", "Glass panes 5mm clear", "100", "m²", "Float glass"],
        ["11", "Stainless steel railing", "50", "rm", "SS 304 grade"],
        ["12", "Fire exit signage", "20", "nos", "As per NBC"],
        ["13", "M25 concrete for slabs", "100", "m³", "IS 456"],
        ["14", "Fe500 steel reinforcement", "5000", "kg", "IS 1786"],
        ["15", "Brickwork for partitions", "80", "m³", "IS 1077"],
    ]

    table = Table(boq_data, colWidths=[20, 90, 30, 30, 50])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#f5f5f5"), white]),
    ]))
    story.append(table)

    story.append(PageBreak())

    story.append(Paragraph("3. SPECIFICATIONS", heading2))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Floor Tiles:</b> First quality ceramic tiles conforming to IS 13630. Size 600x600mm. Water absorption less than 0.5%.", normal))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Granite:</b> Black Galaxy granite, minimum 18mm thick, polished on all sides. Tolerance ±1mm on dimensions.", normal))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>False Ceiling:</b> Aluminum T-bar grid with gypsum board tiles 600x600mm. Main runners at 1200mm c/c.", normal))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Painting:</b> All surfaces to be thoroughly cleaned and primed. 2 coats of premium emulsion paint.", normal))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Electrical:</b> All conduit and wiring as per IS standards. PVC conduit 25mm dia minimum.", normal))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Plumbing:</b> CPVC pipes and fittings for hot/cold water. Working pressure 10 bar.", normal))

    story.append(Spacer(1, 20))
    story.append(Paragraph("4. TERMS AND CONDITIONS", heading2))
    story.append(Spacer(1, 10))
    story.append(Paragraph("• Prices should be exclusive of GST.", normal))
    story.append(Paragraph("• Delivery to site within 21 days.", normal))
    story.append(Paragraph("• Inspection by Quality Engineer before acceptance.", normal))
    story.append(Paragraph("• Payment: 40% advance, 60% on delivery.", normal))

    story.append(PageBreak())

    story.append(Paragraph("5. QUALITY REQUIREMENTS", heading2))
    story.append(Spacer(1, 10))
    story.append(Paragraph("All materials shall be from approved manufacturers with BIS certification. Test certificates to be furnished.", normal))
    story.append(Spacer(1, 15))

    story.append(Paragraph("6. MEASUREMENT AND PAYMENT", heading2))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Measurement based on net quantities delivered and accepted. No allowance for wastage.", normal))

    doc.build(story)
    print(f"Created: {OUTPUT_DIR / 'sample_rfq_medium.pdf'}")


def create_complex_rfq():
    """Complex 10-page RFQ with 25+ items."""
    doc = SimpleDocTemplate(
        str(OUTPUT_DIR / "sample_rfq_complex.pdf"),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    story = []

    story.append(Paragraph("TENDER DOCUMENT", ParagraphStyle("Title", parent=normal, fontSize=20, textColor=BLUE, alignment=TA_CENTER, spaceAfter=20)))
    story.append(Paragraph("<b>Project:</b> Multi-Storied Residential Building - Phase 2", ParagraphStyle("Subtitle", parent=normal, fontSize=12, alignment=TA_CENTER, spaceAfter=20)))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Location:</b> Bangalore, Karnataka", normal))
    story.append(Paragraph("<b>Date:</b> March 1, 2026", normal))
    story.append(Paragraph("<b>Tender No:</b> TND/2026/001", normal))
    story.append(Spacer(1, 20))

    story.append(Paragraph("SECTION 1: SCOPE OF WORK", heading1))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "The scope of work includes design, supply, and delivery of all materials required for the structural and finishing works "
        "of the basement and ground floor of the proposed building as per drawings and specifications attached.",
        normal
    ))
    story.append(Spacer(1, 20))

    story.append(Paragraph("SECTION 2: STRUCTURAL WORKS", heading1))
    story.append(Spacer(1, 10))

    boq_structural = [
        ["Item", "Description", "Qty", "Unit", "Specification"],
        ["1", "M30 concrete for foundation", "120", "m³", "IS 456, OPC 53 grade"],
        ["2", "M35 concrete for columns", "80", "m³", "IS 456, OPC 53 grade"],
        ["3", "M25 concrete for slabs", "200", "m³", "IS 456, OPC 53 grade"],
        ["4", "M25 concrete for beams", "100", "m³", "IS 456, OPC 53 grade"],
        ["5", "Fe550 TMT bars 20mm dia", "8000", "kg", "IS 1786, Fe550 grade"],
        ["6", "Fe550 TMT bars 16mm dia", "6000", "kg", "IS 1786, Fe550 grade"],
        ["7", "Fe550 TMT bars 12mm dia", "4000", "kg", "IS 1786, Fe550 grade"],
        ["8", "Fe550 TMT bars 8mm dia", "3000", "kg", "IS 1786, Fe550 grade"],
        ["9", "Structural steel plates 10mm", "1500", "kg", "IS 2062, E250 grade"],
        ["10", "First class brickwork 230mm", "300", "m³", "IS 1077"],
    ]

    table1 = Table(boq_structural, colWidths=[20, 100, 30, 30, 50])
    table1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, black),
    ]))
    story.append(table1)

    story.append(PageBreak())

    story.append(Paragraph("SECTION 3: FINISHING WORKS", heading1))
    story.append(Spacer(1, 10))

    boq_finishing = [
        ["Item", "Description", "Qty", "Unit", "Specification"],
        ["11", "External plastering 20mm", "1500", "m²", "Cement mortar 1:4"],
        ["12", "Internal plastering 15mm", "2500", "m²", "Cement mortar 1:4"],
        ["13", "Wall putty 2 coats", "2500", "m²", "Birla putty"],
        ["14", "Premium emulsion paint", "3000", "m²", "Asian/Berger/ICI"],
        ["15", "Texture paint accent wall", "200", "m²", "Asian/Berger"],
        ["16", "Ceramic wall tiles 300x450mm", "800", "m²", "IS 13630"],
        ["17", "Granite counter top", "50", "m²", "20mm Black Galaxy"],
    ]

    table2 = Table(boq_finishing, colWidths=[20, 100, 30, 30, 50])
    table2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, black),
    ]))
    story.append(table2)

    story.append(PageBreak())

    story.append(Paragraph("SECTION 4: FLOORING AND WOODWORKS", heading1))
    story.append(Spacer(1, 10))

    boq_flooring = [
        ["Item", "Description", "Qty", "Unit", "Specification"],
        ["18", "Vitrified tiles 800x800mm", "1200", "m²", "IS 15622"],
        ["19", "Granite flooring 18mm", "300", "m²", "Kashmir White"],
        ["20", "Wooden flooring laminate", "150", "m²", "8mm AC3 rated"],
        ["21", "Plywood flush door 35mm", "25", "nos", "IS 2191 Plywood"],
        ["22", "WPC door frame", "25", "nos", "75mm section"],
        ["23", "Aluminum windows", "50", "nos", "Anodized 1.2mm"],
        ["24", "Glass panes 6mm", "120", "m²", "Tinted float glass"],
    ]

    table3 = Table(boq_flooring, colWidths=[20, 100, 30, 30, 50])
    table3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, black),
    ]))
    story.append(table3)

    story.append(PageBreak())

    story.append(Paragraph("SECTION 5: MEP WORKS", heading1))
    story.append(Spacer(1, 10))

    boq_mep = [
        ["Item", "Description", "Qty", "Unit", "Specification"],
        ["25", "Electrical conduit 25mm PVC", "1000", "rm", "IS 9537"],
        ["26", "Electrical wires 2.5mm FR", "3000", "rm", "IS 694"],
        ["27", "DB box 24 way", "5", "nos", "Metal enclosure"],
        ["28", "CPVC pipes 32mm dia", "500", "rm", "IS 15778"],
        ["29", "UPVC pipes 110mm SWV", "200", "rm", "IS 13592"],
        ["30", "Sanitary ware set complete", "20", "set", "Cera/Jaguar/Parryware"],
    ]

    table4 = Table(boq_mep, colWidths=[20, 100, 30, 30, 50])
    table4.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, black),
    ]))
    story.append(table4)

    story.append(PageBreak())

    story.append(Paragraph("SECTION 6: SPECIAL ITEMS", heading1))
    story.append(Spacer(1, 10))

    boq_special = [
        ["Item", "Description", "Qty", "Unit", "Specification"],
        ["31", "Waterproofing for basement", "800", "m²", "K11 BASF/Bituguard"],
        ["32", "Fire alarm system", "1", "set", "Addressable type"],
        ["33", "CCTV surveillance", "1", "set", "16 channel DVR"],
        ["34", "EPS insulation 50mm", "400", "m²", "Density 32 kg/m³"],
        ["35", "False ceiling Gyproc", "600", "m²", "12.5mm gypsum"],
    ]

    table5 = Table(boq_special, colWidths=[20, 100, 30, 30, 50])
    table5.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT_BLUE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, black),
    ]))
    story.append(table5)

    story.append(PageBreak())

    story.append(Paragraph("SECTION 7: TECHNICAL SPECIFICATIONS", heading1))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Concrete:</b> All concrete shall be design mix M30/M35 as per IS 456. Minimum cement content 320 kg/m³.", normal))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Steel:</b> TMT bars Fe550 grade conforming to IS 1786. Yield strength 550 MPa.", normal))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Brickwork:</b> First class bricks IS 1077. Mortar 1:4. All reinforcement as per structural drawings.", normal))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Plastering:</b> Curing for 7 days. Thickness as specified. Key coat on RCC surface.", normal))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Flooring:</b> All tiles from BIS approved manufacturers. Pattern as per drawings.", normal))

    story.append(Spacer(1, 20))
    story.append(Paragraph("SECTION 8: TERMS AND CONDITIONS", heading1))
    story.append(Spacer(1, 10))
    story.append(Paragraph("• Rates are ex-works. GST extra.", normal))
    story.append(Paragraph("• Delivery: 45 days from PO.", normal))
    story.append(Paragraph("• Payment: 30% advance, 70% on delivery.", normal))
    story.append(Paragraph("• LD: 0.5% per week delay, max 5%.", normal))
    story.append(Paragraph("• Warranty: 12 months from completion.", normal))

    doc.build(story)
    print(f"Created: {OUTPUT_DIR / 'sample_rfq_complex.pdf'}")


if __name__ == "__main__":
    from reportlab.lib.colors import white
    create_simple_rfq()
    create_medium_rfq()
    create_complex_rfq()
    print("\nAll sample PDFs generated successfully!")
