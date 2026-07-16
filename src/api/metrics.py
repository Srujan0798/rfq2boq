"""Prometheus metrics for RFQ2BOQ."""

import time
from collections import defaultdict

from prometheus_client import Counter, Gauge, Histogram, generate_latest

REQUEST_COUNT = Counter(
    "rfq2boq_requests_total",
    "Total requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "rfq2boq_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ENTITY_EXTRACTION_COUNT = Counter(
    "rfq2boq_entities_extracted_total",
    "Total entities extracted",
    ["entity_type", "source"],
)

BOQ_ITEMS_COUNT = Histogram(
    "rfq2boq_boq_items_count",
    "Number of BOQ items per extraction",
    buckets=[1, 2, 5, 10, 20, 50],
)

MODEL_LOAD_STATUS = Gauge(
    "rfq2boq_model_loaded",
    "Whether NER model is loaded (1=yes, 0=no)",
)

ONTOLOGY_LOAD_STATUS = Gauge(
    "rfq2boq_ontology_loaded",
    "Whether ontology is loaded (1=yes, 0=no)",
)

MEMORY_USAGE_BYTES = Gauge(
    "rfq2boq_memory_usage_bytes",
    "Current memory usage in bytes",
)

GPU_AVAILABLE = Gauge(
    "rfq2boq_gpu_available",
    "Whether GPU is available for inference (1=yes, 0=no)",
)

ERROR_COUNT = Counter(
    "rfq2boq_errors_total",
    "Total errors",
    ["error_type"],
)

EXTRACTION_CONFIDENCE = Histogram(
    "rfq2boq_extraction_confidence",
    "Confidence score of extractions",
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)


class MetricsCollector:
    """Collect and aggregate metrics for RFQ2BOQ."""

    def __init__(self):
        self._request_counts = defaultdict(int)
        self._entity_counts = defaultdict(int)
        self._error_counts = defaultdict(int)
        self._start_time = time.time()

    def record_request(self, method: str, endpoint: str, status: int, latency: float):
        """Record an API request."""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)

    def record_entities(self, entities: list[dict]):
        """Record entity extraction."""
        for entity in entities:
            entity_type = entity.get("type", "UNKNOWN")
            source = entity.get("source", "unknown")
            ENTITY_EXTRACTION_COUNT.labels(entity_type=entity_type, source=source).inc()

    def record_boq_items(self, count: int):
        """Record BOQ item count."""
        BOQ_ITEMS_COUNT.observe(count)

    def record_extraction_confidence(self, confidence: float):
        """Record extraction confidence score."""
        EXTRACTION_CONFIDENCE.observe(confidence)

    def record_error(self, error_type: str):
        """Record an error."""
        ERROR_COUNT.labels(error_type=error_type).inc()

    def set_model_loaded(self, loaded: bool):
        """Set model loaded status."""
        MODEL_LOAD_STATUS.set(1 if loaded else 0)

    def set_ontology_loaded(self, loaded: bool):
        """Set ontology loaded status."""
        ONTOLOGY_LOAD_STATUS.set(1 if loaded else 0)

    def set_memory_usage(self, bytes_used: int):
        """Set memory usage."""
        MEMORY_USAGE_BYTES.set(bytes_used)

    def set_gpu_available(self, available: bool):
        """Set GPU availability."""
        GPU_AVAILABLE.set(1 if available else 0)


_metrics = MetricsCollector()


def get_metrics() -> bytes:
    """Get all metrics in Prometheus format."""
    return generate_latest()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector."""
    return _metrics
