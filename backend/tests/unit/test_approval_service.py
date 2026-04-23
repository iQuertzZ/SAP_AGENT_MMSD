"""Unit tests for ApprovalService state machine."""
from __future__ import annotations

import pytest

from backend.app.core.exceptions import ApprovalNotFoundError, ApprovalStateError
from backend.app.models.approval import ApprovalStatus
from backend.app.services.approval_service import ApprovalService


@pytest.fixture(autouse=True)
def clear_store() -> None:
    from backend.app.services import approval_service
    approval_service._STORE.clear()


@pytest.fixture
def service() -> ApprovalService:
    return ApprovalService()


def test_submit_moves_to_awaiting(service: ApprovalService, sample_approval_request) -> None:
    submitted = service.submit(sample_approval_request)
    assert submitted.status == ApprovalStatus.AWAITING_APPROVAL
    assert submitted.expires_at is not None


def test_approve_moves_to_approved(service: ApprovalService, sample_approval_request) -> None:
    submitted = service.submit(sample_approval_request)
    approved = service.approve(submitted.request_id, approver="controller_01")
    assert approved.status == ApprovalStatus.APPROVED
    assert approved.approver == "controller_01"


def test_reject_moves_to_rejected(service: ApprovalService, sample_approval_request) -> None:
    submitted = service.submit(sample_approval_request)
    rejected = service.reject(submitted.request_id, approver="controller_01", reason="Insufficient info")
    assert rejected.status == ApprovalStatus.REJECTED
    assert rejected.rejection_reason == "Insufficient info"


def test_cannot_approve_rejected_request(service: ApprovalService, sample_approval_request) -> None:
    submitted = service.submit(sample_approval_request)
    service.reject(submitted.request_id, approver="mgr", reason="denied")
    with pytest.raises(ApprovalStateError):
        service.approve(submitted.request_id, approver="mgr2")


def test_not_found_raises(service: ApprovalService) -> None:
    with pytest.raises(ApprovalNotFoundError):
        service.get("nonexistent-id")


def test_list_pending_returns_only_pending(service: ApprovalService, sample_approval_request) -> None:
    import uuid, copy
    r1 = copy.deepcopy(sample_approval_request)
    r2 = copy.deepcopy(sample_approval_request)
    r2 = r2.model_copy(update={"request_id": str(uuid.uuid4())})

    s1 = service.submit(r1)
    s2 = service.submit(r2)
    service.approve(s2.request_id, approver="mgr")

    pending = service.list_pending()
    ids = [r.request_id for r in pending]
    assert s1.request_id in ids
    assert s2.request_id not in ids
