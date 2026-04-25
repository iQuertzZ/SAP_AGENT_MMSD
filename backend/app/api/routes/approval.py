"""
Approval workflow routes:
  POST /api/v1/approval/submit
  POST /api/v1/approval/{id}/approve
  POST /api/v1/approval/{id}/reject
  GET  /api/v1/approval/{id}
  GET  /api/v1/approval/
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.deps import (
    get_action_planner,
    get_approval_facade,
    get_context_service,
    get_diagnostic_service,
    get_simulator,
    require_role,
)
from backend.app.core.exceptions import ApprovalNotFoundError, ApprovalStateError
from backend.app.models.approval import ApprovalRequest
from backend.app.models.auth import SAPRole
from backend.app.models.context import SAPContext
from backend.app.schemas.auth import CurrentUser
from backend.app.schemas.requests import AnalyzeRequest, ApproveRequest, RejectRequest
from backend.app.schemas.responses import ApprovalListResponse, ApprovalResponse
from backend.app.services.action_planner import ActionPlanner
from backend.app.services.approval_facade import ApprovalFacade
from backend.app.services.context_service import ContextService
from backend.app.services.diagnostic_service import DiagnosticService
from backend.app.services.impact_simulator import ImpactSimulator

router = APIRouter()


@router.post("/approval/submit", response_model=ApprovalRequest)
async def submit_approval(
    body: AnalyzeRequest,
    ctx_svc: ContextService = Depends(get_context_service),
    diag_svc: DiagnosticService = Depends(get_diagnostic_service),
    planner: ActionPlanner = Depends(get_action_planner),
    simulator: ImpactSimulator = Depends(get_simulator),
    facade: ApprovalFacade = Depends(get_approval_facade),
    current_user: CurrentUser = Depends(
        require_role(SAPRole.CONSULTANT, SAPRole.MANAGER, SAPRole.ADMIN)
    ),
) -> ApprovalRequest:
    context = SAPContext(**body.model_dump())
    context = await ctx_svc.enrich(context)
    diagnosis = await diag_svc.diagnose(context)
    actions = planner.plan(context, diagnosis)

    if not actions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No recommended actions available for this issue.",
        )

    primary = actions[0]
    simulation = simulator.simulate(context, diagnosis, primary)

    # Use body.user if provided, else fall back to current_user email
    requested_by = body.user or current_user.email
    request = ApprovalRequest(
        request_id=str(uuid.uuid4()),
        context=context,
        diagnosis=diagnosis,
        recommended_action=primary,
        simulation=simulation,
        requested_by=requested_by,
    )
    return await facade.submit(request)


@router.post("/approval/{request_id}/approve", response_model=ApprovalResponse)
async def approve(
    request_id: str,
    body: ApproveRequest,
    facade: ApprovalFacade = Depends(get_approval_facade),
    _: CurrentUser = Depends(require_role(SAPRole.MANAGER, SAPRole.ADMIN)),
) -> ApprovalResponse:
    try:
        # body.approver is the SAP user ID recorded in the document
        req = await facade.approve(request_id, body.approver, body.comment)
        return ApprovalResponse(
            request_id=req.request_id,
            status=req.status,
            message=f"Approved by {body.approver}.",
        )
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except ApprovalStateError as exc:
        raise HTTPException(status_code=409, detail=exc.message)


@router.post("/approval/{request_id}/reject", response_model=ApprovalResponse)
async def reject(
    request_id: str,
    body: RejectRequest,
    facade: ApprovalFacade = Depends(get_approval_facade),
    _: CurrentUser = Depends(require_role(SAPRole.MANAGER, SAPRole.ADMIN)),
) -> ApprovalResponse:
    try:
        req = await facade.reject(request_id, body.approver, body.reason)
        return ApprovalResponse(
            request_id=req.request_id,
            status=req.status,
            message=f"Rejected by {body.approver}: {body.reason}",
        )
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except ApprovalStateError as exc:
        raise HTTPException(status_code=409, detail=exc.message)


@router.get("/approval/{request_id}", response_model=ApprovalRequest)
async def get_approval(
    request_id: str,
    facade: ApprovalFacade = Depends(get_approval_facade),
    current_user: CurrentUser = Depends(
        require_role(SAPRole.CONSULTANT, SAPRole.MANAGER, SAPRole.ADMIN)
    ),
) -> ApprovalRequest:
    try:
        req = await facade.get(request_id)
        # CONSULTANT sees only their own submissions
        if (
            current_user.role == SAPRole.CONSULTANT
            and req.requested_by != current_user.email
        ):
            raise HTTPException(status_code=404, detail="Approval request not found")
        return req
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.get("/approval/", response_model=ApprovalListResponse)
async def list_approvals(
    pending_only: bool = False,
    facade: ApprovalFacade = Depends(get_approval_facade),
    current_user: CurrentUser = Depends(
        require_role(SAPRole.CONSULTANT, SAPRole.MANAGER, SAPRole.ADMIN)
    ),
) -> ApprovalListResponse:
    items = await facade.list_pending() if pending_only else await facade.list_all()

    # CONSULTANT sees only their own submissions
    if current_user.role == SAPRole.CONSULTANT:
        items = [i for i in items if i.requested_by == current_user.email]

    return ApprovalListResponse(total=len(items), items=items)
