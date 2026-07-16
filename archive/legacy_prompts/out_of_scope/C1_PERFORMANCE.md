# TASK: Performance Optimization — Agent-3

**Wave:** 4 | **Tier:** C | **Priority:** P2

## 1. GOAL
Production-scale performance: ONNX export for 3-5× inference speedup, async pipeline, Redis cache, PostgreSQL persistence, benchmark suite proving improvements.

## 2. CONTEXT
Read first:
- `src/nlp/ner/bert_ner.py` — PyTorch model to export
- `src/nlp/pipeline.py` — current synchronous pipeline
- `src/api/` — current request handling
- [docs/conventions.md](../../../docs/conventions.md)

Current state: PyTorch sync inference, file-based job store, no cache layer.

## 3. DELIVERABLES
- [ ] `scripts/export_onnx.py` — PyTorch → ONNX export with accuracy check
- [ ] `src/nlp/onnx_inference.py` — ONNX Runtime inference, PyTorch fallback
- [ ] `src/cache/redis_cache.py` — Redis cache with LRU + TTL
- [ ] `src/db/postgres.py` — PostgreSQL job store
- [ ] `src/db/migrations/` — Alembic migrations
- [ ] `src/pipeline/async_pipeline.py` — asyncio pipeline (asyncpg, aiofiles)
- [ ] `bench/benchmark_pipeline.py` — Locust + custom benchmark suite
- [ ] `deployment/triton/` — optional Triton inference server config
- [ ] `tests/unit/test_performance.py` — ≥8 tests

## 4. STEPS
1. Export ONNX: `python3 scripts/export_onnx.py --model models/ner-bert-bilstm-crf-v1 --output models/onnx/`
2. Verify ONNX matches PyTorch outputs within 1e-4 tolerance
3. ONNX inference module with PyTorch fallback path
4. Redis cache: key = sha256(text), value = serialized entities, TTL 24h
5. PostgreSQL: replace file-based job store; Alembic migrations for schema
6. Async pipeline: convert blocking ops to async; CPU-bound (inference) uses process pool
7. Benchmark suite measures p50/p95/p99 latency, throughput, resource usage
8. Tests verify cache hits/misses, async correctness

## 5. VERIFICATION
```bash
$ python3 scripts/export_onnx.py --model models/ner-bert-bilstm-crf-v1 --output models/onnx/
$ ls models/onnx/model.onnx
EXPECT: exists

$ python3 -c "from src.nlp.onnx_inference import ONNXInference; o = ONNXInference('models/onnx'); r = o.predict('Supply cement'); assert len(r) >= 0"
EXPECT: no AssertionError

$ python3 -c "from src.cache.redis_cache import RedisCache; c = RedisCache(); c.set('k','v'); assert c.get('k') == 'v'"
EXPECT: no AssertionError (with Redis running)

$ python3 bench/benchmark_pipeline.py --quick
EXPECT: prints p50/p95/p99, all under target

$ python3 -m pytest tests/unit/test_performance.py -v
EXPECT: ≥8 passed
```

## 6. ACCEPTANCE CRITERIA
- [ ] ONNX inference ≥3× faster than PyTorch on same input
- [ ] Cache hit rate ≥50% on repeated benchmark
- [ ] PostgreSQL job store handles 100 concurrent inserts
- [ ] p95 latency < 5s for 1-page PDF
- [ ] Coverage ≥80% on new code
- [ ] No regression in F1 (ONNX accuracy preserved)

## 7. CONSTRAINTS
- All imports `src.` prefix
- ONNX model must produce identical predictions to PyTorch (within 1e-4)
- Redis OPTIONAL — pipeline works without it
- PostgreSQL also optional — fall back to file-based
- Async conversion preserves API contract

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** C2, C3, C4
- **Parallel-safe with:** None (large surface area)
- **Shared files:** Many — sequence carefully

## 9. GOTCHAS
- ONNX export: BiLSTM + CRF layers may need custom ops — test thoroughly
- Apple Silicon MPS doesn't support ONNX Runtime native — use CPU for ONNX
- Redis on macOS: `brew install redis`
- PostgreSQL via docker-compose for dev
- Async + process pool: use `loop.run_in_executor` for CPU-bound inference
- Benchmark reproducibility: fixed seeds, warmed-up state
