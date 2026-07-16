#!/usr/bin/env python3
"""draft_source_truth_extras.py — count BOQ rows for non-sacred BOQ-bearing docs.

Reuses counting functions from draft_source_truth.py. Appends to existing
data/real_rfqs/source_truth.json and writes an extended review markdown.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_JSON = REPO_ROOT / "data/real_rfqs/source_truth.json"
ROWGOLD_DIR = REPO_ROOT / "data/real_rfqs/gold/rows"
TIMEOUT_SECONDS = 90

# Import counting functions from draft_source_truth.py
sys.path.insert(0, str(REPO_ROOT))
from scripts.draft_source_truth import (  # noqa: E402  # must insert repo root before this import
    TableCountResult,
    TimeoutSignalError,
    count_pdf_source_rows,
    count_xlsx_source_rows,
    with_timeout,
)

# Additional BOQ-bearing docs (spec1, spec2) — NOT sacred10, NOT bytes-identical bundles
# Rowgold mapping where available
ROWGOLD_MAP: dict[str, str] = {
    "boq_pdf": "insul_01_tender.rowgold.json",
    "boq_insulation_pdf": "insul_02_swpl.rowgold.json",
    "boq_page_pdf": "insul_03_boq_page.rowgold.json",
    "boq_page_003_pdf": "insul_04_boq_page_003.rowgold.json",
    "copy_of_boq_pdf": "insul_05_copy_of_boq.rowgold.json",
    "insulation_boq_1_pdf": "insul_06_insulation_boq_1.rowgold.json",
    "insulation_boq_2_pdf": "insul_07_insulation_boq_2.rowgold.json",
    "boq_insulation_compliance_pdf": "insul_08_boq_insulation_compliance.rowgold.json",
    "pipe_insulation_boq_compliance_pdf": "insul_09_pipe_insulation_compliance.rowgold.json",
}

EXTRA_DOCS: dict[str, dict[str, Any]] = {
    # --- spec1 ---
    "spec1_boq_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specifications/BOQ.pdf",
    },
    "spec1_boq_insulation_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specifications/BOQ - INSULATION.pdf",
    },
    "spec1_boq_page_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specifications/BOQ PAGE.pdf",
    },
    "spec1_boq_page_003_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specifications/BOQ PAGE (003).pdf",
    },
    "spec1_copy_of_boq_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specifications/Copy of BOQ.pdf",
    },
    "spec1_insulation_boq_1_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specifications/Insulation Boq (1).pdf",
    },
    "spec1_insulation_boq_2_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specifications/Insulation Boq (2).pdf",
    },
    "spec1_boq_insulation_compliance_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specifications/BOQ- Insulation_Compliance.pdf",
    },
    "spec1_pipe_insulation_boq_compliance_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specifications/47_Pipe Insulation_BOQ Compliance.pdf",
    },
    "spec1_tech_specs_insulation_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specifications/Tech Specs  - Insulation.pdf",
    },
    # --- spec2 ---
    "spec2_boq_insulation_xlsx": {
        "type": "xlsx",
        "path": "data/specifications/Specification 2/BOQ - Insulation.xlsx",
    },
    "spec2_boq_thermal_insulation_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specification 2/BOQ_Thermal Insulation.pdf",
    },
    "spec2_ubs_hyderabad_boq_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specification 2/Copy of UBS_Hyderabad_Project_BOQ(1).pdf",
    },
    "spec2_insulation_boq_bluegrass_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specification 2/INSULATION_BOQ_BLUEGRASS.pdf",
    },
    "spec2_insulation_arff_xlsx": {
        "type": "xlsx",
        "path": "data/specifications/Specification 2/Insulation ARFF.xlsx",
    },
    "spec2_insulation_medical_xlsx": {
        "type": "xlsx",
        "path": "data/specifications/Specification 2/Insulation Medical.xlsx",
    },
    "spec2_insulation_xlsx": {
        "type": "xlsx",
        "path": "data/specifications/Specification 2/Insulation.xlsx",
    },
    "spec2_mech_eipl_buffer_tank_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specification 2/MECH-EIPL-HVAC-NXTRA-001-R2-BUFFER TANK.pdf",
    },
    "spec2_boq_pdf": {
        "type": "pdf",
        "path": "data/specifications/Specification 2/boq.pdf",
    },
}

def load_rowgold(doc_id: str) -> dict[str, Any] | None:
    rg_name = ROWGOLD_MAP.get(doc_id)
    if not rg_name:
        return None
    path = ROWGOLD_DIR / rg_name
    if not path.exists():
        return None
    return json.loads(path.read_text())

def draft_one_doc(doc_id: str) -> dict[str, Any]:
    info = EXTRA_DOCS[doc_id]
    file_type = info["type"]
    path = REPO_ROOT / info["path"]
    if not path.exists():
        resp = {
            "doc_id": doc_id,
            "source_row_count": 0,
            "unit": "BOQ line items",
            "method": "human count",
            "evidence": f"ERROR: source file not found: {path}",
            "counted_by": "machine-draft",
            "owner_confirmed": False,
            "error": "missing_source_file",
        }
        return resp

    timed_out = False
    header_found = False
    try:
        with with_timeout(TIMEOUT_SECONDS):
            if file_type == "pdf":
                result, header_found = count_pdf_source_rows([path])
                sheet_note = ""
            else:
                result, sheet_note, header_found = count_xlsx_source_rows(path)
    except TimeoutSignalError:
        timed_out = True
        result = TableCountResult()
        sheet_note = ""

    if timed_out:
        gold = load_rowgold(doc_id)
        if gold and gold.get("entries"):
            n = len(gold["entries"])
            return {
                "doc_id": doc_id,
                "source_row_count": n,
                "unit": "BOQ line items",
                "method": "human count",
                "evidence": (
                    f"TIMEOUT: machine extraction exceeded {TIMEOUT_SECONDS}s on "
                    f"{path.name}. Fell back to DRAFT rowgold transcription "
                    f"({ROWGOLD_DIR / ROWGOLD_MAP.get(doc_id, '?')}, method="
                    f"{gold.get('method')!r}), n={n}."
                ),
                "counted_by": "machine-draft (timeout fallback to draft rowgold)",
                "owner_confirmed": False,
            }
        return {
            "doc_id": doc_id,
            "source_row_count": 0,
            "unit": "BOQ line items",
            "method": "human count",
            "evidence": f"TIMEOUT after {TIMEOUT_SECONDS}s, no rowgold fallback. NEEDS MANUAL COUNT.",
            "counted_by": "machine-draft",
            "owner_confirmed": False,
            "error": "timeout_no_fallback",
        }

    evidence_first3 = result.evidence_lines[:3]
    evidence_last3 = result.evidence_lines[-3:] if len(result.evidence_lines) > 3 else []
    sheet_bit = f"; {sheet_note}" if sheet_note else ""

    # See draft_source_truth.py's draft_one_doc: a bare 0 with no header ever
    # detected is NOT a confirmed-zero claim, it's "auto-counter found
    # nothing it recognized" -- flag it so it can't be silently mistaken for
    # a verified empty document.
    needs_manual_count = result.count == 0 and not header_found

    if needs_manual_count:
        evidence = (
            f"file={path.name}{sheet_bit}; NO BOQ-STYLE HEADER DETECTED "
            f"(description+unit or description+qty column) in any table/page. "
            f"This is NOT a confirmed zero -- the auto-counter's header "
            f"heuristic found nothing it recognized. NEEDS MANUAL COUNT."
        )
    else:
        evidence = (
            f"file={path.name}{sheet_bit}; rows counted={result.count} "
            f"(excluding rate-only/'R.O.' rows: {result.excl_rate_only_count}); "
            f"first3=[{' || '.join(evidence_first3)}]; "
            f"last3=[{' || '.join(evidence_last3)}]"
        )

    resp = {
        "doc_id": doc_id,
        "source_row_count": result.count,
        "unit": "BOQ line items",
        "method": "human count",
        "evidence": evidence,
        "counted_by": "machine-draft",
        "owner_confirmed": False,
        "needs_manual_count": needs_manual_count,
        "_draft_excl_rate_only_count": result.excl_rate_only_count,
        "_draft_evidence_lines": result.evidence_lines,
    }
    return resp

def main() -> int:
    entries = []
    for doc_id in EXTRA_DOCS:
        print(f"Counting {doc_id} ...", end=" ", file=sys.stderr, flush=True)
        e = draft_one_doc(doc_id)
        print(f"{e['source_row_count']} items", file=sys.stderr)
        entries.append(e)

    # Read existing source_truth.json
    existing = json.loads(OUT_JSON.read_text()) if OUT_JSON.exists() else {"entries": []}

    # Merge: skip any doc_id that already exists
    existing_ids = {e["doc_id"] for e in existing["entries"]}
    new_entries = [e for e in entries if e["doc_id"] not in existing_ids]
    for e in entries:
        if e["doc_id"] in existing_ids:
            print(f"  (skipping {e['doc_id']} — already in source_truth.json)", file=sys.stderr)

    # Write clean versions (without internal draft fields)
    clean_entries = []
    for e in new_entries:
        clean = {
            "doc_id": e["doc_id"],
            "source_row_count": e["source_row_count"],
            "unit": e["unit"],
            "method": e["method"],
            "evidence": e["evidence"],
            "counted_by": e["counted_by"],
            "owner_confirmed": e["owner_confirmed"],
            "needs_manual_count": e.get("needs_manual_count", False),
        }
        if e.get("error"):
            clean["error"] = e["error"]
        clean_entries.append(clean)

    all_entries = existing["entries"] + clean_entries
    OUT_JSON.write_text(json.dumps({"entries": all_entries}, indent=2) + "\n")
    print(f"\nUpdated {OUT_JSON} ({len(all_entries)} total entries)", file=sys.stderr)

    # Append to review markdown
    review_path = REPO_ROOT / "results/source_truth_review.md"
    with open(review_path, "a") as f:
        f.write("\n\n---\n\n")
        f.write("## Non-sacred BOQ-bearing docs (spec1, spec2)\n\n")
        f.write("| doc_id | draft count (inclusive) | draft count (excl. rate-only) | notes |\n")
        f.write("|---|---|---|---|\n")
        for e in entries:
            n = e["source_row_count"]
            n_excl = e.get("_draft_excl_rate_only_count", n)
            note = ""
            if n_excl != n:
                note = "MISMATCH excl-rate-only differs"
            if e.get("error"):
                note = f"ERROR: {e['error']}"
            f.write(f"| {e['doc_id']} | {n} | {n_excl} | {note} |\n")

        f.write("\n### Per-document detail\n\n")
        for e in entries:
            f.write(f"#### {e['doc_id']}\n\n")
            f.write(f"- Path: `{EXTRA_DOCS[e['doc_id']]['path']}`\n")
            f.write(f"- Draft count (inclusive of rate-only rows): **{e['source_row_count']}**\n")
            f.write(f"- Draft count (excluding rate-only rows): **{e.get('_draft_excl_rate_only_count', e['source_row_count'])}**\n")
            f.write(f"- Evidence: {e['evidence']}\n")

            gold = load_rowgold(e["doc_id"])
            if gold and gold.get("entries"):
                f.write(
                    f"- Draft rowgold transcription: {len(gold['entries'])} entries "
                    f"(method={gold.get('method')!r}) "
                    f"— DRAFT, needs human review.\n"
                )
            ev_lines = e.get("_draft_evidence_lines", [])
            if ev_lines:
                f.write("\nFirst 3 rows counted:\n")
                for ln in ev_lines[:3]:
                    f.write(f"  - {ln}\n")
                if len(ev_lines) > 3:
                    f.write("Last 3 rows counted:\n")
                    for ln in ev_lines[-3:]:
                        f.write(f"  - {ln}\n")
            f.write("\n")

    print(f"Appended to {review_path}", file=sys.stderr)

    print("\n" + "=" * 60)
    print("NON-SACRED BOQ SUMMARY (all owner_confirmed=false)")
    print("=" * 60)
    total = 0
    for e in entries:
        print(f"  {e['doc_id']:<42} {e['source_row_count']:>4} items")
        total += e["source_row_count"]
    print(f"  {'TOTAL':<42} {total:>4} items")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
