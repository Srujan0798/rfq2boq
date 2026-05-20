"""Process all real RFQ PDFs through the extraction pipeline.

Usage:
    python scripts/process_real_rfqs.py --input data/real_rfqs/raw --output data/real_rfqs/extracted
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.constants import EntityType, RelationType
from src.domain.boq_assembler import BOQAssembler
from src.domain.models import EntitySpan, Relation
from src.ingest.pdf_extractor import PDFExtractor
from src.nlp.pipeline import NLPPipeline


def process_pdfs(input_dir: Path, output_dir: Path, manifest_path: Path | None = None) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    pdfs = list(input_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {input_dir}")
        return {"processed": 0, "failed": 0, "results": []}

    pipeline = NLPPipeline()
    assembler = BOQAssembler()
    pdf_extractor = PDFExtractor()
    results = []
    processed = 0
    failed = 0

    if manifest_path and manifest_path.exists():
        with open(manifest_path) as f:
            json.load(f)

    print(f"Processing {len(pdfs)} PDFs...\n")

    for pdf_path in sorted(pdfs):
        rfq_id = pdf_path.stem
        print(f"[{processed + failed + 1}/{len(pdfs)}] {rfq_id}", end=" ")

        start = time.time()
        try:
            pages = pdf_extractor.extract_text(str(pdf_path))
            text = "\n".join(p.text for p in pages if p.text.strip())

            if not text.strip():
                raise ValueError("Empty PDF - no text extracted")

            result = pipeline.process(text)
            elapsed = time.time() - start

            entity_spans = []
            for e_dict in result.entities:
                ent_type = e_dict.get("type", "MATERIAL")
                try:
                    entity_type = EntityType[ent_type.upper()]
                except (KeyError, ValueError):
                    entity_type = EntityType.MATERIAL
                entity_spans.append(EntitySpan(
                    text=e_dict.get("text", ""),
                    type=entity_type,
                    start=e_dict.get("start", 0),
                    end=e_dict.get("end", 0),
                    page=1,
                    conf=e_dict.get("confidence", 0.5),
                ))

            rel_list = []
            for r_dict in result.relations:
                rel_type = r_dict.get("type", "HAS_QUANTITY")
                try:
                    relation_type = RelationType[rel_type.upper()]
                except (KeyError, ValueError):
                    relation_type = RelationType.HAS_QUANTITY
                rel_list.append(Relation(
                    head_id=str(r_dict.get("head", "")),
                    tail_id=str(r_dict.get("tail", "")),
                    type=relation_type,
                    conf=r_dict.get("confidence", 0.5),
                ))

            boq_rows = assembler.assemble(entity_spans, rel_list, text)

            entities_out = [
                {
                    "text": e.text,
                    "type": e.type.value if hasattr(e.type, "value") else str(e.type),
                    "start": e.start,
                    "end": e.end,
                    "confidence": e.conf,
                }
                for e in entity_spans
            ]

            boq_items_out = []
            for item in boq_rows:
                item_dict = {
                    "item_no": item.item_no,
                    "material": item.material,
                    "quantity": float(item.quantity),
                    "unit": item.unit,
                    "action": item.action,
                    "grade": item.grade,
                    "standard": list(item.standard),
                    "location": item.location,
                    "confidence": item.confidence,
                }
                boq_items_out.append(item_dict)

            ext_data = {
                "doc_id": rfq_id,
                "source_file": str(pdf_path),
                "extraction_date": datetime.now().isoformat(),
                "entities": entities_out,
                "relations": [],
                "boq_items": boq_items_out,
                "metadata": {
                    "total_entities": len(entities_out),
                    "total_relations": 0,
                    "total_boq_items": len(boq_items_out),
                    "avg_confidence": sum(e["confidence"] or 0 for e in entities_out) / max(len(entities_out), 1),
                    "processing_time_sec": elapsed,
                    "pages_extracted": len(pages),
                },
            }

            out_path = output_dir / f"{rfq_id}.json"
            with open(out_path, "w") as f:
                json.dump(ext_data, f, indent=2)

            results.append({
                "doc_id": rfq_id,
                "entities": len(entities_out),
                "boq_items": len(boq_items_out),
                "avg_confidence": ext_data["metadata"]["avg_confidence"],
                "elapsed_sec": elapsed,
                "status": "success",
            })
            processed += 1
            print(f"✓ {len(entities_out)} entities, {len(boq_items_out)} BOQ items ({elapsed:.1f}s)")

        except Exception as e:
            failed += 1
            elapsed = time.time() - start
            results.append({
                "doc_id": rfq_id,
                "entities": 0,
                "boq_items": 0,
                "avg_confidence": 0.0,
                "elapsed_sec": elapsed,
                "status": "failed",
                "error": str(e),
            })
            print(f"✗ ERROR: {e}")

    summary = {
        "total": len(pdfs),
        "processed": processed,
        "failed": failed,
        "results": results,
        "avg_entities": sum(r["entities"] for r in results) / max(len(results), 1),
        "avg_boq_items": sum(r["boq_items"] for r in results) / max(len(results), 1),
        "avg_confidence": sum(r["avg_confidence"] for r in results) / max(len(results), 1),
    }

    summary_path = output_dir / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=== SUMMARY ===")
    print(f"Processed: {processed}/{len(pdfs)}")
    print(f"Failed: {failed}")
    print(f"Avg entities per doc: {summary['avg_entities']:.1f}")
    print(f"Avg BOQ items per doc: {summary['avg_boq_items']:.1f}")
    print(f"Avg confidence: {summary['avg_confidence']:.2f}")
    print(f"Results saved to: {output_dir}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Process real RFQ PDFs through extraction pipeline")
    parser.add_argument("--input", type=str, default="data/real_rfqs/raw", help="Input PDF directory")
    parser.add_argument("--output", type=str, default="data/real_rfqs/extracted", help="Output JSON directory")
    parser.add_argument("--manifest", type=str, default=None, help="Manifest JSON path")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    manifest_path = Path(args.manifest) if args.manifest else input_dir / "manifest.json"

    process_pdfs(input_dir, output_dir, manifest_path)


if __name__ == "__main__":
    main()
