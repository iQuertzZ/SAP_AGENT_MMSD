from __future__ import annotations

from fastapi import APIRouter

from backend.app.connectors.factory import get_connector
from backend.app.connectors.odata.odata_connector import ODataConnector
from backend.app.core.config import settings
from backend.app.schemas.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    connector = get_connector()
    sap_ok = await connector.health_check()

    cb_state: str | None = None
    sap_metrics: dict | None = None
    cache_stats: dict | None = None

    if isinstance(connector, ODataConnector):
        cb_state = connector.circuit_breaker_state
        sap_metrics = connector.metrics.get_summary()
        cache_stats = connector.cache.get_stats()

    return HealthResponse(
        status="ok" if sap_ok else "degraded",
        version=settings.app_version,
        git_sha=settings.git_sha,
        ai_enabled=settings.ai_enabled,
        connector=settings.sap_connector.value,
        execution_enabled=settings.execution_enabled,
        circuit_breaker=cb_state,
        sap_metrics=sap_metrics,
        cache=cache_stats,
    )
