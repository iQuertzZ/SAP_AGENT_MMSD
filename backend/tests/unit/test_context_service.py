"""Unit tests for ContextService."""
from __future__ import annotations

import pytest

from backend.app.connectors.mock_connector import MockConnector
from backend.app.models.context import DocumentStatus, SAPContext, SAPModule
from backend.app.services.context_service import ContextService


@pytest.fixture
def service() -> ContextService:
    return ContextService(MockConnector())


@pytest.mark.asyncio
async def test_enrich_miro_fetches_invoice(service: ContextService) -> None:
    ctx = SAPContext(tcode="MIRO", module=SAPModule.MM, document_id="51000321", status=DocumentStatus.BLOCKED)
    enriched = await service.enrich(ctx)
    assert enriched.raw_data["vendor"] == "V-100012"
    assert enriched.raw_data["grir_diff"] == 3500.0


@pytest.mark.asyncio
async def test_enrich_va03_fetches_sales_order(service: ContextService) -> None:
    ctx = SAPContext(tcode="VA03", module=SAPModule.SD, document_id="1000081234", status=DocumentStatus.BLOCKED)
    enriched = await service.enrich(ctx)
    assert enriched.raw_data["customer"] == "C-10001"
    assert enriched.raw_data["credit_exposure"] == 275000.0


@pytest.mark.asyncio
async def test_enrich_unknown_tcode_returns_empty_raw(service: ContextService) -> None:
    ctx = SAPContext(tcode="SE16", module=SAPModule.MM, document_id="MARD", status=DocumentStatus.OPEN)
    enriched = await service.enrich(ctx)
    assert enriched.raw_data == {}


@pytest.mark.asyncio
async def test_enrich_missing_document_returns_original(service: ContextService) -> None:
    ctx = SAPContext(tcode="MIRO", module=SAPModule.MM, document_id="NONEXISTENT", status=DocumentStatus.OPEN)
    enriched = await service.enrich(ctx)
    # Should not raise — returns original context with empty raw_data
    assert enriched.document_id == "NONEXISTENT"
    assert enriched.raw_data == {}
