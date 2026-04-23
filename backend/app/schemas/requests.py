from __future__ import annotations

from pydantic import BaseModel, Field

from backend.app.models.context import DocumentStatus, SAPModule


class AnalyzeRequest(BaseModel):
    """Submitted by the SAP UI extension when a user requests analysis."""

    tcode: str = Field(..., examples=["MIRO"])
    module: SAPModule
    document_id: str = Field(..., examples=["51000321"])
    document_type: str | None = None
    status: DocumentStatus = DocumentStatus.OPEN
    company_code: str | None = None
    plant: str | None = None
    sales_org: str | None = None
    user: str | None = None
    fiscal_year: str | None = None


class SimulateRequest(BaseModel):
    tcode: str
    module: SAPModule
    document_id: str
    status: DocumentStatus = DocumentStatus.BLOCKED
    action_tcode: str = Field(..., description="The SAP tcode to simulate")
    parameters: dict = Field(default_factory=dict)


class ApproveRequest(BaseModel):
    request_id: str
    approver: str
    comment: str | None = None


class RejectRequest(BaseModel):
    request_id: str
    approver: str
    reason: str


class ExecuteRequest(BaseModel):
    request_id: str
    executor: str
