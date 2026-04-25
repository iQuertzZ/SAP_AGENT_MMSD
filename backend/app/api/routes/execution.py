"""POST /api/v1/execute"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.deps import get_approval_facade, get_execution_service, require_role
from backend.app.core.exceptions import (
    ApprovalNotFoundError,
    ApprovalStateError,
    ExecutionDisabledError,
    ExecutionError,
)
from backend.app.models.approval import ApprovalRequest
from backend.app.models.auth import SAPRole
from backend.app.schemas.auth import CurrentUser
from backend.app.schemas.requests import ExecuteRequest
from backend.app.services.approval_facade import ApprovalFacade
from backend.app.services.execution_service import ExecutionService

router = APIRouter()


@router.post("/execute", response_model=ApprovalRequest)
async def execute(
    body: ExecuteRequest,
    facade: ApprovalFacade = Depends(get_approval_facade),
    exec_svc: ExecutionService = Depends(get_execution_service),
    _: CurrentUser = Depends(require_role(SAPRole.ADMIN)),
) -> ApprovalRequest:
    try:
        req = await facade.get(body.request_id)
        result = await exec_svc.execute(req, executor=body.executor)
        return await facade.mark_executed(body.request_id, result)
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except ApprovalStateError as exc:
        raise HTTPException(status_code=409, detail=exc.message)
    except ExecutionDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    except ExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)


@router.get("/execute/audit")
async def get_audit_log(
    exec_svc: ExecutionService = Depends(get_execution_service),
    _: CurrentUser = Depends(require_role(SAPRole.MANAGER, SAPRole.ADMIN)),
) -> list[dict]:
    return exec_svc.get_audit_log()
