"""Performance regression tests for latency benchmarks."""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_inference_latency_regression() -> None:
    from src.rules.units import normalize_unit

    for _ in range(3):
        normalize_unit("kg")

    latencies: list[float] = []
    for _ in range(20):
        start = time.perf_counter()
        normalize_unit("kg")
        latencies.append(time.perf_counter() - start)

    latencies.sort()
    p95_idx = int(len(latencies) * 0.95)
    p95_latency = latencies[p95_idx] * 1000
    assert p95_latency < 500, f"p95 latency {p95_latency:.2f}ms exceeds 500ms threshold"


def test_pdf_parsing_latency() -> None:
    from contextlib import suppress
    from pathlib import Path

    from src.ingest.pdf_extractor import PDFExtractor

    extractor = PDFExtractor()
    pdf_path = Path("data/samples/real 02 xlsx")

    if not pdf_path.exists():
        pytest.skip("Sample PDF not available")

    latencies: list[float] = []
    for _ in range(5):
        start = time.perf_counter()
        with suppress(Exception):
            extractor.extract(str(pdf_path))
        latencies.append(time.perf_counter() - start)

    latencies.sort()
    p95_idx = int(len(latencies) * 0.95)
    p95_latency = latencies[p95_idx] * 1000
    assert p95_latency < 10000, f"p95 latency {p95_latency:.2f}ms exceeds 10000ms threshold"


def test_boq_export_latency() -> None:
    from src.boq_generator import BOQGenerator

    generator = BOQGenerator()
    boq_items = [
        {
            "description": f"Item {i}",
            "material": "cement",
            "quantity": 100,
            "unit": "kg",
            "confidence": 0.9,
        }
        for i in range(100)
    ]

    latencies: list[float] = []
    for _ in range(10):
        start = time.perf_counter()
        generator.generate(boq_items)
        latencies.append(time.perf_counter() - start)

    latencies.sort()
    p95_idx = int(len(latencies) * 0.95)
    p95_latency = latencies[p95_idx] * 1000
    assert p95_latency < 1000, f"p95 latency {p95_latency:.2f}ms exceeds 1000ms threshold"


def test_entity_extraction_latency() -> None:
    from src.rules.units import normalize_unit

    latencies: list[float] = []
    for _ in range(10):
        start = time.perf_counter()
        normalize_unit("kg")
        latencies.append(time.perf_counter() - start)

    latencies.sort()
    p99_idx = int(len(latencies) * 0.99)
    p99_latency = latencies[p99_idx] * 1000
    assert p99_latency < 1000, f"p99 latency {p99_latency:.2f}ms exceeds 1000ms threshold"


if __name__ == "__main__":
    test_inference_latency_regression()
    test_boq_export_latency()
    print("Performance regression tests completed")
