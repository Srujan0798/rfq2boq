"""NER Inference for RFQ2BOQ using trained BERT model."""

import re
from pathlib import Path

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

LABEL_LIST = [
    "O",
    "S-MATERIAL",
    "B-MATERIAL",
    "I-MATERIAL",
    "E-MATERIAL",
    "S-QUANTITY",
    "B-QUANTITY",
    "I-QUANTITY",
    "E-QUANTITY",
    "S-UNIT",
    "B-UNIT",
    "I-UNIT",
    "E-UNIT",
    "S-LOCATION",
    "B-LOCATION",
    "I-LOCATION",
    "E-LOCATION",
    "S-DIMENSION",
    "B-DIMENSION",
    "I-DIMENSION",
    "E-DIMENSION",
    "S-STANDARD",
    "B-STANDARD",
    "I-STANDARD",
    "E-STANDARD",
    "S-ACTION",
    "B-ACTION",
    "I-ACTION",
    "E-ACTION",
    "S-GRADE",
    "B-GRADE",
    "I-GRADE",
    "E-GRADE",
]
ID2LABEL = {i: label for i, label in enumerate(LABEL_LIST)}

MODEL_DIR = Path("/Users/srujansai/Desktop/rfq2boq/models/ner_model/final_model")
MODEL_PATH = "/Users/srujansai/Desktop/rfq2boq/models/ner-bert-bilstm-crf-v1/model.pt"

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

_tokenizer = None
_model = None


def load_model():
    """Load NER model and tokenizer."""
    global _tokenizer, _model

    if _model is None:
        try:
            # Try to load from final_model
            _tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
            _model = AutoModelForTokenClassification.from_pretrained(str(MODEL_DIR), local_files_only=True)
            _model.to(device)
            _model.eval()
            print("✅ Loaded BERT NER model from final_model")
        except Exception as e:
            print(f"⚠️ Could not load from final_model: {e}")
            try:
                # Fallback to base BERT for tokenizer
                _tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
                _model = None
                print("⚠️ Using rule-based extraction fallback")
            except Exception as e2:
                print(f"❌ Could not load tokenizer: {e2}")
                _model = None


def extract_entities_rule_based(text):
    """Rule-based entity extraction as fallback."""
    entities = []

    # MATERIAL
    materials = [
        "cement",
        "concrete",
        "steel",
        "brick",
        "plaster",
        "TMT",
        "bars",
        "wire",
        "pipe",
        "conduit",
        "gravel",
        "sand",
        "aggregate",
        "tile",
        "wood",
        "plywood",
        "aluminum",
        "glass",
        "ceramic",
        "granite",
    ]
    for mat in materials:
        for m in re.finditer(rf"\b\w*{mat}\w*\b", text, re.IGNORECASE):
            entities.append(
                {"text": m.group(), "type": "MATERIAL", "start": m.start(), "end": m.end(), "confidence": 0.9}
            )

    # QUANTITY
    for m in re.finditer(r"\b(\d+(?:\.\d+)?)\s*(?:m³|m²|m|kg|pieces|nos|tonnes|ltr|rm|%)?\b", text):
        qty_text = m.group().strip()
        if qty_text and any(c.isdigit() for c in qty_text[:3]) and len(qty_text) > 1:
            entities.append(
                {"text": qty_text, "type": "QUANTITY", "start": m.start(), "end": m.end(), "confidence": 0.85}
            )

    # UNIT
    for m in re.finditer(r"\b(m³|m²|m|kg|pieces|nos|tonnes|ltr|rm|%)", text):
        entities.append({"text": m.group(), "type": "UNIT", "start": m.start(), "end": m.end(), "confidence": 0.95})

    # GRADE
    for m in re.finditer(r"\b(M\d+|Fe\d+|C\d+|Grade\s*\d+|SS\s*\d+|E\s*\d+)\b", text):
        entities.append({"text": m.group(), "type": "GRADE", "start": m.start(), "end": m.end(), "confidence": 0.95})

    # STANDARD
    for m in re.finditer(r"\b(IS\s*\d+[A-Z]?|ASTM\s*\w+|BS\s*\d+|IRC\s*\d+)\b", text, re.IGNORECASE):
        entities.append({"text": m.group(), "type": "STANDARD", "start": m.start(), "end": m.end(), "confidence": 0.95})

    # DIMENSION
    for m in re.finditer(r"\b(\d+)mm\b", text):
        entities.append({"text": m.group(), "type": "DIMENSION", "start": m.start(), "end": m.end(), "confidence": 0.9})

    return entities


def extract_entities_bert(text, max_length=128):
    """Extract entities using BERT model."""
    if _model is None or _tokenizer is None:
        return extract_entities_rule_based(text)

    try:
        inputs = _tokenizer(
            text, return_tensors="pt", padding=True, truncation=True, max_length=max_length, return_offsets_mapping=True
        )

        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = _model(**inputs)

        predictions = torch.argmax(outputs.logits, dim=2)
        _tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        offsets = inputs["offset_mapping"][0]

        entities = []
        current_entity = None
        current_text = []
        current_start = None

        for i, (pred, offset) in enumerate(zip(predictions[0], offsets, strict=False)):
            label = ID2LABEL.get(pred.item(), "O")

            if offset[0] == offset[1] == 0:
                continue

            token_text = text[offset[0] : offset[1]]

            if label.startswith("S-"):
                entity_type = label[2:]
                entities.append(
                    {"text": token_text, "type": entity_type, "start": offset[0], "end": offset[1], "confidence": 0.9}
                )
            elif label.startswith("B-"):
                if current_entity:
                    entities.append(
                        {
                            "text": "".join(current_text),
                            "type": current_entity,
                            "start": current_start,
                            "end": offsets[i - 1][1],
                            "confidence": 0.85,
                        }
                    )
                current_entity = label[2:]
                current_text = [token_text]
                current_start = offset[0]
            elif label.startswith("I-") and current_entity == label[2:]:
                current_text.append(token_text)
            elif label == "O" and current_entity:
                entities.append(
                    {
                        "text": "".join(current_text),
                        "type": current_entity,
                        "start": current_start,
                        "end": offsets[i - 1][1],
                        "confidence": 0.85,
                    }
                )
                current_entity = None
                current_text = []

        if current_entity:
            entities.append(
                {
                    "text": "".join(current_text),
                    "type": current_entity,
                    "start": current_start,
                    "end": offsets[i - 1][1] if current_text else 0,
                    "confidence": 0.85,
                }
            )

        return entities

    except Exception as e:
        print(f"⚠️ BERT inference failed: {e}, using rule-based")
        return extract_entities_rule_based(text)


def extract_boq_items(text, entities):
    """Extract BOQ items from text and entities."""
    items = []

    # Find BOQ section
    boq_start = text.find("BILL OF QUANTITIES")
    boq_end = text.find("TECHNICAL SPECIFICATIONS")

    if boq_start == -1:
        boq_start = text.find("ITEMS REQUIRED")
    if boq_end == -1:
        boq_end = text.find("SPECIFICATIONS")

    boq_text = text[boq_start:boq_end] if boq_start != -1 and boq_end != -1 else text

    lines = [ln.strip() for ln in boq_text.split("\n") if ln.strip()]

    item_no = None
    description = []
    quantity = None
    unit = None

    for line in lines:
        if re.match(r"^(\d+)$", line) and item_no is None:
            if item_no is not None and description:
                items.append(
                    {
                        "item_no": int(item_no) if item_no else 0,
                        "material": " ".join(description),
                        "quantity": quantity or "N/A",
                        "unit": unit or "N/A",
                    }
                )
            item_no = line
            description = []
            quantity = None
            unit = None
        elif item_no is not None:
            # Check for quantity pattern
            qty_match = re.search(r"^(\d+(?:\.\d+)?)\s*(m³|m²|m|kg|pieces|nos|tonnes|ltr|rm)?$", line)
            if qty_match:
                quantity = qty_match.group(1)
                unit = qty_match.group(2)
                if description:
                    items.append(
                        {
                            "item_no": int(item_no),
                            "material": " ".join(description),
                            "quantity": quantity,
                            "unit": unit or "N/A",
                        }
                    )
                    item_no = None
                    description = []
                    quantity = None
                    unit = None
            elif line not in ["m³", "m²", "m", "kg", "pieces", "nos", "tonnes", "ltr", "rm"]:
                # It's part of description
                description.append(line)

    if item_no is not None and description:
        items.append(
            {
                "item_no": int(item_no) if item_no else 0,
                "material": " ".join(description),
                "quantity": quantity or "N/A",
                "unit": unit or "N/A",
            }
        )

    return items


def process_rfq(text):
    """Main processing function for RFQ text."""
    load_model()

    # Extract entities
    entities = extract_entities_rule_based(text)  # Use rule-based for now

    # Extract BOQ items
    boq_items = extract_boq_items(text, entities)

    # Group entities by type
    by_type = {}
    for e in entities:
        t = e["type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(e["text"])

    return {
        "entities": entities,
        "boq_items": boq_items,
        "entity_summary": {k: list(set(v))[:10] for k, v in by_type.items()},
        "total_entities": len(entities),
        "total_boq_items": len(boq_items),
    }


if __name__ == "__main__":
    # Test
    test_text = """
    Supply 500 kg cement at ground floor.
    M20 grade concrete for foundation, 50 cubic meters.
    Fe500 TMT steel bars 10mm diameter, 2500 kg.
    """

    print("=" * 60)
    print("RFQ2BOQ NER Inference Test")
    print("=" * 60)

    result = process_rfq(test_text)

    print(f"\n📊 Entities found: {result['total_entities']}")
    for t, items in result["entity_summary"].items():
        print(f"  {t}: {items[:5]}")

    print(f"\n📋 BOQ Items: {result['total_boq_items']}")
    for item in result["boq_items"]:
        print(f"  #{item['item_no']}: {item['material'][:30]} | {item['quantity']} {item['unit']}")
