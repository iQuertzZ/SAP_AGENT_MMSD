.PHONY: install dev test test-unit test-integration test-e2e coverage lint format check \
        docker-build docker-up docker-down docker-logs docker-shell \
        docker-migrate docker-test docker-prod-up docker-prod-build \
        ci-local release deploy-staging deploy-prod audit

# ── Local development ─────────────────────────────────────────────────────────

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

migrate:
	alembic upgrade head

# ── Docker (development) ──────────────────────────────────────────────────────

docker-build:
	docker-compose build --no-cache

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f backend

docker-shell:
	docker-compose exec backend bash

docker-migrate:
	docker-compose exec backend alembic upgrade head

docker-test:
	docker-compose exec -e DATABASE_URL="" backend python -m pytest backend/tests/ -v --no-cov

# ── Docker (production) ───────────────────────────────────────────────────────

docker-prod-build:
	docker-compose -f docker-compose.prod.yml build --no-cache

docker-prod-up:
	docker-compose -f docker-compose.prod.yml up -d

# ── CI/CD helpers ─────────────────────────────────────────────────────────────

ci-local:
	@command -v act >/dev/null 2>&1 || { echo "Install nektos/act first: https://github.com/nektos/act"; exit 1; }
	act -j test-backend

release:
	@read -p "Version (ex: 1.2.0): " v; \
	git tag -a "v$$v" -m "Release v$$v" && \
	git push origin "v$$v"

deploy-staging:
	@command -v gh >/dev/null 2>&1 || { echo "Install gh CLI first: https://cli.github.com"; exit 1; }
	gh workflow run cd.yml -f environment=staging -f image_tag=latest -f run_migrations=true

deploy-prod:
	@command -v gh >/dev/null 2>&1 || { echo "Install gh CLI first: https://cli.github.com"; exit 1; }
	gh workflow run cd.yml -f environment=production -f image_tag=latest -f run_migrations=true

audit:
	@command -v pip-audit >/dev/null 2>&1 || pip install pip-audit
	pip-audit -r requirements.txt
	cd frontend && npm audit
