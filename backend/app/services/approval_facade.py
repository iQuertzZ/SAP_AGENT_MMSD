"""ApprovalFacade — unified async interface over DB or in-memory service."""
from __future__ import annotations

from backend.app.models.approval import ApprovalRequest, ExecutionResult
from backend.app.services.approval_service import ApprovalService
from backend.app.services.approval_service_db import ApprovalServiceDB


class ApprovalFacade:
    """Routes always call this.  Delegates to DB service when available,
    falls back to the sync in-memory ApprovalService otherwise."""

    def __init__(
        self,
        db_svc: ApprovalServiceDB | None,
        mem_svc: ApprovalService,
    ) -> None:
        self._db = db_svc
        self._mem = mem_svc

    async def submit(self, request: ApprovalRequest) -> ApprovalRequest:
        if self._db:
            return await self._db.submit(request)
        return self._mem.submit(request)

    async def approve(
        self, request_id: str, approver: str, comment: str | None = None
    ) -> ApprovalRequest:
        if self._db:
            return await self._db.approve(request_id, approver, comment)
        return self._mem.approve(request_id, approver, comment)

    async def reject(
        self, request_id: str, approver: str, reason: str
    ) -> ApprovalRequest:
        if self._db:
            return await self._db.reject(request_id, approver, reason)
        return self._mem.reject(request_id, approver, reason)

    async def mark_executed(
        self, request_id: str, execution_result: ExecutionResult
    ) -> ApprovalRequest:
        if self._db:
            return await self._db.mark_executed(request_id, execution_result)
        return self._mem.mark_executed(request_id, execution_result)

    async def get(self, request_id: str) -> ApprovalRequest:
        if self._db:
            return await self._db.get(request_id)
        return self._mem.get(request_id)

    async def list_pending(self) -> list[ApprovalRequest]:
        if self._db:
            return await self._db.list_pending()
        return self._mem.list_pending()

    async def list_all(self) -> list[ApprovalRequest]:
        if self._db:
            return await self._db.list_all()
        return self._mem.list_all()
