"""Audit gold files and list dirty rows (headers, specs, totals).

Usage:
    python scripts/clean_gold.py
"""

import contextlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _is_valid_gold_row(row: dict) -> bool:
    """Filter out headers, specs, totals, and other non-BOQ rows from gold."""
    material = row.get("material", "")
    qty = row.get("quantity", 0)
    unit = row.get("unit", "")
    if not material or qty <= 0 or not unit:
        return False
    if len(material) > 200:
        return False
    lower = material.lower()
    if any(kw in lower for kw in ["total", "sub-total", "grand total", "sub total"]):
        return False
    if material.isupper() and len(material) < 30:
        return False
    return not lower.startswith(("note", "remark", "refer", "see"))


def load_gold_rows(gold_path: Path) -> list[dict]:
    """Load BOQ-like rows from a gold annotation file."""
    data = json.load(gold_path.open())
    rows = []
    for entity in data.get("entities", []):
        etype = entity.get("type", "")
        if etype not in ("MATERIAL", "QUANTITY", "UNIT"):
            continue
        rows.append(
            {
                "material": entity.get("text", ""),
                "quantity": 0,
                "unit": "",
                "type": etype,
            }
        )
    # Try to reconstruct BOQ rows by grouping nearby MATERIAL + QUANTITY + UNIT
    boq_rows: list[dict] = []
    current: dict = {}
    for entity in data.get("entities", []):
        etype = entity.get("type", "")
        text = entity.get("text", "")
        if etype == "MATERIAL":
            if current.get("material"):
                boq_rows.append(current)
            current = {"material": text, "quantity": 0, "unit": ""}
        elif etype == "QUANTITY" and current:
            with contextlib.suppress(ValueError, TypeError):
                current["quantity"] = float(text.replace(",", ""))
        elif etype == "UNIT" and current:
            current["unit"] = text
    if current.get("material"):
        boq_rows.append(current)
    return boq_rows


def main() -> None:
    gold_dir = Path("data/real_rfqs/gold")
    if not gold_dir.exists():
        print(f"Gold directory not found: {gold_dir}")
        return

    gold_files = sorted(gold_dir.glob("*.json"))
    print(f"Auditing {len(gold_files)} gold files...")
    print("=" * 60)

    total_clean = 0
    total_dirty = 0

    for gf in gold_files:
        rows = load_gold_rows(gf)
        clean = [r for r in rows if _is_valid_gold_row(r)]
        dirty = [r for r in rows if not _is_valid_gold_row(r)]

        total_clean += len(clean)
        total_dirty += len(dirty)

        print(f"\n{gf.name}: {len(clean)} clean / {len(dirty)} dirty / {len(rows)} total")
        if dirty:
            for d in dirty[:5]:
                mat = d.get("material", "")[:60]
                print(f"  DIRTY: {mat!r} (qty={d.get('quantity', 0)}, unit={d.get('unit', '')})")
            if len(dirty) > 5:
                print(f"  ... and {len(dirty) - 5} more dirty rows")

    print("\n" + "=" * 60)
    print(f"TOTAL: {total_clean} clean / {total_dirty} dirty / {total_clean + total_dirty} total")
    print(
        f"Removal rate: {total_dirty / (total_clean + total_dirty) * 100:.1f}%"
        if (total_clean + total_dirty) > 0
        else "No data"
    )


if __name__ == "__main__":
    main()
