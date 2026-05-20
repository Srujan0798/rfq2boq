#!/usr/bin/env python3
"""Collect and organize real RFQ tender PDFs."""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest.pdf_extractor import PDFExtractor


def scan_existing_pdfs(raw_dir: Path) -> list[dict]:
    """Scan existing PDFs and categorize them."""
    pdfs = list(raw_dir.glob("*.pdf"))

    sources = {
        "ireps": [],
        "cpwd": [],
        "delhi_pwd": [],
        "synthetic_building": [],
        "synthetic_road": [],
        "synthetic_bridge": [],
        "synthetic_electrical": [],
        "synthetic_plumbing": [],
        "unknown": [],
    }

    for pdf in pdfs:
        name = pdf.name.lower()
        if "ireps" in name:
            sources["ireps"].append(pdf.name)
        elif "cpwd" in name:
            sources["cpwd"].append(pdf.name)
        elif "delhi" in name or "pwd" in name:
            sources["delhi_pwd"].append(pdf.name)
        elif "rfq_building" in name:
            sources["synthetic_building"].append(pdf.name)
        elif "rfq_road" in name:
            sources["synthetic_road"].append(pdf.name)
        elif "rfq_bridge" in name:
            sources["synthetic_bridge"].append(pdf.name)
        elif "rfq_electrical" in name:
            sources["synthetic_electrical"].append(pdf.name)
        elif "rfq_plumbing" in name:
            sources["synthetic_plumbing"].append(pdf.name)
        else:
            sources["unknown"].append(pdf.name)

    return sources


def create_manifest(raw_dir: Path, output_path: Path) -> dict:
    """Create manifest.json for collected PDFs."""
    sources = scan_existing_pdfs(raw_dir)

    manifest = {
        "version": "1.0",
        "created": datetime.now().isoformat(),
        "total_pdfs": sum(len(v) for v in sources.values()),
        "source_breakdown": {k: len(v) for k, v in sources.items()},
        "provenance": {
            "ireps": "IREPS (Indian Railway Electronic Procurement System) - real government tenders",
            "cpwd": "CPWD (Central Public Works Department) - real government tenders",
            "delhi_pwd": "Delhi PWD - real government tenders",
            "synthetic_building": "Synthetic building construction RFQs",
            "synthetic_road": "Synthetic road construction RFQs",
            "synthetic_bridge": "Synthetic bridge construction RFQs",
            "synthetic_electrical": "Synthetic electrical RFQs",
            "synthetic_plumbing": "Synthetic plumbing RFQs",
        },
        "files": [],
        "notes": {
            "real_tenders": ["ireps", "cpwd", "delhi_pwd"],
            "synthetic_tenders": ["synthetic_building", "synthetic_road", "synthetic_bridge", "synthetic_electrical", "synthetic_plumbing"],
        }
    }

    extractor = PDFExtractor()

    for category, files in sources.items():
        for filename in files:
            pdf_path = raw_dir / filename
            if not pdf_path.exists():
                continue

            try:
                doc = extractor.extract(str(pdf_path))
                pages = len(doc.pages)
                chars = sum(len(p.text) for p in doc.pages)
                is_scanned = doc.is_scanned

                manifest["files"].append({
                    "filename": filename,
                    "category": category,
                    "is_real": category in ["ireps", "cpwd", "delhi_pwd"],
                    "is_synthetic": "synthetic" in category,
                    "pages": pages,
                    "chars": chars,
                    "is_scanned": is_scanned,
                })
            except Exception as e:
                manifest["files"].append({
                    "filename": filename,
                    "category": category,
                    "is_real": category in ["ireps", "cpwd", "delhi_pwd"],
                    "is_synthetic": "synthetic" in category,
                    "error": str(e),
                })

    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return manifest


def create_annotation_template(output_dir: Path) -> None:
    """Create annotation template file."""
    template = {
        "doc_id": "",
        "source_file": "",
        "tokens": [],
        "ner_tags": [],
        "entities": [],
        "relations": [],
        "metadata": {
            "annotator": "",
            "date": "",
            "agreement": None,
            "notes": "",
        }
    }

    template_path = output_dir / "gold_annotation_template.json"
    with open(template_path, 'w') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print(f"Annotation template created at {template_path}")


def generate_sample_annotations(raw_dir: Path, annotations_dir: Path, count: int = 20) -> None:
    """Generate sample gold annotations for testing."""
    extractor = PDFExtractor()

    pdfs = list(raw_dir.glob("*.pdf"))[:count]

    gold_file = annotations_dir / "gold_annotations.json"
    annotations = []

    for i, pdf_path in enumerate(pdfs):
        try:
            doc = extractor.extract(str(pdf_path))
            full_text = "\n".join(p.text for p in doc.pages)

            tokens = full_text.split()[:100]
            ner_tags = ["O"] * len(tokens)

            annotation = {
                "doc_id": f"gold_{i+1:03d}",
                "source_file": pdf_path.name,
                "tokens": tokens,
                "ner_tags": ner_tags,
                "entities": [],
                "relations": [],
                "metadata": {
                    "annotator": "pending",
                    "date": "",
                    "agreement": None,
                    "status": "pending",
                }
            }
            annotations.append(annotation)
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")

    with open(gold_file, 'w') as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)

    print(f"Created {len(annotations)} annotation templates at {gold_file}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Organize real RFQ collection")
    parser.add_argument("--raw-dir", default="data/real_rfqs/raw", help="Raw PDFs directory")
    parser.add_argument("--output-dir", default="data/real_rfqs", help="Output directory")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    output_dir = Path(args.output_dir)

    if not raw_dir.exists():
        print(f"Directory {raw_dir} not found")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / "manifest.json"
    manifest = create_manifest(raw_dir, manifest_path)
    print(f"Manifest created: {manifest_path}")
    print(f"  Total PDFs: {manifest['total_pdfs']}")
    print(f"  Real tenders: {sum(1 for f in manifest['files'] if f.get('is_real', False))}")
    print(f"  Synthetic: {sum(1 for f in manifest['files'] if f.get('is_synthetic', False))}")

    annotations_dir = output_dir / "annotations"
    annotations_dir.mkdir(exist_ok=True)

    generate_sample_annotations(raw_dir, annotations_dir, count=20)
    create_annotation_template(annotations_dir)
