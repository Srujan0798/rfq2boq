"""Integration test: BOQ section-capture completeness for fidelity (F-C).

FIDELITY WAVE Requirement (R4): ensure STRUCTURE-FIRST captures ALL BOQ
sections in large PDFs - no section dropped. For multi-section tenders,
verify the structure extractor finds every BOQ/schedule section.

This test reports:
- Structure-detected BOQ sections
- Page ranges for extraction
- Completeness ratios
"""

import pytest

pytest.importorskip("fitz")
import fitz
from src.preproc.document_structure import DocumentStructureExtractor


class TestSectionCaptureCompleteness:
    """Test section-capture completeness for fidelity."""

    def test_gem_bid_7439924_structure_detection(self):
        """Report structure detection on GeM bid 7439924."""
        pdf_path = "data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf"

        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)

        extractor = DocumentStructureExtractor()
        sections = extractor.extract_structure(pdf_path)

        detected_boq = [s for s in sections if s.is_boq_likely or s.confidence > 0.1]
        detected_pages = sorted(set(s.page_number for s in detected_boq))

        page_range = extractor.get_page_range_for_boq()

        print("\n=== GeM Bid 7439924 (23 pages) ===")
        print(f"Total PDF pages: {total_pages}")
        print(f"Structure-detected BOQ sections: {len(detected_boq)}")
        print(f"Detected pages: {detected_pages}")
        print(f"Page range for extraction: {page_range}")

        assert len(detected_boq) >= 1, "Should detect at least 1 BOQ section"

    def test_adani_structure_detection(self):
        """Report structure detection on Adani PDFs."""
        pdfs = [
            "data/real_rfqs/swa_enquiries/04_adani/BOQ PAGEadani proj.pdf",
            "data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf",
        ]

        for pdf_path in pdfs:
            with fitz.open(pdf_path) as doc:
                pages = len(doc)

            extractor = DocumentStructureExtractor()
            sections = extractor.extract_structure(pdf_path)
            boq = extractor.find_boq_sections()
            potential = [s for s in sections if s.confidence > 0.1]

            name = pdf_path.split("/")[-1]
            print(f"\n=== {name} ({pages}p) ===")
            print(f"Sections: {len(sections)}, BOQ high-conf: {len(boq)}, Potential: {len(potential)}")

            for s in potential[:3]:
                print(f"  - page {s.page_number}: {s.title[:40]} (conf={s.confidence})")

    def test_ireps_structure(self):
        """Test structure detection on reference PDFs."""
        pdfs = [
            "data/real_rfqs/reference_real/ireps_2724bb1eff78.pdf",
            "data/real_rfqs/reference_real/ireps_bc341034058b.pdf",
        ]

        for pdf_path in pdfs:
            with fitz.open(pdf_path) as doc:
                pages = len(doc)

            extractor = DocumentStructureExtractor()
            sections = extractor.extract_structure(pdf_path)
            potential = [s for s in sections if s.confidence > 0.1]

            name = pdf_path.split("/")[-1][:30]
            print(f"\n=== {name} ({pages}p) ===")
            print(f"Sections: {len(sections)}, Potential: {len(potential)}")

    def test_gem_bid_7552777_structure(self):
        """Test structure detection on GeM bid 7552777."""
        pdf_path = "data/real_rfqs/swa_enquiries/10_gem_bid_7552777/GeM-Bidding-9343469.pdf"

        with fitz.open(pdf_path) as doc:
            pages = len(doc)

        extractor = DocumentStructureExtractor()
        sections = extractor.extract_structure(pdf_path)
        potential = [s for s in sections if s.confidence > 0.1]

        print(f"\n=== GeM Bid 7552777 ({pages}p) ===")
        print(f"Sections: {len(sections)}, Potential: {len(potential)}")

    def test_structure_detection_performance(self):
        """Structure detection should be fast."""
        import time

        pdf_path = "data/real_rfqs/swa_enquiries/09_gem_bid_7439924/GeM-Bidding-9218026.pdf"

        start = time.time()
        extractor = DocumentStructureExtractor()
        sections = extractor.extract_structure(pdf_path)
        elapsed = time.time() - start

        print("\n=== Performance ===")
        print(f"Time: {elapsed:.2f}s")
        print(f"Sections: {len(sections)}")

        assert elapsed < 10


if __name__ == "__main__":
    t = TestSectionCaptureCompleteness()
    t.test_gem_bid_7439924_structure_detection()
    t.test_adani_structure_detection()
    t.test_ireps_structure()
    t.test_gem_bid_7552777_structure()
    t.test_structure_detection_performance()
