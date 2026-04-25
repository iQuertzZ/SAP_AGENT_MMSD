"""Unit tests for ApprovalRepository — skipped when TEST_DATABASE_URL is not set."""
from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.db.base import Base
from backend.app.db.repositories.approval_repository import ApprovalRepository
from backend.app.models.approval import ApprovalRequest, ApprovalStatus
from backend.app.models.action import RecommendedAction, RiskLevel
from backend.app.models.context import DocumentStatus, SAPContext, SAPModule
from backend.app.models.diagnosis import DiagnosisResult, IssueSeverity, IssueType
from backend.app.models.simulation import FinancialImpact, SimulationResult, WorkflowImpact

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "")

pytestmark = pytest.mark.skipif(
    not TEST_DB_URL,
    reason="TEST_DATABASE_URL not set — skipping DB repository tests",
)


@pytest_asyncio.fixture(scope="module")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture()
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture()
def sample_request() -> ApprovalRequest:
    return ApprovalRequest(
        request_id=str(uuid.uuid4()),
        context=SAPContext(
            tcode="MIRO",
            module=SAPModule.MM,
            document_id="51000321",
            status=DocumentStatus.BLOCKED,
        ),
        diagnosis=DiagnosisResult(
            issue_type=IssueType.GRIR_MISMATCH,
            root_cause="GR/IR balance mismatch",
            severity=IssueSeverity.HIGH,
            confidence=0.92,
            supporting_evidence=[],
            source="rule_engine",
        ),
        recommended_action=RecommendedAction(
            action_id="act-001",
            tcode="MR11",
            description="GR/IR maintenance",
            risk=RiskLevel.MEDIUM,
            confidence=0.87,
            rollback_plan="Reverse MR11 via MR8M.",
        ),
        simulation=SimulationResult(
            documents_affected=1,
            financial=FinancialImpact(posting_required=True, amount=3500.0, currency="EUR"),
            workflow=WorkflowImpact(),
            risk_score=0.4,
            reversible=True,
        ),
        status=ApprovalStatus.PROPOSED,
    )


@pytest.mark.asyncio
async def test_create_and_get(db_session: AsyncSession, sample_request: ApprovalRequest) -> None:
    repo = ApprovalRepository(db_session)
    created = await repo.create(sample_request)
    assert created.request_id == sample_request.request_id

    fetched = await repo.get_by_request_id(sample_request.request_id)
    assert fetched is not None
    assert fetched.request_id == sample_request.request_id
    assert fetched.status == ApprovalStatus.PROPOSED


@pytest.mark.asyncio
async def test_get_missing_returns_none(db_session: AsyncSession) -> None:
    repo = ApprovalRepository(db_session)
    result = await repo.get_by_request_id("does-not-exist")
    assert result is None


@pytest.mark.asyncio
async def test_update_state(db_session: AsyncSession, sample_request: ApprovalRequest) -> None:
    repo = ApprovalRepository(db_session)
    await repo.create(sample_request)

    updated = sample_request.model_copy(
        update={"status": ApprovalStatus.APPROVED, "approver": "jdoe"}
    )
    await repo.update_state(updated)

    fetched = await repo.get_by_request_id(sample_request.request_id)
    assert fetched is not None
    assert fetched.status == ApprovalStatus.APPROVED
    assert fetched.approver == "jdoe"


@pytest.mark.asyncio
async def test_list_all(db_session: AsyncSession, sample_request: ApprovalRequest) -> None:
    repo = ApprovalRepository(db_session)
    await repo.create(sample_request)

    all_requests = await repo.list_all()
    ids = [r.request_id for r in all_requests]
    assert sample_request.request_id in ids


@pytest.mark.asyncio
async def test_append_audit_log(
    db_session: AsyncSession, sample_request: ApprovalRequest
) -> None:
    repo = ApprovalRepository(db_session)
    await repo.create(sample_request)
    await repo.append_audit_log(sample_request.request_id, "approve", "jdoe", {"note": "ok"})
    # No assertion on content — just verify no exception is raised
