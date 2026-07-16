"""BOQ Assembler — builds BOQ rows from extracted entities and relations."""

from __future__ import annotations

import re
from decimal import Decimal

from config.constants import EntityType

from src.domain.models import BoqRow, EntitySpan, Relation
from src.rules.units import UnitNormalizer

# P3_04: a single instance used by the tie-breaker.  Stateless, so
# sharing across calls is safe.
_UNIT_NORMALIZER = UnitNormalizer()


# P3_04: typed-flag import is deferred to runtime to avoid a
# circular import (flags.py -> config.constants is fine, but
# models.py -> flags.py -> models.py is a cycle).
def _flag_module():
    from src.domain import flags as _flags

    return _flags


class BOQAssembler:
    # Material nouns — if a material has no material noun, it's likely a dimension header.
    _MATERIAL_NOUNS = frozenset(
        {
            "pipe",
            "pipes",
            "duct",
            "ducts",
            "insulation",
            "lining",
            "laying",
            "cement",
            "concrete",
            "steel",
            "rebar",
            "rod",
            "rods",
            "bar",
            "bars",
            "aggregate",
            "sand",
            "mortar",
            "grout",
            "screed",
            "plaster",
            "paint",
            "painting",
            "primer",
            "coating",
            "waterproofing",
            "tile",
            "tiles",
            "flooring",
            "granite",
            "marble",
            "glass",
            "plywood",
            "board",
            "panel",
            "panels",
            "cladding",
            "sheet",
            "sheets",
            "wool",
            "mattress",
            "mattresses",
            "cable",
            "cables",
            "wire",
            "wires",
            "conductor",
            "conduit",
            "junction",
            "box",
            "aluminum",
            "brick",
            "bricks",
            "block",
            "blocks",
            "paver",
            "pavers",
            "adhesive",
            "sealant",
            "tape",
            "fastener",
            "bolt",
            "nut",
            "washer",
            "valve",
            "fitting",
            "elbow",
            "tee",
            "flange",
            "gasket",
        }
    )

    # Pure-dimension pattern: matches cells like "15MM", "20 mm" (number + unit ONLY, no qualifier).
    _PURE_DIMENSION_RE = re.compile(
        r"^\s*\d+\s*(mm|cm|m|inch|in|ft)\s*$",
        re.IGNORECASE,
    )

    # Dimension with qualifier: "15mm OD", "15mm ID", "15mm thick", "20mm dia" — VALID (has material context).
    _DIMENSION_WITH_QUALIFIER_RE = re.compile(
        r"^\s*\d+\s*(mm|cm|m|inch|in|ft)\s*(od|id|thick|thick\.|dia|diameter)\s*$",
        re.IGNORECASE,
    )

    # Spec paragraph phrases — if a material text contains 2+ of these, it's likely a spec paragraph.
    # Spec keywords — individual words that indicate specification text (not material names).
    _SPEC_KEYWORDS: tuple[str, ...] = (
        "astm",
        "shall",
        "testing",
        "commissioning",
        "application",
        "installation",
        "certified",
        "approved",
        "compliance",
        "density",
        "conductivity",
        "thickness",
        "temperature",
        "adhesive",
        "workmanship",
    )

    # Section header patterns — text matching these is likely a section/group header.
    _SECTION_HEADER_MARKERS: tuple[str, ...] = (
        "structure & civil",
        "thermal insulation",
        "acoustic lining",
        "thermal & acoustic insulation",
        "thermal and acoustic insulation",
    )

    def __init__(self):
        self._item_counter = 0

    @classmethod
    def _is_pure_dimension_material(cls, material_text: str) -> bool:
        """Check if material text is purely a dimension value with no material context.

        Examples of pure dimensions (REJECT):
        - "15MM"
        - "20 mm"
        - "32mm"
        - "50MM"
        - "15 mm thick" (short fragment with no material noun)

        Examples of valid materials (KEEP):
        - "15mm OD" (has qualifier "OD" — outer diameter, gives material context)
        - "15mm ID" (has qualifier "ID" — inner diameter)
        - "15mm thick insulation" (has material noun "insulation")
        - "20mm dia pipes" (has material noun "pipes")
        - "13 mm thick insulation for supply air ducts" (has material noun "insulation")
        - "15 mm thick acoustic lining" (has material noun "lining")
        """
        if not material_text:
            return False
        mat_stripped = material_text.strip()
        if not mat_stripped:
            return False
        mat_lower = mat_stripped.lower()

        # If it has a material noun, it's valid.
        if any(noun in mat_lower.split() for noun in cls._MATERIAL_NOUNS):
            return False

        # Short text (≤12 chars) that matches dimension+qualifier with no material noun
        # is a pure dimension (e.g., "15 mm thick", "20mm dia").
        # Longer texts with qualifier + additional context words are valid.
        if len(mat_stripped) <= 12 and cls._DIMENSION_WITH_QUALIFIER_RE.match(mat_stripped):
            return True

        # If it has a dimension qualifier (OD, ID, thick, dia) with other context, it's valid.
        if cls._DIMENSION_WITH_QUALIFIER_RE.match(mat_stripped):
            return False

        # Must match pure-dimension pattern (number + unit, nothing else).
        return bool(cls._PURE_DIMENSION_RE.match(mat_stripped))

    @classmethod
    def _is_spec_paragraph(cls, material_text: str) -> bool:
        if not material_text or len(material_text) < 100:
            return False
        lower = material_text.lower()
        keyword_count = sum(1 for kw in cls._SPEC_KEYWORDS if kw in lower)
        return keyword_count >= 3

    @classmethod
    def _is_section_header(cls, material_text: str) -> bool:
        if not material_text:
            return False
        # Exact match only: a bare header row ("Structure & civil", "THERMAL
        # INSULATION") has nothing else in its cell. `startswith` used to also
        # match here, but that wrongly caught real rows whose text happens to
        # *open* with the same phrase before continuing into a full
        # description + quantity (e.g. 07_grew's "ACOUSTIC LINING Supply,
        # Installation and Testing of..." merged PDF cell, qty=500 sqm).
        lower = material_text.lower().strip()
        return any(marker == lower for marker in cls._SECTION_HEADER_MARKERS)

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

        # Merge adjacent MATERIAL fragments (common failure on real PDF text / OCR / NER on unseen tenders).
        # If two MATERIALs are consecutive in text with no QUANTITY/UNIT between and small gap, glue them.
        # This directly improves BOQ correctness on new RFQs the user keeps (e.g., "orcement steel" type splits seen in harness on bridge).
        material_entities = self._merge_material_fragments(material_entities, entities)

        # Filter out pure-dimension materials (e.g., "15MM", "20 mm thick") that have no material noun.
        # These are column headers or dimension specifications, not actual materials.
        material_entities = [e for e in material_entities if not self._is_pure_dimension_material(e.text)]

        # Filter out spec paragraphs (long text with specification language).
        material_entities = [e for e in material_entities if not self._is_spec_paragraph(e.text)]

        # Filter out section headers (short labels that are not actual materials).
        material_entities = [e for e in material_entities if not self._is_section_header(e.text)]

        for material in material_entities:
            row = self._build_boq_row(material, entities, relations, text, pages or [material.page or 1])
            if row:
                rows.append(row)

        # Do not emit placeholder empty rows. If no valid MATERIALs were found,
        # return empty list so callers (pipeline, exporters) can handle gracefully.
        # This prevents junk " | 0 no." rows on difficult PDFs (seen on unseen bridge tenders).
        for idx, row in enumerate(rows, start=1):
            row.item_no = idx

        return rows

    def _merge_material_fragments(
        self, materials: list[EntitySpan], all_entities: list[EntitySpan]
    ) -> list[EntitySpan]:
        """Merge adjacent MATERIAL entities if no qty/unit between and small text gap.

        Addresses common NER fragmentation on real PDF tender text (seen in harness on unseen bridge: "orcement steel", "tressed steel s", etc.).
        General fix — improves BOQ material correctness on any new RFQ without special-casing.
        """
        if not materials:
            return []
        sorted_mats = sorted(materials, key=lambda e: e.start)
        merged: list[EntitySpan] = []
        current = sorted_mats[0]
        for nxt in sorted_mats[1:]:
            # small gap (token/OCR tolerance)
            if nxt.start > current.end + 5:
                merged.append(current)
                current = nxt
                continue
            # anything qty or unit between them?
            between = [
                e
                for e in all_entities
                if current.end < e.start < nxt.start and e.type in (EntityType.QUANTITY, EntityType.UNIT)
            ]
            if between:
                merged.append(current)
                current = nxt
                continue
            # glue
            current = EntitySpan(
                text=current.text + " " + nxt.text,
                type=current.type,
                start=current.start,
                end=nxt.end,
                page=current.page,
                conf=(current.conf + nxt.conf) / 2,
                source=current.source,
            )
        merged.append(current)
        return merged

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

        row_confidence = self._compute_row_confidence(material, quantity, unit)
        warnings: list[str] = []
        flags: list = []
        flags_mod = _flag_module()
        if row_confidence < 0.7:
            warnings.append("LOW_CONFIDENCE")
            flags.append(flags_mod.low_confidence_flag(1, row_confidence))
        if quantity is None or (quantity.text or "").strip() in ("", "0"):
            flags.append(flags_mod.quantity_missing_flag(1))
        if unit is not None:
            norm = _UNIT_NORMALIZER.normalize(unit.text)
            if norm.is_unknown and not norm.is_ambiguous:
                flags.append(flags_mod.unknown_unit_flag(unit.text, 1))
            elif norm.is_ambiguous:
                flags.append(flags_mod.ambiguous_unit_flag(unit.text, 1))

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
            confidence=row_confidence,
            description_raw=description,
            source_pages=page_list[:1],
            warnings=warnings,
            flags=flags,
        )

    def _find_related(
        self,
        entities: list[EntitySpan],
        anchor: EntitySpan | None,
        target_type: EntityType,
        relations: list[Relation] | None = None,
        max_char_distance: int = 200,
    ) -> EntitySpan | None:
        candidates = [e for e in entities if e.type == target_type]
        if not candidates:
            return None

        relation_match = self._find_by_relation(entities, anchor, target_type, relations or [])
        if relation_match:
            return relation_match

        if anchor is None:
            return None

        # For quantities, strongly prefer candidates *after* the anchor.
        # If any after-candidate exists, ignore before-candidates entirely.
        # This fixes leakage where a nearby earlier qty (e.g. from prev line)
        # beats the correct later qty by raw char distance.
        has_after = target_type == EntityType.QUANTITY and any(c.start >= anchor.end for c in candidates)

        best: EntitySpan | None = None
        best_score: tuple[float, int, int] = (float("inf"), 999999, 999999)
        for candidate in candidates:
            contained_dims = self._get_contained_in_dimension(candidate, entities)
            if contained_dims:
                continue
            if target_type == EntityType.UNIT and self._is_contextual_noise(candidate):
                continue
            if has_after and candidate.start < anchor.end:
                continue

            score = self._proximity_score(anchor, candidate, entities)
            # Only consider candidates within reasonable distance
            if score[0] <= max_char_distance and score < best_score:
                best_score = score
                best = candidate
        return best

    @staticmethod
    def _get_contained_in_dimension(entity: EntitySpan, entities: list[EntitySpan]) -> list[EntitySpan]:
        result: list[EntitySpan] = []
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
            "department",
            "item",
            "from",
            "payment",
            "conform",
            "submitted",
            "not",
            "aluminum",
            "a5luminum",
            "box",
            "plate",
        }
        text_lower = entity.text.lower().strip()
        return text_lower in noise_units

    @staticmethod
    def _normalize_unit(unit_str: str, material_text: str) -> str:
        """Resolve conflicting unit signals per row using material context.

        P3_04: this is the "tie-breaker" the spec refers to in §9 gotcha.
        It sits ABOVE the canonical ``UnitNormalizer`` (which is the only
        function that knows how to turn a raw unit string into a canonical
        symbol).  Algorithm:

        1. ``canonical`` = the raw unit run through UnitNormalizer.
        2. Material-context rules decide which canonical is the FINAL
           per-row unit (e.g. concrete + length-canonical → cum).
        3. If no material rule fires, the canonical from step 1 is used.

        This is the contract the spec calls out: the normalizer
        "slots UNDER" this method, not replacing its resolution logic.
        """
        # Step 1: normalize the raw unit via the canonical normalizer.
        # P3_04 typed normalizer (with dimension + is_unknown + is_ambiguous).
        norm = _UNIT_NORMALIZER.normalize(unit_str)
        u = norm.canonical or ""
        # Keep the original raw text for keyword matching (e.g. "Nos" must
        # match the count-keyword set even after canonicalizing to "nos").
        u_raw = unit_str.lower().strip() if isinstance(unit_str, str) else ""

        material_lower = material_text.lower() if isinstance(material_text, str) else ""

        concrete_keywords = {"concrete", "cement", "mortar", "grout", "screed"}
        surface_keywords = {
            "plaster",
            "painting",
            "pointing",
            "finishing",
            "tiling",
            "flooring",
            "granite",
            "marble",
            "tile",
            "plywood",
            "glass",
            "board",
            "panel",
            "insulation",
            "waterproofing",
            "coating",
            "wool",
            "mattress",
            "mattresses",
            "sheet",
            "aluminum",
            "cladding",
        }
        steel_keywords = {"steel", "rebar", "tmt", "tor", "ms rod", " HYSD", "fe550", "fe415"}
        aggregate_keywords = {"aggregate", "sand", "crusher"}
        pipe_keywords = {"pipe", "ci pipe", "di pipe", "pvc pipe", "cpvc pipe", "gi pipe", "conduit", "junction box"}
        cable_keywords = {"cable", "wire", "conductor"}
        paint_keywords = {"paint", "primer", "emulsion", "enamel", "distemper"}
        brick_keywords = {"brick", "block", "paver"}

        if any(k in material_lower for k in concrete_keywords):
            # Length canonicals → cum for concrete (volume).
            if u == "rmt" or u == "m" or u_raw in {"rm", "r.m", "running meter", "l.m", "m", "meters", "rmt"}:
                return "cum"
            if u == "kg" or u_raw in {"kg", "kilogram", "kgs"}:
                return u
            if u == "nos" or u_raw in {"nos", "no", "nos.", "no.", "piece", "bars", "rods"}:
                return u
            if u == "bag" or u_raw in {"bags", "bag"}:
                return u  # e.g., cement bags — keep as detected
            return "cum"

        if any(k in material_lower for k in surface_keywords):
            # Ambiguous case: "insulated pipe/piping" can be either surface insulation
            # (area unit) or insulated pipe supply (length unit). Use the source unit
            # as a tie-breaker when both surface and pipe keywords are present.
            if any(k in material_lower for k in pipe_keywords) and (
                u == "rmt"
                or u_raw in {"rm", "r.m", "running meter", "running metre", "l.m", "rmt", "rmt.", "m", "meters"}
            ):
                return "rmt"
            if u == "nos" or u_raw in {"nos", "no", "nos.", "no.", "piece", "pieces", "ea", "each"}:
                return "nos"
            if u == "rmt" or u_raw in {"rm", "r.m", "meters", "m", "rmt"}:
                return "sqm"
            if u_raw in {"mm", "cm", "m³", "cum", "cbm"}:
                return "sqm"
            return "sqm"

        if any(k in material_lower for k in steel_keywords) and (
            u == "nos" or u_raw in {"nos", "no", "nos.", "no.", "piece", "pieces", "bars", "rod"}
        ):
            return "kg"

        if any(k in material_lower for k in aggregate_keywords):
            if u == "rmt" or u_raw in {"rm", "r.m", "meters"}:
                return "cum"
            if u == "mt" or u_raw in {"ton", "tonne", "mt"}:
                return "cum"
            if u == "nos" or u_raw in {"nos", "no", "nos.", "no.", "piece"}:
                return "nos"
            if u == "rmt" or u_raw in {"rm", "r.m", "running meter", "running metre", "l.m", "rmt"}:
                return "rmt"
            return "rmt"

        if any(k in material_lower for k in pipe_keywords):
            if u == "nos" or u_raw in {"nos", "no", "nos.", "no.", "piece"}:
                return "nos"
            if u == "rmt" or u_raw in {"rm", "r.m", "running meter", "running metre", "l.m", "rmt"}:
                return "rmt"
            return "rmt"

        if any(k in material_lower for k in cable_keywords):
            if u == "nos" or u_raw in {"nos", "no", "roll", "coil"}:
                return "nos"
            if u == "rmt" or u_raw in {"rm", "r.m", "running meter", "running metre", "rmt"}:
                return "rmt"

        if any(k in material_lower for k in paint_keywords):
            if u_raw in {"nos", "no", "can", "tin", "litre", "liter", "ltr"}:
                return "ltr"
            if u == "kg" or u_raw in {"kg", "kgs"}:
                return "ltr"

        if any(k in material_lower for k in brick_keywords) and (u == "nos" or u_raw in {"nos", "no", "piece"}):
            return "nos"

        # Fallback: use the canonical from step 1.  If it was unknown,
        # keep the unknown string so downstream flag-emission can pick
        # it up (R1: flag, never silently coerce to "no.").
        return u if u else "no."

    @staticmethod
    def _compute_row_confidence(
        material: EntitySpan,
        quantity: EntitySpan | None,
        unit: EntitySpan | None,
    ) -> float:
        """Compute row-level confidence based on presence/quality of core fields.

        Tiers:
        - 1.0: material + quantity + explicit unit all present and non-ambiguous
        - 0.7: material + quantity present but unit was defaulted/guessed
        - 0.5: quantity missing or zero; unit present
        - 0.3: material is very short (likely a label) and no quantity
        """
        has_material = bool(material.text.strip())
        has_quantity = quantity is not None and quantity.text.strip() not in ("", "0")
        has_unit = unit is not None

        if not has_material:
            return 0.1

        # Very short material labels with no quantity — likely dimension headers slipping through
        if len(material.text.strip()) <= 4 and not has_quantity:
            return 0.3

        if has_material and has_quantity and has_unit and quantity is not None:
            # Weight by NER confidence of material + quantity
            raw = (material.conf + quantity.conf) / 2
            # Clamp to [0.7, 1.0] — all 3 fields present guarantees at least 0.7
            return round(max(0.7, min(1.0, raw)), 2)

        if has_material and has_quantity and not has_unit and quantity is not None:
            # Quantity present but unit was defaulted — slightly reduced
            raw = (material.conf + quantity.conf) / 2
            return round(max(0.5, min(0.69, raw)), 2)

        if has_material and not has_quantity:
            # Quantity missing — flag for review
            return round(max(0.3, min(0.49, material.conf * 0.6)), 2)

        return round(material.conf * 0.5, 2)

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

        result: list[BoqRow] = []
        for items in seen.values():
            if len(items) == 1:
                result.append(items[0])
            else:
                first = items[0]
                from decimal import Decimal

                total_qty = sum((item.quantity for item in items), Decimal("0"))
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
