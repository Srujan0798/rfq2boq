# MLOps Runbook — RFQ2BOQ

Operational guide for MLflow, model promotion, drift detection, and retraining.

---

## Starting MLflow

```bash
# Start MLflow via docker-compose
docker compose up -d mlflow

# Or standalone
mlflow server --host 0.0.0.0 --port 5000 \
  --backend-store-uri sqlite:///mlflow.db \
  --default-artifact-root /mlflow/artifacts
```

Access at: http://localhost:5000

---

## Training with MLflow Tracking

```bash
# Train with automatic logging
python scripts/train_ner_mlflow.py \
  --epochs 30 \
  --batch-size 16 \
  --lr 5e-5 \
  --output models/ner-bert-bilstm-crf-v1
```

Every training run automatically logs:
- Hyperparameters (epochs, batch_size, lr, model config)
- Per-epoch metrics (train_loss, val_f1, val_precision, val_recall)
- Model artifacts (PyTorch state_dict)
- Git commit hash
- System info (Python version, device)

View in MLflow UI → Experiment `rfq2boq-ner`

---

## Promoting a Model

```bash
# Dry run — see what would be promoted
python scripts/promote_model.py --dry-run

# List all versions
python scripts/promote_model.py --list

# Promote specific version to Staging
python scripts/promote_model.py --version 3 --to Staging --threshold 0.65

# Promote to Production (requires F1 >= 0.65)
python scripts/promote_model.py --version 3 --to Production --threshold 0.65
```

**Promotion Rules:**
- F1 ≥ threshold → promoted
- F1 < threshold → skipped with warning
- Threshold configurable via `--threshold` or `MLFLOW_MIN_F1_THRESHOLD` env var

---

## Loading Model from Registry

```python
from src.mlflow.registry import MLflowModelLoader

loader = MLflowModelLoader()
model_path = loader.load_production_model("rfq2boq-ner")

# Fallback if registry empty
# → returns os.getenv("RFQ2BOQ_MODEL_DIR", "models/ner-bert-bilstm-crf-v1")
```

**Fallback behavior:** Pipeline always works even if MLflow is down.

---

## Drift Detection

```bash
# Run drift detection
python scripts/detect_drift.py \
  --training data/annotations/train.json \
  --recent data/jobs/ \
  --output data/drift/
```

**What it detects:**
- KS test on token frequency distribution
- Compares recent request distribution vs training distribution
- Alert if drift score > 0.15

**Alert output:** `data/drift/drift_alerts.jsonl`

**Schedule:** Run daily via cron or CI workflow

---

## A/B Testing

```python
from src.api.routes.ab_test import ABConfig, get_router_for_config

config = ABConfig(
    production_model="rfq2boq-ner",
    candidate_model="rfq2boq-ner-v2",
    candidate_percentage=0.1,  # 10% to candidate
)

router = get_router_for_config(config)
# Apply to FastAPI app
app.include_router(router)
```

**Safety:** If candidate crashes, falls back to production. Error logged.

---

## Triggering Retraining on Data Changes

```bash
# Manual trigger
python scripts/trigger_retraining.py --branch main

# CI triggers automatically on push to data/annotations/
# See: .github/workflows/train_on_data.yml
```

---

## Calibration

```bash
# Fit temperature scaling on validation set
python scripts/calibrate_model.py \
  --model models/ner-bert-bilstm-crf-v1 \
  --val data/annotations/val.json \
  --output models/ner-bert-bilstm-crf-v1/temperature.json

# Generate reliability diagrams
python scripts/calibration_plot.py \
  --before data/calibration/raw_confidences.json \
  --after data/calibration/calibrated_confidences.json \
  --output report/figures/calibration.png
```

Temperature scaling improves confidence reliability:
- Before: ECE ~0.15
- After: ECE ~0.05

---

## ONNX Export for Production

```bash
# Export PyTorch model to ONNX
python scripts/export_onnx.py \
  --model models/ner-bert-bilstm-crf-v1 \
  --output models/onnx/

# Benchmark ONNX vs PyTorch
python scripts/benchmark_onnx.py \
  --onnx models/onnx/model.onnx \
  --pytorch models/ner-bert-bilstm-crf-v1/model.pt
```

**Speedup:** ~3-4× faster on CPU. Note: MPS (Apple Silicon) not supported for ONNX Runtime — use CPU on Mac.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MLFLOW_TRACKING_URI` | http://localhost:5000 | MLflow server |
| `MLFLOW_MIN_F1_THRESHOLD` | 0.65 | Promotion gate |
| `RFQ2BOQ_MODEL_DIR` | models/ner-bert-bilstm-crf-v1 | Fallback model |
| `CUDA_VISIBLE_DEVICES` | (none) | GPU selection |
| `LLAMA_MODEL` | meta-llama/Llama-2-7b-chat-hf | Local fallback model |
