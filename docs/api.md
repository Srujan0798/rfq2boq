# API Documentation

RFQ to BOQ Extraction API

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

```
GET /v1/health
```

Returns system health status.

**Response:**

```json
{
  "status": "ok",
  "model_loaded": true,
  "version": "1.0.0"
}
```

---

### Upload PDF

```
POST /v1/upload
```

Upload a PDF file for BOQ extraction.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `file` | file | Yes | PDF file to process |
| `project_name` | string | No | Project name (default: "Untitled") |
| `format` | string | No | Output format: "json" or "excel" (default: "json") |

**Example:**

```bash
curl -X POST "http://localhost:8000/v1/upload" \
  -F "file=@sample_rfq.pdf" \
  -F "project_name=Test Project"
```

**Response:**

```json
{
  "extraction_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": {
    "project_name": "Test Project",
    "extraction_date": "2024-05-15T10:30:00",
    "source_file": "sample_rfq.pdf",
    "entities": [...],
    "relations": [...],
    "boq_items": [...],
    "metadata": {
      "total_items": 25,
      "avg_confidence": 0.87,
      "processing_time_sec": 12.5,
      "pages_processed": 15,
      "entity_counts": {...},
      "warnings": []
    }
  }
}
```

---

### Extract from Text

```
POST /v1/extract
```

Extract BOQ from raw text (skip PDF ingestion).

**Request Body:**

```json
{
  "text": "Supply and install 2mm galvanized steel cladding to exterior walls as per IS 2062 Grade 43. Quantity: 500 sqm.",
  "project_name": "Test Project"
}
```

**Response:**

```json
{
  "extraction_id": "550e8400-e29b-41d4-a716-446655440000",
  "result": {
    "project_name": "Test Project",
    "extraction_date": "2024-05-15T10:30:00",
    "source_file": "text-input",
    "entities": [...],
    "relations": [...],
    "boq_items": [...],
    "metadata": {...}
  }
}
```

---

### Get BOQ Result

```
GET /v1/boq/{extraction_id}
```

Retrieve a previous extraction result.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `extraction_id` | string | Yes | Extraction ID from upload/extract |
| `format` | string | No | "json" (default) or "excel" |

**Example:**

```bash
curl "http://localhost:8000/v1/boq/550e8400-e29b-41d4-a716-446655440000"
```

**Response (JSON):**

```json
{
  "project_name": "Test Project",
  "extraction_date": "2024-05-15T10:30:00",
  "boq_items": [...],
  "metadata": {...}
}
```

**Response (Excel):**

Returns downloadable `.xlsx` file when `format=excel`.

---

### Download Excel

```
POST /v1/upload/download-excel
```

Upload a PDF and directly download Excel output.

**Parameters:**

Same as `/v1/upload`.

**Response:**

Binary Excel file download.

---

## BOQ Item Schema

Each item in `boq_items` array:

```json
{
  "item_no": 1,
  "description": "2mm galvanized steel cladding to exterior walls",
  "material": "galvanized steel",
  "grade": "Grade 43",
  "dimension": "2mm",
  "location": "exterior walls",
  "quantity": 500,
  "unit": "m²",
  "action": "install",
  "standard": ["IS 2062"],
  "confidence": 0.88,
  "source_text": "...",
  "source_pages": [3],
  "warnings": []
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad request / invalid file type |
| 404 | Extraction not found |
| 422 | Validation error |
| 500 | Internal server error |

## Error Response Schema

All errors follow this structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": {
      "field": "specific field with issue",
      "value": "the invalid value"
    },
    "request_id": "abc123"
  }
}
```

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `FILE_TOO_LARGE` | 413 | PDF exceeds 50MB limit |
| `UNSUPPORTED_FILE` | 415 | Not a PDF file |
| `EXTRACTION_FAILED` | 500 | Processing error |
| `MODEL_NOT_LOADED` | 503 | Model loading in progress |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /v1/extract` | 10 | requests/minute/IP |
| `POST /v1/upload` | 5 | requests/minute/IP |
| `GET /v1/*` | 60 | requests/minute/IP |

Rate limit headers returned:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1620123456
```

## Authentication

**Design (not yet implemented):**

| Method | Use case | Status |
|--------|----------|--------|
| API Key (`X-API-Key` header) | Production integrations | Planned |
| OAuth 2.0 (client credentials) | Enterprise deployments | Future |
| JWT tokens | Web frontend sessions | Future |

Request with API key:
```bash
curl -H "X-API-Key: your-api-key" \
     -X POST "http://localhost:8000/v1/upload" \
     -F "file=@sample.pdf"
```

## Versioning

API is versioned via URL path prefix:

| Version | Status | Notes |
|---------|--------|-------|
| `/v1` | Current | Production ready |
| `/v2` | Planned | Multi-language support |

Breaking changes will increment version. Non-breaking additions (new fields, new endpoints) do not require version bump.

## SLA Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Availability | 99.5% | Excluding planned maintenance |
| p50 latency | <5s | For 1-page text-only PDF |
| p95 latency | <30s | For 10-page mixed PDF |
| p99 latency | <60s | For complex multi-page PDF |
| Error rate | <1% | Non-timeout errors |
| Cold start | <15s | API server startup |

SLA monitoring: `GET /metrics` endpoint (Prometheus format)

## Interactive Documentation

Visit `http://localhost:8000/docs` for Swagger UI interactive documentation.
