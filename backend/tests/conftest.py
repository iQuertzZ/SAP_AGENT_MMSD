"""Shared pytest fixtures."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models.action import RecommendedAction, RiskLevel
from backend.app.models.approval import ApprovalRequest, ApprovalStatus
from backend.app.models.context import DocumentStatus, SAPContext, SAPModule
from backend.app.models.diagnosis import DiagnosisResult, IssueSeverity, IssueType
from backend.app.models.simulation import FinancialImpact, SimulationResult, WorkflowImpact


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def mm_miro_blocked_context() -> SAPContext:
    return SAPContext(
        tcode="MIRO",
        module=SAPModule.MM,
        document_id="51000321",
        document_type="RE",
        status=DocumentStatus.BLOCKED,
        company_code="1000",
        plant="1000",
        raw_data={
            "vendor": "V-100012",
            "po_number": "4500012345",
            "gr_amount": 45000.0,
            "invoice_amount": 48500.0,
            "grir_diff": 3500.0,
            "block_reason": "price_variance",
            "currency": "EUR",
        },
    )


@pytest.fixture
def mm_miro_missing_gr_context() -> SAPContext:
    return SAPContext(
        tcode="MIRO",
        module=SAPModule.MM,
        document_id="51000322",
        document_type="RE",
        status=DocumentStatus.BLOCKED,
        company_code="1000",
        raw_data={
            "vendor": "V-200045",
            "po_number": "4500012346",
            "gr_amount": 0.0,
            "invoice_amount": 12000.0,
            "grir_diff": 12000.0,
            "block_reason": "missing_gr",
            "currency": "EUR",
        },
    )


@pytest.fixture
def sd_va03_credit_blocked_context() -> SAPContext:
    return SAPContext(
        tcode="VA03",
        module=SAPModule.SD,
        document_id="1000081234",
        status=DocumentStatus.BLOCKED,
        sales_org="1000",
        raw_data={
            "customer": "C-10001",
            "credit_limit": 200000.0,
            "credit_exposure": 275000.0,
            "total_value": 250000.0,
            "block_reason": "credit_block",
            "currency": "EUR",
        },
    )


@pytest.fixture
def sample_diagnosis_grir() -> DiagnosisResult:
    return DiagnosisResult(
        issue_type=IssueType.GRIR_MISMATCH,
        root_cause="GR/IR balance of 3500 EUR — invoice price exceeds PO price.",
        severity=IssueSeverity.HIGH,
        confidence=0.92,
        supporting_evidence=["GR/IR difference of 3500 EUR"],
        source="rule_engine",
    )


@pytest.fixture
def sample_action_mr11() -> RecommendedAction:
    return RecommendedAction(
        action_id="test-action-001",
        tcode="MR11",
        description="Run GR/IR account maintenance",
        risk=RiskLevel.MEDIUM,
        confidence=0.87,
        rollback_plan="Reverse MR11 posting with MR8M.",
    )


@pytest.fixture
def sample_simulation() -> SimulationResult:
    return SimulationResult(
        documents_affected=2,
        financial=FinancialImpact(
            posting_required=True,
            amount=3500.0,
            currency="EUR",
            gl_accounts_affected=["WRX", "GR/IR Clearing"],
        ),
        workflow=WorkflowImpact(
            steps_triggered=["FI posting created"],
            approvals_required=["Supervisor sign-off"],
        ),
        risk_score=0.42,
        reversible=True,
    )


@pytest.fixture
def sample_approval_request(
    mm_miro_blocked_context: SAPContext,
    sample_diagnosis_grir: DiagnosisResult,
    sample_action_mr11: RecommendedAction,
    sample_simulation: SimulationResult,
) -> ApprovalRequest:
    import uuid
    return ApprovalRequest(
        request_id=str(uuid.uuid4()),
        context=mm_miro_blocked_context,
        diagnosis=sample_diagnosis_grir,
        recommended_action=sample_action_mr11,
        simulation=sample_simulation,
        status=ApprovalStatus.PROPOSED,
    )
