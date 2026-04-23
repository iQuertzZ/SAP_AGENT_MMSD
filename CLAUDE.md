# SAP MM/SD AI Copilot — CLAUDE.md

## Project Overview

Enterprise-grade AI Copilot for SAP Materials Management (MM) and Sales & Distribution (SD) modules. Diagnoses SAP issues, recommends actions, simulates impact, and manages a safe approval workflow.

## Architecture

```
backend/app/
├── core/           config.py, logging.py, exceptions.py
├── models/         context.py, diagnosis.py, action.py, simulation.py, approval.py
├── schemas/        requests.py, responses.py  (Pydantic v2)
├── knowledge/      tcodes.py, mm_rules.py, sd_rules.py  (SAP rule engine)
├── connectors/     base.py, mock_connector.py, odata_connector.py, factory.py
├── services/       context_service.py, diagnostic_service.py, action_planner.py,
│                   impact_simulator.py, approval_service.py, execution_service.py,
│                   ai_service.py  (Claude API)
├── api/routes/     analyze.py, simulate.py, approval.py, execution.py, health.py
└── main.py         FastAPI app + static frontend mount

frontend/           index.html, styles.css, app.js  (vanilla JS, dark theme)
backend/tests/      unit/, integration/, e2e/  (47 tests, all passing)
```

## Running

```bash
# Install
pip install -r requirements.txt

# Start server (mock SAP, no AI key needed)
SAP_CONNECTOR=mock uvicorn backend.app.main:app --reload

# With real AI analysis
ANTHROPIC_API_KEY=sk-ant-... uvicorn backend.app.main:app --reload

# Run tests
python3 -m pytest backend/tests/ -v --no-cov

# Enable execution layer (disabled by default — safety)
EXECUTION_ENABLED=true uvicorn backend.app.main:app --reload
```

## Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analyze` | Full analysis: context → diagnosis → actions |
| POST | `/api/v1/simulate` | Simulate impact of a specific action |
| POST | `/api/v1/approval/submit` | Submit for approval workflow |
| POST | `/api/v1/approval/{id}/approve` | Approve a request |
| POST | `/api/v1/approval/{id}/reject` | Reject a request |
| POST | `/api/v1/execute` | Execute approved action (requires EXECUTION_ENABLED=true) |
| GET | `/api/v1/health` | Health + connector status |
| GET | `/api/docs` | Swagger UI |

## Environment Variables

See `.env.example` for all options. Key ones:
- `SAP_CONNECTOR` — `mock` (default) | `odata` | `rfc`
- `ANTHROPIC_API_KEY` — enables Claude AI analysis (rule engine fallback if absent)
- `ANTHROPIC_MODEL` — default `claude-sonnet-4-6`
- `EXECUTION_ENABLED` — `false` by default (safety)

## Safety Contracts

1. **No execution without approval** — enforced at API level
2. **Every action has a rollback plan** — tested in e2e suite
3. **Confidence score on every recommendation** — float 0–1
4. **Audit log** for all executions (`GET /api/v1/execute/audit`)
5. **Risk score blockers** — execution blocked if risk_score > 0.85

## Diagnostic Rule Engine

Rule matching priority (`mm_rules.py`, `sd_rules.py`):
1. Exact `block_reason` == `condition_key` match (most specific)
2. `condition_key` present as a data key in `raw_data`
3. First status match (catch-all fallback)

## AI Service (Claude)

`ai_service.py` uses:
- Model: `claude-sonnet-4-6` (configurable)
- Prompt caching on the SAP knowledge system prompt (`cache_control: ephemeral`)
- Tool use (`report_diagnosis`) for structured JSON output
- Graceful fallback to rule engine if API key absent or confidence < 0.70

## Test Coverage

```bash
python3 -m pytest backend/tests/ --cov=backend/app --cov-report=term-missing
```

47 tests across unit, integration, and e2e layers. Target: ≥80% coverage.

## Connector Swap

Add a new connector by:
1. Extending `SAPConnectorBase` in `connectors/`
2. Adding the new type to `ConnectorType` enum in `core/config.py`
3. Registering in `connectors/factory.py`
