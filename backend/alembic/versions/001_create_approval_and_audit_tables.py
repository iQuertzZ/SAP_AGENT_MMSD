"""Create approval_requests and approval_audit_log tables.

Revision ID: 001
Revises:
Create Date: 2026-04-23
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "approval_requests",
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_by", sa.String(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("approver", sa.String(), nullable=True),
        sa.Column("approval_timestamp", sa.DateTime(), nullable=True),
        sa.Column("rejection_reason", sa.String(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("context_data", postgresql.JSONB(), nullable=False),
        sa.Column("diagnosis_data", postgresql.JSONB(), nullable=False),
        sa.Column("action_data", postgresql.JSONB(), nullable=False),
        sa.Column("simulation_data", postgresql.JSONB(), nullable=False),
        sa.Column("execution_result_data", postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_index("ix_approval_requests_status", "approval_requests", ["status"])
    op.create_index("ix_approval_requests_expires_at", "approval_requests", ["expires_at"])

    op.create_table(
        "approval_audit_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["approval_requests.request_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_approval_audit_log_request_id", "approval_audit_log", ["request_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_approval_audit_log_request_id", table_name="approval_audit_log")
    op.drop_table("approval_audit_log")
    op.drop_index("ix_approval_requests_expires_at", table_name="approval_requests")
    op.drop_index("ix_approval_requests_status", table_name="approval_requests")
    op.drop_table("approval_requests")
