"""Async approval service backed by PostgreSQL via ApprovalRepository."""
from __future__ import annotations

from datetime import datetime, timedelta

from backend.app.core.exceptions import ApprovalNotFoundError, ApprovalStateError
from backend.app.core.logging import get_logger
from backend.app.db.repositories.approval_repository import ApprovalRepository
from backend.app.models.approval import ApprovalRequest, ApprovalStatus, ExecutionResult

logger = get_logger(__name__)

_APPROVAL_TTL_HOURS = 48


class ApprovalServiceDB:
    def __init__(self, repo: ApprovalRepository) -> None:
        self._repo = repo

    async def submit(self, request: ApprovalRequest) -> ApprovalRequest:
        request = request.model_copy(
            update={
                "status": ApprovalStatus.AWAITING_APPROVAL,
                "requested_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=_APPROVAL_TTL_HOURS),
            }
        )
        await self._repo.create(request)
        await self._repo.append_audit_log(
            request.request_id, "submit", request.requested_by or "system"
        )
        logger.info("Approval request submitted (DB)", request_id=request.request_id)
        return request

    async def approve(
        self, request_id: str, approver: str, comment: str | None = None
    ) -> ApprovalRequest:
        req = await self._get_or_raise(request_id)
        self._assert_state(req, {ApprovalStatus.AWAITING_APPROVAL, ApprovalStatus.PROPOSED})

        req = req.model_copy(
            update={
                "status": ApprovalStatus.APPROVED,
                "approver": approver,
                "approval_timestamp": datetime.utcnow(),
            }
        )
        await self._repo.update_state(req)
        await self._repo.append_audit_log(
            request_id, "approve", approver, {"comment": comment}
        )
        logger.info("Approval granted (DB)", request_id=request_id, approver=approver)
        return req

    async def reject(
        self, request_id: str, approver: str, reason: str
    ) -> ApprovalRequest:
        req = await self._get_or_raise(request_id)
        self._assert_state(req, {ApprovalStatus.AWAITING_APPROVAL, ApprovalStatus.PROPOSED})

        req = req.model_copy(
            update={
                "status": ApprovalStatus.REJECTED,
                "approver": approver,
                "approval_timestamp": datetime.utcnow(),
                "rejection_reason": reason,
            }
        )
        await self._repo.update_state(req)
        await self._repo.append_audit_log(
            request_id, "reject", approver, {"reason": reason}
        )
        logger.info("Approval rejected (DB)", request_id=request_id, approver=approver)
        return req

    async def mark_executed(
        self, request_id: str, execution_result: ExecutionResult
    ) -> ApprovalRequest:
        req = await self._get_or_raise(request_id)
        self._assert_state(req, {ApprovalStatus.APPROVED})

        req = req.model_copy(
            update={
                "status": ApprovalStatus.EXECUTED,
                "execution_result": execution_result,
            }
        )
        await self._repo.update_state(req)
        await self._repo.append_audit_log(request_id, "execute", "system")
        logger.info("Request marked as executed (DB)", request_id=request_id)
        return req

    async def get(self, request_id: str) -> ApprovalRequest:
        return await self._get_or_raise(request_id)

    async def list_pending(self) -> list[ApprovalRequest]:
        return await self._repo.list_pending()

    async def list_all(self) -> list[ApprovalRequest]:
        return await self._repo.list_all()

    # ── helpers ─────────────────────────────────────────────────────────────

    async def _get_or_raise(self, request_id: str) -> ApprovalRequest:
        req = await self._repo.get_by_request_id(request_id)
        if req is None:
            raise ApprovalNotFoundError(request_id)
        return req

    @staticmethod
    def _assert_state(
        req: ApprovalRequest, allowed: set[ApprovalStatus]
    ) -> None:
        if req.status not in allowed:
            raise ApprovalStateError(
                f"Cannot transition from {req.status!r}. Allowed states: {allowed}",
                code="INVALID_STATE_TRANSITION",
            )
