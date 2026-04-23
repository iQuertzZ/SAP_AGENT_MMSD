from __future__ import annotations

from pydantic import BaseModel, Field


class FinancialImpact(BaseModel):
    posting_required: bool
    amount: float | None = None
    currency: str | None = None
    gl_accounts_affected: list[str] = Field(default_factory=list)
    cost_centers_affected: list[str] = Field(default_factory=list)


class WorkflowImpact(BaseModel):
    steps_triggered: list[str] = Field(default_factory=list)
    approvals_required: list[str] = Field(default_factory=list)
    notifications_sent: list[str] = Field(default_factory=list)


class SimulationResult(BaseModel):
    documents_affected: int
    financial: FinancialImpact
    workflow: WorkflowImpact
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Composite risk 0-1")
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(
        default_factory=list, description="Issues that prevent execution"
    )
    reversible: bool = Field(default=True)
    simulation_notes: str = ""
