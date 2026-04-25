from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from backend.app.models.action import RecommendedAction
from backend.app.models.approval import ApprovalRequest, ApprovalStatus
from backend.app.models.context import SAPContext
from backend.app.models.diagnosis import DiagnosisResult
from backend.app.models.simulation import SimulationResult


class AnalysisResponse(BaseModel):
    """Full copilot analysis result returned to the UI."""

    request_id: str
    context: SAPContext
    diagnosis: DiagnosisResult
    recommended_actions: list[RecommendedAction]
    primary_action: RecommendedAction | None = None
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_ms: int = 0


class SimulationResponse(BaseModel):
    action_tcode: str
    simulation: SimulationResult
    simulated_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalResponse(BaseModel):
    request_id: str
    status: ApprovalStatus
    message: str


class ApprovalListResponse(BaseModel):
    total: int
    items: list[ApprovalRequest]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    git_sha: str = "unknown"
    ai_enabled: bool = False
    connector: str = "mock"
    execution_enabled: bool = False
    circuit_breaker: str | None = None
    sap_metrics: dict | None = None
    cache: dict | None = None
