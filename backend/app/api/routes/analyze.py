"""
POST /api/v1/analyze

Full copilot pipeline:
  1. Build SAPContext
  2. Enrich with document data
  3. Run diagnosis
  4. Plan actions
  5. Return ranked recommendations
"""
from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends

from backend.app.api.deps import (
    get_action_planner,
    get_context_service,
    get_diagnostic_service,
    require_role,
)
from backend.app.models.auth import SAPRole
from backend.app.models.context import SAPContext
from backend.app.schemas.auth import CurrentUser
from backend.app.schemas.requests import AnalyzeRequest
from backend.app.schemas.responses import AnalysisResponse
from backend.app.services.action_planner import ActionPlanner
from backend.app.services.context_service import ContextService
from backend.app.services.diagnostic_service import DiagnosticService

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    body: AnalyzeRequest,
    ctx_svc: ContextService = Depends(get_context_service),
    diag_svc: DiagnosticService = Depends(get_diagnostic_service),
    planner: ActionPlanner = Depends(get_action_planner),
    current_user: CurrentUser = Depends(
        require_role(SAPRole.CONSULTANT, SAPRole.MANAGER, SAPRole.ADMIN, SAPRole.SERVICE)
    ),
) -> AnalysisResponse:
    t0 = time.monotonic()

    context = SAPContext(**body.model_dump())
    context = await ctx_svc.enrich(context)
    diagnosis = await diag_svc.diagnose(context)
    actions = planner.plan(context, diagnosis)

    return AnalysisResponse(
        request_id=str(uuid.uuid4()),
        context=context,
        diagnosis=diagnosis,
        recommended_actions=actions,
        primary_action=actions[0] if actions else None,
        processing_ms=int((time.monotonic() - t0) * 1000),
    )
