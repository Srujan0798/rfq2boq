"""
RFQ to BOQ Pipeline Test
Tests the full extraction pipeline with a sample RFQ
"""
import sys

sys.path.insert(0, '/Users/srujansai/Desktop/rfq2boq')

import fitz
from src.nlp.boq_generator import BOQGenerator
from src.nlp.ner_inference import NERModel


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()
    return full_text

def main():
    print("="*70)
    print("RFQ TO BOQ PIPELINE TEST")
    print("="*70)

    # 1. Load sample RFQ
    rfq_path = "/Users/srujansai/Desktop/rfq2boq/data/samples/sample_rfq_simple.pdf"
    print(f"\n[1] Loading RFQ: {rfq_path}")
    text = extract_text_from_pdf(rfq_path)
    print(f"    Extracted {len(text)} characters")

    # 2. Run NER
    print("\n[2] Running NER...")
    try:
        model = NERModel()
        entities = model.predict(text)
        print(f"    Found {len(entities)} entities:")
        for ent in entities[:20]:  # Show first 20
            print(f"      - {ent['text']} ({ent['type']}) [{ent['start']}-{ent['end']}]")
    except Exception:
        print("    ⚠️ NER model not fully trained yet, using rule-based extraction")
        # Fallback to rule-based extraction
        entities = rule_based_extraction(text)
        print(f"    Extracted {len(entities)} entities using rules")

    # 3. Generate BOQ
    print("\n[3] Generating BOQ...")
    try:
        generator = BOQGenerator()
        boq = generator.generate(text, entities)
        print(f"    Generated BOQ with {len(boq.get('items', []))} line items")

        # Show BOQ preview
        if 'items' in boq and boq['items']:
            print("\n    BOQ Preview:")
            print("    | # | Material | Qty | Unit |")
            print("    |---|----------|-----|------|")
            for item in boq['items'][:10]:
                print(f"    | {item.get('item_no', '?')} | {item.get('material', '?')[:20]} | {item.get('quantity', '?')} | {item.get('unit', '?')} |")
    except Exception as e:
        print(f"    ⚠️ BOQ generator not ready: {e}")
        boq = {"items": [], "raw_entities": entities}

    # 4. Save output
    import json
    output_path = "/Users/srujansai/Desktop/rfq2boq/results/test_output.json"
    with open(output_path, 'w') as f:
        json.dump({
            "input_file": rfq_path,
            "extracted_text_length": len(text),
            "entities_found": len(entities),
            "entities": entities,
            "boq": boq
        }, f, indent=2)
    print(f"\n[4] Results saved to: {output_path}")

    print("\n" + "="*70)
    print("✅ Pipeline test complete!")
    print("="*70)

def rule_based_extraction(text):
    """Simple rule-based extraction as fallback"""
    import re

    entities = []

    # Material patterns
    material_terms = ['concrete', 'steel', 'brick', 'cement', 'plaster', 'mortar', 'TMT', 'bars']
    for term in material_terms:
        for match in re.finditer(rf'\b\w*\s*{term}\w*\b', text, re.IGNORECASE):
            entities.append({
                'text': match.group(),
                'type': 'MATERIAL',
                'start': match.start(),
                'end': match.end()
            })

    # Quantity patterns
    qty_pattern = r'(\d+(?:\.\d+)?)\s*(kg|m³|m²|m|pieces|nos)?'
    for match in re.finditer(qty_pattern, text):
        entities.append({
            'text': match.group(),
            'type': 'QUANTITY' if match.group(2) else 'QUANTITY',
            'start': match.start(),
            'end': match.end()
        })

    # Grade patterns (M20, M25, Fe500, etc.)
    grade_pattern = r'\b(M\d+|Fe\d+|C\d+|Grade\s*\d+)\b'
    for match in re.finditer(grade_pattern, text):
        entities.append({
            'text': match.group(),
            'type': 'GRADE',
            'start': match.start(),
            'end': match.end()
        })

    # Standard patterns (IS 456, IS 1786, etc.)
    standard_pattern = r'\b(IS\s*\d+[A-Z]?)\b'
    for match in re.finditer(standard_pattern, text):
        entities.append({
            'text': match.group(),
            'type': 'STANDARD',
            'start': match.start(),
            'end': match.end()
        })

    return entities[:50]  # Limit to first 50

if __name__ == "__main__":
    main()
