# TASK: Observability Stack — Agent-3

**Wave:** 4 | **Tier:** C | **Priority:** P2

## 1. GOAL
Production observability: Prometheus metrics, Grafana dashboards, Loki logs, OpenTelemetry traces, Sentry errors, alerting on SLO breaches.

## 2. CONTEXT
Read first:
- `src/api/main.py` — FastAPI app
- `src/nlp/pipeline.py` — instrument inference
- `docker-compose.yml`
- [docs/conventions.md](../../docs/conventions.md)

Current state: Print-based logs, no metrics, no tracing, no alerts.

## 3. DELIVERABLES
- [ ] `src/observability/__init__.py`
- [ ] `src/observability/metrics.py` — Prometheus metrics
- [ ] `src/observability/tracing.py` — OpenTelemetry setup
- [ ] `src/observability/logging.py` — structured JSON logging
- [ ] `src/api/metrics.py` — `/metrics` endpoint
- [ ] `deployment/prometheus/prometheus.yml` — scrape config
- [ ] `deployment/grafana/dashboards/` — 3 dashboards (overview, model, infra)
- [ ] `deployment/loki/loki-config.yml` — log aggregation
- [ ] `deployment/tempo/tempo-config.yml` — distributed tracing backend
- [ ] `deployment/alerts.yml` — Prometheus alertmanager rules
- [ ] `docker-compose.yml` — add prometheus, grafana, loki, tempo services
- [ ] `tests/unit/test_observability.py` — ≥6 tests

## 4. STEPS
1. Instrument with `prometheus_client`: request_count, request_duration, model_latency, entities_per_request, confidence_distribution
2. OpenTelemetry: trace each pipeline stage (PDF → ingest → NER → RE → export)
3. Structured logging: JSON format, ship to Loki via Promtail
4. Sentry SDK for error tracking
5. Grafana dashboards as JSON + provisioning config
6. Alertmanager rules:
   - p95 latency > 5s
   - error rate > 1%
   - model confidence drift > 10%
   - disk > 80%
   - GPU memory > 90%
7. Docker compose stack: prometheus + grafana + loki + tempo + sentry-relay

## 5. VERIFICATION
```bash
$ curl http://localhost:8000/metrics | grep -c "rfq2boq_"
EXPECT: ≥10 metrics

$ curl http://localhost:9090/api/v1/targets | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='success'"
EXPECT: no AssertionError

$ curl -s http://localhost:3000/api/dashboards/uid/overview
EXPECT: 200 OK with dashboard JSON

$ python3 -m pytest tests/unit/test_observability.py -v
EXPECT: ≥6 passed
```

## 6. ACCEPTANCE CRITERIA
- [ ] Prometheus scrapes /metrics every 15s
- [ ] 3 Grafana dashboards rendered and useful
- [ ] Loki ingests app logs
- [ ] Tempo traces span the full pipeline
- [ ] Sentry captures unhandled exceptions
- [ ] Alerts fire correctly in test scenarios
- [ ] Coverage ≥80% on new code

## 7. CONSTRAINTS
- All imports `src.` prefix
- Metric labels: low cardinality (no user_id, no PII)
- Logs: JSON format, never log full document content at INFO+
- Tracing sampling: 100% in dev, 10% in prod (configurable)

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** None
- **Parallel-safe with:** C2, C5

## 9. GOTCHAS
- Prometheus metric labels create cardinality explosion if misused — review carefully
- Loki: 1 stream per label combination; over-labeling = slow queries
- OpenTelemetry: context propagation across async boundaries needs careful setup
- Sentry: don't ship PII or full extraction text in error context
- Grafana provisioning: dashboards as JSON + datasource YAML
