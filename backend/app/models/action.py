from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecommendedAction(BaseModel):
    action_id: str = Field(..., description="Unique identifier for this action instance")
    tcode: str = Field(..., description="SAP transaction code to execute", examples=["MR11"])
    description: str
    risk: RiskLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    parameters: dict[str, Any] = Field(default_factory=dict, description="Pre-filled SAP parameters")
    prerequisites: list[str] = Field(default_factory=list)
    rollback_plan: str = Field(..., description="Steps to undo this action if needed")
    estimated_duration_minutes: int = Field(default=5)
    requires_authorization: list[str] = Field(
        default_factory=list, description="SAP authorization objects required"
    )
    documentation_url: str | None = None
