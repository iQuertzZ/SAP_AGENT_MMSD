from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ApprovalRequestORM(Base):
    __tablename__ = "approval_requests"

    request_id: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    requested_by: Mapped[str | None] = mapped_column(String, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    approver: Mapped[str | None] = mapped_column(String, nullable=True)
    approval_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Nested Pydantic objects serialised as JSONB
    context_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    diagnosis_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    action_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    simulation_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    execution_result_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_approval_requests_status", "status"),
        Index("ix_approval_requests_expires_at", "expires_at"),
    )
