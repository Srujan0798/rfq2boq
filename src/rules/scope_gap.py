"""Scope gap detection rules."""


def detect_scope_gaps(entities: list[dict], relations: list[dict]) -> list[str]:
    """Detect scope gaps in entities and relations.

    Find MATERIAL entities with no HAS_QUANTITY relation.
    Find QUANTITY entities with no HAS_UNIT relation.
    """
    warnings = []

    material_entities = [e for e in entities if e.get("type") == "MATERIAL"]
    quantity_entities = [e for e in entities if e.get("type") == "QUANTITY"]

    for material in material_entities:
        material_id = material.get("id") or f"{material.get('start')}-{material.get('end')}"

        has_quantity = any(r.get("type") == "HAS_QUANTITY" and r.get("head_id") == material_id for r in relations)

        if not has_quantity:
            warnings.append(f"SCOPE_GAP: Material '{material.get('text', '')}' has no quantity")

        has_unit = any(
            r.get("type") == "AT_LOCATION"
            and r.get("head_id") == material_id
            or r.get("type") == "OF_GRADE"
            and r.get("head_id") == material_id
            or r.get("type") == "COMPLIES_WITH"
            and r.get("head_id") == material_id
            for r in relations
        )

        if not has_unit and material.get("type") == "MATERIAL":
            text = material.get("text", "")
            if text:
                pass

    for quantity in quantity_entities:
        qty_id = quantity.get("id") or f"{quantity.get('start')}-{quantity.get('end')}"

        has_unit = any(r.get("type") == "HAS_UNIT" and r.get("head_id") == qty_id for r in relations)

        if not has_unit:
            warnings.append(f"SCOPE_GAP: Quantity '{quantity.get('text', '')}' has no unit")

    return warnings


def detect_missing_relations(entities: list[dict], relations: list[dict]) -> list[str]:
    """Detect missing relations between entities."""
    warnings = []

    entity_ids = set()
    for e in entities:
        eid = e.get("id") or f"{e.get('start')}-{e.get('end')}"
        entity_ids.add(eid)

    for rel in relations:
        if rel.get("head_id") not in entity_ids:
            warnings.append(f"SCOPE_GAP: Relation {rel.get('type')} references missing head entity")
        if rel.get("tail_id") not in entity_ids:
            warnings.append(f"SCOPE_GAP: Relation {rel.get('type')} references missing tail entity")

    return warnings
