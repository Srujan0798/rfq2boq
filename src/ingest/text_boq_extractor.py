"""Text BOQ Extractor — extracts BOQ items from raw text when tables are not available.

Handles common construction tender text formats:
- Numbered lists with quantity + unit
- Tabular text (space-aligned columns)
- Bullet points with specs
- Multi-line items with dimensions/grades
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from src.rules.units import normalize_unit


@dataclass(slots=True)
class TextBoqItem:
    material: str
    quantity: Decimal
    unit: str
    grade: str = ""
    dimension: str = ""
    standard: str = ""
    action: str = "supply"
    confidence: float = 0.75


_QUANTITY_RE = re.compile(
    r"(?<![\w.])"  # negative lookbehind: not preceded by word char or dot
    r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?![\w.])"  # negative lookahead: not followed by word char or dot
)

# Common unit tokens that appear after quantities
_UNIT_RE = re.compile(
    r"\b(nos\.?|no\.?|nr|ea|each|pcs?|kg|kgs|mt|tons?|tonnes?|"
    r"cum|cu\.m|cbm|m³|sqm|sq\.m|sft|sqft|sq\s*ft|m²|"
    r"rm|r\.m|l\.m|lm|rmt|running\s*m(?:et)?re|m|"
    r"ltr|liters?|litres?|set|sets|bag|bags|roll|rolls|coil|"
    r"pair|pairs|pr|box|boxes|can|cans|hr|hours?|day|days?)\b",
    re.IGNORECASE,
)

# Action keywords at start of description
_ACTION_RE = re.compile(
    r"^(supply|install|provide|lay|erect|apply|fix|construct|build|pour|cast|"
    r"fabricate|execution|carrying\s+out|performing)\b",
    re.IGNORECASE,
)

# Standard codes
_STANDARD_RE = re.compile(r"\b(IS\s*\d+(?::\d+)?|ASTM\s+[A-Z]\d+|BS\s*EN\s*\d+|EN\s*\d+|ACI\s*\d+)\b", re.IGNORECASE)

# Grade codes
_GRADE_RE = re.compile(r"\b(M\d{1,2}|Fe\d{3}|Grade\s+[A-Z]|Class\s+[A-Z]|OPC\s*\d{2}|Type\s*[A-Z])\b", re.IGNORECASE)

# Dimension patterns
_DIM_RE = re.compile(
    r"\b(\d{2,}(?:\.\d+)?\s*mm(?:\s*(?:dia|thick|width|height|depth|length))?|"
    r"\d{2,}(?:\.\d+)?\s*cm|"
    r"\d+(?:\.\d+)?\s*m(?:\s*(?:long|wide|high|dia))?|"
    r"Ø\s*\d+\s*mm|"
    r"\d+\s*mm\s*x\s*\d+\s*mm)\b",
    re.IGNORECASE,
)

# Item number at start of line (e.g., "1.", "1.1.", "(a)", "i.", "1)")
_ITEM_NUM_RE = re.compile(r"^(?:\d+(?:\.\d+)*[.):\-]?\s*|[a-z]\)[.:\-]?\s*|[ivx]+\.[.:\-]?\s*)")

# Bullet markers
_BULLET_RE = re.compile(r"^(?:[•\-\*\u2022\u2013\u2014]|\(\d+\)|\d+\.)\s*")

# Section headers to skip
_HEADER_RE = re.compile(
    r"^(schedule|section|part|note|specification|general|scope|"
    r"boq|bill of quantities|bill of quantity|summary|total|grand total|"
    r"terms and conditions|technical specification|commercial terms|"
    r"annexure|appendix|reference|drawing)\b",
    re.IGNORECASE,
)

_JUNK_PHRASES = [
    "shall be",
    "to be",
    "as per",
    "in accordance with",
    "compliance to",
    "contractor shall",
    "bidder shall",
    "tenderer shall",
    "vendor shall",
    "the successful bidder",
    "the contractor",
    "all works",
    "all materials",
    "inspection and testing",
    "quality assurance",
    "safety measures",
    "method statement",
    "program of works",
    "site clearance",
]


class TextBoqExtractor:
    """Extract BOQ items from unstructured text."""

    def extract(self, text: str) -> list[TextBoqItem]:
        """Extract BOQ items from raw text."""
        lines = text.splitlines()
        items: list[TextBoqItem] = []
        pending_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped or len(stripped) < 5:
                continue
            if self._is_header(stripped):
                continue
            if self._is_junk(stripped):
                continue

            # Try to extract item from this line
            item = self._parse_line(stripped)
            if item:
                # If we have pending lines, prepend them as context
                if pending_lines:
                    context = " ".join(pending_lines)
                    if len(context) < 200:
                        item.material = f"{context} {item.material}"
                    pending_lines = []
                items.append(item)
            else:
                # Could be a continuation line or section header
                if self._looks_like_continuation(stripped):
                    pending_lines.append(stripped)
                else:
                    pending_lines = []

        return items

    def _is_header(self, line: str) -> bool:
        return bool(_HEADER_RE.search(line[:80])) or line.isupper() and len(line) < 60

    def _is_junk(self, line: str) -> bool:
        lower = line.lower()
        return any(p in lower for p in _JUNK_PHRASES) and not _QUANTITY_RE.search(line)

    def _looks_like_continuation(self, line: str) -> bool:
        """A continuation line has no quantity/unit but descriptive text."""
        if _QUANTITY_RE.search(line) and _UNIT_RE.search(line):
            return False
        if _ITEM_NUM_RE.match(line):
            return False
        # Has dimension or grade but no qty = likely continuation
        if _DIM_RE.search(line) or _GRADE_RE.search(line):
            return True
        return len(line) > 20 and not line[0].isdigit()

    def _parse_line(self, line: str) -> TextBoqItem | None:
        """Try to parse a single line as a BOQ item."""
        # Remove item number prefix
        clean = _ITEM_NUM_RE.sub("", line).strip()
        clean = _BULLET_RE.sub("", clean).strip()
        if not clean:
            return None

        # Find all quantities in the line
        qty_matches = list(_QUANTITY_RE.finditer(clean))
        if not qty_matches:
            return None

        # Find all units in the line
        unit_matches = list(_UNIT_RE.finditer(clean))

        # Strategy: find the RIGHTMOST quantity+unit pair (closest to end of line)
        # This handles "material ... qty unit" format
        best_qty: Decimal | None = None
        best_unit: str = ""
        best_qty_end: int = 0

        for um in unit_matches:
            # Find the nearest quantity before this unit
            nearest_qty = None
            nearest_dist = float("inf")
            for qm in qty_matches:
                if qm.end() <= um.start():
                    dist = um.start() - qm.end()
                    if dist < nearest_dist and dist < 20:  # max 20 chars between qty and unit
                        nearest_dist = dist
                        nearest_qty = qm
            if nearest_qty:
                qty_val = self._parse_qty(nearest_qty.group(1))
                if qty_val > 0 and (best_qty is None or nearest_qty.start() > best_qty_end):
                    best_qty = qty_val
                    best_unit = um.group(0).lower()
                    best_qty_end = nearest_qty.end()

        # If no unit found, take the last quantity and default unit
        if best_qty is None and qty_matches:
            last_qty = qty_matches[-1]
            best_qty = self._parse_qty(last_qty.group(1))
            best_unit = "no."
            best_qty_end = last_qty.end()

        if best_qty is None or best_qty <= 0:
            return None

        # Material is everything before the quantity (or before the last qty if no unit)
        material_end = best_qty_end
        # If there's a unit, material ends before the quantity
        if unit_matches and best_unit:
            # Find which quantity we paired with
            for qm in qty_matches:
                if qm.end() == best_qty_end:
                    material_end = qm.start()
                    break

        material = clean[:material_end].strip()
        # Remove trailing punctuation/connectors
        material = re.sub(r"[\-–—:]+$", "", material).strip()

        if len(material) < 5:
            return None

        # Extract grade, dimension, standard from material
        grade = ""
        dimension = ""
        standard = ""

        g_match = _GRADE_RE.search(material)
        if g_match:
            grade = g_match.group(0)

        d_match = _DIM_RE.search(material)
        if d_match:
            dimension = d_match.group(0)

        s_match = _STANDARD_RE.search(material)
        if s_match:
            standard = s_match.group(0)

        action = "supply"
        a_match = _ACTION_RE.search(material)
        if a_match:
            action = a_match.group(1).lower()

        normalized_unit = normalize_unit(best_unit)

        # Compute confidence
        conf = 0.75
        if best_unit and best_unit != "no.":
            conf += 0.1
        if grade or dimension or standard:
            conf += 0.05
        if len(material) > 30:
            conf += 0.05

        return TextBoqItem(
            material=material,
            quantity=best_qty,
            unit=normalized_unit,
            grade=grade,
            dimension=dimension,
            standard=standard,
            action=action,
            confidence=round(min(1.0, conf), 2),
        )

    @staticmethod
    def _parse_qty(val: str) -> Decimal:
        try:
            return Decimal(val.replace(",", "").strip())
        except (InvalidOperation, ValueError):
            return Decimal("0")
