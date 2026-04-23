"""FastAPI dependency injection."""
from __future__ import annotations

from functools import lru_cache

from backend.app.connectors.factory import get_connector
from backend.app.services.action_planner import ActionPlanner
from backend.app.services.ai_service import AIService
from backend.app.services.approval_service import ApprovalService
from backend.app.services.context_service import ContextService
from backend.app.services.diagnostic_service import DiagnosticService
from backend.app.services.execution_service import ExecutionService
from backend.app.services.impact_simulator import ImpactSimulator


@lru_cache(maxsize=1)
def _ai_service() -> AIService | None:
    try:
        return AIService()
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_context_service() -> ContextService:
    return ContextService(get_connector())


@lru_cache(maxsize=1)
def get_diagnostic_service() -> DiagnosticService:
    return DiagnosticService(ai_service=_ai_service())


@lru_cache(maxsize=1)
def get_action_planner() -> ActionPlanner:
    return ActionPlanner()


@lru_cache(maxsize=1)
def get_simulator() -> ImpactSimulator:
    return ImpactSimulator()


@lru_cache(maxsize=1)
def get_approval_service() -> ApprovalService:
    return ApprovalService()


@lru_cache(maxsize=1)
def get_execution_service() -> ExecutionService:
    return ExecutionService(get_connector())
