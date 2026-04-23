from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueType(str, Enum):
    # MM issues
    GRIR_MISMATCH = "GRIR_MISMATCH"
    MISSING_GR = "MISSING_GR"
    INVOICE_BLOCKED = "INVOICE_BLOCKED"
    PRICE_VARIANCE = "PRICE_VARIANCE"
    QUANTITY_VARIANCE = "QUANTITY_VARIANCE"
    STOCK_INCONSISTENCY = "STOCK_INCONSISTENCY"
    PO_NOT_RELEASED = "PO_NOT_RELEASED"
    VENDOR_BLOCKED = "VENDOR_BLOCKED"
    TOLERANCE_EXCEEDED = "TOLERANCE_EXCEEDED"

    # SD issues
    CREDIT_BLOCK = "CREDIT_BLOCK"
    PRICING_ERROR = "PRICING_ERROR"
    DELIVERY_BLOCK = "DELIVERY_BLOCK"
    BILLING_BLOCK = "BILLING_BLOCK"
    MATERIAL_NOT_AVAILABLE = "MATERIAL_NOT_AVAILABLE"
    PARTNER_MISSING = "PARTNER_MISSING"
    INCOMPLETION_LOG = "INCOMPLETION_LOG"
    OUTPUT_MISSING = "OUTPUT_MISSING"

    # Generic
    UNKNOWN = "UNKNOWN"


class DiagnosisResult(BaseModel):
    issue_type: IssueType
    root_cause: str = Field(..., description="Human-readable root cause explanation")
    severity: IssueSeverity
    confidence: float = Field(..., ge=0.0, le=1.0)
    details: dict[str, Any] = Field(default_factory=dict)
    supporting_evidence: list[str] = Field(default_factory=list)
    affected_documents: list[str] = Field(default_factory=list)
    source: str = Field(default="rule_engine", description="rule_engine | ai | hybrid")
