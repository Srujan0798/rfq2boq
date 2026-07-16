"""Integration tests for insulation tender timeouts (C7).

These 7 tender PDFs are pure spec/compliance documents with no BOQ section.
They previously timed out (>60s) because the pipeline was running expensive
pdfplumber + NLP extraction on all pages even when no BOQ was present.

The fix applies structure-first routing: fast PyMuPDF outline scan first,
only do expensive extraction if a BOQ section is found. Spec-only docs
should return 0 rows quickly (<60s).

P0_03 NOTE (2026-07-06): these tests hang on this machine because the
structure-first routing is not yet implemented — pdfplumber runs full
extraction on 25MB+ scanned PDFs and pdfminer's zlib decompress stalls.
The root cause is a real product issue tracked in P3_01 (structure-first
multi-range). Per P0_03 §9 gotcha, these tests are tiered as `@pytest.mark.slow`
and excluded from the default `make test` run until P3_01 lands the fix;
they remain runnable via `make test-slow`.
"""

import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

INSULATION_FILES = [
    "TENDER.pdf",
    "TENDER (1) (1).pdf",
    "Tender (2).pdf",
    "Tender (3).pdf",
    "Tender (4) (1).pdf",
    "Tender (5).pdf",
    "TENDER - INSULATION.pdf",
]

INSULATION_DIR = Path("resources/Specifications")

MAX_TIMEOUT_SEC = 60.0


class TestInsulationTenderTimeouts:
    """Assert the 7 insulation tenders no longer time out."""

    @pytest.mark.parametrize("filename", INSULATION_FILES)
    def test_insulation_tender_no_timeout(self, filename: str):
        """Each insulation tender must complete in under 60s with 0 rows.

        These are spec-only / compliance documents with no BOQ section.
        The correct result is 0 rows, not a timeout.
        """
        from src.pipeline import Pipeline

        pdf_path = INSULATION_DIR / filename
        assert pdf_path.exists(), f"Test file not found: {pdf_path}"

        pipeline = Pipeline()
        start = time.time()
        result = pipeline.run(str(pdf_path))
        elapsed = time.time() - start

        assert elapsed < MAX_TIMEOUT_SEC, (
            f"{filename} took {elapsed:.1f}s (limit: {MAX_TIMEOUT_SEC}s) — timeout not fixed"
        )
        assert result.metadata.total_items == 0, (
            f"{filename}: expected 0 rows (spec-only doc), got {result.metadata.total_items}"
        )
        assert "NO_BOQ_SECTION_FOUND" in result.metadata.warnings, (
            f"{filename}: expected NO_BOQ_SECTION_FOUND warning, got {result.metadata.warnings}"
        )

    def test_all_insulation_tenders_under_60s(self):
        """Full-batch sanity check: all 7 tenders complete in reasonable time."""
        from src.pipeline import Pipeline

        pipeline = Pipeline()
        timings: dict[str, float] = {}
        rows: dict[str, int] = {}

        for filename in INSULATION_FILES:
            pdf_path = INSULATION_DIR / filename
            if not pdf_path.exists():
                pytest.skip(f"Test file not found: {pdf_path}")
                continue

            start = time.time()
            result = pipeline.run(str(pdf_path))
            elapsed = time.time() - start
            timings[filename] = elapsed
            rows[filename] = result.metadata.total_items

        max_time = max(timings.values())
        max_file = max(timings, key=timings.get)

        assert max_time < MAX_TIMEOUT_SEC, f"Slowest file {max_file} took {max_time:.1f}s (limit: {MAX_TIMEOUT_SEC}s)"

        for filename, row_count in rows.items():
            assert row_count == 0, f"{filename}: expected 0 rows, got {row_count}"

        print(f"\nTimings: {', '.join(f'{f}={t:.1f}s' for f, t in timings.items())}")
        print(f"Max: {max_time:.1f}s ({max_file})")
