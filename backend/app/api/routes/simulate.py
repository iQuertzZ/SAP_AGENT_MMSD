"""POST /api/v1/simulate"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.app.api.deps import (
    get_action_planner,
    get_context_service,
    get_diagnostic_service,
    get_simulator,
    require_role,
)
from backend.app.models.auth import SAPRole
from backend.app.models.context import SAPContext
from backend.app.schemas.auth import CurrentUser
from backend.app.schemas.requests import SimulateRequest
from backend.app.schemas.responses import SimulationResponse
from backend.app.services.action_planner import ActionPlanner
from backend.app.services.context_service import ContextService
from backend.app.services.diagnostic_service import DiagnosticService
from backend.app.services.impact_simulator import ImpactSimulator

router = APIRouter()


@router.post("/simulate", response_model=SimulationResponse)
async def simulate(
    body: SimulateRequest,
    ctx_svc: ContextService = Depends(get_context_service),
    diag_svc: DiagnosticService = Depends(get_diagnostic_service),
    planner: ActionPlanner = Depends(get_action_planner),
    simulator: ImpactSimulator = Depends(get_simulator),
    current_user: CurrentUser = Depends(
        require_role(SAPRole.CONSULTANT, SAPRole.MANAGER, SAPRole.ADMIN, SAPRole.SERVICE)
    ),
) -> SimulationResponse:
    context = SAPContext(
        tcode=body.tcode,
        module=body.module,
        document_id=body.document_id,
        status=body.status,
    )
    context = await ctx_svc.enrich(context)
    diagnosis = await diag_svc.diagnose(context)
    actions = planner.plan(context, diagnosis)

    # Find the specific action to simulate
    target = next(
        (a for a in actions if a.tcode.upper() == body.action_tcode.upper()),
        actions[0] if actions else None,
    )

    if target is None:
        from backend.app.models.action import RecommendedAction, RiskLevel
        import uuid
        target = RecommendedAction(
            action_id=str(uuid.uuid4()),
            tcode=body.action_tcode,
            description="Custom action simulation",
            risk=RiskLevel.MEDIUM,
            confidence=0.5,
            rollback_plan="Manual rollback required.",
        )

    result = simulator.simulate(context, diagnosis, target)
    return SimulationResponse(action_tcode=body.action_tcode, simulation=result)
