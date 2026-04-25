from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models.approval import ApprovalRequestORM
from backend.app.db.models.audit import AuditLogORM
from backend.app.models.approval import ApprovalRequest, ApprovalStatus
from backend.app.models.context import SAPContext
from backend.app.models.diagnosis import DiagnosisResult
from backend.app.models.action import RecommendedAction
from backend.app.models.simulation import SimulationResult
from backend.app.models.approval import ExecutionResult


class ApprovalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── internal helpers ────────────────────────────────────────────────────

    @staticmethod
    def _to_orm(req: ApprovalRequest) -> ApprovalRequestORM:
        return ApprovalRequestORM(
            request_id=req.request_id,
            status=req.status.value,
            requested_by=req.requested_by,
            requested_at=req.requested_at,
            approver=req.approver,
            approval_timestamp=req.approval_timestamp,
            rejection_reason=req.rejection_reason,
            expires_at=req.expires_at,
            context_data=req.context.model_dump(mode="json"),
            diagnosis_data=req.diagnosis.model_dump(mode="json"),
            action_data=req.recommended_action.model_dump(mode="json"),
            simulation_data=req.simulation.model_dump(mode="json"),
            execution_result_data=(
                req.execution_result.model_dump(mode="json")
                if req.execution_result
                else None
            ),
        )

    @staticmethod
    def _from_orm(row: ApprovalRequestORM) -> ApprovalRequest:
        return ApprovalRequest(
            request_id=row.request_id,
            context=SAPContext.model_validate(row.context_data),
            diagnosis=DiagnosisResult.model_validate(row.diagnosis_data),
            recommended_action=RecommendedAction.model_validate(row.action_data),
            simulation=SimulationResult.model_validate(row.simulation_data),
            status=ApprovalStatus(row.status),
            requested_by=row.requested_by,
            requested_at=row.requested_at,
            approver=row.approver,
            approval_timestamp=row.approval_timestamp,
            rejection_reason=row.rejection_reason,
            execution_result=(
                ExecutionResult.model_validate(row.execution_result_data)
                if row.execution_result_data
                else None
            ),
            expires_at=row.expires_at,
        )

    # ── public API ──────────────────────────────────────────────────────────

    async def create(self, request: ApprovalRequest) -> ApprovalRequest:
        orm = self._to_orm(request)
        self._session.add(orm)
        await self._session.flush()
        return request

    async def get_by_request_id(self, request_id: str) -> ApprovalRequest | None:
        result = await self._session.execute(
            select(ApprovalRequestORM).where(
                ApprovalRequestORM.request_id == request_id
            )
        )
        row = result.scalar_one_or_none()
        return self._from_orm(row) if row else None

    async def update_state(self, request: ApprovalRequest) -> ApprovalRequest:
        result = await self._session.execute(
            select(ApprovalRequestORM).where(
                ApprovalRequestORM.request_id == request.request_id
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise ValueError(f"ApprovalRequest {request.request_id!r} not found in DB")

        row.status = request.status.value
        row.approver = request.approver
        row.approval_timestamp = request.approval_timestamp
        row.rejection_reason = request.rejection_reason
        row.execution_result_data = (
            request.execution_result.model_dump(mode="json")
            if request.execution_result
            else None
        )
        await self._session.flush()
        return request

    async def append_audit_log(
        self,
        request_id: str,
        action: str,
        actor: str,
        details: dict | None = None,
    ) -> None:
        self._session.add(
            AuditLogORM(
                request_id=request_id,
                action=action,
                actor=actor,
                timestamp=datetime.utcnow(),
                details=details,
            )
        )
        await self._session.flush()

    async def list_all(self) -> list[ApprovalRequest]:
        result = await self._session.execute(select(ApprovalRequestORM))
        return [self._from_orm(row) for row in result.scalars().all()]

    async def list_pending(self) -> list[ApprovalRequest]:
        result = await self._session.execute(
            select(ApprovalRequestORM).where(
                ApprovalRequestORM.status == ApprovalStatus.AWAITING_APPROVAL.value
            )
        )
        return [self._from_orm(row) for row in result.scalars().all()]

    async def delete_expired(self) -> int:
        now = datetime.utcnow()
        result = await self._session.execute(
            delete(ApprovalRequestORM).where(
                ApprovalRequestORM.expires_at < now
            )
        )
        await self._session.flush()
        return result.rowcount  # type: ignore[return-value]
