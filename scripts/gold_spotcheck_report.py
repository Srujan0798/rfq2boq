#!/usr/bin/env python3
"""Generate a gold spot-check report for insulation gold pairs.

Renders each insul_*.rowgold.json side-by-side with the source PDF table row
so a human can quickly verify or flag mismatches. Outputs a markdown report.

Usage:
    python3 scripts/gold_spotcheck_report.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pdfplumber

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = REPO_ROOT / "data" / "real_rfqs" / "gold" / "rows"
RAW_DIR = REPO_ROOT / "data" / "real_rfqs" / "raw" / "insulation_hvac"
OUT_DIR = REPO_ROOT / "results"
OUT_FILE = OUT_DIR / "gold_spotcheck_report.md"


def _load_gold_files() -> list[dict]:
    """Load all insul_*.rowgold.json files sorted by doc_id."""
    gold_files = sorted(GOLD_DIR.glob("insul_*.rowgold.json"))
    if not gold_files:
        print("No insul_*.rowgold.json files found", file=sys.stderr)
        sys.exit(1)
    result = []
    for path in gold_files:
        with open(path) as f:
            data = json.load(f)
        result.append(data)
    return result


def _resolve_pdf_path(source_file: str, gold_source: str) -> Path | None:
    """Resolve the absolute path to the source PDF."""
    candidate = REPO_ROOT / gold_source
    if candidate.exists():
        return candidate
    candidate = RAW_DIR / source_file
    if candidate.exists():
        return candidate
    fname = Path(source_file).name
    for d in [RAW_DIR, RAW_DIR / "boq_references"]:
        candidate = d / fname
        if candidate.exists():
            return candidate
    return None


def _open_pdf_tables(pdf_path: Path) -> dict[int, list[list[list[str | None]]]]:
    """Open a PDF once and cache all tables by page number (1-indexed).

    Returns {page_num: [tables_on_page]} where each table is a list of rows.
    """
    cache: dict[int, list[list[list[str | None]]]] = {}
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for idx, page in enumerate(pdf.pages):
                tables = page.extract_tables() or []
                cache[idx + 1] = tables
    except Exception:
        pass
    return cache


def _get_source_row_text(
    tables_by_page: dict[int, list[list[list[str | None]]]],
    entry: dict,
) -> str:
    """Get the text of the source table row referenced by a gold entry."""
    page_num = entry.get("source_page", 1)
    source_row_idx = entry.get("source_row", 0)
    table_idx = entry.get("source_table", 0)

    tables = tables_by_page.get(page_num, [])
    if not tables:
        return f"[no tables on page {page_num}]"
    if table_idx >= len(tables):
        return f"[table {table_idx} not found; only {len(tables)} tables on page]"
    table = tables[table_idx]
    if source_row_idx >= len(table):
        return f"[row {source_row_idx} not found; only {len(table)} rows in table]"
    row = table[source_row_idx]
    cells = [str(c).strip() if c else "" for c in row]
    return " | ".join(cells)


def _match_quality(entry: dict, source_text: str) -> str:
    """Heuristic match quality indicator."""
    material = entry.get("material", "")
    quantity = entry.get("quantity", "")
    unit = entry.get("unit", "")

    score = 0
    hints: list[str] = []

    if quantity and quantity in source_text:
        score += 2
    elif quantity:
        qty_clean = quantity.rstrip("0").rstrip(".")
        if qty_clean and qty_clean in source_text:
            score += 1
            hints.append(f"qty '{qty_clean}' found (cleaned)")

    if unit and unit.lower() in source_text.lower():
        score += 1
    elif unit:
        unit_aliases = {
            "sqm": "sqm", "sqm.": "sqm", "sq.mtr.": "sqm",
            "sqft": "sqft", "sqft.": "sqft",
            "rmt": "rmt", "rmt.": "rmt", "rmtr": "rmt",
            "mtrs": "mtr", "mtr": "mtr", "mtr.": "mtr",
        }
        for alias, norm in unit_aliases.items():
            if unit.lower().startswith(alias) and norm in source_text.lower():
                score += 1
                hints.append(f"unit '{unit}' matched as '{norm}'")
                break

    if material:
        words = material.split()
        if len(words) >= 2:
            probe = " ".join(words[:2]).lower()
            if probe in source_text.lower():
                score += 1

    if score >= 3:
        return "**GOOD**"
    elif score >= 2:
        label = "**LIKELY OK**"
        if hints:
            label += f" ({'; '.join(hints)})"
        return label
    elif score >= 1:
        return "**NEEDS REVIEW**"
    else:
        return "**MISMATCH?**"


def generate_report() -> None:
    """Generate the markdown spot-check report."""
    gold_files = _load_gold_files()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Pre-load all PDFs to avoid re-opening per entry
    pdf_caches: dict[str, dict[int, list[list[list[str | None]]]]] = {}
    for gold_data in gold_files:
        sf = gold_data.get("source_file", "")
        gs = gold_data.get("gold_source", "")
        pdf_path = _resolve_pdf_path(sf, gs)
        if pdf_path and str(pdf_path) not in pdf_caches:
            pdf_caches[str(pdf_path)] = _open_pdf_tables(pdf_path)

    lines: list[str] = []
    lines.append("# Gold Spot-Check Report: Insulation Pairs")
    lines.append("")
    total_entries = sum(len(g["entries"]) for g in gold_files)
    lines.append(f"Generated for **{len(gold_files)}** gold files with **{total_entries}** total entries.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## How to use this report")
    lines.append("")
    lines.append("For each entry:")
    lines.append("1. Compare **Gold** values against **Source PDF** row text")
    lines.append("2. Confirm match quality indicator is correct")
    lines.append("3. If mismatched, add a note and flag for correction")
    lines.append("4. When verified, update `human_verified: true` in the gold JSON")
    lines.append("")
    lines.append("---")
    lines.append("")

    for gold_data in gold_files:
        doc_id = gold_data.get("doc_id", "unknown")
        source_file = gold_data.get("source_file", "unknown")
        gold_source = gold_data.get("gold_source", "")
        entries = gold_data.get("entries", [])
        method = gold_data.get("method", "unknown")

        lines.append(f"## {doc_id}")
        lines.append("")
        lines.append(f"- **Source file:** `{source_file}`")
        lines.append(f"- **Gold source:** `{gold_source}`")
        lines.append(f"- **Method:** {method}")
        lines.append(f"- **Entries:** {len(entries)}")
        lines.append(f"- **Human verified:** {gold_data.get('human_verified', False)}")
        lines.append("")

        pdf_path = _resolve_pdf_path(source_file, gold_source)
        if not pdf_path:
            lines.append(f"> **WARNING:** Source PDF not found for `{source_file}`")
            lines.append("")
            for i, entry in enumerate(entries):
                lines.append(f"### Entry {i + 1} (item `{entry.get('item_no', '?')}`)")
                lines.append("")
                lines.append("| Field | Value |")
                lines.append("|-------|-------|")
                lines.append(f"| item_no | `{entry.get('item_no', '')}` |")
                lines.append(f"| material | {entry.get('material', '')} |")
                lines.append(f"| quantity | `{entry.get('quantity', '')}` |")
                lines.append(f"| unit | `{entry.get('unit', '')}` |")
                lines.append(f"| source_page | {entry.get('source_page', '?')} |")
                lines.append(f"| source_row | {entry.get('source_row', '?')} |")
                lines.append("")
                lines.append("**Source:** PDF not found")
                lines.append("")
            lines.append("---")
            lines.append("")
            continue

        tables_cache = pdf_caches[str(pdf_path)]
        lines.append(f"PDF found at: `{pdf_path.relative_to(REPO_ROOT)}`")
        lines.append("")

        for i, entry in enumerate(entries):
            item_no = entry.get("item_no", "?")
            material = entry.get("material", "")
            quantity = entry.get("quantity", "")
            unit = entry.get("unit", "")
            page = entry.get("source_page", "?")
            row_idx = entry.get("source_row", "?")
            table_idx = entry.get("source_table", 0)
            verified = entry.get("human_verified", False)

            source_text = _get_source_row_text(tables_cache, entry)
            quality = _match_quality(entry, source_text)

            mat_display = material if len(material) <= 120 else material[:117] + "..."

            lines.append(f"### Entry {i + 1} (item `{item_no}`)")
            lines.append("")

            if verified:
                lines.append("> Status: VERIFIED")
                lines.append("")

            lines.append(f"**Match quality:** {quality}")
            lines.append("")
            lines.append("| Field | Gold Value | Source PDF Row |")
            lines.append("|-------|-----------|----------------|")
            lines.append(f"| item_no | `{item_no}` | - |")
            lines.append(f"| material | {mat_display} | - |")
            lines.append(f"| quantity | `{quantity}` | - |")
            lines.append(f"| unit | `{unit}` | - |")
            lines.append(f"| page / table / row | p{page} t{table_idx} r{row_idx} | - |")
            lines.append("")

            lines.append(f"<details><summary>Source PDF row text (page {page}, table {table_idx}, row {row_idx})</summary>")
            lines.append("")
            lines.append("```")
            lines.append(source_text)
            lines.append("```")
            lines.append("</details>")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    total = sum(len(g["entries"]) for g in gold_files)
    verified = sum(
        1 for g in gold_files for e in g.get("entries", []) if e.get("human_verified", False)
    )
    lines.append(f"- **Gold files:** {len(gold_files)}")
    lines.append(f"- **Total entries:** {total}")
    lines.append(f"- **Verified:** {verified}")
    lines.append(f"- **Unverified:** {total - verified}")
    lines.append("")
    lines.append("| Gold File | Entries | Verified | Source PDF Found |")
    lines.append("|-----------|---------|----------|------------------|")
    for gold_data in gold_files:
        doc_id = gold_data.get("doc_id", "unknown")
        n = len(gold_data.get("entries", []))
        v = sum(1 for e in gold_data.get("entries", []) if e.get("human_verified", False))
        sf = gold_data.get("source_file", "")
        gs = gold_data.get("gold_source", "")
        found = "Yes" if _resolve_pdf_path(sf, gs) else "No"
        lines.append(f"| `{doc_id}` | {n} | {v} | {found} |")
    lines.append("")

    OUT_FILE.write_text("\n".join(lines))
    print(f"Report written to {OUT_FILE}")
    print(f"  {len(gold_files)} gold files, {total_entries} entries")


if __name__ == "__main__":
    generate_report()
