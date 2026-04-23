"""
Approval Service — manages the lifecycle of approval requests.

State machine:
  proposed → awaiting_approval → approved → executed
                               ↘ rejected
"""
from __future__ import annotations

from datetime import datetime, timedelta

from backend.app.core.exceptions import ApprovalNotFoundError, ApprovalStateError
from backend.app.core.logging import get_logger
from backend.app.models.approval import ApprovalRequest, ApprovalStatus

logger = get_logger(__name__)

# In-memory store — replace with Redis or a DB in production
_STORE: dict[str, ApprovalRequest] = {}

_APPROVAL_TTL_HOURS = 48


class ApprovalService:
    def submit(self, request: ApprovalRequest) -> ApprovalRequest:
        request = request.model_copy(
            update={
                "status": ApprovalStatus.AWAITING_APPROVAL,
                "requested_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=_APPROVAL_TTL_HOURS),
            }
        )
        _STORE[request.request_id] = request
        logger.info("Approval request submitted", request_id=request.request_id)
        return request

    def approve(self, request_id: str, approver: str, comment: str | None = None) -> ApprovalRequest:
        req = self._get_or_raise(request_id)
        self._assert_state(req, {ApprovalStatus.AWAITING_APPROVAL, ApprovalStatus.PROPOSED})

        req = req.model_copy(
            update={
                "status": ApprovalStatus.APPROVED,
                "approver": approver,
                "approval_timestamp": datetime.utcnow(),
            }
        )
        _STORE[request_id] = req
        logger.info("Approval granted", request_id=request_id, approver=approver)
        return req

    def reject(self, request_id: str, approver: str, reason: str) -> ApprovalRequest:
        req = self._get_or_raise(request_id)
        self._assert_state(req, {ApprovalStatus.AWAITING_APPROVAL, ApprovalStatus.PROPOSED})

        req = req.model_copy(
            update={
                "status": ApprovalStatus.REJECTED,
                "approver": approver,
                "approval_timestamp": datetime.utcnow(),
                "rejection_reason": reason,
            }
        )
        _STORE[request_id] = req
        logger.info("Approval rejected", request_id=request_id, approver=approver, reason=reason)
        return req

    def mark_executed(self, request_id: str, execution_result: "ExecutionResult") -> ApprovalRequest:  # noqa: F821
        req = self._get_or_raise(request_id)
        self._assert_state(req, {ApprovalStatus.APPROVED})

        req = req.model_copy(
            update={
                "status": ApprovalStatus.EXECUTED,
                "execution_result": execution_result,
            }
        )
        _STORE[request_id] = req
        logger.info("Request marked as executed", request_id=request_id)
        return req

    def get(self, request_id: str) -> ApprovalRequest:
        return self._get_or_raise(request_id)

    def list_pending(self) -> list[ApprovalRequest]:
        return [
            r for r in _STORE.values()
            if r.status == ApprovalStatus.AWAITING_APPROVAL
        ]

    def list_all(self) -> list[ApprovalRequest]:
        return list(_STORE.values())

    def _get_or_raise(self, request_id: str) -> ApprovalRequest:
        req = _STORE.get(request_id)
        if req is None:
            raise ApprovalNotFoundError(request_id)
        return req

    def _assert_state(
        self, req: ApprovalRequest, allowed: set[ApprovalStatus]
    ) -> None:
        if req.status not in allowed:
            raise ApprovalStateError(
                f"Cannot transition from {req.status!r}. Allowed states: {allowed}",
                code="INVALID_STATE_TRANSITION",
            )
