.PHONY: help install test test-slow regression lint typecheck verify run-api run-ui docker-build docker-up docker-down clean demo demo-api demo-ui push-first

help:
	@echo "RFQ2BOQ - Make targets"
	@echo ""
	@echo "  install        Install dependencies"
	@echo "  test           Run test suite (skips slow tests)"
	@echo "  test-slow      Run only slow tests"
	@echo "  regression     Run full regression suite (Tier 1 exact + Tier 2 invariance)"
	@echo "  lint           Run ruff linter"
	@echo "  typecheck      Run mypy type checking"
	@echo "  verify         CI gate: tests + lint + anti-cheat + clean tree"
	@echo "  run-api        Run FastAPI server"
	@echo "  run-ui         Run Streamlit UI"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-up      Start Docker Compose"
	@echo "  clean          Remove generated files"
	@echo "  demo           Run end-to-end demo"
	@echo "  demo-api       Start API server"
	@echo "  demo-ui        Start Streamlit UI"
	@echo "  push-first     First-time push to GitHub (sets upstream)"

push-first:
	@echo "Setting upstream and pushing to origin/main..."
	git push -u origin main

regression:
	@echo "=== regression: Tier 1 exact + Tier 2 invariance ==="
	python3 -m pytest tests/regression/ -v --tb=short --timeout=600 || (echo "FAIL: regression suite failed"; exit 1)
	@echo "=== regression: PASSED ==="

verify:
	@echo "=== verify: CI gate ==="
	@echo ""
	@echo "1. Running critical tests..."
	python3 -m pytest tests/unit/test_boq_assembler.py tests/unit/test_pipeline_xlsx.py tests/unit/test_anti_cheat.py tests/unit/test_validator.py tests/unit/test_final_model.py tests/unit/test_ui_app.py tests/integration/test_real_rfq_corpus.py tests/integration/test_self_attack.py tests/integration/test_xlsx_row_preservation_e2e.py -q --tb=short || (echo "FAIL: tests failed"; exit 1)
	@echo ""
	@echo "2. Running regression safety net..."
	$(MAKE) regression || (echo "FAIL: regression failed"; exit 1)
	@echo ""
	@echo "3. Running lint..."
	python3 -m ruff check src/ --quiet || (echo "FAIL: lint failed"; exit 1)
	@echo ""
	@echo "4. Anti-cheat: checking for '100% COMPLETE' claims..."
	@matches=$$(grep -rln "100% COMPLETE" docs/ deliverables/ results/ HANDOFF.md 2>/dev/null | grep -v ".pyc" | grep -v "attic/" | grep -v "docs/historical/" | grep -v -e "ULTRA_PLAN" -e "honest_baseline" -e "HANDOFF" | head -5); \
	if [ -n "$${matches}" ]; then \
		echo "FAIL: found '100% COMPLETE' claims in: $${matches}"; \
		exit 1; \
	fi
	@echo "  (clean)"
	@echo ""
	@echo "5. Anti-cheat: checking gold provenance (not pipeline-derived)..."
	@python3 scripts/check_gold_provenance.py || (echo "FAIL: gold provenance check failed"; exit 1)
	@echo "  (clean)"
	@echo ""
	@echo "6. Anti-cheat: checking gold not modified..."
	@if git diff HEAD -- data/real_rfqs/gold/rows/ | grep -q "human_verified.*true"; then \
		echo "FAIL: human_verified set to true after modification"; \
		exit 1; \
	fi
	@echo "  (clean)"
	@echo ""
	@echo "7. Anti-cheat: checking eval scripts for threshold / filename hacks..."
	@python3 scripts/check_eval_hacks.py || (echo "FAIL: script check failed"; exit 1)
	@echo "  (clean)"
	@echo ""
	@echo "8. Checking git tree clean..."
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "FAIL: uncommitted changes"; \
		git status --short; \
		exit 1; \
	fi
	@echo "  (clean)"
	@echo ""
	@echo "=== verify: ALL PASSED ==="

install:
	pip install -e ".[dev]"
	python -m spacy download en_core_web_sm || true

test:
	python3 -m pytest tests/ -q --ignore=tests/unit/test_ocr_processor.py -m "not slow"

test-slow:
	python3 -m pytest tests/ -q -m "slow"

lint:
	python3 -m ruff check src/

typecheck:
	python3 -m mypy src/ --ignore-missing-imports

run-api:
	uvicorn src.api.main:app --reload --port 8000

run-ui:
	streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	rm -rf .pytest_cache __pycache__ */__pycache__ */*/__pycache__ */*/*/__pycache__
	rm -rf .ruff_cache
	rm -rf results/*.{json,xlsx}
	find . -name "*.pyc" -delete

demo:
	python3 scripts/demo.py

demo-api:
	uvicorn src.api.main:app --reload --port 8000

demo-ui:
	streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0
