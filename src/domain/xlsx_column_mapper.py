"""XLSX column mapper — infers which column is MATERIAL / QUANTITY / UNIT etc from header text + content sample."""

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


QUANTITY_NUMERIC_PATTERNS = (
    r"^\s*\d+\.?\d*\s*$",
    r"^\s*\d+/\d+\s*$",
    r"^\s*[,\d]+\s*$",
)

UNIT_PATTERNS = (
    r"\b(sqm\.?|sq\.m\.?|square\s*m(et(er|re)s?)?|m2|m²)\b",
    r"\b(running\s*m(et|re)?s?|rm|r\.?m\.?|l\.?m\.?|m(et|re)?s?)\b",
    r"\b(cum|cu\.?m\.?|cubic\s*m(et|re)?s?|m3|m³)\b",
    r"\b(kgs?|kilograms?|kg)\b",
    r"\b(nos?\.?|numbers?|pcs?\.?|pieces?)\b",
    r"\b(ltr\.?|lit(er|re)s?|litres?)\b",
    r"\b(rolls?|coils?)\b",
    r"\b(set|sets?)\b",
    r"\b(pairs?|pr\.?)\b",
    r"\b(bags?|sacks?)\b",
    r"\b(bundles?|lots?)\b",
    r"\b(box|boxes|boxful)\b",
    r"\b(can|cans|tin|tins)\b",
    r"\b(mt|metric\s*tonnes?|tonnes?)\b",
    r"\b(rmt|running\s*m(et|re)?)\b",
    r"\b(dia|Ø|diam(eter)?)\b",
    r"\b(l\s*x\s*w|lxw)\b",
)


IGNORE_PATTERNS = (
    # Note: bare "total" is NOT ignored — headers like "Total qty" are quantity cols.
    # Rate/amount totals are still ignored via rate|amount|price|cost|subtotal.
    r"\b(rate|amount|inr|price|cost|subtotal|exc|edi[st]|per\s*unit)\b",
    r"\b(s?no\.?|sr\.?|serial|item\s*no\.?|row\s*no\.?)\b",
    r"\b(remarks?|comment|note|narration|description\s*only)\b",
    r"\b(freight|tax|gst|cgst|sgst|cess)\b",
)


@dataclass
class ColumnMapping:
    material_col: int | None
    quantity_col: int | None
    unit_col: int | None
    grade_col: int | None = None
    standard_col: int | None = None
    location_col: int | None = None
    action_col: int | None = None
    dimension_col: int | None = None


class XLSXColumnMapper:
    def __init__(self):
        self._unit_patterns = [re.compile(p, re.IGNORECASE) for p in UNIT_PATTERNS]
        self._ignore_patterns = [re.compile(p, re.IGNORECASE) for p in IGNORE_PATTERNS]
        self._quantity_patterns = [re.compile(p) for p in QUANTITY_NUMERIC_PATTERNS]

    def map_columns(self, headers: list[Any], sample_rows: list[list[Any]]) -> ColumnMapping:
        n = len(headers)
        col_types: dict[int, str | None] = {i: None for i in range(n)}

        for i, header in enumerate(headers):
            h = str(header).strip() if header is not None else ""
            col_types[i] = self._classify_header(h)

        for i, header in enumerate(headers):
            if col_types[i] is None:
                h = str(header).strip() if header is not None else ""
                col_types[i] = self._classify_by_sample(
                    h, [row[i] if i < len(row) else None for row in sample_rows[:5]]
                )

        material_col = self._get_first_of(col_types, ["MATERIAL", "DESCRIPTION"])
        # If the chosen material_col is actually a SERIAL column, pick the next
        # best text column (prefer the longest average text length).
        if material_col is not None and col_types.get(material_col) == "SERIAL":
            material_col = self._pick_best_text_column(col_types, sample_rows)

        quantity_col = self._get_first_of(col_types, ["QUANTITY", "QTY"])
        unit_col = self._get_first_of(col_types, ["UNIT", "UoM"])
        grade_col = self._get_first_of(col_types, ["GRADE", "CLASS", "TYPE"])
        standard_col = self._get_first_of(col_types, ["STANDARD", "IS_CODE", "SPEC"])
        location_col = self._get_first_of(col_types, ["LOCATION", "LOCATION_DESC"])
        action_col = self._get_first_of(col_types, ["ACTION", "WORK_TYPE", "SCOPE"])
        dimension_col = self._get_first_of(col_types, ["DIMENSION", "SIZE", "THICKNESS"])

        if quantity_col is None and unit_col is not None:
            quantity_col = self._infer_quantity_near_unit(headers, sample_rows, unit_col)

        return ColumnMapping(
            material_col=material_col,
            quantity_col=quantity_col,
            unit_col=unit_col,
            grade_col=grade_col,
            standard_col=standard_col,
            location_col=location_col,
            action_col=action_col,
            dimension_col=dimension_col,
        )

    def _classify_header(self, header: str) -> str | None:
        h = header.lower().strip()
        if not h or h == "none" or h == "nan":
            return None

        for pat in self._ignore_patterns:
            if pat.search(h):
                return "IGNORE"

        if re.search(r"\b(description|item\s*desc|narr|scope|work\s*desc|material\s*desc|particulars?)\b", h):
            return "MATERIAL"
        # "Total qty" / "Total quantity" are quantity columns (not financial totals).
        if re.search(r"\btotal\s*(qty|quantity|qnty)\b", h):
            return "QUANTITY"
        if re.search(r"\b(qty|quantity|qty\.|qnty|nos?\.?|vol)\b", h) and not re.search(
            r"\b(rate|price|amount|inr)\b", h
        ):
            return "QUANTITY"
        if re.search(r"\b(units?|uom|u\.o\.m|measure)\b", h):
            return "UNIT"
        if re.search(r"\b(grade|class|type|grade/class)\b", h):
            return "GRADE"
        if re.search(r"\b(is\s*code|standard|bis|spec|standard/spec)\b", h):
            return "STANDARD"
        if re.search(r"\b(location|location\s*desc|area|floor|zone)\b", h):
            return "LOCATION"
        if re.search(r"\b(action|work\s*type|scope|activity)\b", h):
            return "ACTION"
        if re.search(r"\b(thickness|size|dim|dimension|length|breadth|width|depth)\b", h):
            return "DIMENSION"

        return None

    _ITEM_NUMBER_PATTERN = re.compile(r"^\d+(\.\d+)*$")

    def _classify_by_sample(self, header: str, samples: list[Any]) -> str | None:
        if not header or header == "None":
            numeric_count = sum(1 for s in samples if self._is_numeric(s))
            if numeric_count >= len(samples) * 0.6 and numeric_count >= 2:
                return "QUANTITY"

        non_none_samples = [s for s in samples if s is not None and str(s).strip() not in ("", "None", "nan")]
        if not non_none_samples:
            return None

        unit_matches = sum(1 for s in non_none_samples if self._matches_unit(str(s)))
        if unit_matches >= len(non_none_samples) * 0.6:
            return "UNIT"

        # Reject columns that are purely item/section numbers (11.1, 11.1.1, 8.1, etc.)
        item_number_count = sum(1 for s in non_none_samples if bool(self._ITEM_NUMBER_PATTERN.match(str(s).strip())))
        if item_number_count >= len(non_none_samples) * 0.6 and item_number_count >= 2:
            return "SERIAL"

        text_matches = sum(1 for s in non_none_samples if not self._is_numeric(s) and not self._matches_unit(str(s)))
        if text_matches >= len(non_none_samples) * 0.6 and text_matches >= 2:
            return "MATERIAL"

        return None

    def _is_numeric(self, val: Any) -> bool:
        if val is None:
            return False
        s = str(val).strip()
        if not s or s in ("None", "nan", "-"):
            return False
        for p in self._quantity_patterns:
            if p.match(s):
                return True
        try:
            float(s.replace(",", ""))
            return True
        except ValueError:
            return False

    def _matches_unit(self, text: str) -> bool:
        return any(pat.search(text) for pat in self._unit_patterns)

    def _get_first_of(self, col_types: dict[int, str | None], types: list[str]) -> int | None:
        for t in types:
            for i, ct in col_types.items():
                if ct == t:
                    return i
        return None

    def _pick_best_text_column(self, col_types: dict[int, str | None], sample_rows: list[list[Any]]) -> int | None:
        """Pick the text column with longest average content as material."""
        best_col: int | None = None
        best_avg_len = 0.0
        for i, ct in col_types.items():
            if ct in ("MATERIAL", "DESCRIPTION", None, "SERIAL"):
                samples = [row[i] if i < len(row) else None for row in sample_rows[:10]]
                texts = [str(s).strip() for s in samples if s is not None and str(s).strip() not in ("", "None", "nan")]
                if not texts:
                    continue
                avg_len = sum(len(t) for t in texts) / len(texts)
                # Strongly prefer columns with actual descriptive text over serial numbers
                desc_ratio = sum(1 for t in texts if len(t) > 10) / len(texts)
                if desc_ratio < 0.3:
                    continue
                if avg_len > best_avg_len:
                    best_avg_len = avg_len
                    best_col = i
        return best_col

    def _infer_quantity_near_unit(self, headers: list[Any], sample_rows: list[list[Any]], unit_col: int) -> int | None:
        for i in range(len(headers)):
            if i == unit_col:
                continue
            samples = [row[i] if i < len(row) else None for row in sample_rows[:5]]
            if all(self._is_numeric(s) for s in samples if s is not None):
                return i
        return None
