# Operations Runbook

## Deployment

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Restart services
docker-compose restart api

# Stop services
docker-compose down
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RFQ2BOQ_MODEL_DIR` | `models/ner-bert-bilstm-crf-v1` | Path to trained model |
| `RFQ2BOQ_ONTOLOGY_DIR` | `src/ontology` | Path to ontology JSON files |
| `RFQ2BOQ_MAX_FILE_SIZE_MB` | `50` | Maximum upload file size |
| `RFQ2BOQ_CORS_ORIGINS` | `*` | Allowed CORS origins |
| `RFQ2BOQ_LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR) |
| `RFQ2BOQ_RATE_LIMIT` | `10` | Requests per minute per IP |

## Monitoring

### Health Endpoints

```bash
# Basic health
curl http://localhost:8000/api/health

# Readiness (model loaded)
curl http://localhost:8000/api/ready

# Prometheus metrics
curl http://localhost:8000/metrics
```

### Key Metrics

| Metric | Description | Alert threshold |
|--------|-------------|-----------------|
| `rfq2boq_requests_total` | Total requests | - |
| `rfq2boq_latency_seconds` | Request latency histogram | p95 > 30s |
| `rfq2boq_errors_total` | Error count | rate > 1% |
| `rfq2boq_entities_extracted` | Total entities extracted | - |
| `rfq2boq_model_loaded` | Model load status (1/0) | 0 = down |

### Log Files

| Path | Content |
|------|---------|
| `logs/app.log` | Application logs (rotated, 10MB max, 5 backups) |
| `data/jobs/*.json` | Background job state files |

## Troubleshooting

### Common Issues

**Model won't load**
```bash
# Check model directory exists
ls -la models/ner-bert-bilstm-crf-v1/

# Check model.pt exists
ls -la models/ner-bert-bilstm-crf-v1/model.pt

# Check disk space
df -h
```

**High memory usage**
```bash
# Check memory usage of container
docker stats

# Restart to clear memory
docker-compose restart api
```

**Slow processing**
```bash
# Check logs for timing info
grep "timing" logs/app.log | tail -20

# Check PDF page count
python3 -c "
import pdfplumber
with pdfplumber.open('sample.pdf') as pdf:
    print(f'Pages: {len(pdf.pages)}')
"
```

**Rate limit errors**
```bash
# Check current rate limit config
grep RATE_LIMIT .env

# Increase limit
echo "RFQ2BOQ_RATE_LIMIT=30" >> .env
docker-compose restart api
```

### Debug Mode

Enable debug logging:
```bash
echo "RFQ2BOQ_LOG_LEVEL=DEBUG" >> .env
docker-compose restart api
docker-compose logs -f api | grep DEBUG
```

## Backup and Recovery

### Model Backup

```bash
# Backup model directory
tar -czf model-backup-$(date +%Y%m%d).tar.gz models/ner-bert-bilstm-crf-v1/

# Restore from backup
tar -xzf model-backup-20240115.tar.gz -C models/
```

### Job State Recovery

```bash
# List recent jobs
ls -lt data/jobs/ | head -10

# Clean old jobs (>24h)
python3 -c "
from pathlib import Path
import time
jobs_dir = Path('data/jobs')
cutoff = time.time() - 86400
for f in jobs_dir.glob('*.json'):
    if f.stat().st_mtime < cutoff:
        f.unlink()
        print(f'Removed: {f.name}')
"
```

## Scaling

### Vertical Scaling

For higher throughput:
```yaml
# docker-compose.override.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

### Horizontal Scaling

For multi-instance deployment:
```yaml
# docker-compose.scale.yml
services:
  api:
    image: rfq2boq-api
    deploy:
      replicas: 3
    ports:
      - "8000:8000"
    depends_on:
      - redis
  redis:
    image: redis:7-alpine
```

Use a load balancer (nginx, traefik) in front of multiple replicas.

## Rotation

### Log Rotation

Logs automatically rotate at 10MB with 5 backups kept. Old logs are deleted after 5 rotations.

### Model Rotation

To update the model without downtime:
1. Deploy new model to `models/ner-bert-bilstm-crf-v2/`
2. Update `RFQ2BOQ_MODEL_DIR` env var
3. Rolling restart: `docker-compose up -d --no-deps --scale api=0 && docker-compose up -d --no-deps --scale api=1`
4. Monitor for errors
5. Remove old model directory after validation

## Escalation

| Issue | Action |
|-------|--------|
| API down | Check logs, restart service, verify model files |
| High error rate | Enable DEBUG logging, check data quality |
| Memory leak | Restart service, check for file descriptor leaks |
| Disk full | Clean old job files, rotate logs, expand disk |