# Deployment Guide

## Table of Contents
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [HuggingFace Spaces Deployment](#huggingface-spaces-deployment)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Production Considerations](#production-considerations)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.11+ (3.14 has CLI compatibility issues with Typer)
- Tesseract OCR (for scanned PDFs)
- 4GB RAM minimum
- 500MB disk space

## Local Setup

```bash
# Clone repository
git clone <repo-url>
cd rfq2boq

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Download spaCy model
python -m spacy download en_core_web_sm

# Set environment variables
cp .env.example .env
# Edit .env as needed
```

## Local Development with Docker

```bash
# Start services
docker-compose -f deployment/docker-compose.yml up -d

# View logs
docker-compose -f deployment/docker-compose.yml logs -f api

# Stop services
docker-compose -f deployment/docker-compose.yml down

# Rebuild
docker-compose -f deployment/docker-compose.yml build
```

API runs at `http://localhost:7860`
UI runs at `http://localhost:8501`

---

## HuggingFace Spaces Deployment

HuggingFace Spaces provides free hosting for ML applications with Docker support.

### Space URL
`https://huggingface.co/spaces/<username>/rfq2boq`

### Deployment Steps

1. **Create a new Space**
   - Go to https://huggingface.co/new-space
   - Select "Docker" as the SDK
   - Choose "public" for free tier
   - Name your space (e.g., `rfq2boq`)

2. **Clone the repository**
   ```bash
   git clone https://huggingface.co/spaces/<username>/rfq2boq
   cd rfq2boq
   ```

3. **Copy deployment files**
   ```bash
   cp deployment/Dockerfile .
   cp deployment/.env.example .env
   ```

4. **Configure environment variables**
   Edit `.env` with your settings:
   ```bash
   # Required for HF Spaces
   RFQ2BOQ_API_PORT=7860
   HF_SPACE_ID=<your-username>/rfq2boq
   ```

5. **Push to HF Spaces**
   ```bash
   git add .
   git commit -m "Add HF Spaces Docker configuration"
   git push
   ```

6. **Verify deployment**
   - Space builds automatically on push
   - Check build logs at https://huggingface.co/spaces/<username>/rfq2boq/settings
   - Access your Space at the provided URL

### Model Storage

The NER model (~433MB) fits comfortably in the 16GB free tier disk quota.

| Component | Size |
|-----------|------|
| NER Model | ~433MB |
| Dependencies | ~2GB |
| Free tier limit | 16GB |

To use a pre-trained model:
```bash
# Option 1: Mount model via volume (local development)
# Option 2: Download from HuggingFace Hub on startup
```

### Environment Variables for HF Spaces

| Variable | Value | Description |
|----------|-------|-------------|
| `RFQ2BOQ_API_PORT` | `7860` | HF Spaces requires port 7860 |
| `RFQ2BOQ_API_HOST` | `0.0.0.0` | Bind to all interfaces |
| `HF_SPACE_ID` | `<user>/rfq2boq` | Your Space identifier |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `CORS_ORIGINS` | `*` | Allow all origins |

### Health Check Setup

HF Spaces automatically monitors the `/api/health` endpoint:

```bash
# Manual health check
curl https://huggingface.co/spaces/<username>/rfq2boq/api/health

# Expected response
{
  "status": "ok",
  "version": "1.0.0",
  "model_loaded": true,
  "ontology_loaded": true,
  "disk_space_gb": 10.5,
  "memory_mb": 2048.3,
  "memory_percent": 45.2
}
```

### Logs Aggregation

Docker logs are accessible via HF Spaces UI or CLI:

```bash
# Using huggingface_hub CLI
hf space logs <username>/rfq2boq

# Local Docker logs
docker logs <container-id>
docker-compose -f deployment/docker-compose.yml logs api
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| RFQ2BOQ_API_HOST | 0.0.0.0 | API server host |
| RFQ2BOQ_API_PORT | 8000 | API server port |
| RFQ2BOQ_API_KEY | (empty) | API authentication key |
| RFQ2BOQ_MODEL_DIR | models/ner-bert-bilstm-crf-v1 | NER model directory |
| RFQ2BOQ_ONTOLOGY_DIR | src/ontology | Ontology directory |
| RFQ2BOQ_DATA_DIR | data | Data directory |
| RFQ2BOQ_TESSERACT_CMD | tesseract | Tesseract executable path |
| RFQ2BOQ_OCR_CONFIDENCE_THRESHOLD | 0.80 | Minimum OCR confidence |
| RFQ2BOQ_ENTITY_CONFIDENCE_THRESHOLD | 0.70 | Minimum entity confidence |
| RFQ2BOQ_MAX_FILE_SIZE_MB | 50 | Maximum upload file size |
| RFQ2BOQ_MAX_PAGES | 200 | Maximum PDF pages |
| RFQ2BOQ_NER_LEARNING_RATE | 2e-5 | NER model learning rate |
| RFQ2BOQ_NER_BATCH_SIZE | 16 | NER training batch size |

## Running Locally

### API Server

```bash
# Using Python directly
python -m src.api.main

# Or using make
make run-api
```

API runs at `http://localhost:8000`

### Streamlit UI

```bash
# Using Streamlit directly
streamlit run src/ui/app.py

# Or using make
make run-ui
```

UI runs at `http://localhost:8501`

## Docker Deployment

### Build Image

```bash
docker build -t rfq2boq:latest .
```

### Run Container

```bash
# Run API only
docker run -p 8000:8000 rfq2boq:latest

# Run with custom environment
docker run -p 8000:8000 \
  -e RFQ2BOQ_API_KEY=my-secret-key \
  -e RFQ2BOQ_ONTOLOGY_DIR=/data/ontology \
  -v /path/to/models:/models \
  rfq2boq:latest
```

## Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Rebuild
docker-compose build
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/api/health` | GET | Health check |
| `/api/extract` | POST | Extract BOQ from text |
| `/api/upload` | POST | Upload PDF for extraction |
| `/api/boq/{id}` | GET | Retrieve BOQ by extraction ID |

### Health Check

```bash
curl http://localhost:8000/api/health
# Returns: {"status":"ok","version":"0.1.0"}
```

### Extract Text

```bash
curl -X POST http://localhost:8000/api/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Supply 500 kg of steel for foundation work", "project_name": "Project 1"}'
```

### Upload PDF

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@rfq.pdf" \
  -F "project_name=Project 1"
```

## Production Considerations

### File Storage
- Use external volume for `/tmp` (extraction files)
- Consider S3-compatible storage for persistent BOQ results
- Clean up temporary files regularly

### Memory
- Default container: 2GB RAM
- For large PDFs: increase memory to 4GB+
- Consider worker pool for concurrent processing

### Model Loading
- First request loads NER model (~500MB)
- Subsequent requests use cached model
- Mount model directory as volume for zero-downtime updates

### OCR Configuration
- Tesseract 4.0+ recommended
- For GPU acceleration: use paddleocr with GPU image
- Set `TESSERACT_CMD` environment variable if not in PATH

## Troubleshooting

### "Module not found" errors
```bash
pip install -e ".[dev]"
```

### OCR not working
```bash
# Verify tesseract is installed
tesseract --version

# If not found, install:
# macOS: brew install tesseract
# Ubuntu: sudo apt install tesseract-ocr
```

### Slow startup
- First request loads spaCy model
- Pre-load model on container startup with entrypoint script

### Coverage drops
```bash
# Run with coverage
pytest tests/ --cov=src --cov-report=html
# View HTML report at htmlcov/index.html
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific test suite
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```