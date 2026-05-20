"""Observability - Prometheus metrics, Grafana dashboards, alerts."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest

logger = logging.getLogger(__name__)


@dataclass
class Metrics:
    requests_total: Any
    request_duration_seconds: Any
    extractions_total: Any
    extraction_duration_seconds: Any
    active_requests: Any
    model_load_status: Any
    cache_hits_total: Any
    cache_misses_total: Any
    error_total: Any


def create_metrics() -> Metrics:
    registry = CollectorRegistry()

    requests_total = Counter(
        "rfq2boq_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status"],
        registry=registry,
    )
    request_duration_seconds = Histogram(
        "rfq2boq_request_duration_seconds",
        "Request duration in seconds",
        ["method", "endpoint"],
        buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        registry=registry,
    )
    extractions_total = Counter(
        "rfq2boq_extractions_total",
        "Total extraction requests",
        ["status"],
        registry=registry,
    )
    extraction_duration_seconds = Histogram(
        "rfq2boq_extraction_duration_seconds",
        "Extraction processing time",
        ["source"],
        buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
        registry=registry,
    )
    active_requests = Gauge(
        "rfq2boq_active_requests",
        "Number of active requests",
        registry=registry,
    )
    model_load_status = Gauge(
        "rfq2boq_model_load_status",
        "Model loading status (1=loaded, 0=not loaded)",
        registry=registry,
    )
    cache_hits_total = Counter(
        "rfq2boq_cache_hits_total",
        "Total cache hits",
        registry=registry,
    )
    cache_misses_total = Counter(
        "rfq2boq_cache_misses_total",
        "Total cache misses",
        registry=registry,
    )
    error_total = Counter(
        "rfq2boq_errors_total",
        "Total errors",
        ["type"],
        registry=registry,
    )

    return Metrics(
        requests_total=requests_total,
        request_duration_seconds=request_duration_seconds,
        extractions_total=extractions_total,
        extraction_duration_seconds=extraction_duration_seconds,
        active_requests=active_requests,
        model_load_status=model_load_status,
        cache_hits_total=cache_hits_total,
        cache_misses_total=cache_misses_total,
        error_total=error_total,
    )


metrics = create_metrics()


class PrometheusMiddleware:
    def __init__(self):
        self.requests = 0

    async def __call__(self, request, call_next):
        metrics.active_requests.inc()
        start = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start
            metrics.requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=response.status_code,
            ).inc()
            metrics.request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(duration)
            return response
        except Exception as e:
            metrics.error_total.labels(type=type(e).__name__).inc()
            raise
        finally:
            metrics.active_requests.dec()


class GrafanaDashboard:
    @staticmethod
    def generate_dashboard_json() -> dict[str, Any]:
        return {
            "dashboard": {
                "title": "RFQ2BOQ Monitoring",
                "panels": [
                    {
                        "title": "Request Rate",
                        "type": "graph",
                        "targets": [{"expr": "rate(rfq2boq_requests_total[5m])"}],
                    },
                    {
                        "title": "Request Latency (p95)",
                        "type": "graph",
                        "targets": [{"expr": "histogram_quantile(0.95, rate(rfq2boq_request_duration_seconds_bucket[5m]))"}],
                    },
                    {
                        "title": "Extraction Success Rate",
                        "type": "graph",
                        "targets": [{"expr": "rate(rfq2boq_extractions_total{status='success'}[5m]) / rate(rfq2boq_extractions_total[5m])"}],
                    },
                    {
                        "title": "Cache Hit Ratio",
                        "type": "gauge",
                        "targets": [{"expr": "rate(rfq2boq_cache_hits_total[5m]) / (rate(rfq2boq_cache_hits_total[5m]) + rate(rfq2boq_cache_misses_total[5m]))"}],
                    },
                    {
                        "title": "Active Requests",
                        "type": "stat",
                        "targets": [{"expr": "rfq2boq_active_requests"}],
                    },
                    {
                        "title": "Error Rate",
                        "type": "graph",
                        "targets": [{"expr": "rate(rfq2boq_errors_total[5m])"}],
                    },
                ],
            }
        }

    @staticmethod
    def save_dashboard(output_path: str = "deployment/grafana/dashboard.json"):
        dashboard = GrafanaDashboard.generate_dashboard_json()
        import json
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(dashboard, f, indent=2)
        logger.info(f"Dashboard saved to {output_path}")


class AlertingRules:
    @staticmethod
    def generate_alert_rules() -> dict[str, Any]:
        return {
            "groups": [
                {
                    "name": "rfq2boq.alerts",
                    "rules": [
                        {
                            "alert": "HighErrorRate",
                            "expr": "rate(rfq2boq_errors_total[5m]) > 0.05",
                            "for": "5m",
                            "labels": {"severity": "critical"},
                            "annotations": {
                                "summary": "RFQ2BOQ error rate above 5%",
                                "description": "Error rate is {{ $value }} errors/sec",
                            },
                        },
                        {
                            "alert": "HighLatency",
                            "expr": "histogram_quantile(0.95, rate(rfq2boq_request_duration_seconds_bucket[5m])) > 10",
                            "for": "5m",
                            "labels": {"severity": "warning"},
                            "annotations": {
                                "summary": "RFQ2BOQ p95 latency above 10s",
                                "description": "p95 latency is {{ $value }}s",
                            },
                        },
                        {
                            "alert": "ModelNotLoaded",
                            "expr": "rfq2boq_model_load_status == 0",
                            "for": "1m",
                            "labels": {"severity": "critical"},
                            "annotations": {
                                "summary": "ML model not loaded",
                                "description": "Model loading failed or not attempted",
                            },
                        },
                        {
                            "alert": "LowCacheHitRatio",
                            "expr": "rate(rfq2boq_cache_hits_total[5m]) / (rate(rfq2boq_cache_hits_total[5m]) + rate(rfq2boq_cache_misses_total[5m])) < 0.5",
                            "for": "10m",
                            "labels": {"severity": "warning"},
                            "annotations": {
                                "summary": "Cache hit ratio below 50%",
                                "description": "Current cache hit ratio: {{ $value }}",
                            },
                        },
                    ],
                }
            ]
        }

    @staticmethod
    def save_alert_rules(output_path: str = "deployment/grafana/alerts.yml"):
        import yaml
        rules = AlertingRules.generate_alert_rules()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            yaml.dump(rules, f)
        logger.info(f"Alert rules saved to {output_path}")


def get_metrics() -> bytes:
    return generate_latest()


def get_content_type() -> str:
    return CONTENT_TYPE_LATEST
