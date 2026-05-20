.PHONY: help install test lint typecheck run-api run-ui docker-build docker-up clean demo demo-api demo-ui push-first

help:
	@echo "RFQ2BOQ - Make targets"
	@echo ""
	@echo "  install        Install dependencies"
	@echo "  test           Run test suite"
	@echo "  lint           Run ruff linter"
	@echo "  typecheck      Run mypy type checking"
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

install:
	pip install -e ".[dev]"
	python -m spacy download en_core_web_sm || true

test:
	python -m pytest tests/ -v --ignore=tests/unit/test_ocr_processor.py --ignore=tests/unit/test_bert_ner.py

lint:
	python -m ruff check src/

typecheck:
	python -m mypy src/ --ignore-missing-imports

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
	rm -rf .pytest_cache __pycache__ */__pycache__ */*/__pycache__
	rm -rf .ruff_cache
	rm -rf results/*.{json,xlsx}
	find . -name "*.pyc" -delete

demo:
	python3 scripts/demo.py

demo-api:
	uvicorn src.api.main:app --reload --port 8000

demo-ui:
	streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0