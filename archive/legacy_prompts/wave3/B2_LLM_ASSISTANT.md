# TASK: LLM Assistant Integration — Agent-2

**Wave:** 3 | **Tier:** B | **Priority:** P2

## 1. GOAL
Integrate Claude/GPT for ambiguity resolution, executive summaries, and natural-language Q&A over extracted BOQs.

## 2. CONTEXT
Read first:
- `src/nlp/pipeline.py` — where ambiguous entities are produced
- `src/domain/models.py` — ExtractionResult schema
- `config/settings.py` — for API key config
- [docs/conventions.md](../../../docs/conventions.md)

Current state: Low-confidence entities are flagged but not resolved. No human-readable summaries. No NL queries.

## 3. DELIVERABLES
- [ ] `src/llm/__init__.py`
- [ ] `src/llm/client.py` — Anthropic SDK wrapper with cache + fallback
- [ ] `src/llm/resolver.py` — ambiguity resolver (low-conf entity → ask LLM)
- [ ] `src/llm/summarizer.py` — executive summary generator
- [ ] `src/llm/qa.py` — Q&A over BOQ JSON
- [ ] `src/llm/prompts.py` — prompt templates
- [ ] `src/api/routes/llm_routes.py` — `/v1/llm/resolve`, `/v1/llm/summary`, `/v1/llm/ask`
- [ ] `tests/unit/test_llm_assistant.py` — ≥8 tests (with mocked API)

## 4. STEPS
1. Add `anthropic` to pyproject.toml
2. LLM client: read `ANTHROPIC_API_KEY` from env, default model `claude-opus-4-7`
3. Cache layer: LRU + Redis (key = sha256(prompt)), TTL 24h, controls cost
4. Resolver: when entity confidence < 0.5, call LLM with sentence + entity span + ask which type
5. Summarizer: take ExtractionResult → return 2-3 paragraph summary highlighting key items, totals, anomalies
6. Q&A: NL question → translate to JSON query over BOQ → answer with citations
7. Fallback: if API unavailable, return None (don't crash pipeline)
8. Tests use mock responses

## 5. VERIFICATION
```bash
$ python3 -c "from src.llm.client import LLMClient; c = LLMClient(use_cache=False); print(type(c).__name__)"
EXPECT: "LLMClient"

$ python3 -m pytest tests/unit/test_llm_assistant.py -v
EXPECT: ≥8 passed

$ curl -X POST http://localhost:8000/v1/llm/summary -H "Content-Type: application/json" -d '{"job_id":"test"}' | python3 -c "import sys,json; r=json.load(sys.stdin); 'summary' in r"
EXPECT: response is valid JSON (or graceful error if no job)
```

## 6. ACCEPTANCE CRITERIA
- [ ] Cache reduces duplicate calls by ≥80%
- [ ] All endpoints return structured JSON or 5xx with detail
- [ ] Pipeline doesn't crash if LLM unavailable
- [ ] Coverage ≥80% on new code (mocked tests)
- [ ] No PII leak: prompts redact identifying info before sending

## 7. CONSTRAINTS
- All imports `src.` prefix
- API key only from env, never hardcoded
- Cost cap: max 100 calls per extraction (configurable)
- DO NOT call LLM in synchronous request path without timeout (5s max)

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** None
- **Parallel-safe with:** B1, B3, B4, B5

## 9. GOTCHAS
- Anthropic SDK requires Python ≥ 3.8 — compatible
- Rate limits on Claude API: handle 429 with exponential backoff
- Q&A over BOQ: structured query is safer than free-form prompt — convert NL → filter spec
- Streaming responses not needed for these use cases
- Test mocking: use `unittest.mock.patch` on the SDK call site
