"""Unit tests for ImpactSimulator."""
from __future__ import annotations

import pytest

from backend.app.models.action import RecommendedAction, RiskLevel
from backend.app.models.context import DocumentStatus, SAPContext, SAPModule
from backend.app.models.diagnosis import DiagnosisResult, IssueSeverity, IssueType
from backend.app.services.impact_simulator import ImpactSimulator


@pytest.fixture
def simulator() -> ImpactSimulator:
    return ImpactSimulator()


def _action(tcode: str, risk: str = "medium") -> RecommendedAction:
    import uuid
    return RecommendedAction(
        action_id=str(uuid.uuid4()),
        tcode=tcode,
        description=f"Test action {tcode}",
        risk=RiskLevel(risk),
        confidence=0.9,
        rollback_plan="Reverse the action.",
    )


def _diagnosis(issue: IssueType) -> DiagnosisResult:
    return DiagnosisResult(
        issue_type=issue,
        root_cause="Test",
        severity=IssueSeverity.HIGH,
        confidence=0.9,
    )


def test_simulate_mr11_posts_financially(
    simulator: ImpactSimulator,
    mm_miro_blocked_context: SAPContext,
) -> None:
    action = _action("MR11")
    diagnosis = _diagnosis(IssueType.GRIR_MISMATCH)
    result = simulator.simulate(mm_miro_blocked_context, diagnosis, action)
    assert result.financial.posting_required is True
    assert result.financial.amount == 3500.0
    assert result.financial.currency == "EUR"


def test_simulate_vkm1_not_financial_posting(
    simulator: ImpactSimulator,
    sd_va03_credit_blocked_context: SAPContext,
) -> None:
    action = _action("VKM1")
    diagnosis = _diagnosis(IssueType.CREDIT_BLOCK)
    result = simulator.simulate(sd_va03_credit_blocked_context, diagnosis, action)
    # VKM1 releases the block — financial amount comes from order value
    assert result.documents_affected >= 1


def test_simulate_high_risk_score_for_high_risk_action(
    simulator: ImpactSimulator,
    mm_miro_blocked_context: SAPContext,
) -> None:
    action = _action("MR11", risk="high")
    diagnosis = _diagnosis(IssueType.GRIR_MISMATCH)
    result = simulator.simulate(mm_miro_blocked_context, diagnosis, action)
    assert result.risk_score >= 0.60


def test_simulate_low_risk_action_has_lower_score(
    simulator: ImpactSimulator,
    mm_miro_blocked_context: SAPContext,
) -> None:
    action = _action("MIR4", risk="low")
    diagnosis = _diagnosis(IssueType.GRIR_MISMATCH)
    result = simulator.simulate(mm_miro_blocked_context, diagnosis, action)
    assert result.risk_score <= 0.40


def test_simulate_returns_warnings_for_high_amount(
    simulator: ImpactSimulator,
) -> None:
    ctx = SAPContext(
        tcode="MIRO",
        module=SAPModule.MM,
        document_id="99999",
        status=DocumentStatus.BLOCKED,
        company_code="1000",
        raw_data={
            "grir_diff": 200000.0,
            "invoice_amount": 200000.0,
            "currency": "EUR",
            "po_number": "4500099999",
        },
    )
    action = _action("MR11")
    diagnosis = _diagnosis(IssueType.GRIR_MISMATCH)
    result = simulator.simulate(ctx, diagnosis, action)
    assert any("200,000" in w or "High financial" in w for w in result.warnings)


def test_simulate_non_reversible_tcode(
    simulator: ImpactSimulator,
    mm_miro_blocked_context: SAPContext,
) -> None:
    action = _action("MR11")
    diagnosis = _diagnosis(IssueType.GRIR_MISMATCH)
    result = simulator.simulate(mm_miro_blocked_context, diagnosis, action)
    assert result.reversible is False


def test_simulate_reversible_tcode(
    simulator: ImpactSimulator,
    mm_miro_blocked_context: SAPContext,
) -> None:
    action = _action("MRBR")
    diagnosis = _diagnosis(IssueType.INVOICE_BLOCKED)
    result = simulator.simulate(mm_miro_blocked_context, diagnosis, action)
    assert result.reversible is True
