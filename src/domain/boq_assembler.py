"""BOQ Assembler — builds BOQ rows from extracted entities and relations."""

from decimal import Decimal

from config.constants import EntityType

from src.domain.models import BoqRow, EntitySpan, Relation


class BOQAssembler:
    def __init__(self):
        self._item_counter = 0

    def assemble(
        self,
        entities: list[EntitySpan],
        relations: list[Relation] | None = None,
        text: str | None = None,
        pages: list[int] | None = None,
        source_text: str | None = None,
    ) -> list[BoqRow]:
        self._item_counter = 0
        text = source_text if source_text is not None else (text or "")
        relations = relations or []
        rows = []
        entities = sorted(entities, key=lambda e: (e.start, e.end))
        material_entities = [e for e in entities if e.type == EntityType.MATERIAL]

        for material in material_entities:
            row = self._build_boq_row(material, entities, relations, text, pages or [material.page or 1])
            if row:
                rows.append(row)

        if not rows:
            rows.append(self._create_empty_row(pages or [1]))

        for idx, row in enumerate(rows, start=1):
            row.item_no = idx

        return rows

    def _build_boq_row(
        self,
        material: EntitySpan,
        entities: list[EntitySpan],
        relations: list[Relation],
        text: str,
        pages: list[int],
    ) -> BoqRow | None:
        quantity = self._find_related(entities, material, EntityType.QUANTITY, relations)
        unit = self._find_related(entities, quantity, EntityType.UNIT, relations)
        dimension = self._find_related(entities, material, EntityType.DIMENSION, relations)
        grade = self._find_related(entities, material, EntityType.GRADE, relations)
        location = self._find_related(entities, material, EntityType.LOCATION, relations)
        standard = self._find_related(entities, material, EntityType.STANDARD, relations)
        action = self._find_action(entities, material)

        desc_parts = []
        if dimension and dimension.text:
            desc_parts.append(dimension.text)
        desc_parts.append(material.text)
        if location and location.text:
            desc_parts.append(f"to {location.text}")
        description = " ".join(desc_parts) if desc_parts else material.text

        page_list = pages if pages else [1]

        return BoqRow(
            item_no=1,
            material=material.text,
            quantity=self._parse_decimal(quantity.text) if quantity else Decimal("0"),
            unit=self._normalize_unit(unit.text if unit else "no.", material.text),
            action=action.text if action else "supply",
            grade=grade.text if grade else "",
            dimensions=[dimension.text] if dimension else [],
            standard=[standard.text] if standard else [],
            location=location.text if location else "",
            confidence=round(
                (material.conf + (quantity.conf if quantity else 0)) / 2, 2
            ),
            description_raw=description,
            source_pages=page_list[:1],
        )

    def _find_related(
        self,
        entities: list[EntitySpan],
        anchor: EntitySpan | None,
        target_type: EntityType,
        relations: list[Relation] | None = None,
    ) -> EntitySpan | None:
        candidates = [e for e in entities if e.type == target_type]
        if not candidates:
            return None

        relation_match = self._find_by_relation(entities, anchor, target_type, relations or [])
        if relation_match:
            return relation_match

        if anchor is None:
            return candidates[0]

        best: EntitySpan | None = None
        best_score: tuple[float, int, int] = (float("inf"), 999999, 999999)
        for candidate in candidates:
            contained_dims = self._get_contained_in_dimension(candidate, entities)
            if contained_dims:
                continue
            if target_type == EntityType.UNIT and self._is_contextual_noise(candidate):
                continue

            score = self._proximity_score(anchor, candidate, entities)
            if score < best_score:
                best_score = score
                best = candidate
        return best

    @staticmethod
    def _get_contained_in_dimension(entity: EntitySpan, entities: list[EntitySpan]) -> list[EntitySpan]:
        result = []
        unit_text_lower = entity.text.lower().strip()
        length_units = {"mm", "cm", "m", "ft", "in", "inch"}
        if unit_text_lower not in length_units:
            return result
        for dim in entities:
            if dim.type == EntityType.DIMENSION and dim.start <= entity.start <= dim.end:
                result.append(dim)
        return result

    def _proximity_score(
        self,
        anchor: EntitySpan,
        candidate: EntitySpan,
        entities: list[EntitySpan],
    ) -> tuple[float, int, int]:
        """Return (distance, direction_penalty, index_distance) for ordering.

        Distance = chars from anchor.end to candidate.start.
        direction_penalty = 100 if candidate is before anchor, else 0.
        index_distance = absolute difference in entity list positions.
        """
        if anchor.end <= candidate.start:
            char_dist = candidate.start - anchor.end
            direction = 0
        else:
            char_dist = anchor.start - candidate.end
            direction = 100
        idx_dist = abs(entities.index(candidate) - entities.index(anchor)) if anchor in entities else 999999
        return (char_dist, direction, idx_dist)

    @staticmethod
    def _is_contextual_noise(entity: EntitySpan) -> bool:
        noise_units = {
            "department", "item", "from", "payment", "conform", "submitted",
            "not", "aluminum", "a5luminum", "box", "plate",
        }
        text_lower = entity.text.lower().strip()
        return text_lower in noise_units

    @staticmethod
    def _normalize_unit(unit_str: str, material_text: str) -> str:
        """Normalize unit string to standard form based on material type."""
        u = unit_str.lower().strip()

        material_lower = material_text.lower()

        concrete_keywords = {"concrete", "cement", "mortar", "grout", "plaster", "screed"}
        steel_keywords = {"steel", "rebar", "tmt", "tor", "ms rod", " HYSD", "fe550", "fe415"}
        aggregate_keywords = {"aggregate", "sand", "crusher"}
        pipe_keywords = {"pipe", "ci pipe", "di pipe", "pvc pipe", "cpvc pipe", "gi pipe", "conduit", "junction box"}
        cable_keywords = {"cable", "wire", "conductor"}
        paint_keywords = {"paint", "primer", "emulsion", "enamel", "distemper"}
        brick_keywords = {"brick", "block", "paver"}
        sheet_keywords = {"granite", "marble", "tile", "flooring", "plywood", "glass", "board", "panel", "m²"}

        if any(k in material_lower for k in concrete_keywords):
            if u in {"rm", "r.m", "running meter", "l.m", "m", "meters"}:
                return "m³"
            if u in {"kg", "kilogram", "kgs"}:
                return u
            if u in {"nos", "no", "piece", "bars", "rods"}:
                return u
            if u in {"bags", "bag"}:
                return u  # e.g., cement bags — keep as detected
            return "m³"

        if any(k in material_lower for k in steel_keywords) and u in {"nos", "no", "piece", "pieces", "bars", "rod"}:
                return "kg"

        if any(k in material_lower for k in aggregate_keywords):
            if u in {"rm", "r.m", "meters"}:
                return "m³"
            if u in {"ton", "tonne", "mt"}:
                return "m³"

        if any(k in material_lower for k in pipe_keywords):
            if u in {"nos", "no", "piece", "nos.", "rm", "r.m", "running meter", "l.m"}:
                return "m"
            return "m"

        if any(k in material_lower for k in cable_keywords):
            if u in {"nos", "no", "roll", "coil"}:
                return "m"
            if u in {"rm", "r.m"}:
                return "m"

        if any(k in material_lower for k in paint_keywords):
            if u in {"nos", "no", "can", "tin", "litre", "liter", "ltr"}:
                return "ltr"
            if u in {"kg", "kgs"}:
                return "ltr"

        if any(k in material_lower for k in brick_keywords) and u in {"nos", "no", "piece"}:
            return "nos"

        if any(k in material_lower for k in sheet_keywords):
            if u in {"nos", "no", "piece", "rm", "r.m", "meters"}:
                return "m²"
            if u in {"mm", "cm"}:
                return "m²"

        # Standard unit mappings for common unit tokens
        unit_map = {
            "nos": "nos", "no": "nos", "nos.": "nos",
            "kg": "kg", "kgs": "kg", "kilogram": "kg",
            "m³": "m³", "cum": "m³", "cu.m": "m³", "cbm": "m³",
            "m²": "m²", "sqm": "m²", "sq.m": "m²",
            "m": "m", "rm": "m", "r.m": "m", "l.m": "m", "running meter": "m",
            "ltr": "ltr", "liter": "ltr", "litre": "ltr",
            "set": "set", "sets": "set",
            "sqmm": "sqmm", "sq.mm": "sqmm", "mm²": "sqmm",
        }
        return unit_map.get(u, u)

    def _find_action(self, entities: list[EntitySpan], material: EntitySpan) -> EntitySpan | None:
        actions = [entity for entity in entities if entity.type == EntityType.ACTION]
        if not actions:
            return None
        return min(actions, key=lambda entity: abs(entity.end - material.start))

    def _find_by_relation(
        self,
        entities: list[EntitySpan],
        anchor: EntitySpan | None,
        target_type: EntityType,
        relations: list[Relation],
    ) -> EntitySpan | None:
        if anchor is None or anchor not in entities:
            return None
        anchor_id = str(entities.index(anchor))
        for relation in relations:
            if relation.head_id == anchor_id:
                try:
                    candidate = entities[int(relation.tail_id)]
                except (ValueError, IndexError):
                    continue
                if candidate.type == target_type:
                    return candidate
            if relation.tail_id == anchor_id:
                try:
                    candidate = entities[int(relation.head_id)]
                except (ValueError, IndexError):
                    continue
                if candidate.type == target_type:
                    return candidate
        return None

    def _parse_decimal(self, text: str) -> Decimal:
        try:
            return Decimal(text.replace(",", "").strip())
        except Exception:
            return Decimal("0")

    def _create_empty_row(self, pages: list[int]) -> BoqRow:
        return BoqRow(
            item_no=1,
            material="",
            quantity=Decimal("0"),
            unit="no.",
            action="supply",
            grade="",
            standard=[],
            location="",
            confidence=0.0,
            description_raw="",
            source_pages=pages[:1] if pages else [1],
        )

    def deduplicate(self, rows: list[BoqRow]) -> list[BoqRow]:
        seen: dict[str, list[BoqRow]] = {}
        for row in rows:
            key = f"{row.material}|{row.unit}"
            if key not in seen:
                seen[key] = []
            seen[key].append(row)

        result = []
        for items in seen.values():
            if len(items) == 1:
                result.append(items[0])
            else:
                first = items[0]
                total_qty = sum(item.quantity for item in items)
                merged = BoqRow(
                    item_no=first.item_no,
                    material=first.material,
                    quantity=total_qty,
                    unit=first.unit,
                    action=first.action,
                    grade=first.grade,
                    dimensions=first.dimensions,
                    standard=first.standard,
                    location=first.location,
                    confidence=sum(i.confidence for i in items) / len(items),
                    description_raw=first.description_raw,
                    source_pages=first.source_pages,
                )
                result.append(merged)
        return result
