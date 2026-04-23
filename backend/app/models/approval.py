from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from backend.app.models.action import RecommendedAction
from backend.app.models.context import SAPContext
from backend.app.models.diagnosis import DiagnosisResult
from backend.app.models.simulation import SimulationResult


class ApprovalStatus(str, Enum):
    PROPOSED = "proposed"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    ROLLED_BACK = "rolled_back"
    EXPIRED = "expired"


class ExecutionResult(BaseModel):
    success: bool
    sap_document_number: str | None = None
    message: str = ""
    executed_at: datetime = Field(default_factory=datetime.utcnow)
    execution_log: list[str] = Field(default_factory=list)


class ApprovalRequest(BaseModel):
    request_id: str
    context: SAPContext
    diagnosis: DiagnosisResult
    recommended_action: RecommendedAction
    simulation: SimulationResult
    status: ApprovalStatus = ApprovalStatus.PROPOSED
    requested_by: str | None = None
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    approver: str | None = None
    approval_timestamp: datetime | None = None
    rejection_reason: str | None = None
    execution_result: ExecutionResult | None = None
    expires_at: datetime | None = None
