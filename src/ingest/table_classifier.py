"""Table-type classifier for XLSX/PDF tables.

P3_03 deliverable: classify a detected table by its header shape + sample-row
content into a TableType, so the pipeline can route non-BOQ tables to a typed
document-level flag (R1-honest zero rows + flag) instead of inventing fake
BOQ rows.

Design:
- Rule-based on header shape + column content signatures
- Tolerant to header case (upper / lower / mixed) and whitespace
- Tolerant to multi-line header cells (newlines flattened to spaces)
- Conservative: when in doubt -> UNKNOWN (caller decides what to do)
- Document-level flag emission via classification_to_flag()

Real-corpus header census used to design the signatures (see P3_03 §4):
- 03_zydus BOQ            : sr. no., description, unit, quantity, remarks
- spec2__Insulation        : item, description, unit, qty., make
- 05_zydus_animal BOQ      : sr. no., description of work, units, ... qty cols ...
- 05 TDS (compliance)      : sr. no., description, unit, tender specification, vendor confirmation
- 03_zydus COMPLIANCE sheet: sr. no., description, unit, quantity, compliance, compliance
- ARFF sheet1 (make list)  : s. no., description, unit, qty, make
- ARFF sheet2 (compliance) : s. no., description, unit, qty, make, complaince
- Gopin sub-vendors        : sr. no., item, SUB VENDORS
- spec2__BOQ - Insulation  : sl.no., particulars, units, total qty, ... rate/amount
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from enum import StrEnum


class TableType(StrEnum):
    """Classified table shape. The pipeline only extracts BOQ rows.

    Non-BOQ types are flagged at document level (R1: 0 rows + typed flag)
    instead of being silently dropped or hallucinated into BOQ.
    """

    BOQ = "BOQ"
    COMPLIANCE_CHECKLIST = "COMPLIANCE_CHECKLIST"
    MAKE_LIST = "MAKE_LIST"
    VENDOR_LIST = "VENDOR_LIST"
    GENERIC_SPEC = "GENERIC_SPEC"
    UNKNOWN = "UNKNOWN"


# ----------------------------------------------------------------------
# Header normalization
# ----------------------------------------------------------------------

_WS_RE = re.compile(r"\s+", re.MULTILINE)


def _normalize_header(raw: Iterable[object]) -> list[str]:
    """Lowercase, strip whitespace, flatten newlines to spaces."""
    out: list[str] = []
    for cell in raw:
        if cell is None:
            out.append("")
            continue
        s = str(cell).replace("\n", " ").replace("\r", " ")
        s = _WS_RE.sub(" ", s).strip().lower()
        out.append(s)
    return out


def _has_token(header_lower: list[str], token: str) -> bool:
    return any(token in h for h in header_lower)


def _count_containing(header_lower: list[str], token: str) -> int:
    return sum(1 for h in header_lower if token in h)


# ----------------------------------------------------------------------
# Signature detection
# ----------------------------------------------------------------------

# Compliance-checklist signature: must have all three of these signals
# (sl.no. variant + specification column + reply/confirm column).
_CHECKLIST_SPEC_TOKENS = ("specification", "tce spec", "spec ")
_CHECKLIST_REPLY_TOKENS = (
    "bidder reply",
    "vendor confirmation",
    "vendor confirm",
    "vendor reply",
    "compliance",
    "reply",
    "deviations",
    "complaince",
)
_CHECKLIST_SLNO_TOKENS = (
    "sl.no",
    "sl. no",
    "s.no",
    "s. no",
    "sr. no",
    "sr no",
    "item no",
    "row no",
    "sno",
    "s.no.",
)


def _has_serial_token(header_lower: list[str]) -> bool:
    """True if any header cell indicates a row-number / item-number column.

    Catches the corpus's most common patterns (sl.no, s.no, sr.no, item,
    sno, item no, row no). Uses exact-cell match for ambiguous short tokens
    so "item" alone is a serial column but "item description" is not.
    """
    for h in header_lower:
        h_strip = h.strip().rstrip(".")
        if any(tok in h for tok in _CHECKLIST_SLNO_TOKENS):
            return True
        if h_strip in ("item", "sno", "no", "no.", "sl no", "row", "index"):
            return True
    return False


def _is_compliance_checklist(
    header_lower: list[str],
    sample_rows: list[list[str]] | None = None,
) -> bool:
    if len(header_lower) < 3:
        return False
    has_spec = any(any(tok in h for tok in _CHECKLIST_SPEC_TOKENS) for h in header_lower)
    has_reply = any(any(tok in h for tok in _CHECKLIST_REPLY_TOKENS) for h in header_lower)
    has_sl = _has_serial_token(header_lower)

    # If there's a "reply" column but it's mostly empty in sample data,
    # it's a BOQ with an optional tracking column, not a compliance checklist.
    if has_reply and sample_rows:
        reply_col = _find_reply_col(header_lower)
        if reply_col is not None:
            filled = sum(1 for r in sample_rows if reply_col < len(r) and r[reply_col] not in (None, "", "-", "n/a", "N/A"))
            total = sum(1 for r in sample_rows if reply_col < len(r))
            fill_ratio = filled / max(total, 1)
            if fill_ratio < 0.3:
                has_reply = False

    # The reply column doubles as the spec-confirmation side of the checklist
    if has_spec and has_reply and has_sl:
        return True
    # Some checklists use only "compliance" + serial + item columns (no
    # explicit "specification" column -- the spec is in the row text).
    # ARFF sheet2 shape: sl.no, description, unit, qty, make, complaince
    return has_reply and has_sl and any(t in header_lower for t in ("description", "particulars", "item", "details"))


# BOQ signature: sl.no variant + description/item + unit + (quantity or qty)
# plus at least one numeric column. This is the dominant shape across the
# corpus (03_zydus, 05_zydus_animal, spec2__Insulation, etc.).
def _is_boq(header_lower: list[str], sample_rows: list[list[str]]) -> bool:
    if len(header_lower) < 3:
        return False
    has_sl = _has_serial_token(header_lower)
    has_desc = any(
        t in h
        for h in header_lower
        for t in ("description", "item desc", "item", "particulars", "scope of work", "description of work")
    )
    has_unit = any(t in h for h in header_lower for t in ("unit", "units", "uom", "measure"))
    has_qty = any(
        t in h for h in header_lower for t in ("qty", "quantity", "total qty", "total quantity", "boq quantity")
    )

    if not (has_sl and has_desc and has_unit and has_qty):
        return False

    # Reject if the shape is also a checklist (compliance tables also have
    # unit/description/qty columns sometimes).
    if _is_compliance_checklist(header_lower):
        return False

    # Sanity: at least one sample row with a numeric qty cell.
    if sample_rows:
        qty_idx = _find_qty_col(header_lower)
        if qty_idx is not None:
            for r in sample_rows:
                if qty_idx < len(r):
                    v = r[qty_idx]
                    if v is None:
                        continue
                    s = str(v).strip().replace(",", "")
                    if s and s not in ("-", "n/a", "na", "—") and _is_numeric(s):
                        return True
    return True  # header signature is enough; sample is bonus


def _is_numeric(s: str) -> bool:
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def _find_qty_col(header_lower: list[str]) -> int | None:
    for i, h in enumerate(header_lower):
        if "qty" in h or "quantity" in h:
            return i
    return None


def _find_reply_col(header_lower: list[str]) -> int | None:
    for i, h in enumerate(header_lower):
        if any(tok in h for tok in _CHECKLIST_REPLY_TOKENS):
            return i
    return None


# Make-list signature: serial + description + unit + qty + make/vendor column
_MAKE_TOKENS = ("make", "brand", "manufacturer")


def _find_make_col(header_lower: list[str]) -> int | None:
    for i, h in enumerate(header_lower):
        if any(tok in h for tok in _MAKE_TOKENS):
            return i
    return None


def _is_make_list(header_lower: list[str], sample_rows: list[list[str]] | None = None) -> bool:
    if len(header_lower) < 4:
        return False
    has_sl = _has_serial_token(header_lower)
    has_desc = any(t in h for h in header_lower for t in ("description", "item", "particulars"))
    has_qty = any(t in h for h in header_lower for t in ("qty", "quantity"))
    has_make = any(t in h for h in header_lower for t in _MAKE_TOKENS)
    # If the Make column is present but mostly empty in sample data, treat it as
    # a BOQ with an optional vendor tracking column, not a vendor/make list.
    if has_make and sample_rows:
        make_col = _find_make_col(header_lower)
        if make_col is not None:
            filled = sum(
                1 for r in sample_rows if make_col < len(r) and r[make_col] not in (None, "", "-", "n/a", "N/A")
            )
            total = sum(1 for r in sample_rows if make_col < len(r))
            fill_ratio = filled / max(total, 1)
            if fill_ratio < 0.3:
                has_make = False
    # Compliance signature trumps make-list
    if _is_compliance_checklist(header_lower):
        return False
    return has_sl and has_desc and has_qty and has_make


# Vendor-list signature: serial + item + sub-vendors/approved-vendor column
_VENDOR_TOKENS = ("sub vendor", "vendor", "supplier", "make ", "approved make", "oem")


def _is_vendor_list(header_lower: list[str]) -> bool:
    if len(header_lower) < 2:
        return False
    has_sl = _has_serial_token(header_lower)
    has_item = any(t in h for h in header_lower for t in ("item", "particulars", "description", "equipment"))
    has_vendor = any(t in h for h in header_lower for t in _VENDOR_TOKENS)
    # No quantity column expected
    has_qty = any(t in h for h in header_lower for t in ("qty", "quantity", "total qty"))
    return has_sl and has_item and has_vendor and not has_qty


# Generic-spec signature: 2-3 columns, no quantity, no make/vendor/serial
# column, and at least one sample row is a long descriptive paragraph.
_SPEC_PARA_MIN_LEN = 120


def _is_generic_spec(header_lower: list[str], sample_rows: list[list[str]]) -> bool:
    if not header_lower or len(header_lower) > 4:
        return False
    if _is_compliance_checklist(header_lower):
        return False
    if _is_boq(header_lower, sample_rows):
        return False
    if _is_make_list(header_lower):
        return False
    if _is_vendor_list(header_lower):
        return False
    # A serial-like column disqualifies
    if _has_serial_token(header_lower):
        return False
    if not sample_rows:
        return False
    long_count = 0
    for r in sample_rows:
        for c in r:
            if c is None:
                continue
            s = str(c).strip()
            if len(s) >= _SPEC_PARA_MIN_LEN:
                long_count += 1
                break
    return long_count >= 1


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def classify_table(
    header_row: list[str] | None,
    sample_rows: list[list[str]] | None,
) -> TableType:
    """Classify a detected table by its header + sample rows.

    Returns one of:
    - BOQ                 : line-item table with qty + unit (extract)
    - COMPLIANCE_CHECKLIST: Sl.No | Details | Specification | Bidder Reply (flag, no extract)
    - MAKE_LIST           : Sl.No | Description | Unit | Qty | Make (flag)
    - VENDOR_LIST         : Sl.No | Item | Sub-vendors (flag)
    - GENERIC_SPEC        : spec-only paragraphs (flag)
    - UNKNOWN             : ambiguous or empty (caller decides)
    """
    if not header_row:
        return TableType.UNKNOWN
    if sample_rows is None:
        sample_rows = []

    header_lower = _normalize_header(header_row)
    if not any(h for h in header_lower):
        return TableType.UNKNOWN

    # Order matters:
    # 1. compliance-checklist first (some checklists have qty/unit too)
    # 2. make-list before BOQ (a "S. No. | Desc | Unit | Qty | Make" table
    #    is a vendor/make list, not a bill of quantities)
    # 3. vendor-list before make-list (some make-lists also look like vendors)
    # 4. BOQ last among the structured types
    if _is_compliance_checklist(header_lower, sample_rows):
        return TableType.COMPLIANCE_CHECKLIST
    if _is_make_list(header_lower, sample_rows):
        return TableType.MAKE_LIST
    if _is_vendor_list(header_lower):
        return TableType.VENDOR_LIST
    if _is_boq(header_lower, sample_rows):
        return TableType.BOQ
    if _is_generic_spec(header_lower, sample_rows):
        return TableType.GENERIC_SPEC
    return TableType.UNKNOWN


def classification_to_flag(table_type: TableType) -> str | None:
    """Map a TableType to a document-level flag string.

    Returns None for BOQ (no flag needed; rows are extracted normally).
    Returns a stable, UPPER_SNAKE_CASE flag for every other type so
    downstream code (audit, exports) can surface the document kind.
    """
    if table_type == TableType.BOQ:
        return None
    return table_type.value
