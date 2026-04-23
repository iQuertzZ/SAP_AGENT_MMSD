"""
Execution Service — the controlled write layer.

Safety contract:
  1. EXECUTION_ENABLED must be True in config.
  2. Approval must be in APPROVED state.
  3. Pre-execution checks are run.
  4. All actions are audit-logged.
  5. Rollback plan is always returned.

This service delegates actual SAP writes to the connector layer.
In a real integration, this would call SAP BAPIs/OData POST endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from backend.app.connectors.base import SAPConnectorBase
from backend.app.core.config import settings
from backend.app.core.exceptions import (
    ApprovalStateError,
    ExecutionDisabledError,
    ExecutionError,
)
from backend.app.core.logging import get_logger
from backend.app.models.approval import ApprovalRequest, ApprovalStatus, ExecutionResult
from backend.app.models.context import SAPModule

logger = get_logger(__name__)

# Audit log — replace with a proper audit DB table in production
_AUDIT_LOG: list[dict] = []


class ExecutionService:
    def __init__(self, connector: SAPConnectorBase) -> None:
        self._connector = connector

    async def execute(self, request: ApprovalRequest, executor: str) -> ExecutionResult:
        if not settings.execution_enabled:
            raise ExecutionDisabledError()

        if request.status != ApprovalStatus.APPROVED:
            raise ApprovalStateError(
                f"Cannot execute request in state {request.status!r} — must be APPROVED",
                code="INVALID_STATE_TRANSITION",
            )

        action = request.recommended_action
        logger.info(
            "Executing SAP action",
            request_id=request.request_id,
            tcode=action.tcode,
            executor=executor,
        )

        pre_check_errors = self._pre_execution_checks(request)
        if pre_check_errors:
            raise ExecutionError(
                f"Pre-execution checks failed: {'; '.join(pre_check_errors)}",
                code="PRE_CHECK_FAILED",
            )

        try:
            result = await self._dispatch(request)
        except ExecutionError:
            raise
        except Exception as exc:
            logger.error("Unexpected execution error", error=str(exc))
            raise ExecutionError(f"SAP execution failed: {exc}") from exc

        self._write_audit(request, executor, result)
        return result

    def _pre_execution_checks(self, request: ApprovalRequest) -> list[str]:
        errors: list[str] = []
        simulation = request.simulation

        if simulation.blockers:
            errors.extend(simulation.blockers)

        if simulation.risk_score > 0.85:
            errors.append(
                f"Risk score {simulation.risk_score:.2f} exceeds maximum allowed threshold (0.85). "
                "Escalate to senior management."
            )

        if request.expires_at and datetime.utcnow() > request.expires_at:
            errors.append("Approval request has expired — re-request approval.")

        return errors

    async def _dispatch(self, request: ApprovalRequest) -> ExecutionResult:
        """
        Route to the correct SAP action.

        In a real system each branch would call an SAP BAPI or OData POST.
        Here we simulate success with a generated document number.
        """
        tcode = request.recommended_action.tcode.upper()
        doc_num = f"SIM-{uuid.uuid4().hex[:8].upper()}"
        log: list[str] = []

        if tcode == "MR11":
            log.append(f"Executed GR/IR maintenance for PO {request.context.raw_data.get('po_number')}")
            log.append(f"FI document {doc_num} created in company code {request.context.company_code}")
        elif tcode == "MIGO":
            log.append(f"Goods receipt posted — material document {doc_num}")
            log.append("Stock updated in MARD")
        elif tcode == "MRBR":
            log.append(f"Invoice {request.context.document_id} released from block")
            log.append("Scheduled for next payment run")
        elif tcode == "VKM1":
            log.append(f"Credit block released for order {request.context.document_id}")
            log.append("Order forwarded to delivery scheduling")
        elif tcode == "VA02":
            log.append(f"Sales order {request.context.document_id} updated")
        else:
            log.append(f"Transaction {tcode} executed — document {doc_num}")

        return ExecutionResult(
            success=True,
            sap_document_number=doc_num,
            message=f"Action {tcode} completed successfully. Document: {doc_num}",
            executed_at=datetime.utcnow(),
            execution_log=log,
        )

    def _write_audit(
        self, request: ApprovalRequest, executor: str, result: ExecutionResult
    ) -> None:
        _AUDIT_LOG.append({
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request.request_id,
            "tcode": request.recommended_action.tcode,
            "document_id": request.context.document_id,
            "module": request.context.module,
            "executor": executor,
            "approver": request.approver,
            "success": result.success,
            "sap_document": result.sap_document_number,
            "rollback_plan": request.recommended_action.rollback_plan,
        })
        logger.info(
            "Audit entry written",
            request_id=request.request_id,
            sap_doc=result.sap_document_number,
        )

    def get_audit_log(self) -> list[dict]:
        return list(_AUDIT_LOG)
