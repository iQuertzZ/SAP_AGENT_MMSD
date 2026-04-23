"""Unit tests for DiagnosticService (rule engine path)."""
from __future__ import annotations

import pytest

from backend.app.models.context import DocumentStatus, SAPContext, SAPModule
from backend.app.models.diagnosis import IssueType
from backend.app.services.diagnostic_service import DiagnosticService


@pytest.fixture
def service() -> DiagnosticService:
    return DiagnosticService(ai_service=None)


@pytest.mark.asyncio
async def test_diagnose_grir_mismatch(service: DiagnosticService, mm_miro_blocked_context: SAPContext) -> None:
    result = await service.diagnose(mm_miro_blocked_context)
    assert result.issue_type == IssueType.GRIR_MISMATCH
    assert result.confidence >= 0.85
    assert "GR/IR" in result.root_cause
    assert result.source == "rule_engine"


@pytest.mark.asyncio
async def test_diagnose_missing_gr(service: DiagnosticService, mm_miro_missing_gr_context: SAPContext) -> None:
    result = await service.diagnose(mm_miro_missing_gr_context)
    assert result.issue_type == IssueType.MISSING_GR
    assert result.confidence >= 0.85


@pytest.mark.asyncio
async def test_diagnose_credit_block(service: DiagnosticService, sd_va03_credit_blocked_context: SAPContext) -> None:
    result = await service.diagnose(sd_va03_credit_blocked_context)
    assert result.issue_type == IssueType.CREDIT_BLOCK
    assert result.confidence >= 0.85
    assert "credit" in result.root_cause.lower()


@pytest.mark.asyncio
async def test_diagnose_unknown_falls_back(service: DiagnosticService) -> None:
    ctx = SAPContext(
        tcode="SE16",
        module=SAPModule.MM,
        document_id="MARD",
        status=DocumentStatus.OPEN,
        raw_data={},
    )
    result = await service.diagnose(ctx)
    assert result.issue_type == IssueType.UNKNOWN
    assert result.confidence < 0.5


@pytest.mark.asyncio
async def test_diagnose_includes_evidence(service: DiagnosticService, mm_miro_blocked_context: SAPContext) -> None:
    result = await service.diagnose(mm_miro_blocked_context)
    assert len(result.supporting_evidence) > 0
    assert any("3500" in ev for ev in result.supporting_evidence)


@pytest.mark.asyncio
async def test_diagnose_sd_pricing_error(service: DiagnosticService) -> None:
    ctx = SAPContext(
        tcode="VA03",
        module=SAPModule.SD,
        document_id="1000081235",
        status=DocumentStatus.OPEN,
        raw_data={
            "pricing_incomplete": True,
            "missing_conditions": ["PR00", "MWST"],
            "block_reason": "pricing_error",
        },
    )
    result = await service.diagnose(ctx)
    assert result.issue_type == IssueType.PRICING_ERROR
