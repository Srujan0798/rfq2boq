# TASK: C3 Observability — Tracing, Logging, Dashboards, Tests

**Wave:** 4 | **Tier:** C | **Priority:** P2

## 1. GOAL

Complete the observability implementation by adding: observability package (tracing, logging), Grafana dashboard for infrastructure, Loki/Tempo configs, alerts, and test file.

## 2. CONTEXT

Files to read first:
- `src/api/metrics.py` — existing Prometheus metrics
- `src/api/metrics_observability.py` — existing observability metrics
- `src/api/main.py` — existing app entry point
- `deployment/grafana/dashboards/overview.json` — existing dashboard
- `deployment/grafana/dashboards/model_performance.json` — existing dashboard
- `pyproject.toml` — pytest configuration

## 3. DELIVERABLES

Exact paths to create:
1. `src/observability/__init__.py` — package init
2. `src/observability/tracing.py` — OpenTelemetry tracing setup
3. `src/observability/logging.py` — structured logging (JSON format, log levels)
4. `src/observability/metrics.py` — metrics wrapper (re-exports from src/api/metrics.py with extra)
5. `tests/unit/test_observability.py` — test file
6. `deployment/prometheus/prometheus.yml` — Prometheus scrape config
7. `deployment/grafana/dashboards/infra.json` — infrastructure dashboard (3rd dashboard)
8. `deployment/loki/loki-config.yml` — Loki configuration
9. `deployment/tempo/tempo-config.yml` — Tempo configuration
10. `deployment/alerts.py` — Prometheus alerting rules (Python → YAML)
11. `deployment/alerts.yml` — generated alerts YAML

Also update:
- `src/api/main.py` — add tracing/logging initialization on startup
- `docker-compose.yml` — add Loki and Tempo services if not present

## 4. STEPS

1. **Create `src/observability/__init__.py`:**
   - Exports: `setup_tracing`, `setup_logging`, `get_tracer`, `get_logger`
   - Version: `__version__ = "1.0.0"`

2. **Create `src/observability/tracing.py`:**
   - `setup_tracing(service_name: str)` — configure OpenTelemetry with OTLP exporter
   - `get_tracer(name: str)` — return a tracer for the given name
   - Support for both Jaeger and Tempo backends via env var `OTEL_EXPORTER_OTLP_ENDPOINT`
   - Add span attributes for: tenant_id, user_id, model_version, request_id

3. **Create `src/observability/logging.py`:**
   - `setup_logging(level: str = "INFO", format: str = "json")` — configure structured logging
   - `get_logger(name: str)` — return a logger with context
   - JSON format: `{"time": "...", "level": "...", "name": "...", "message": "...", "tenant_id": "...", "trace_id": "..."}`
   - Add correlation IDs (trace_id, span_id) to every log entry when available
   - Use `structlog` if available, else standard `logging` with custom JSON encoder

4. **Create `src/observability/metrics.py`:**
   - Re-export all metrics from `src.api.metrics`
   - Add `OBSERVABILITY_METRICS` dict for internal observability metrics
   - `increment_counter(name, labels)` and `record_gauge(name, value, labels)` helpers

5. **Create `tests/unit/test_observability.py`:**
   - `TestTracing` — test tracer creation, span creation, attributes
   - `TestLogging` — test logger creation, JSON output, correlation IDs
   - `TestMetrics` — test metric increment and gauge recording
   - Mock OpenTelemetry and structlog appropriately

6. **Create `deployment/prometheus/prometheus.yml`:**
   - Scrape config for the FastAPI app (`localhost:8000`)
   - Scrape config for node-exporter, redis-exporter if available
   - Alerting rules for: high error rate, high latency, low success rate

7. **Create `deployment/grafana/dashboards/infra.json`:**
   - Panels: CPU usage, Memory usage, Disk I/O, Network, Pod/Container restarts
   - Use data source: Prometheus
   - Variables: tenant_id, instance
   - Base it on the existing overview.json structure

8. **Create `deployment/loki/loki-config.yml`:**
   - Local file scraping (logs from `/app/logs/`)
   - Remote write for structured logs
   - Retention: 30 days

9. **Create `deployment/tempo/tempo-config.yml`:**
   - OTLP receiver (grpc:4317, http:4318)
   - Storage: local file (`/var/tempo`)
   - Retention: 30 days

10. **Create `deployment/alerts.py`** and generate **`deployment/alerts.yml`:**
    - Alert rules: `HighErrorRate`, `HighLatencyP95`, `LowSuccessRate`, `QueueBacklog`
    - Python script generates YAML for Prometheus alertmanager

11. **Update `src/api/main.py`:**
    - Add `from src.observability import setup_tracing, setup_logging` on startup
    - Call `setup_tracing("rfq2boq-api")` and `setup_logging()` before app startup
    - Add `/health` and `/ready` endpoints if not already present

12. **Update `docker-compose.yml`:**
    - Add `loki` service (image: grafana/loki:latest)
    - Add `tempo` service (image: grafana/tempo:latest)
    - Add `promtail` service for log collection

## 5. VERIFICATION

```bash
# Test observability package
python3 -c "from src.observability import setup_tracing, setup_logging; print('OK')"

# Run observability tests
python3 -m pytest tests/unit/test_observability.py -v --tb=short

# Verify configs exist
ls deployment/prometheus/prometheus.yml
ls deployment/loki/loki-config.yml
ls deployment/tempo/tempo-config.yml
ls deployment/grafana/dashboards/infra.json

# Generate alerts
python3 deployment/alerts.py && cat deployment/alerts.yml | head -20

# Verify docker-compose has loki/tempo
grep -E "loki|tempo" docker-compose.yml

# ruff check new files
ruff check src/observability/ tests/unit/test_observability.py
```

## 6. ACCEPTANCE CRITERIA

- [ ] `src/observability/` package has `tracing.py`, `logging.py`, `metrics.py`, `__init__.py`
- [ ] `tests/unit/test_observability.py` exists with ≥15 passing tests
- [ ] `deployment/prometheus/prometheus.yml` exists and is valid YAML
- [ ] `deployment/loki/loki-config.yml` and `deployment/tempo/tempo-config.yml` exist
- [ ] `deployment/grafana/dashboards/infra.json` is a valid Grafana dashboard JSON
- [ ] `deployment/alerts.yml` generated from `deployment/alerts.py`
- [ ] `docker-compose.yml` includes loki and tempo services
- [ ] `src/api/main.py` calls `setup_tracing` and `setup_logging` on startup
- [ ] All new files pass `ruff check`

## 7. CONSTRAINTS

- Python 3.11–3.13 only
- Type hints required on all new code
- Use `src.` import prefix
- Observability must NOT block normal app operation (graceful degradation if tracing/logging unavailable)
- If `structlog` is not installed, use standard `logging` with a custom JSON formatter

## 8. DEPENDENCIES

- Blocks: None
- Blocked by: C2 Security (shares auth context for tenant_id in traces)

## 9. GOTCHAS

- Tracing setup must be called BEFORE any FastAPI routes are loaded (import order matters)
- JSON logging must handle non-serializable objects gracefully (use str() fallback)
- Grafana dashboard JSON must have correct `uid` and `version` fields
- Loki config must point to correct log paths; create parent directories with `mkdir -p` in the container
