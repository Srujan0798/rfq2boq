"""Batch extract ALL 26 unique BOQ documents and produce quality report."""

import json
import logging
import signal
import sys
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BASE = Path("/Users/srujansai/Desktop/rfq2boq")
OUTPUT_DIR = BASE / "output" / "batch_extractions_v2"
LOG_DIR = Path("cli_agents/agent_batch_extract")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(LOG_DIR / "error.log"), mode="w"),
    ],
)
logger = logging.getLogger("batch_extract")

sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "src"))

# Suppress noisy logging from pipeline components
for name in [
    "src.ingest.table_extractor",
    "src.ingest.pdf_extractor",
    "src.nlp.pipeline",
    "src.confidence.calibration",
    "src.export",
    "src.preproc.sections",
    "src.risk.engine",
    "src.rules",
]:
    logging.getLogger(name).setLevel(logging.WARNING)


DOCUMENTS = [
    # SWA enquiries (1-8)
    ("1", "02_isro_vssc", "xlsx", str(BASE / "data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx")),
    ("2", "03_zydus_matoda_osd", "xlsx", str(BASE / "data/real_rfqs/swa_enquiries/03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx")),
    ("3", "04_adani_boq1", "pdf", str(BASE / "data/real_rfqs/swa_enquiries/04_adani/BOQ PAGEadani proj.pdf")),
    ("4", "04_adani_boq2", "pdf", str(BASE / "data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf")),
    ("5", "05_zydus_animal", "xlsx", str(BASE / "data/real_rfqs/swa_enquiries/05_zydus_animal_pharmez/Copy of TDS TO BE FILLED BY VENDOR-INSULATION.xlsx")),
    ("6", "06_avante_kirloskar", "pdf", str(BASE / "data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Boq_132.pdf")),
    ("7", "07_grew_solar", "pdf", str(BASE / "data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf")),
    ("8", "08_sael", "xlsx", str(BASE / "data/real_rfqs/swa_enquiries/08_sael/Copy of TDS - Insulation - SAEL (1).xlsx")),
    # Specifications 1 (9-18)
    ("9", "47_pipe_insulation_boq_compliance", "pdf", str(BASE / "data/specifications/Specifications/47_Pipe Insulation_BOQ Compliance.pdf")),
    ("10", "boq_insulation", "pdf", str(BASE / "data/specifications/Specifications/BOQ - INSULATION.pdf")),
    ("11", "boq_page_003", "pdf", str(BASE / "data/specifications/Specifications/BOQ PAGE (003).pdf")),
    ("12", "boq_page", "pdf", str(BASE / "data/specifications/Specifications/BOQ PAGE.pdf")),
    ("13", "boq_insulation_compliance", "pdf", str(BASE / "data/specifications/Specifications/BOQ- Insulation_Compliance.pdf")),
    ("14", "boq", "pdf", str(BASE / "data/specifications/Specifications/BOQ.pdf")),
    ("15", "copy_of_boq", "pdf", str(BASE / "data/specifications/Specifications/Copy of BOQ.pdf")),
    ("16", "insulation_boq_1", "pdf", str(BASE / "data/specifications/Specifications/Insulation Boq (1).pdf")),
    ("17", "insulation_boq_2", "pdf", str(BASE / "data/specifications/Specifications/Insulation Boq (2).pdf")),
    ("18", "tech_specs_insulation", "pdf", str(BASE / "data/specifications/Specifications/Tech Specs  - Insulation.pdf")),
    # Specifications 2 (19-26)
    ("19", "boq_insulation_xlsx", "xlsx", str(BASE / "data/specifications/Specification 2/BOQ - Insulation.xlsx")),
    ("20", "boq_thermal_insulation", "pdf", str(BASE / "data/specifications/Specification 2/BOQ_Thermal Insulation.pdf")),
    ("21", "ubs_hyderabad_boq", "pdf", str(BASE / "data/specifications/Specification 2/Copy of UBS_Hyderabad_Project_BOQ(1).pdf")),
    ("22", "insulation_boq_bluegrass", "pdf", str(BASE / "data/specifications/Specification 2/INSULATION_BOQ_BLUEGRASS.pdf")),
    ("23", "insulation_arff", "xlsx", str(BASE / "data/specifications/Specification 2/Insulation ARFF.xlsx")),
    ("24", "insulation_medical", "xlsx", str(BASE / "data/specifications/Specification 2/Insulation Medical.xlsx")),
    ("25", "insulation_xlsx", "xlsx", str(BASE / "data/specifications/Specification 2/Insulation.xlsx")),
    ("26", "buffer_tank", "pdf", str(BASE / "data/specifications/Specification 2/MECH-EIPL-HVAC-NXTRA-001-R2-BUFFER TANK.pdf")),
]


class TimeoutError(Exception):
    pass


@contextmanager
def timeout(seconds: int):
    def handler(signum, frame):
        raise TimeoutError(f"Timed out after {seconds}s")

    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def extract_xlsx(path: str) -> list[dict[str, Any]]:
    from src.pipeline_xlsx import XLSXRowPipeline
    pipe = XLSXRowPipeline()
    items = pipe.run(path)
    result = []
    for item in items:
        d = {
            "item_no": item.item_no,
            "material": item.material,
            "quantity": float(item.quantity) if hasattr(item.quantity, "__float__") else 0.0,
            "unit": item.unit,
            "description_raw": item.description_raw,
            "grade": item.grade,
            "location": item.location,
            "action": item.action,
            "confidence": item.confidence,
            "rate_only": item.rate_only,
        }
        result.append(d)
    return result


def extract_pdf(path: str) -> list[dict[str, Any]]:
    from src.pipeline import Pipeline
    pipe = Pipeline()
    result = pipe.run(path)
    items = []
    for item in result.boq_items:
        d = {
            "item_no": item.item_no,
            "material": item.material,
            "quantity": float(item.quantity) if hasattr(item.quantity, "__float__") else 0.0,
            "unit": item.unit,
            "description_raw": item.description_raw,
            "grade": item.grade,
            "location": item.location,
            "action": item.action,
            "confidence": item.confidence,
            "rate_only": item.rate_only,
            "source_pages": list(item.source_pages) if hasattr(item, "source_pages") else [],
            "dimensions": list(item.dimensions) if hasattr(item, "dimensions") else [],
        }
        items.append(d)
    return items


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (BASE / "cli_agents/agent_batch_extract").mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    total_rows_all = 0
    total_errors = 0

    for doc_id, project_name, doc_type, filepath in DOCUMENTS:
        logger.info("Processing doc %s: %s (%s)", doc_id, project_name, doc_type)
        print(f"\n{'='*60}")
        print(f"Doc {doc_id}: {project_name} ({doc_type})")
        print(f"  File: {filepath}")
        print(f"{'='*60}")

        start = time.time()
        row_count = 0
        materials: list[str] = []
        errors: list[str] = []
        status = "success"
        boq_rows: list[dict[str, Any]] = []

        try:
            boq_rows = extract_xlsx(filepath) if doc_type == "xlsx" else extract_pdf(filepath)

            row_count = len(boq_rows)
            total_rows_all += row_count
            materials = [r.get("material", "") for r in boq_rows if r.get("material")]
            print(f"  -> {row_count} rows extracted ({len(materials)} items)")
            if materials:
                sample = materials[:3]
                print(f"  -> Sample materials: {sample}")

        except TimeoutError as e:
            errors.append(str(e))
            status = "timeout"
            total_errors += 1
            print(f"  -> TIMEOUT: {e}")
        except Exception as e:
            errors.append(f"{type(e).__name__}: {str(e)}")
            status = "error"
            total_errors += 1
            logger.exception("Failed to extract %s", filepath)
            print(f"  -> ERROR: {e}")

        elapsed = time.time() - start

        doc_result = {
            "doc_id": doc_id,
            "project_name": project_name,
            "type": doc_type,
            "filepath": filepath,
            "status": status,
            "rows_extracted": row_count,
            "unique_materials": len(set(materials)),
            "errors": errors,
            "processing_time_sec": round(elapsed, 2),
            "boq_items": boq_rows,
        }
        results.append(doc_result)

        # Save per-document output
        out_path = OUTPUT_DIR / f"{project_name}.json"
        with open(out_path, "w") as f:
            json.dump(doc_result, f, indent=2, default=str)
        print(f"  -> Saved to {out_path}")

    # Summary
    print("\n\n" + "="*60)
    print("BATCH EXTRACTION SUMMARY")
    print("="*60)

    header = f"{'Doc':>4} | {'Project':<35} | {'Type':<5} | {'Rows':>6} | {'Materials':>10} | {'Time':>6} | {'Status':<10}"
    sep = "-" * len(header)
    print(header)
    print(sep)

    successful = 0
    failed_list = []
    for r in results:
        row_label = f"{r['rows_extracted']}"
        mat_label = f"{r['unique_materials']}"
        time_label = f"{r['processing_time_sec']}s"
        status_label = r['status']
        print(f"{r['doc_id']:>4} | {r['project_name']:<35} | {r['type']:<5} | {row_label:>6} | {mat_label:>10} | {time_label:>6} | {status_label:<10}")
        if r['status'] == 'success':
            successful += 1
        else:
            failed_list.append(f"  Doc {r['doc_id']} ({r['project_name']}): {r['errors']}")

    print(sep)
    print(f"\nTotal documents: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed/timeout: {len(results) - successful}")
    print(f"Total rows across all documents: {total_rows_all}")
    print(f"Total errors: {total_errors}")

    if failed_list:
        print("\nFailed documents:")
        for f in failed_list:
            print(f)

    # Save summary JSON
    summary = {
        "extraction_date": datetime.now(UTC).isoformat(),
        "total_documents": len(results),
        "successful": successful,
        "failed": len(results) - successful,
        "total_rows": total_rows_all,
        "documents": [
            {
                "doc_id": r["doc_id"],
                "project_name": r["project_name"],
                "type": r["type"],
                "rows_extracted": r["rows_extracted"],
                "unique_materials": r["unique_materials"],
                "status": r["status"],
                "processing_time_sec": r["processing_time_sec"],
                "errors": r["errors"],
            }
            for r in results
        ],
    }
    with open(OUTPUT_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\nSummary saved to {OUTPUT_DIR / 'summary.json'}")
    print(f"Error log: {LOG_DIR / 'error.log'}")

    return results


if __name__ == "__main__":
    main()
