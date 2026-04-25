# SAP MM/SD AI Copilot

[![CI](https://github.com/iQuertzZ/SAP_AGENT_MMSD/actions/workflows/ci.yml/badge.svg)](https://github.com/iQuertzZ/SAP_AGENT_MMSD/actions/workflows/ci.yml)
[![Security](https://github.com/iQuertzZ/SAP_AGENT_MMSD/actions/workflows/security.yml/badge.svg)](https://github.com/iQuertzZ/SAP_AGENT_MMSD/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/iQuertzZ/SAP_AGENT_MMSD/branch/main/graph/badge.svg)](https://codecov.io/gh/iQuertzZ/SAP_AGENT_MMSD)

Enterprise-grade AI Copilot for SAP Materials Management (MM) and Sales &
Distribution (SD) modules. Diagnoses blocked documents, recommends corrective
actions, simulates financial impact, and manages a safe approval workflow.

## Features

- **Context detection** — MIRO, MIGO, ME21N/23N, VA01-03, VL01N, VF01-03, VKM1
- **Rule engine** — deterministic diagnosis (mm_rules, sd_rules) with confidence scores
- **AI enrichment** — Claude claude-sonnet-4-6 via Anthropic API (optional, graceful fallback)
- **Impact simulation** — financial & workflow impact before any action
- **Approval workflow** — proposed → awaiting → approved/rejected → executed
- **JWT/RBAC auth** — ADMIN > MANAGER > CONSULTANT > SERVICE hierarchy
- **PostgreSQL** — persistent approvals, audit log, user management via Alembic migrations
- **Safety gates** — `EXECUTION_ENABLED=false` by default; every action requires a rollback plan

---

## Démarrage rapide (Docker)

### Prérequis
- Docker ≥ 24 and Docker Compose ≥ 2.20
- `make` (optional but convenient)

### 1. Cloner et configurer

```bash
git clone https://github.com/iQuertzZ/SAP_AGENT_MMSD
cd SAP_AGENT_MMSD
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY, change SECRET_KEY
```

### 2. Générer une clé secrète

```bash
openssl rand -hex 32
# Paste the result as SECRET_KEY in .env
```

### 3. Démarrer la stack

```bash
make docker-build   # build the image (first time ~3 min)
make docker-up      # start db + backend
```

Or without make:

```bash
docker compose build --no-cache
docker compose up -d
```

### 4. Vérifier

```bash
# Wait ~15s for Postgres + migrations to finish
curl http://localhost:8000/api/v1/health
# → {"status":"ok","connector":"mock"}
```

### 5. Se connecter (admin créé automatiquement)

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin@sap-copilot.local&password=changeme"
# → {"access_token":"eyJ...","refresh_token":"eyJ...","token_type":"bearer"}
```

### 6. Analyser un document SAP

```bash
TOKEN="<access_token from login>"

curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tcode": "MIRO",
    "module": "MM",
    "document_id": "51000321",
    "status": "BLOCKED"
  }'
```

### 7. Logs et debug

```bash
make docker-logs    # stream backend logs
make docker-shell   # bash inside the container
make docker-migrate # run alembic upgrade head manually
```

---

## Déploiement production

```bash
# Required secrets (never commit these)
export SECRET_KEY=$(openssl rand -hex 32)
export DATABASE_URL="postgresql+asyncpg://user:pass@your-db-host:5432/sap_copilot"
export POSTGRES_PASSWORD="your-strong-password"
export FIRST_ADMIN_PASSWORD="your-strong-admin-password"
export ANTHROPIC_API_KEY="sk-ant-..."

# Build production image (gunicorn + 4 uvicorn workers, no --reload)
make docker-prod-build

# Start
make docker-prod-up
```

Production differences vs development:
- `gunicorn -k uvicorn.workers.UvicornWorker -w 4` — 4 async workers, no reload
- No host-mount volume — code is baked into the image
- DB port not exposed to the host
- All secrets injected via environment variables (never stored in the image)

---

## Développement local (sans Docker)

```bash
pip install -e ".[dev]"

# Start without DB (in-memory approval store)
SAP_CONNECTOR=mock uvicorn backend.app.main:app --reload

# With PostgreSQL
export DATABASE_URL="postgresql+asyncpg://sap_user:sap_pass@localhost:5432/sap_copilot"
alembic upgrade head
uvicorn backend.app.main:app --reload

# With real AI analysis
ANTHROPIC_API_KEY=sk-ant-... uvicorn backend.app.main:app --reload
```

---

## Tests

```bash
# Local (no DB required — in-memory fallback)
make test

# With DB (enables test_approval_repository.py)
TEST_DATABASE_URL=postgresql+asyncpg://... make test

# Inside Docker
make docker-test
```

Target: ≥ 80% coverage. Current: 87 tests passing, 5 skipped (DB-only tests).

---

## API Reference

| Method | Path | Auth required | Description |
|--------|------|---------------|-------------|
| GET | `/api/v1/health` | None | Health + connector status |
| POST | `/api/v1/auth/login` | None | Issue JWT tokens |
| POST | `/api/v1/auth/refresh` | None | Rotate tokens |
| GET | `/api/v1/auth/me` | Bearer | Current user info |
| POST | `/api/v1/auth/users` | ADMIN | Create user |
| GET | `/api/v1/auth/users` | ADMIN | List users |
| POST | `/api/v1/analyze` | CONSULTANT+ | Full diagnosis + action plan |
| POST | `/api/v1/simulate` | CONSULTANT+ | Simulate action impact |
| POST | `/api/v1/approval/submit` | CONSULTANT+ | Submit for approval |
| POST | `/api/v1/approval/{id}/approve` | MANAGER+ | Approve request |
| POST | `/api/v1/approval/{id}/reject` | MANAGER+ | Reject request |
| GET | `/api/v1/approval/{id}` | CONSULTANT+ | Get request (CONSULTANT: own only) |
| POST | `/api/v1/execute` | ADMIN | Execute approved action |
| GET | `/api/v1/execute/audit` | MANAGER+ | Audit log |
| GET | `/api/docs` | None | Swagger UI |

### Roles

| Role | Level | Permissions |
|------|-------|-------------|
| `admin` | 4 | Everything |
| `manager` | 3 | Analyze, simulate, submit, approve/reject, audit |
| `consultant` | 2 | Analyze, simulate, submit, view own approvals |
| `service` | 1 | Analyze, simulate (M2M integrations) |

---

## Architecture

```
backend/app/
├── core/           config.py, logging.py, exceptions.py
├── models/         context.py, diagnosis.py, action.py, simulation.py, approval.py, auth.py
├── schemas/        requests.py, responses.py, auth.py  (Pydantic v2)
├── knowledge/      tcodes.py, mm_rules.py, sd_rules.py  (SAP rule engine)
├── connectors/     base.py, mock_connector.py, odata_connector.py, factory.py
├── db/             engine.py, base.py, models/, repositories/
├── services/       context_service.py, diagnostic_service.py, action_planner.py,
│                   impact_simulator.py, approval_service.py, approval_facade.py,
│                   approval_service_db.py, auth_service.py, execution_service.py,
│                   ai_service.py
├── api/routes/     analyze.py, simulate.py, approval.py, execution.py, auth.py, health.py
└── main.py         FastAPI app + lifespan (DB init, admin seed)

frontend/           index.html, styles.css, app.js  (vanilla JS, dark theme)
backend/alembic/    env.py, versions/  (001: approvals+audit, 002: users)
backend/tests/      unit/, integration/, e2e/  (87 tests)
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SAP_CONNECTOR` | `mock` | `mock` \| `odata` \| `rfc` |
| `ANTHROPIC_API_KEY` | _(empty)_ | Enables Claude AI analysis |
| `DATABASE_URL` | _(empty)_ | PostgreSQL async URL; empty → in-memory |
| `SECRET_KEY` | dev value | JWT signing key (min 32 chars) |
| `EXECUTION_ENABLED` | `false` | Safety gate for SAP writes |
| `FIRST_ADMIN_EMAIL` | `admin@sap-copilot.local` | Seed admin email |
| `FIRST_ADMIN_PASSWORD` | `changeme` | Seed admin password |
| `APP_ENV` | `development` | `development` \| `staging` \| `production` |

---

## CI/CD

### Pipeline GitHub Actions

| Workflow | Déclencheur | Description |
|----------|-------------|-------------|
| [`ci.yml`](.github/workflows/ci.yml) | push main/develop, PR | Lint → Tests → Docker build → Deploy |
| [`cd.yml`](.github/workflows/cd.yml) | `workflow_dispatch`, release tag | Déploiement manuel ou sur release |
| [`security.yml`](.github/workflows/security.yml) | push main, lundi 02h | pip-audit + Trivy + Gitleaks |

### Images Docker (GHCR)

```
ghcr.io/iquertzz/sap_agent_mmsd/backend:latest
ghcr.io/iquertzz/sap_agent_mmsd/frontend:latest
```

### Déploiement manuel

```bash
make deploy-staging   # gh workflow run cd.yml -f environment=staging
make deploy-prod      # gh workflow run cd.yml -f environment=production

# Créer un tag de release
make release          # → prompt version → git tag + push
```

### CI local (nektos/act)

```bash
make ci-local   # act -j test-backend
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full setup instructions (SSH keys, GitHub environments, secrets).
