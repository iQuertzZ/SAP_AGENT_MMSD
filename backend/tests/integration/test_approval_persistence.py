"""Integration tests verifying approval state survives through the facade.

These tests run against the in-memory service (no real DB required) and
verify that the ApprovalFacade correctly delegates to ApprovalService when
DATABASE_URL is not set — i.e., the full round-trip works end-to-end via
the facade without breaking existing behaviour.
"""
from __future__ import annotations

import uuid

import pytest

from backend.app.models.action import RecommendedAction, RiskLevel
from backend.app.models.approval import ApprovalRequest, ApprovalStatus
from backend.app.models.context import DocumentStatus, SAPContext, SAPModule
from backend.app.models.diagnosis import DiagnosisResult, IssueSeverity, IssueType
from backend.app.models.simulation import FinancialImpact, SimulationResult, WorkflowImpact
from backend.app.services.approval_facade import ApprovalFacade
from backend.app.services.approval_service import ApprovalService


@pytest.fixture(autouse=True)
def clear_store() -> None:
    from backend.app.services import approval_service
    approval_service._STORE.clear()


@pytest.fixture()
def facade() -> ApprovalFacade:
    return ApprovalFacade(db_svc=None, mem_svc=ApprovalService())


@pytest.fixture()
def approval_request() -> ApprovalRequest:
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
            rollback_plan="Reverse via MR8M.",
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
async def test_submit_sets_awaiting(
    facade: ApprovalFacade, approval_request: ApprovalRequest
) -> None:
    submitted = await facade.submit(approval_request)
    assert submitted.status == ApprovalStatus.AWAITING_APPROVAL


@pytest.mark.asyncio
async def test_approve_lifecycle(
    facade: ApprovalFacade, approval_request: ApprovalRequest
) -> None:
    submitted = await facade.submit(approval_request)
    approved = await facade.approve(submitted.request_id, "manager1")
    assert approved.status == ApprovalStatus.APPROVED
    assert approved.approver == "manager1"


@pytest.mark.asyncio
async def test_reject_lifecycle(
    facade: ApprovalFacade, approval_request: ApprovalRequest
) -> None:
    submitted = await facade.submit(approval_request)
    rejected = await facade.reject(submitted.request_id, "manager1", "Not within tolerance")
    assert rejected.status == ApprovalStatus.REJECTED
    assert rejected.rejection_reason == "Not within tolerance"


@pytest.mark.asyncio
async def test_get_by_id(
    facade: ApprovalFacade, approval_request: ApprovalRequest
) -> None:
    submitted = await facade.submit(approval_request)
    fetched = await facade.get(submitted.request_id)
    assert fetched.request_id == submitted.request_id


@pytest.mark.asyncio
async def test_list_pending(
    facade: ApprovalFacade, approval_request: ApprovalRequest
) -> None:
    await facade.submit(approval_request)
    pending = await facade.list_pending()
    assert len(pending) == 1
    assert pending[0].status == ApprovalStatus.AWAITING_APPROVAL


@pytest.mark.asyncio
async def test_list_all(
    facade: ApprovalFacade, approval_request: ApprovalRequest
) -> None:
    await facade.submit(approval_request)
    all_items = await facade.list_all()
    assert len(all_items) == 1
