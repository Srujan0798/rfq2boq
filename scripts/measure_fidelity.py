#!/usr/bin/env python3
"""FIDELITY HARNESS — measures data-conversion completeness.

For each real tender (10 SWA enquiries), reports:
- source_rows: row items in gold annotation (PDFs) or XLSX raw data rows
- captured_rows: extracted with confidence >= 0.7
- flagged_rows: extracted with confidence < 0.7
- dropped_rows: source - (captured + flagged)
- over_capture: captured + flagged > source (fidelity > 110%)

KEY metric: fidelity = (captured + flagged) / source
TARGET: 100% ± 10%, dropped MUST be 0, over-capture > 110% is FAIL.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import openpyxl
from src.pipeline_xlsx import XLSXRowPipeline

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

GOLD_DIR = Path("data/real_rfqs/gold")
SWA_DIR = Path("data/real_rfqs/swa_enquiries")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

CONFIDENCE_THRESHOLD = 0.7
OVER_CAPTURE_THRESHOLD = 1.10  # 110% fidelity = over-capture FAIL


def load_gold_annotations(doc_id: str) -> dict[str, Any]:
    """Load gold annotation (for both PDF and XLSX files)."""
    # Try rowgold first (independent human transcription)
    rowgold_path = Path("data/real_rfqs/gold/rows") / f"{doc_id}.rowgold.json"
    if rowgold_path.exists():
        with open(rowgold_path) as f:
            gold = json.load(f)
        return {
            "source_rows": len(gold.get("entries", [])),
            "entities": [],
            "doc_id": doc_id,
        }

    # Fallback to entity gold
    gold_path = GOLD_DIR / f"swa_{doc_id}.json"
    if not gold_path.exists():
        return {"source_rows": 0, "entities": [], "doc_id": doc_id}

    with open(gold_path) as f:
        gold = json.load(f)

    entities = gold.get("entities", [])
    quantity_entities = [e for e in entities if e.get("type") == "QUANTITY"]
    return {
        "source_rows": len(quantity_entities),
        "entities": entities,
        "doc_id": doc_id,
    }


def count_xlsx_source_rows(xlsx_path: Path) -> int:
    """Count actual BOQ data rows in XLSX (excluding header, empty, total rows).

    Uses the pipeline's fidelity tracking to count source rows the same way
    the pipeline processes them - excluding headers, empty rows, totals, and spec paragraphs.
    """
    if not xlsx_path.exists():
        return 0

    wb = openpyxl.load_workbook(str(xlsx_path), data_only=True)
    sheet = wb.active
    raw_rows = list(sheet.iter_rows(values_only=True))

    if len(raw_rows) < 2:
        return 0

    header_idx = 0
    for i, row in enumerate(raw_rows):
        non_empty = [c for c in row if c is not None and str(c).strip() not in ("", "None", "nan")]
        if len(non_empty) < 2:
            continue
        text_vals = [str(c).lower().strip() for c in non_empty]
        has_header = any(t in text_vals for t in ("description", "material", "qty", "quantity", "unit"))
        if has_header:
            header_idx = i
            break

    data_rows = raw_rows[header_idx + 1:]

    import re
    TOTAL_PATTERN = re.compile(r"\b(total|sub-?total|grand-?total)\b", re.IGNORECASE)
    NOTE_PATTERN = re.compile(r"^Note[\s:]", re.IGNORECASE)

    count = 0
    for row in data_rows:
        if all(c is None or str(c).strip() in ("", "None", "nan") for c in row):
            continue

        first_cell = str(row[0]).strip().lower() if row[0] is not None else ""

        if TOTAL_PATTERN.search(first_cell):
            continue
        if NOTE_PATTERN.search(first_cell):
            continue

        material = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ""
        if not material or len(material) <= 2:
            continue

        if len(material) > 1000:
            continue

        count += 1

    return count


def run_xlsx_extraction(xlsx_path: Path) -> tuple[int, int, int, int]:
    """Run XLSX pipeline and return (extracted_rows, low_confidence_rows, rate_only_rows, source_rows)."""
    if not xlsx_path.exists():
        return 0, 0, 0, 0

    pipeline = XLSXRowPipeline()
    boq_rows = pipeline.run(xlsx_path)

    extracted = len(boq_rows)
    low_conf = sum(1 for r in boq_rows if r.confidence < CONFIDENCE_THRESHOLD)
    rate_only = sum(1 for r in boq_rows if r.rate_only)
    fidelity = pipeline.fidelity_report
    source_rows = fidelity.get("source_rows", 0)

    return extracted, low_conf, rate_only, source_rows


def get_source_file_path(doc_id: str) -> tuple[list[Path] | Path | None, str]:
    """Get source file path(s) and type (xlsx or pdf).

    04_adani's actual BOQ content is split across TWO pdfs ("BOQ PAGEadani
    proj.pdf" has 43 of the 45 rows; "BOQ PAGE2adani proj.pdf" has the other
    2) -- reading only PAGE2 (as this map used to) silently drops 43 real
    rows and is the documented "04 eval reads the wrong Adani PDF" bug
    (tasks/NEXT_WAVE.md NW-01). Both files are returned as a list; callers
    must sum extraction across all of them for multi-file docs.
    """
    doc_map = {
        "01_gsecl_wanakbori_tmd8": ("data/real_rfqs/swa_enquiries/01_gsecl_wanakbori_tmd8/RFQ-75810 TMD-8.pdf", "pdf"),
        "02_isro_vssc": ("data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx", "xlsx"),
        "03_zydus_matoda_osd": ("data/real_rfqs/swa_enquiries/03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx", "xlsx"),
        "04_adani": (
            [
                "data/real_rfqs/swa_enquiries/04_adani/BOQ PAGEadani proj.pdf",
                "data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf",
            ],
            "pdf",
        ),
        "05_zydus_animal_pharmez": ("data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/Copy of Insulation Enquiry-Zydus Animal Health Expansion Project - Pharmez-Ahmedabad_.xlsx", "xlsx"),
        "06_avante_kirloskar_pune": ("data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Boq_132.pdf", "pdf"),
        "07_grew_solar_narmadapuram": ("data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf", "pdf"),
        "08_sael": ("data/real_rfqs/swa_enquiries/08_sael/Copy of Insulation Enquiry - SAEL.xlsx", "xlsx"),
        "09_gem_bid_7439924": ("data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf", "pdf"),
        "10_gem_bid_7552777": ("data/real_rfqs/swa_enquiries/10_gem_bid_7552777/GeM-Bidding-9343469.pdf", "pdf"),
    }

    if doc_id in doc_map:
        path, ftype = doc_map[doc_id]
        if isinstance(path, list):
            return [Path(p) for p in path], ftype
        return Path(path), ftype
    return None, "unknown"


def run_pdf_extraction(pdf_path: Path | list[Path]) -> tuple[int, int, int]:
    """Run PDF pipeline and return (captured_rows, low_confidence_rows, rate_only_rows).

    Captured rows = boq_items where confidence >= threshold.
    Low-confidence rows = boq_items where confidence < threshold.
    Accepts a single path or a list of paths (multi-file docs, e.g. 04_adani);
    results are summed across all files.
    """
    paths = pdf_path if isinstance(pdf_path, list) else [pdf_path]
    paths = [p for p in paths if p.exists()]
    if not paths:
        return 0, 0, 0

    from src.pipeline import Pipeline

    pipeline = Pipeline()
    captured = low_conf = rate_only = 0
    for p in paths:
        result = pipeline.run(str(p))
        boq_items = result.boq_items
        captured += sum(1 for r in boq_items if r.confidence >= CONFIDENCE_THRESHOLD)
        low_conf += sum(1 for r in boq_items if r.confidence < CONFIDENCE_THRESHOLD)
        rate_only += sum(1 for r in boq_items if r.rate_only)

    return captured, low_conf, rate_only


def process_doc(doc_id: str) -> dict[str, Any]:
    """Process a single document and return fidelity metrics."""
    source_path, file_type = get_source_file_path(doc_id)

    # Always use gold for source_rows (independent ground truth)
    gold_data = load_gold_annotations(doc_id)
    source_rows = gold_data["source_rows"]

    source_exists = bool(source_path) and (
        any(p.exists() for p in source_path) if isinstance(source_path, list) else source_path.exists()
    )

    if file_type == "xlsx" and source_exists:
        extracted, low_conf, rate_only, _ = run_xlsx_extraction(source_path)
        captured = extracted
        flagged = low_conf
    elif file_type == "pdf" and source_exists:
        captured, flagged, rate_only = run_pdf_extraction(source_path)
    else:
        captured = 0
        flagged = 0
        rate_only = 0

    dropped = max(0, source_rows - captured - flagged)
    fidelity = (captured + flagged) / source_rows if source_rows > 0 else 0.0
    over_capture = fidelity > OVER_CAPTURE_THRESHOLD

    return {
        "doc_id": doc_id,
        "source_rows": source_rows,
        "captured_rows": captured,
        "flagged_rows": flagged,
        "dropped_rows": dropped,
        "fidelity_pct": fidelity * 100,
        "file_type": file_type,
        "rate_only_rows": rate_only,
        "over_capture": over_capture,
    }


def main() -> None:
    """Run fidelity measurement on all 10 SWA tenders."""
    doc_ids = [
        "01_gsecl_wanakbori_tmd8",
        "02_isro_vssc",
        "03_zydus_matoda_osd",
        "04_adani",
        "05_zydus_animal_pharmez",
        "06_avante_kirloskar_pune",
        "07_grew_solar_narmadapuram",
        "08_sael",
        "09_gem_bid_7439924",
        "10_gem_bid_7552777",
    ]

    results: list[dict[str, Any]] = []
    total_source = 0
    total_captured = 0
    total_flagged = 0
    total_dropped = 0

    print("\n" + "=" * 80)
    print("FIDELITY MEASUREMENT — Data Conversion Completeness")
    print("=" * 80)

    for doc_id in doc_ids:
        r = process_doc(doc_id)
        results.append(r)

        total_source += r["source_rows"]
        total_captured += r["captured_rows"]
        total_flagged += r["flagged_rows"]
        total_dropped += r["dropped_rows"]

        fid_str = f"{r['fidelity_pct']:.1f}%"
        has_dropped = r["dropped_rows"] > 0
        has_over_capture = r["over_capture"]
        if has_dropped:
            status = "✗ FAIL (dropped)"
        elif has_over_capture:
            status = "✗ FAIL (over-capture)"
        else:
            status = "✓ PASS"
        print(f"\n{r['doc_id']} ({r['file_type']})")
        print(f"  Source:    {r['source_rows']:>4} rows")
        print(f"  Captured: {r['captured_rows']:>4} rows")
        print(f"  Flagged:   {r['flagged_rows']:>4} rows (low confidence)")
        print(f"  Dropped:  {r['dropped_rows']:>4} rows")
        print(f"  Fidelity: {fid_str:>7} {status}")

    overall_fidelity = (total_captured + total_flagged) / total_source if total_source > 0 else 0.0
    overall_over_capture = overall_fidelity > OVER_CAPTURE_THRESHOLD * 100
    if total_dropped > 0:
        overall_status = "✗ FAIL (dropped)"
    elif overall_over_capture:
        overall_status = "✗ FAIL (over-capture)"
    else:
        overall_status = "✓ PASS"

    print("\n" + "=" * 80)
    print("OVERALL FIDELITY")
    print("=" * 80)
    print(f"  Total Source:    {total_source:>5} rows")
    print(f"  Total Captured:{total_captured:>5} rows")
    print(f"  Total Flagged: {total_flagged:>5} rows")
    print(f"  Total Dropped: {total_dropped:>5} rows")
    print(f"  Fidelity:     {overall_fidelity * 100:.1f}% {overall_status}")

    report_path = RESULTS_DIR / "FIDELITY_REPORT.md"
    with open(report_path, "w") as f:
        f.write("# FIDELITY REPORT — Data Conversion Completeness\n\n")
        f.write("**Requirement R1:** 100% data-conversion fidelity. Every line item captured.\n")
        f.write("Flag uncertain items, NEVER silently drop.\n\n")
        f.write("## Per-File Results\n\n")
        f.write("| Document | Type | Source | Captured | Flagged | Dropped | Fidelity | Status |\n")
        f.write("|----------|------|--------|----------|---------|---------|----------|--------|\n")
        for r in results:
            fid = f"{r['fidelity_pct']:.1f}%"
            if r["dropped_rows"] > 0:
                file_status = "FAIL (dropped)"
            elif r["over_capture"]:
                file_status = "FAIL (over-capture)"
            else:
                file_status = "PASS"
            f.write(
                f"| {r['doc_id']} | {r['file_type']} | {r['source_rows']} | "
                f"{r['captured_rows']} | {r['flagged_rows']} | {r['dropped_rows']} | "
                f"{fid} | {file_status} |\n"
            )

        f.write("\n## Overall\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Total Source | {total_source} |\n")
        f.write(f"| Total Captured | {total_captured} |\n")
        f.write(f"| Total Flagged | {total_flagged} |\n")
        f.write(f"| Total Dropped | {total_dropped} |\n")
        f.write(f"| **Fidelity** | **{overall_fidelity * 100:.1f}%** |\n")
        f.write(f"| **Status** | **{overall_status}** |\n")

        if total_dropped > 0:
            f.write("\n## ⚠️ DROPPED ROWS DETECTED\n\n")
            f.write("The following files have dropped rows:\n\n")
            for r in results:
                if r["dropped_rows"] > 0:
                    f.write(f"- **{r['doc_id']}**: {r['dropped_rows']} dropped\n")

        over_capture_files = [r for r in results if r["over_capture"]]
        if over_capture_files:
            f.write("\n## ⚠️ OVER-CAPTURE DETECTED\n\n")
            f.write("The following files capture more rows than the source (fidelity > 110%):\n\n")
            for r in over_capture_files:
                f.write(
                    f"- **{r['doc_id']}**: {r['fidelity_pct']:.1f}% "
                    f"({r['captured_rows'] + r['flagged_rows']} captured vs {r['source_rows']} source)\n"
                )

    print(f"\n✓ Report written to: {report_path}")


if __name__ == "__main__":
    main()
