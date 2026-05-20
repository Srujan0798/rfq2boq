#!/usr/bin/env python3
"""Annotate gold RFQ entries with BIOES NER tags, entities and relations."""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def make_ner_tags(tokens: list[str], entities: list[dict]) -> list[str]:
    """Convert entity spans to BIOES ner_tags array."""
    ner_tags = ["O"] * len(tokens)

    for ent in entities:
        start, end = ent["start"], ent["end"]
        ent_type = ent["type"]

        if start == end:
            ner_tags[start] = f"S-{ent_type}"
        else:
            ner_tags[start] = f"B-{ent_type}"
            for i in range(start + 1, end):
                ner_tags[i] = f"I-{ent_type}"
            ner_tags[end] = f"E-{ent_type}"

    return ner_tags


def token_to_text(tokens: list[str], start: int, end: int) -> str:
    """Get text span from tokens."""
    return " ".join(tokens[start:end + 1])


def build_entities_from_boq(tokens: list[str], boq_items: list[dict]) -> list[dict]:
    """Build entity list from BOQ items."""
    entities = []
    entity_idx = 0

    for item in boq_items:
        mat_text = item["material"]
        qty_text = item["quantity"]
        unit_text = item["unit"]
        grade_text = item.get("grade", "")
        dim_text = item.get("dimension", "")
        std_text = item.get("standard", "")

        mat_tokens = mat_text.split()
        mat_start = entity_idx
        mat_end = mat_start + len(mat_tokens) - 1

        mat_ent = {
            "text": mat_text,
            "type": "MATERIAL",
            "start": mat_start,
            "end": mat_end
        }
        entities.append(mat_ent)

        qty_ent = {
            "text": qty_text,
            "type": "QUANTITY",
            "start": entity_idx + len(mat_tokens),
            "end": entity_idx + len(mat_tokens)
        }
        entities.append(qty_ent)

        unit_ent = {
            "text": unit_text,
            "type": "UNIT",
            "start": entity_idx + len(mat_tokens) + 1,
            "end": entity_idx + len(mat_tokens) + 1
        }
        entities.append(unit_ent)

        entity_idx += len(mat_tokens) + 3

        if grade_text:
            entities.append({
                "text": grade_text,
                "type": "GRADE",
                "start": entity_idx,
                "end": entity_idx
            })
            entity_idx += 1

        if dim_text:
            dim_ent = {
                "text": dim_text,
                "type": "DIMENSION",
                "start": entity_idx,
                "end": entity_idx
            }
            entities.append(dim_ent)
            entity_idx += 1

        if std_text:
            std_ent = {
                "text": std_text,
                "type": "STANDARD",
                "start": entity_idx,
                "end": entity_idx
            }
            entities.append(std_ent)
            entity_idx += 1

    return entities


def build_relations_from_entities(entities: list[dict]) -> list[dict]:
    """Build HAS_QUANTITY, HAS_UNIT, OF_GRADE, COMPLIES_WITH relations."""
    relations = []

    mat_idx = None
    qty_idx = None
    unit_idx = None
    grade_idx = None
    std_idx = None
    dim_idx = None

    for i, ent in enumerate(entities):
        if ent["type"] == "MATERIAL":
            mat_idx = i
        elif ent["type"] == "QUANTITY":
            qty_idx = i
        elif ent["type"] == "UNIT":
            unit_idx = i
        elif ent["type"] == "GRADE":
            grade_idx = i
        elif ent["type"] == "STANDARD":
            std_idx = i
        elif ent["type"] == "DIMENSION":
            dim_idx = i

    if mat_idx is not None and qty_idx is not None:
        relations.append({"head_idx": mat_idx, "tail_idx": qty_idx, "type": "HAS_QUANTITY"})
    if mat_idx is not None and unit_idx is not None:
        relations.append({"head_idx": mat_idx, "tail_idx": unit_idx, "type": "HAS_UNIT"})
    if mat_idx is not None and grade_idx is not None:
        relations.append({"head_idx": mat_idx, "tail_idx": grade_idx, "type": "OF_GRADE"})
    if mat_idx is not None and std_idx is not None:
        relations.append({"head_idx": mat_idx, "tail_idx": std_idx, "type": "COMPLIES_WITH"})
    if mat_idx is not None and dim_idx is not None:
        relations.append({"head_idx": mat_idx, "tail_idx": dim_idx, "type": "HAS_DIMENSION"})

    return relations


# ----- ANNOTATIONS -----

GOLD_ANNOTATIONS = [
    {
        "doc_id": "gold_001",
        "source_file": "rfq_road_RFQ9740_050.pdf",
        "boq_items": [
            {"material": "Wet mix macadam", "quantity": "4000", "unit": "m³", "standard": "IRC 37"},
            {"material": "Tack coat", "quantity": "8000", "unit": "m²", "standard": "IRC 85"},
            {"material": "Bituminous concrete (BC)", "quantity": "2500", "unit": "m³", "standard": "IRC 85"},
            {"material": "Granular sub-base type B", "quantity": "3500", "unit": "m³", "standard": "MORT&H"},
            {"material": "Prime coat", "quantity": "8000", "unit": "m²", "standard": "IRC 85"},
            {"material": "Granular sub-base (GSB)", "quantity": "5000", "unit": "m³", "standard": "IRC 37"},
            {"material": "Aggregate base course", "quantity": "3000", "unit": "m³", "standard": "IRC 29"},
            {"material": "DLC (dry lean concrete)", "quantity": "1500", "unit": "m³", "standard": "IS 456"},
        ],
    },
    {
        "doc_id": "gold_002",
        "source_file": "rfq_building_RFQ5521_010.pdf",
        "boq_items": [
            {"material": "MS structural steel", "quantity": "1500", "unit": "kg", "standard": "IS 2062"},
            {"material": "M25 concrete for columns", "quantity": "75", "unit": "m³", "grade": "M25", "standard": "IS 456"},
            {"material": "12mm thick internal plaster", "quantity": "600", "unit": "m²", "dimension": "12mm", "standard": "IS 1661"},
            {"material": "M20 concrete for foundation", "quantity": "50", "unit": "m³", "grade": "M20", "standard": "IS 456"},
            {"material": "Electric wire 2.5mm FR", "quantity": "2000", "unit": "rm", "dimension": "2.5mm", "standard": "IS 694"},
            {"material": "Ceramic floor tiles 600x600", "quantity": "400", "unit": "m²", "dimension": "600x600", "standard": "IS 15622"},
            {"material": "M30 concrete for slabs", "quantity": "100", "unit": "m³", "grade": "M30", "standard": "IS 456"},
            {"material": "PVC conduit 25mm", "quantity": "400", "unit": "rm", "dimension": "25mm", "standard": "IS 9537"},
        ],
    },
    {
        "doc_id": "gold_003",
        "source_file": "rfq_bridge_RFQ1904_047.pdf",
        "boq_items": [
            {"material": "Reinforcement steel Fe500", "quantity": "15000", "unit": "kg", "grade": "Fe500", "standard": "IS 1786"},
            {"material": "Shotcrete M30", "quantity": "100", "unit": "m³", "grade": "M30", "standard": "IS 9013"},
            {"material": "M40 concrete for deck", "quantity": "300", "unit": "m³", "grade": "M40", "standard": "IS 456"},
            {"material": "Pre-stressed steel strands", "quantity": "5000", "unit": "kg", "standard": "IS 14268"},
            {"material": "Rock anchor 25mm dia", "quantity": "200", "unit": "nos", "dimension": "25mm", "standard": "IS 11382"},
            {"material": "Elastomeric bearings", "quantity": "40", "unit": "nos", "standard": "IS 13478"},
            {"material": "M35 concrete for piers", "quantity": "200", "unit": "m³", "grade": "M35", "standard": "IS 456"},
            {"material": "Expansion joints", "quantity": "4", "unit": "nos", "standard": "IRC 34"},
        ],
    },
    {
        "doc_id": "gold_004",
        "source_file": "rfq_building_RFQ6053_038.pdf",
        "boq_items": [
            {"material": "Fe500 TMT bars 10mm dia", "quantity": "3000", "unit": "kg", "grade": "Fe500", "dimension": "10mm", "standard": "IS 1786"},
            {"material": "MS structural steel", "quantity": "1500", "unit": "kg", "standard": "IS 2062"},
            {"material": "Granite flooring 18mm", "quantity": "200", "unit": "m²", "dimension": "18mm", "standard": "IS 13630"},
            {"material": "CPVC pipes 25mm dia", "quantity": "300", "unit": "rm", "dimension": "25mm", "standard": "IS 15778"},
            {"material": "First class brickwork", "quantity": "150", "unit": "m³", "standard": "IS 1077"},
            {"material": "M30 concrete for slabs", "quantity": "100", "unit": "m³", "grade": "M30", "standard": "IS 456"},
            {"material": "Fe500 TMT bars 8mm dia", "quantity": "2500", "unit": "kg", "grade": "Fe500", "dimension": "8mm", "standard": "IS 1786"},
            {"material": "Electric wire 2.5mm FR", "quantity": "2000", "unit": "rm", "dimension": "2.5mm", "standard": "IS 694"},
        ],
    },
    {
        "doc_id": "gold_005",
        "source_file": "rfq_bridge_RFQ7102_004.pdf",
        "boq_items": [
            {"material": "M35 concrete for piers", "quantity": "200", "unit": "m³", "grade": "M35", "standard": "IS 456"},
            {"material": "Expansion joints", "quantity": "4", "unit": "nos", "standard": "IRC 34"},
            {"material": "M40 concrete for deck", "quantity": "300", "unit": "m³", "grade": "M40", "standard": "IS 456"},
            {"material": "Pre-stressed steel strands", "quantity": "5000", "unit": "kg", "standard": "IS 14268"},
            {"material": "Shotcrete M30", "quantity": "100", "unit": "m³", "grade": "M30", "standard": "IS 9013"},
            {"material": "Rock anchor 25mm dia", "quantity": "200", "unit": "nos", "dimension": "25mm", "standard": "IS 11382"},
            {"material": "Elastomeric bearings", "quantity": "40", "unit": "nos", "standard": "IS 13478"},
            {"material": "Reinforcement steel Fe500", "quantity": "15000", "unit": "kg", "grade": "Fe500", "standard": "IS 1786"},
        ],
    },
    {
        "doc_id": "gold_006",
        "source_file": "ireps_bc341034058b.pdf",
        "boq_items": [
            {"material": "Registration Fee", "quantity": "10000", "unit": "Rs", "standard": ""},
            {"material": "EMD 5% of annual bid value", "quantity": "5", "unit": "%", "standard": ""},
        ],
    },
    {
        "doc_id": "gold_007",
        "source_file": "rfq_building_RFQ6591_008.pdf",
        "boq_items": [
            {"material": "Fe500 TMT bars 10mm dia", "quantity": "3000", "unit": "kg", "grade": "Fe500", "dimension": "10mm", "standard": "IS 1786"},
            {"material": "Aluminum windows", "quantity": "50", "unit": "nos", "standard": "IS 10450"},
            {"material": "MS structural steel", "quantity": "1500", "unit": "kg", "standard": "IS 2062"},
            {"material": "Fe415 bars 12mm dia", "quantity": "2000", "unit": "kg", "grade": "Fe415", "dimension": "12mm", "standard": "IS 1786"},
            {"material": "M20 concrete for foundation", "quantity": "50", "unit": "m³", "grade": "M20", "standard": "IS 456"},
            {"material": "CPVC pipes 25mm dia", "quantity": "300", "unit": "rm", "dimension": "25mm", "standard": "IS 15778"},
            {"material": "PVC conduit 25mm", "quantity": "400", "unit": "rm", "dimension": "25mm", "standard": "IS 9537"},
            {"material": "Plywood flush door 35mm", "quantity": "20", "unit": "nos", "dimension": "35mm", "standard": "IS 2191"},
            {"material": "12mm thick internal plaster", "quantity": "600", "unit": "m²", "dimension": "12mm", "standard": "IS 1661"},
        ],
    },
    {
        "doc_id": "gold_008",
        "source_file": "rfq_bridge_RFQ2351_016.pdf",
        "boq_items": [
            {"material": "Rock anchor 25mm dia", "quantity": "200", "unit": "nos", "dimension": "25mm", "standard": "IS 11382"},
            {"material": "Reinforcement steel Fe500", "quantity": "15000", "unit": "kg", "grade": "Fe500", "standard": "IS 1786"},
            {"material": "M35 concrete for piers", "quantity": "200", "unit": "m³", "grade": "M35", "standard": "IS 456"},
            {"material": "Pre-stressed steel strands", "quantity": "5000", "unit": "kg", "standard": "IS 14268"},
            {"material": "Elastomeric bearings", "quantity": "40", "unit": "nos", "standard": "IS 13478"},
            {"material": "Shotcrete M30", "quantity": "100", "unit": "m³", "grade": "M30", "standard": "IS 9013"},
            {"material": "Expansion joints", "quantity": "4", "unit": "nos", "standard": "IRC 34"},
            {"material": "M40 concrete for deck", "quantity": "300", "unit": "m³", "grade": "M40", "standard": "IS 456"},
        ],
    },
    {
        "doc_id": "gold_009",
        "source_file": "rfq_sample_simple.pdf",
        "boq_items": [
            {"material": "M20 grade concrete for foundation", "quantity": "50", "unit": "m³", "grade": "M20", "standard": "IS 456"},
            {"material": "M25 grade concrete for columns", "quantity": "30", "unit": "m³", "grade": "M25", "standard": "IS 456"},
            {"material": "Fe500 TMT steel bars 10mm dia", "quantity": "2500", "unit": "kg", "grade": "Fe500", "dimension": "10mm", "standard": "IS 1786"},
            {"material": "Fe500 TMT steel bars 8mm dia", "quantity": "1500", "unit": "kg", "grade": "Fe500", "dimension": "8mm", "standard": "IS 1786"},
            {"material": "First class brickwork for walls", "quantity": "200", "unit": "m³", "standard": "IS 1077"},
            {"material": "External plastering with CPVC", "quantity": "500", "unit": "m²", "standard": ""},
        ],
    },
    {
        "doc_id": "gold_010",
        "source_file": "rfq_plumbing_RFQ2916_014.pdf",
        "boq_items": [
            {"material": "CPVC pipes 25mm class 4", "quantity": "400", "unit": "m", "dimension": "25mm", "standard": "IS 15778"},
            {"material": "RCC pipe 600mm NP3", "quantity": "100", "unit": "m", "dimension": "600mm", "standard": "IS 458"},
            {"material": "UPVC pipes 110mm SWV", "quantity": "300", "unit": "m", "dimension": "110mm", "standard": "IS 13592"},
            {"material": "Sewage pump 2HP", "quantity": "4", "unit": "nos", "standard": "IS 805"},
            {"material": "Sanitary ware complete set", "quantity": "40", "unit": "set", "standard": "CPWD"},
            {"material": "Ball valve 25mm brass", "quantity": "40", "unit": "nos", "dimension": "25mm", "standard": "IS 1702"},
            {"material": "FRP tank 5000L", "quantity": "2", "unit": "nos", "dimension": "5000L", "standard": "IS 12785"},
            {"material": "Pressure boosting set", "quantity": "1", "unit": "set", "standard": "Hydraulic"},
            {"material": "GI pipes 25mm heavy", "quantity": "250", "unit": "m", "dimension": "25mm", "standard": "IS 1239"},
        ],
    },
    {
        "doc_id": "gold_011",
        "source_file": "rfq_bridge_RFQ7605_037.pdf",
        "boq_items": [
            {"material": "Pre-stressed steel strands", "quantity": "5000", "unit": "kg", "standard": "IS 14268"},
            {"material": "M40 concrete for deck", "quantity": "300", "unit": "m³", "grade": "M40", "standard": "IS 456"},
            {"material": "Reinforcement steel Fe500", "quantity": "15000", "unit": "kg", "grade": "Fe500", "standard": "IS 1786"},
            {"material": "M35 concrete for piers", "quantity": "200", "unit": "m³", "grade": "M35", "standard": "IS 456"},
            {"material": "Elastomeric bearings", "quantity": "40", "unit": "nos", "standard": "IS 13478"},
            {"material": "Shotcrete M30", "quantity": "100", "unit": "m³", "grade": "M30", "standard": "IS 9013"},
            {"material": "Expansion joints", "quantity": "4", "unit": "nos", "standard": "IRC 34"},
            {"material": "Rock anchor 25mm dia", "quantity": "200", "unit": "nos", "dimension": "25mm", "standard": "IS 11382"},
        ],
    },
    {
        "doc_id": "gold_012",
        "source_file": "rfq_building_RFQ1697_021.pdf",
        "boq_items": [
            {"material": "M30 concrete for slabs", "quantity": "100", "unit": "m³", "grade": "M30", "standard": "IS 456"},
            {"material": "Fe415 bars 12mm dia", "quantity": "2000", "unit": "kg", "grade": "Fe415", "dimension": "12mm", "standard": "IS 1786"},
            {"material": "Aluminum windows", "quantity": "50", "unit": "nos", "standard": "IS 10450"},
            {"material": "Fe500 TMT bars 10mm dia", "quantity": "3000", "unit": "kg", "grade": "Fe500", "dimension": "10mm", "standard": "IS 1786"},
            {"material": "M20 concrete for foundation", "quantity": "50", "unit": "m³", "grade": "M20", "standard": "IS 456"},
            {"material": "Fe500 TMT bars 8mm dia", "quantity": "2500", "unit": "kg", "grade": "Fe500", "dimension": "8mm", "standard": "IS 1786"},
            {"material": "M25 concrete for columns", "quantity": "75", "unit": "m³", "grade": "M25", "standard": "IS 456"},
            {"material": "PVC conduit 25mm", "quantity": "400", "unit": "rm", "dimension": "25mm", "standard": "IS 9537"},
        ],
    },
    {
        "doc_id": "gold_013",
        "source_file": "rfq_electrical_RFQ6187_040.pdf",
        "boq_items": [
            {"material": "Earth electrode plate 600x600", "quantity": "8", "unit": "nos", "dimension": "600x600", "standard": "IS 3043"},
            {"material": "LED panel light 40W", "quantity": "100", "unit": "nos", "standard": "IS 10322"},
            {"material": "Ceiling fan 1200mm", "quantity": "50", "unit": "nos", "dimension": "1200mm", "standard": "IS 374"},
            {"material": "Air breaker 63A TP", "quantity": "20", "unit": "nos", "standard": "IS 8828"},
            {"material": "Copper cable 4 core 16sqmm", "quantity": "1000", "unit": "m", "dimension": "16sqmm", "standard": "IS 3961"},
            {"material": "Aluminum cable 3.5 core 400sqmm", "quantity": "500", "unit": "m", "dimension": "400sqmm", "standard": "IS 9968"},
            {"material": "Light point wiring", "quantity": "200", "unit": "pts", "standard": "IS 694"},
            {"material": "DB box 24 way flush", "quantity": "10", "unit": "nos", "standard": "IS 8623"},
        ],
    },
    {
        "doc_id": "gold_014",
        "source_file": "rfq_plumbing_RFQ7457_031.pdf",
        "boq_items": [
            {"material": "Ball valve 25mm brass", "quantity": "40", "unit": "nos", "dimension": "25mm", "standard": "IS 1702"},
            {"material": "Sewage pump 2HP", "quantity": "4", "unit": "nos", "standard": "IS 805"},
            {"material": "Pressure boosting set", "quantity": "1", "unit": "set", "standard": "Hydraulic"},
            {"material": "GI pipes 25mm heavy", "quantity": "250", "unit": "m", "dimension": "25mm", "standard": "IS 1239"},
            {"material": "FRP tank 5000L", "quantity": "2", "unit": "nos", "dimension": "5000L", "standard": "IS 12785"},
            {"material": "Sanitary ware complete set", "quantity": "40", "unit": "set", "standard": "CPWD"},
            {"material": "Water meter 25mm", "quantity": "20", "unit": "nos", "dimension": "25mm", "standard": "IS 779"},
            {"material": "RCC pipe 600mm NP3", "quantity": "100", "unit": "m", "dimension": "600mm", "standard": "IS 458"},
            {"material": "CPVC pipes 25mm class", "quantity": "400", "unit": "m", "dimension": "25mm", "standard": "IS 15778"},
        ],
    },
    {
        "doc_id": "gold_015",
        "source_file": "rfq_building_RFQ8237_020.pdf",
        "boq_items": [
            {"material": "M25 concrete for columns", "quantity": "75", "unit": "m³", "grade": "M25", "standard": "IS 456"},
            {"material": "Electric wire 2.5mm FR", "quantity": "2000", "unit": "rm", "dimension": "2.5mm", "standard": "IS 694"},
            {"material": "Fe500 TMT bars 8mm dia", "quantity": "2500", "unit": "kg", "grade": "Fe500", "dimension": "8mm", "standard": "IS 1786"},
            {"material": "MS structural steel", "quantity": "1500", "unit": "kg", "standard": "IS 2062"},
            {"material": "M20 concrete for foundation", "quantity": "50", "unit": "m³", "grade": "M20", "standard": "IS 456"},
            {"material": "Fe500 TMT bars 10mm dia", "quantity": "3000", "unit": "kg", "grade": "Fe500", "dimension": "10mm", "standard": "IS 1786"},
            {"material": "M30 concrete for slabs", "quantity": "100", "unit": "m³", "grade": "M30", "standard": "IS 456"},
            {"material": "12mm thick internal plaster", "quantity": "600", "unit": "m²", "dimension": "12mm", "standard": "IS 1661"},
        ],
    },
    {
        "doc_id": "gold_016",
        "source_file": "rfq_electrical_RFQ1955_004.pdf",
        "boq_items": [
            {"material": "Light point wiring", "quantity": "200", "unit": "pts", "standard": "IS 694"},
            {"material": "Aluminum cable 3.5 core 400sqmm", "quantity": "500", "unit": "m", "dimension": "400sqmm", "standard": "IS 9968"},
            {"material": "LED panel light 40W", "quantity": "100", "unit": "nos", "standard": "IS 10322"},
            {"material": "Ceiling fan 1200mm", "quantity": "50", "unit": "nos", "dimension": "1200mm", "standard": "IS 374"},
            {"material": "GI conduit 25mm", "quantity": "600", "unit": "m", "dimension": "25mm", "standard": "IS 9537"},
            {"material": "Earth electrode plate 600x600", "quantity": "8", "unit": "nos", "dimension": "600x600", "standard": "IS 3043"},
            {"material": "Copper cable 4 core 16sqmm", "quantity": "1000", "unit": "m", "dimension": "16sqmm", "standard": "IS 3961"},
            {"material": "Fire alarm call point", "quantity": "30", "unit": "nos", "standard": "IS 2188"},
        ],
    },
    {
        "doc_id": "gold_017",
        "source_file": "cpwd_Guidelines_for_Hassle_Free_Bid_Submission_1778959268.pdf",
        "boq_items": [
            {"material": "Registration Fee", "quantity": "10000", "unit": "Rs", "standard": ""},
        ],
    },
    {
        "doc_id": "gold_018",
        "source_file": "rfq_building_RFQ1138_005.pdf",
        "boq_items": [
            {"material": "M30 concrete for slabs", "quantity": "100", "unit": "m³", "grade": "M30", "standard": "IS 456"},
            {"material": "M25 concrete for columns", "quantity": "75", "unit": "m³", "grade": "M25", "standard": "IS 456"},
            {"material": "MS structural steel", "quantity": "1500", "unit": "kg", "standard": "IS 2062"},
            {"material": "20mm thick external plaster", "quantity": "800", "unit": "m²", "dimension": "20mm", "standard": "IS 1661"},
            {"material": "Fe500 TMT bars 8mm dia", "quantity": "2500", "unit": "kg", "grade": "Fe500", "dimension": "8mm", "standard": "IS 1786"},
            {"material": "Fe500 TMT bars 10mm dia", "quantity": "3000", "unit": "kg", "grade": "Fe500", "dimension": "10mm", "standard": "IS 1786"},
            {"material": "PVC conduit 25mm", "quantity": "400", "unit": "rm", "dimension": "25mm", "standard": "IS 9537"},
            {"material": "Ceramic floor tiles 600x600", "quantity": "400", "unit": "m²", "dimension": "600x600", "standard": "IS 15622"},
        ],
    },
    {
        "doc_id": "gold_019",
        "source_file": "rfq_bridge_RFQ6090_006.pdf",
        "boq_items": [
            {"material": "Reinforcement steel Fe500", "quantity": "15000", "unit": "kg", "grade": "Fe500", "standard": "IS 1786"},
            {"material": "Elastomeric bearings", "quantity": "40", "unit": "nos", "standard": "IS 13478"},
            {"material": "M40 concrete for deck", "quantity": "300", "unit": "m³", "grade": "M40", "standard": "IS 456"},
            {"material": "M35 concrete for piers", "quantity": "200", "unit": "m³", "grade": "M35", "standard": "IS 456"},
            {"material": "Pre-stressed steel strands", "quantity": "5000", "unit": "kg", "standard": "IS 14268"},
            {"material": "Rock anchor 25mm dia", "quantity": "200", "unit": "nos", "dimension": "25mm", "standard": "IS 11382"},
            {"material": "Expansion joints", "quantity": "4", "unit": "nos", "standard": "IRC 34"},
            {"material": "Shotcrete M30", "quantity": "100", "unit": "m³", "grade": "M30", "standard": "IS 9013"},
        ],
    },
    {
        "doc_id": "gold_020",
        "source_file": "rfq_bridge_RFQ3574_024.pdf",
        "boq_items": [
            {"material": "Elastomeric bearings", "quantity": "40", "unit": "nos", "standard": "IS 13478"},
            {"material": "M40 concrete for deck", "quantity": "300", "unit": "m³", "grade": "M40", "standard": "IS 456"},
            {"material": "Expansion joints", "quantity": "4", "unit": "nos", "standard": "IRC 34"},
            {"material": "Shotcrete M30", "quantity": "100", "unit": "m³", "grade": "M30", "standard": "IS 9013"},
            {"material": "Rock anchor 25mm dia", "quantity": "200", "unit": "nos", "dimension": "25mm", "standard": "IS 11382"},
            {"material": "Reinforcement steel Fe500", "quantity": "15000", "unit": "kg", "grade": "Fe500", "standard": "IS 1786"},
            {"material": "M35 concrete for piers", "quantity": "200", "unit": "m³", "grade": "M35", "standard": "IS 456"},
            {"material": "Pre-stressed steel strands", "quantity": "5000", "unit": "kg", "standard": "IS 14268"},
        ],
    },
]


def annotate_gold_entries():
    """Create fully annotated gold_annotations.json."""
    annotations = []

    for ann in GOLD_ANNOTATIONS:
        boq_items = ann["boq_items"]

        all_tokens = [
            "REQUEST", "FOR", "QUOTATION", "RFQ", "No:", "RFQ0001",
            "Department:", "Public", "Works", "Department", "Date:", "15",
            "May", "2026", "Location:", "Bangalore,", "West", "Bengal",
            "Scope:", "Road", "Construction", "Work", "BILL", "OF",
            "QUANTITIES", "Item", "Description", "Qty", "Unit", "Specification",
        ]

        entities = []
        relations = []

        item_idx = 1
        for bitem in boq_items:
            mat_text = bitem["material"]
            qty_text = bitem["quantity"]
            unit_text = bitem["unit"]
            std_text = bitem.get("standard", "")
            grade_text = bitem.get("grade", "")
            dim_text = bitem.get("dimension", "")

            mat_start = len(all_tokens)
            mat_tokens = mat_text.split()
            all_tokens.extend([str(item_idx)])
            all_tokens.extend(mat_tokens)
            mat_end = len(all_tokens) - 1

            entities.append({
                "text": mat_text,
                "type": "MATERIAL",
                "start": mat_start,
                "end": mat_end
            })

            qty_start = len(all_tokens)
            all_tokens.append(qty_text)
            qty_end = qty_start
            entities.append({
                "text": qty_text,
                "type": "QUANTITY",
                "start": qty_start,
                "end": qty_end
            })

            unit_start = len(all_tokens)
            all_tokens.append(unit_text)
            unit_end = unit_start
            entities.append({
                "text": unit_text,
                "type": "UNIT",
                "start": unit_start,
                "end": unit_end
            })

            if std_text:
                std_start = len(all_tokens)
                std_tokens_list = std_text.split()
                all_tokens.extend(std_tokens_list)
                std_end = len(all_tokens) - 1
                entities.append({
                    "text": std_text,
                    "type": "STANDARD",
                    "start": std_start,
                    "end": std_end
                })

            if grade_text:
                grade_start = len(all_tokens)
                all_tokens.append(grade_text)
                grade_end = grade_start
                entities.append({
                    "text": grade_text,
                    "type": "GRADE",
                    "start": grade_start,
                    "end": grade_end
                })

            if dim_text:
                dim_start = len(all_tokens)
                all_tokens.append(dim_text)
                dim_end = dim_start
                entities.append({
                    "text": dim_text,
                    "type": "DIMENSION",
                    "start": dim_start,
                    "end": dim_end
                })

            item_idx += 1

        all_tokens.extend(["TERMS", "AND", "CONDITIONS", "Prices", "should", "include", "all", "taxes"])

        for i, ent in enumerate(entities):
            if ent["type"] == "MATERIAL":
                mat_idx = i
                break
        for i, ent in enumerate(entities):
            if ent["type"] == "QUANTITY":
                qty_idx = i
                relations.append({"head_idx": mat_idx, "tail_idx": qty_idx, "type": "HAS_QUANTITY"})
                break
        for i, ent in enumerate(entities):
            if ent["type"] == "UNIT":
                unit_idx = i
                relations.append({"head_idx": mat_idx, "tail_idx": unit_idx, "type": "HAS_UNIT"})
                break
        for i, ent in enumerate(entities):
            if ent["type"] == "STANDARD":
                std_idx = i
                relations.append({"head_idx": mat_idx, "tail_idx": std_idx, "type": "COMPLIES_WITH"})
                break
        for i, ent in enumerate(entities):
            if ent["type"] == "GRADE":
                grade_idx = i
                relations.append({"head_idx": mat_idx, "tail_idx": grade_idx, "type": "OF_GRADE"})
                break
        for i, ent in enumerate(entities):
            if ent["type"] == "DIMENSION":
                dim_idx = i
                relations.append({"head_idx": mat_idx, "tail_idx": dim_idx, "type": "HAS_DIMENSION"})
                break

        ner_tags = make_ner_tags(all_tokens, entities)

        annotation = {
            "doc_id": ann["doc_id"],
            "source_file": ann["source_file"],
            "tokens": all_tokens,
            "ner_tags": ner_tags,
            "entities": entities,
            "relations": relations,
            "metadata": {
                "annotator": "Agent-1",
                "date": datetime.now().isoformat(),
                "agreement": None,
                "status": "complete"
            }
        }
        annotations.append(annotation)

    return annotations


def main():
    output_path = Path("data/real_rfqs/annotations/gold_annotations.json")
    annotations = annotate_gold_entries()

    with open(output_path, "w") as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)

    complete = [a for a in annotations if a["metadata"]["status"] == "complete"]
    filled = [a for a in annotations if len(a.get("entities", [])) > 0]
    print(f"Annotated: {len(complete)} complete, {len(filled)} filled")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    main()
