from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.connectors.factory import get_connector
from backend.app.core.config import settings
from backend.app.schemas.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    connector = get_connector()
    sap_ok = await connector.health_check()
    return HealthResponse(
        status="ok" if sap_ok else "degraded",
        ai_enabled=settings.ai_enabled,
        connector=settings.sap_connector.value,
        execution_enabled=settings.execution_enabled,
    )
