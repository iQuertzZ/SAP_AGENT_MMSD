.PHONY: install dev test lint format check

install:
	pip install -e ".[dev]"

dev:
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest backend/tests/ -v

test-unit:
	pytest backend/tests/unit/ -v

test-integration:
	pytest backend/tests/integration/ -v

test-e2e:
	pytest backend/tests/e2e/ -v

coverage:
	pytest --cov=backend/app --cov-report=html backend/tests/
	@echo "Open htmlcov/index.html"

lint:
	ruff check backend/

format:
	ruff format backend/

check: lint
	mypy backend/app/
