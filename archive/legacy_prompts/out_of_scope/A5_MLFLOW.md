# TASK: MLflow MLOps — Agent-4

**Wave:** 2 | **Tier:** A | **Priority:** P1

## 1. GOAL
Set up MLflow tracking + model registry so every training run is logged, models can be promoted Staging → Production, and drift detection triggers retraining.

## 2. CONTEXT
Read first:
- `scripts/train_ner.py` — current training script (unintrumented)
- `models/ner-bert-bilstm-crf-v1/metrics.json` — example metrics format
- `docker-compose.yml` — to add MLflow service
- [docs/conventions.md](../../../docs/conventions.md)

Current state: training metrics live in flat JSON files. No lineage, no comparison, no promotion gates.

## 3. DELIVERABLES
- [ ] `docker-compose.yml` — add `mlflow` service on port 5000
- [ ] `scripts/train_ner.py` — wrap with `mlflow.start_run()`, log all hyperparams, per-epoch metrics, artifacts, git_commit, system info
- [ ] `scripts/promote_model.py` — promote None → Staging → Production with F1 gate
- [ ] `src/nlp/pipeline.py` — load model from MLflow Registry (Production stage) with local fallback
- [ ] `src/api/ab_test.py` — A/B routing middleware (X% to candidate)
- [ ] `scripts/detect_drift.py` — daily KS test on input distributions, save alert to `data/drift/`
- [ ] `.github/workflows/train_on_data.yml` — CI trigger on `data/annotations/` changes
- [ ] `docs/mlops.md` — runbook
- [ ] `tests/unit/test_mlflow_integration.py` — minimum 5 tests

## 4. STEPS
1. Add to `docker-compose.yml`:
   ```yaml
   mlflow:
     image: ghcr.io/mlflow/mlflow:v2.10.0
     ports: ["5000:5000"]
     command: mlflow server --host 0.0.0.0 --backend-store-uri sqlite:///mlflow.db --default-artifact-root /mlflow/artifacts
     volumes:
       - mlflow_data:/mlflow
   volumes:
     mlflow_data:
   ```
2. Start: `docker compose up -d mlflow` — verify http://localhost:5000 loads
3. Add MLflow to `pyproject.toml`: `mlflow>=2.10`
4. Instrument `scripts/train_ner.py`:
   - `mlflow.set_tracking_uri("http://localhost:5000")`
   - `mlflow.set_experiment("rfq2boq-ner")`
   - `with mlflow.start_run():` wrap training loop
   - Log hyperparams via `mlflow.log_params(...)`
   - Log per-epoch via `mlflow.log_metrics(...)`
   - Log model via `mlflow.pytorch.log_model(...)`
   - Log git commit via `mlflow.set_tag("git_commit", ...)`
5. Implement `scripts/promote_model.py`:
   - Reads latest run for experiment
   - Checks F1 ≥ threshold (default 0.65)
   - Calls MLflow client to transition stage
6. Update pipeline loader:
   ```python
   def _load_model_from_registry(self, name="rfq2boq-ner", stage="Production"):
       try:
           return mlflow.pytorch.load_model(f"models:/{name}/{stage}")
       except Exception:
           return self._load_local_fallback()
   ```
7. Implement A/B router (FastAPI dependency injection)
8. Implement drift detector (KS test on token frequency distribution between training data and recent requests)
9. CI workflow: triggers training on changes to `data/annotations/**`
10. Verification

## 5. VERIFICATION
```bash
# MLflow service up
$ curl -fsS http://localhost:5000/ -o /dev/null && echo "MLflow OK"
EXPECT: "MLflow OK"

# A training run logs
$ python3 scripts/train_ner.py --epochs 1 --output models/test-run/
$ python3 -c "import mlflow; mlflow.set_tracking_uri('http://localhost:5000'); runs = mlflow.search_runs('rfq2boq-ner'); assert len(runs) > 0"
EXPECT: no AssertionError

# Promotion script works (dry run on existing model)
$ python3 scripts/promote_model.py --dry-run --threshold 0.65
EXPECT: prints what would be promoted

# Pipeline can load from registry (with fallback)
$ python3 -c "from src.nlp.pipeline import NLPPipeline; p = NLPPipeline(use_registry=True); r = p.process('cement 500 kg'); assert len(r.entities) >= 0"
EXPECT: no AssertionError (registry empty falls back to local)

# Drift script runs
$ python3 scripts/detect_drift.py --training data/annotations/train.json --recent data/jobs/
EXPECT: outputs drift score, no exception

# Tests
$ python3 -m pytest tests/unit/test_mlflow_integration.py -v
EXPECT: ≥5 passed

# Lint
$ python3 -m ruff check src/api/ab_test.py scripts/
EXPECT: clean
```

## 6. ACCEPTANCE CRITERIA
- [ ] MLflow service runs in docker-compose
- [ ] Every `train_ner.py` invocation creates a tracked run
- [ ] Model artifacts visible in MLflow UI
- [ ] Promotion gate enforces F1 ≥ threshold
- [ ] Pipeline falls back gracefully if MLflow down
- [ ] A/B router stable under load (no race conditions)
- [ ] `docs/mlops.md` covers: start MLflow, train, promote, A/B test, drift response
- [ ] Coverage of new code ≥ 80%

## 7. CONSTRAINTS
- All imports use `src.` prefix
- DO NOT make MLflow a hard dependency — pipeline must work without it
- DO NOT log PII or full document text to MLflow
- A/B routing must default to 0% candidate (safe-by-default)

## 8. DEPENDENCIES
- **Blocked by:** A0 (test fix)
- **Blocks:** None directly, but enables principled model selection for D2 (paper)
- **Parallel-safe with:** A1, A2, A3, A4, A6, A7
- **Shared files:** `scripts/train_ner.py`, `src/nlp/pipeline.py` — sequence after A3 (which also touches pipeline)

## 9. GOTCHAS
- MLflow SQLite backend OK for dev; production needs PostgreSQL
- Docker volume `mlflow_data` persists runs across restarts — clean before fresh experiments
- `mlflow.pytorch.log_model` requires the model class to be importable at load time — ensure `src/nlp/ner/bert_ner.py` is on path
- A/B router: if candidate crashes, fall back to production, log the error
- Drift detector needs ≥100 recent requests to be meaningful — gracefully skip if insufficient data
- GitHub Actions training would need GPU runner OR external trigger to a GPU service — document this; don't try to train on free runner
