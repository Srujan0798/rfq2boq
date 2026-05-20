#!/usr/bin/env python3
"""Batch process all real PDFs and generate BOQ."""

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest.pdf_extractor import PDFExtractor
from src.nlp.pipeline import NLPPipeline


def process_all_pdfs(pdf_dir, output_dir):
    pdf_dir = Path(pdf_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    pdfs = list(pdf_dir.glob("*.pdf"))
    print(f"Found {len(pdfs)} PDFs to process")

    pipeline = NLPPipeline()
    extractor = PDFExtractor()

    results = []
    stats = defaultdict(int)

    for i, pdf_path in enumerate(pdfs):
        print(f"[{i+1}/{len(pdfs)}] Processing {pdf_path.name}...", end=" ", flush=True)

        try:
            doc = extractor.extract(str(pdf_path))
            full_text = "\n".join(page.text for page in doc.pages)

            result = pipeline.process(full_text)

            stats['total_pdfs'] += 1
            stats['total_entities'] += len(result.entities)
            stats['warnings'] += len(result.warnings)

            out_file = output_dir / f"{pdf_path.stem}_result.json"
            with open(out_file, 'w') as f:
                json.dump({
                    'doc_id': pdf_path.stem,
                    'source_file': str(pdf_path),
                    'entities': result.entities,
                    'relations': result.relations,
                    'warnings': result.warnings,
                    'avg_confidence': result.confidence,
                }, f, indent=2, default=str)

            print(f"✓ {len(result.entities)} entities, conf={result.confidence:.2f}")
            results.append({
                'pdf': pdf_path.name,
                'entities': len(result.entities),
                'relations': len(result.relations),
                'confidence': result.confidence,
                'status': 'success'
            })

        except Exception as e:
            print(f"✗ Error: {e}")
            results.append({'pdf': pdf_path.name, 'status': 'error', 'error': str(e)})
            stats['errors'] += 1

    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            'stats': dict(stats),
            'results': results
        }, f, indent=2)

    print("\n=== SUMMARY ===")
    print(f"Processed: {stats['total_pdfs']} PDFs")
    print(f"Total entities: {stats['total_entities']}")
    print(f"Avg confidence: {sum(r.get('confidence', 0) for r in results if r.get('status') == 'success') / max(1, len([r for r in results if r.get('status') == 'success'])):.3f}")
    print(f"Errors: {stats.get('errors', 0)}")
    print(f"Results saved to: {output_dir}")
    return stats


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Batch process PDFs")
    parser.add_argument("--pdf-dir", default="data/real_rfqs/raw", help="Directory with PDFs")
    parser.add_argument("--output-dir", default="data/real_rfqs/extracted", help="Output directory")
    args = parser.parse_args()

    process_all_pdfs(args.pdf_dir, args.output_dir)
