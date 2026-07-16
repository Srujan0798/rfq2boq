"""Unit tests for src/ingest/xlsx_hierarchy.py.

Covers:
- Item-number parsing (e.g. "11.1.1" -> parents)
- Parent chain construction
- Sibling ordering under a common parent
- Malformed-numbering tolerance
- Multi-line-wrap assembly (XLSX path: merged-cell + wrapped description)

These tests are the regression lock for P3_03's hierarchy + wrap handling.
"""

from __future__ import annotations

from src.ingest.xlsx_hierarchy import (
    ParsedNumber,
    apply_parent_context,
    assemble_wrapped_description,
    build_hierarchy,
    parent_chain,
    parse_item_number,
)

# ----------------------------------------------------------------------
# parse_item_number
# ----------------------------------------------------------------------


def test_parse_item_number_top_level() -> None:
    """Top-level item (no dots) -> level 1, no parents."""
    p = parse_item_number("11")
    assert p == ParsedNumber(parts=(11,), parent_parts=(), display="11", level=1)
    assert str(p) == "11"
    assert p.level == 1
    assert p.parents == ()


def test_parse_item_number_two_levels() -> None:
    """Two-level item (11.1) -> level 2, one parent (11)."""
    p = parse_item_number("11.1")
    assert p.parts == (11, 1)
    assert p.parents == (11,)
    assert p.display == "11.1"
    assert p.level == 2


def test_parse_item_number_three_levels() -> None:
    """Three-level item (11.1.1) -> level 3, parts (11, 1, 1)."""
    p = parse_item_number("11.1.1")
    assert p.parts == (11, 1, 1)
    assert p.display == "11.1.1"
    assert p.level == 3


def test_parse_item_number_with_whitespace() -> None:
    """Whitespace is stripped before parsing."""
    p = parse_item_number("  11.1  ")
    assert p.parts == (11, 1)


# ----------------------------------------------------------------------
# parent_chain
# ----------------------------------------------------------------------


def test_parent_chain_for_three_levels() -> None:
    """parent_chain('11.1.1') -> ['11', '11.1']."""
    assert parent_chain("11.1.1") == ["11", "11.1"]


def test_parent_chain_for_top_level() -> None:
    """Top-level item has no parents -> empty chain."""
    assert parent_chain("11") == []


def test_parent_chain_for_two_levels() -> None:
    """Two-level item has one parent."""
    assert parent_chain("11.1") == ["11"]


def test_parent_chain_for_malformed_is_empty() -> None:
    """Malformed numbers (non-numeric) return empty parent chain.

    The hierarchy module must not crash on bad input -- it must treat
    malformed numbers as leaf nodes (no parents).
    """
    assert parent_chain("abc") == []
    assert parent_chain("11.x") == []
    assert parent_chain("") == []


# ----------------------------------------------------------------------
# Sibling ordering
# ----------------------------------------------------------------------


def test_sibling_ordering_under_parent() -> None:
    """build_hierarchy sorts siblings by their integer parts under a parent."""
    rows = [
        {"item_no_raw": "11.3", "material": "C"},
        {"item_no_raw": "11.1", "material": "A"},
        {"item_no_raw": "11.2", "material": "B"},
    ]
    result = build_hierarchy(rows)
    siblings = [r for r in result if r["item_no_raw"].startswith("11.")]
    assert [r["material"] for r in siblings] == ["A", "B", "C"]


def test_sibling_ordering_preserves_insertion_for_malformed() -> None:
    """Malformed items are sorted AFTER all valid items, keeping their relative order."""
    rows = [
        {"item_no_raw": "11.1", "material": "A"},
        {"item_no_raw": "bad", "material": "BAD1"},
        {"item_no_raw": "11.2", "material": "B"},
        {"item_no_raw": "weird", "material": "BAD2"},
    ]
    result = build_hierarchy(rows)
    materials = [r["material"] for r in result]
    # Valid items first (sorted by parts); malformed items last (insertion order).
    assert materials == ["A", "B", "BAD1", "BAD2"]


# ----------------------------------------------------------------------
# apply_parent_context
# ----------------------------------------------------------------------


def test_apply_parent_context_basic() -> None:
    """Children carry their parent's description chain in parent_context."""
    items = [
        {"item_no_raw": "11", "material": "Thermal Insulation", "parent_context": []},
        {"item_no_raw": "11.1", "material": "50mm pipe", "parent_context": []},
        {"item_no_raw": "11.2", "material": "32mm pipe", "parent_context": []},
    ]
    result = apply_parent_context(items)
    by_no = {r["item_no_raw"]: r for r in result}
    # Parent carries its own material (no inherited parent)
    assert by_no["11"]["parent_context"] == ["Thermal Insulation"]
    # Children carry parent description first
    assert by_no["11.1"]["parent_context"] == ["Thermal Insulation", "50mm pipe"]
    assert by_no["11.2"]["parent_context"] == ["Thermal Insulation", "32mm pipe"]


def test_apply_parent_context_three_levels() -> None:
    """Three-level items carry the full ancestor chain."""
    items = [
        {"item_no_raw": "11", "material": "Thermal Insulation", "parent_context": []},
        {"item_no_raw": "11.1", "material": "Ducts", "parent_context": []},
        {"item_no_raw": "11.1.1", "material": "50mm duct", "parent_context": []},
    ]
    result = apply_parent_context(items)
    by_no = {r["item_no_raw"]: r for r in result}
    assert by_no["11.1.1"]["parent_context"] == [
        "Thermal Insulation",
        "Ducts",
        "50mm duct",
    ]


def test_apply_parent_context_malformed_no_inheritance() -> None:
    """Malformed items get no parent context (treated as orphans)."""
    items = [
        {"item_no_raw": "11", "material": "Thermal Insulation", "parent_context": []},
        {"item_no_raw": "bad", "material": "Some text", "parent_context": []},
    ]
    result = apply_parent_context(items)
    by_no = {r["item_no_raw"]: r for r in result}
    assert by_no["bad"]["parent_context"] == ["Some text"]


def test_apply_parent_context_does_not_merge_rows() -> None:
    """apply_parent_context MUST NOT merge or drop rows (R1)."""
    items = [
        {"item_no_raw": "11", "material": "Parent", "parent_context": []},
        {"item_no_raw": "11.1", "material": "Child", "parent_context": []},
        {"item_no_raw": "11.2", "material": "Sibling", "parent_context": []},
    ]
    result = apply_parent_context(items)
    assert len(result) == 3  # no rows merged
    assert {r["item_no_raw"] for r in result} == {"11", "11.1", "11.2"}


# ----------------------------------------------------------------------
# assemble_wrapped_description (multi-line / merged-cell)
# ----------------------------------------------------------------------


def test_assemble_wrapped_description_simple() -> None:
    """Consecutive wrapped rows below an item-numbered row are assembled."""
    rows = [
        ["11.1", "Pipe insulation"],
        [None, "50mm thick with aluminium foil facing"],
        [None, "Class O fire rating"],
        ["11.2", "Duct insulation"],
        [None, "25mm thick closed cell"],
    ]
    assembled = assemble_wrapped_description(rows)
    # First item gets its 2 wrapped continuation rows merged into one description
    assert assembled[0] == ["11.1", "Pipe insulation 50mm thick with aluminium foil facing Class O fire rating"]
    assert assembled[1] == ["11.2", "Duct insulation 25mm thick closed cell"]


def test_assemble_wrapped_description_no_item_number_no_assembly() -> None:
    """Rows without an item number are returned as-is (no assembly)."""
    rows = [
        ["Some", "Text"],
        ["Other", "Things"],
    ]
    assembled = assemble_wrapped_description(rows)
    assert assembled == rows


def test_assemble_wrapped_description_preserves_count() -> None:
    """Wrapped assembly MUST NOT add or drop rows (R1)."""
    rows = [
        ["11.1", "Parent"],
        [None, "Continuation 1"],
        [None, "Continuation 2"],
        ["11.2", "Sibling"],
    ]
    assembled = assemble_wrapped_description(rows)
    assert len(assembled) == 2  # 11.1 + 11.2 (continuations merged in)
    # 4 source rows -> 2 assembled rows (2 continuations merged into 11.1)
