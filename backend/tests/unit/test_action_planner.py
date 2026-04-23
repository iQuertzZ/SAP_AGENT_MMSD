"""Unit tests for ActionPlanner."""
from __future__ import annotations

import pytest

from backend.app.models.action import RiskLevel
from backend.app.models.context import DocumentStatus, SAPContext, SAPModule
from backend.app.models.diagnosis import DiagnosisResult, IssueSeverity, IssueType
from backend.app.services.action_planner import ActionPlanner


@pytest.fixture
def planner() -> ActionPlanner:
    return ActionPlanner()


def _make_diagnosis(issue: IssueType, confidence: float = 0.92) -> DiagnosisResult:
    return DiagnosisResult(
        issue_type=issue,
        root_cause="Test root cause",
        severity=IssueSeverity.HIGH,
        confidence=confidence,
    )


def test_plan_grir_returns_mr11_first(planner: ActionPlanner, mm_miro_blocked_context: SAPContext) -> None:
    diagnosis = _make_diagnosis(IssueType.GRIR_MISMATCH)
    actions = planner.plan(mm_miro_blocked_context, diagnosis)
    assert actions, "Should return at least one action"
    assert actions[0].tcode == "MR11"


def test_plan_credit_block_returns_vkm1_first(planner: ActionPlanner, sd_va03_credit_blocked_context: SAPContext) -> None:
    diagnosis = _make_diagnosis(IssueType.CREDIT_BLOCK)
    actions = planner.plan(sd_va03_credit_blocked_context, diagnosis)
    assert actions[0].tcode == "VKM1"


def test_plan_actions_sorted_by_confidence(planner: ActionPlanner, mm_miro_blocked_context: SAPContext) -> None:
    diagnosis = _make_diagnosis(IssueType.PRICE_VARIANCE)
    actions = planner.plan(mm_miro_blocked_context, diagnosis)
    assert len(actions) >= 2
    confidences = [a.confidence for a in actions]
    assert confidences == sorted(confidences, reverse=True)


def test_plan_unknown_issue_returns_empty(planner: ActionPlanner, mm_miro_blocked_context: SAPContext) -> None:
    diagnosis = _make_diagnosis(IssueType.UNKNOWN)
    actions = planner.plan(mm_miro_blocked_context, diagnosis)
    assert actions == []


def test_plan_action_has_rollback(planner: ActionPlanner, mm_miro_blocked_context: SAPContext) -> None:
    diagnosis = _make_diagnosis(IssueType.GRIR_MISMATCH)
    actions = planner.plan(mm_miro_blocked_context, diagnosis)
    for action in actions:
        assert action.rollback_plan, "Every action must have a rollback plan"


def test_plan_prefills_parameters(planner: ActionPlanner, mm_miro_blocked_context: SAPContext) -> None:
    diagnosis = _make_diagnosis(IssueType.GRIR_MISMATCH)
    actions = planner.plan(mm_miro_blocked_context, diagnosis)
    primary = actions[0]
    assert "BUKRS" in primary.parameters
    assert primary.parameters["BUKRS"] == "1000"


def test_plan_missing_gr_returns_migo(planner: ActionPlanner, mm_miro_missing_gr_context: SAPContext) -> None:
    diagnosis = _make_diagnosis(IssueType.MISSING_GR)
    actions = planner.plan(mm_miro_missing_gr_context, diagnosis)
    assert actions[0].tcode == "MIGO"
    assert actions[0].risk == RiskLevel.MEDIUM
