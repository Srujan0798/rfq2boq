"""XLSX hierarchy + multi-line-wrap handling.

P3_03 deliverable: item-number parsing with parent inheritance, plus
multi-line/merged-cell description assembly on the XLSX path.

Design:
- An item number like "11.1.1" is parsed into a list of integer parts.
- Each non-top-level row carries a ``parent_context`` list of its
  ancestor descriptions (parent first, then grandparent, etc.) so
  BOQ assembly + export display can show children in their parent's frame.
- Multi-line/merged-cell assembly joins consecutive wrapped continuation
  rows (None in the first column, non-empty in the description column)
  into a single row's description. NO rows are dropped or merged away
  (R1: every source row is preserved; this only normalizes display text).
- Both pieces are pure data transforms with no openpyxl / NER coupling,
  so they are unit-testable from synthetic inputs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ----------------------------------------------------------------------
# Item-number parsing
# ----------------------------------------------------------------------

_ITEM_NUMBER_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\s*$")


@dataclass(frozen=True)
class ParsedNumber:
    """Parsed hierarchical item number."""

    parts: tuple[int, ...]
    parent_parts: tuple[int, ...] = field(default_factory=tuple)
    display: str = ""
    level: int = 1

    @property
    def parents(self) -> tuple[int, ...]:
        """Backwards-compat alias for the immediate parent's integer parts."""
        return self.parent_parts

    def __str__(self) -> str:
        return self.display


def parse_item_number(raw: object) -> ParsedNumber | None:
    """Parse an item-number cell. Returns None if it isn't a hierarchical number.

    Examples:
        "11"     -> ParsedNumber(parts=(11,), parent_parts=(), display="11", level=1)
        "11.1"   -> ParsedNumber(parts=(11,1), parent_parts=(11,), display="11.1", level=2)
        "11.1.1" -> ParsedNumber(parts=(11,1,1), parent_parts=(11,1), display="11.1.1", level=3)
        "abc"    -> None
        ""       -> None
    """
    if raw is None:
        return None
    s = str(raw).strip()
    m = _ITEM_NUMBER_RE.match(s)
    if not m:
        return None
    parts_str = m.group(1)
    parts = tuple(int(p) for p in parts_str.split("."))
    display = parts_str
    level = len(parts)
    parent_parts = parts[:-1] if level > 1 else ()
    return ParsedNumber(parts=parts, parent_parts=parent_parts, display=display, level=level)


def _int_pow10(parts: tuple[int, ...]) -> int:
    """Encode a parts tuple as a sortable integer key.

    Each level is encoded in 8 digits to keep collisions impossible in real
    construction tenders (max ~100 items per parent, max ~6 levels).
    """
    out = 0
    for p in parts:
        out = out * 100 + p
    return out


def parent_chain(raw: object) -> list[str]:
    """Return the chain of parent displays for a given item number.

    Examples:
        parent_chain("11.1.1") -> ["11", "11.1"]
        parent_chain("11.1")   -> ["11"]
        parent_chain("11")     -> []
        parent_chain("bad")    -> []
    """
    parsed = parse_item_number(raw)
    if parsed is None:
        return []
    if parsed.level <= 1:
        return []
    chain: list[str] = []
    for cut in range(1, parsed.level):
        chain.append(".".join(str(p) for p in parsed.parts[:cut]))
    return chain


def is_item_number(raw: object) -> bool:
    """True if the cell looks like a hierarchical item number."""
    return parse_item_number(raw) is not None


# ----------------------------------------------------------------------
# Multi-line / merged-cell description assembly
# --------------------------------------------------------------------


def assemble_wrapped_description(
    rows: list[list[object] | tuple[object, ...]],
    item_col: int = 0,
    desc_col: int = 1,
) -> list[list[str]]:
    """Assemble wrapped / merged-cell descriptions under their item-numbered parent.

    A "wrapped" row is one where the item-number column is empty/None and
    the description column has text. Consecutive wrapped rows below an
    item-numbered row are joined into the parent's description.

    The total number of OUTPUT rows is less than or equal to the input
    (continuation rows are absorbed into the parent). NO rows are added
    or dropped; only continuation text is concatenated.

    Args:
        rows:    list of source rows (each may be list or tuple of cells)
        item_col: index of the item-number column (default 0)
        desc_col: index of the description column (default 1)

    Returns:
        list of [item_no_str, description_str] rows; description rows
        have the item_no cell from the parent.
    """
    if not rows:
        return []

    out: list[list[str]] = []
    for row in rows:
        cells = [("" if c is None else str(c)) for c in row]
        if item_col >= len(cells):
            out.append([cells[0] if cells else "", ""])
            continue
        item_val = cells[item_col].strip() if cells[item_col] else ""
        if item_val:
            # Item-numbered parent row: start a new entry
            desc = cells[desc_col] if desc_col < len(cells) else ""
            out.append([item_val, desc.strip()])
        else:
            # Continuation row: append to the previous entry's description
            if not out:
                # Stray continuation at the top of the file: keep as-is with
                # an empty item number so no data is lost.
                desc = cells[desc_col] if desc_col < len(cells) else ""
                out.append(["", desc.strip()])
            else:
                desc = cells[desc_col] if desc_col < len(cells) else ""
                if desc and desc.strip():
                    sep = "" if out[-1][1].endswith((" ", "\n")) or not out[-1][1] else " "
                    out[-1][1] = (out[-1][1] + sep + desc.strip()).strip()
    return out


# ----------------------------------------------------------------------
# Parent context (hierarchy inheritance)
# --------------------------------------------------------------------


def apply_parent_context(
    items: list[dict],
    item_no_key: str = "item_no_raw",
    material_key: str = "material",
    context_key: str = "parent_context",
) -> list[dict]:
    """Mutate each item in place: set ``parent_context`` to the ancestor chain.

    For each item with a parseable item number, ``parent_context`` is set
    to a list of descriptions, ordered from outermost parent to the item
    itself. For top-level items, the list is just the item's own material.
    For malformed / unparseable item numbers, ``parent_context`` is set to
    just the item's own material (orphan node, no parents).

    No rows are merged, dropped, or reordered (R1: every source row
    remains in the output).

    Returns the same list reference (mutated in place for convenience).
    """
    by_no: dict[str, str] = {}
    for it in items:
        no = str(it.get(item_no_key, "")).strip()
        if is_item_number(no):
            by_no[no] = str(it.get(material_key, "")).strip()

    for it in items:
        no = str(it.get(item_no_key, "")).strip()
        own_material = str(it.get(material_key, "")).strip()
        chain = parent_chain(no)
        ctx: list[str] = []
        for ancestor in chain:
            anc_mat = by_no.get(ancestor, "").strip()
            if anc_mat:
                ctx.append(anc_mat)
        ctx.append(own_material)
        it[context_key] = ctx
    return items


def build_hierarchy(
    items: list[dict],
    item_no_key: str = "item_no_raw",
) -> list[dict]:
    """Sort items by item number (with malformed items stable at the end).

    Sibling order under the same parent is preserved by their integer parts
    (e.g. 11.1, 11.2, 11.10 sort correctly by the integer value of the leaf
    part, not lexicographically). Malformed items keep their original
    insertion order.

    No rows are dropped or merged. Returns a new list.
    """
    indexed: list[tuple[int, int, dict]] = []
    malformed_count = 0
    for _idx, it in enumerate(items):
        no = it.get(item_no_key, "")
        parsed = parse_item_number(no)
        if parsed is None:
            indexed.append((1, malformed_count, it))
            malformed_count += 1
        else:
            indexed.append((0, _int_pow10(parsed.parts), it))
    # sort: parseable first (0 before 1), then by sort key
    indexed.sort(key=lambda t: (t[0], t[1]))
    return [t[2] for t in indexed]
