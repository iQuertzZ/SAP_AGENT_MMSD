"""Integration tests for the OData connector with mocked HTTP responses (respx)."""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
import respx
from httpx import Response

from backend.app.connectors.odata.auth.basic import BasicAuthHandler
from backend.app.connectors.odata.client import SAPODataClient
from backend.app.connectors.odata.exceptions import (
    SAPAuthError,
    SAPConnectionError,
    SAPDocumentNotFoundError,
    SAPServiceError,
)

FIXTURES = Path(__file__).parent.parent / "fixtures"
BASE = "https://sap-test.example.com"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def make_client() -> SAPODataClient:
    """Return a pre-configured SAPODataClient pointing at the test base URL."""
    c = SAPODataClient.__new__(SAPODataClient)
    # Manually init instead of reading from settings
    from backend.app.connectors.odata.cache import ODataCache
    from backend.app.connectors.odata.client import CircuitBreaker
    from backend.app.connectors.odata.metrics import SAPMetrics
    c._base_url = BASE
    c._verify_ssl = False
    c._timeout = httpx.Timeout(10.0)
    c._max_retries = 2
    c._backoff = 0.0
    c._oauth = None
    c._basic = BasicAuthHandler("testuser", "testpass")
    c._csrf_token = None
    c._sap_version = None
    c._cb = CircuitBreaker(failure_threshold=10, recovery_timeout=3600)
    c.metrics = SAPMetrics()
    c._client = None
    return c


@pytest.fixture()
def client():
    return make_client()


# ── Invoice S/4HANA ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_get_invoice_s4hana(client):
    fixture = load("odata_invoice_s4hana.json")
    respx.get(
        f"{BASE}/sap/opu/odata/sap/API_SUPPLIER_INVOICE_SRV/A_SupplierInvoice('5100032100')"
    ).mock(return_value=Response(200, json=fixture))

    client._sap_version = "s4hana"
    data = await client.get(
        "/sap/opu/odata/sap/API_SUPPLIER_INVOICE_SRV/A_SupplierInvoice('5100032100')",
        service="test",
    )
    assert data["SupplierInvoice"] == "5100032100"
    await client.close()


# ── Invoice ECC ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_get_invoice_ecc(client):
    fixture = load("odata_invoice_ecc.json")
    respx.get(
        f"{BASE}/sap/opu/odata/sap/MM_IV_GDC_MIRO_SRV/InvoiceDocumentSet"
    ).mock(return_value=Response(200, json=fixture))

    client._sap_version = "ecc"
    data = await client.get(
        "/sap/opu/odata/sap/MM_IV_GDC_MIRO_SRV/InvoiceDocumentSet",
        service="test",
    )
    # The "d" wrapper is stripped — results is now at top level
    assert "results" in data
    await client.close()


# ── 404 → SAPDocumentNotFoundError ────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_document_not_found(client):
    fixture = load("odata_error_document_not_found.json")
    respx.get(
        f"{BASE}/sap/opu/odata/sap/API_SUPPLIER_INVOICE_SRV/A_SupplierInvoice('9999')"
    ).mock(return_value=Response(404, json=fixture))

    with pytest.raises(SAPDocumentNotFoundError):
        await client.get(
            "/sap/opu/odata/sap/API_SUPPLIER_INVOICE_SRV/A_SupplierInvoice('9999')",
            service="test",
        )
    await client.close()


# ── 4xx service error → SAPServiceError ───────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_service_error(client):
    fixture = load("odata_error_service.json")
    respx.get(f"{BASE}/sap/opu/odata/sap/TEST_SRV/Items").mock(
        return_value=Response(400, json=fixture)
    )

    with pytest.raises(SAPServiceError) as exc_info:
        await client.get("/sap/opu/odata/sap/TEST_SRV/Items", service="test")
    assert exc_info.value.sap_error_code == "MIRO/001"
    await client.close()


# ── 401 → SAPAuthError ────────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_auth_error(client):
    respx.get(f"{BASE}/sap/opu/odata/sap/TEST_SRV/Items").mock(
        return_value=Response(401, json={"error": {"code": "401", "message": {"value": "Unauthorized"}}})
    )

    with pytest.raises(SAPAuthError):
        await client.get("/sap/opu/odata/sap/TEST_SRV/Items", service="test")
    await client.close()


# ── 500 → retry N times → SAPConnectionError ──────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_retry_on_500(client):
    respx.get(f"{BASE}/sap/opu/odata/sap/TEST_SRV/Items").mock(
        return_value=Response(500, text="Internal Server Error")
    )

    with pytest.raises(SAPConnectionError):
        await client.get("/sap/opu/odata/sap/TEST_SRV/Items", service="test")

    # max_retries=2 → 3 total attempts
    assert respx.calls.call_count == 3
    await client.close()


# ── CSRF token fetch + retry on 403 ───────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_csrf_fetch_and_retry(client):
    respx.get(f"{BASE}/sap/opu/odata/").mock(
        return_value=Response(200, headers={"x-csrf-token": "tok123"})
    )
    respx.post(f"{BASE}/sap/opu/odata/sap/TEST_SRV/Items").mock(
        side_effect=[
            Response(403, text="CSRF token validation failed"),
            Response(201, json={"d": {"id": "1"}}),
        ]
    )

    result = await client._request(
        "POST",
        "/sap/opu/odata/sap/TEST_SRV/Items",
        json={"test": True},
        service="test",
    )
    assert result == {"id": "1"}
    await client.close()


# ── Health check ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_health_check_ok(client):
    respx.get(
        f"{BASE}/sap/opu/odata/IWFND/CATALOGSERVICE/ServiceCollection"
    ).mock(return_value=Response(200, json={"d": {"results": []}}))

    ok = await client.health_check()
    assert ok is True
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_health_check_fail(client):
    respx.get(
        f"{BASE}/sap/opu/odata/IWFND/CATALOGSERVICE/ServiceCollection"
    ).mock(return_value=Response(503, text="Service Unavailable"))

    ok = await client.health_check()
    assert ok is False
    await client.close()


# ── Metrics are recorded ───────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_metrics_recorded(client):
    fixture = load("odata_invoice_s4hana.json")
    respx.get(
        f"{BASE}/sap/opu/odata/sap/API_SUPPLIER_INVOICE_SRV/A_SupplierInvoice('123')"
    ).mock(return_value=Response(200, json=fixture))

    client._sap_version = "s4hana"
    await client.get(
        "/sap/opu/odata/sap/API_SUPPLIER_INVOICE_SRV/A_SupplierInvoice('123')",
        service="mm_invoice",
    )
    summary = client.metrics.get_summary()
    assert summary["total_requests"] == 1
    assert summary["successful_requests"] == 1
    assert summary["requests_by_service"]["mm_invoice"] == 1
    await client.close()
