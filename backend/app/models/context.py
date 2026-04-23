from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SAPModule(str, Enum):
    MM = "MM"
    SD = "SD"


class DocumentStatus(str, Enum):
    OPEN = "OPEN"
    BLOCKED = "BLOCKED"
    PARKED = "PARKED"
    POSTED = "POSTED"
    REVERSED = "REVERSED"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"
    PENDING = "PENDING"


class SAPContext(BaseModel):
    """Current SAP session state captured from the client."""

    tcode: str = Field(..., description="Active SAP transaction code", examples=["MIRO", "VA03"])
    module: SAPModule
    document_id: str = Field(..., description="Primary document number")
    document_type: str | None = Field(None, description="SAP document type (e.g. RE, RV)")
    status: DocumentStatus
    company_code: str | None = Field(None, description="SAP company code")
    plant: str | None = Field(None, description="SAP plant")
    sales_org: str | None = Field(None, description="Sales organization (SD)")
    user: str | None = Field(None, description="SAP user running the transaction")
    fiscal_year: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict, description="Full document payload")
