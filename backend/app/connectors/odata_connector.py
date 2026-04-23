"""
SAP OData connector — calls SAP Gateway services via REST/OData v2.

Endpoints used:
  /MM_PUR_PO_MAINT_SRV     — Purchase Orders
  /MM_IV_GDC_MIRO_SRV      — Invoice Verification
  /MM_WM_GR_GI_SRV         — Goods Movements
  /SD_SALESORDER_MANAGE_SRV — Sales Orders
  /SD_ORDER_DELIVER_SRV    — Deliveries
  /SD_BILLING_MANAGE_SRV   — Billing
"""
from __future__ import annotations

from typing import Any

import httpx

from backend.app.connectors.base import SAPConnectorBase
from backend.app.core.config import settings
from backend.app.core.exceptions import DocumentNotFoundError, SAPConnectorError
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class ODataConnector(SAPConnectorBase):
    """Connects to SAP via OData v2 REST API."""

    def __init__(self) -> None:
        self._base_url = settings.sap_odata_base_url.rstrip("/")
        self._auth = (settings.sap_odata_user, settings.sap_odata_password)
        self._headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                auth=self._auth,
                headers=self._headers,
                timeout=30.0,
                verify=True,
            )
        return self._client

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            resp = await self._get_client().get(url, params=params)
            if resp.status_code == 404:
                raise DocumentNotFoundError(path.split("/")[-1])
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            return data.get("d", data)
        except httpx.HTTPStatusError as exc:
            logger.error("SAP OData HTTP error", url=url, status=exc.response.status_code)
            raise SAPConnectorError(
                f"SAP returned HTTP {exc.response.status_code} for {url}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("SAP OData connection error", url=url, error=str(exc))
            raise SAPConnectorError(f"Cannot reach SAP: {exc}") from exc

    async def get_invoice(self, document_id: str, company_code: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {
            "$filter": f"DocumentNumber eq '{document_id}'",
            "$expand": "to_Items",
            "$format": "json",
        }
        return await self._get("/MM_IV_GDC_MIRO_SRV/A_InvoiceDocument", params)

    async def get_purchase_order(self, po_number: str) -> dict[str, Any]:
        params: dict[str, Any] = {
            "$filter": f"PurchaseOrder eq '{po_number}'",
            "$expand": "to_PurchaseOrderItem",
            "$format": "json",
        }
        return await self._get("/MM_PUR_PO_MAINT_SRV/A_PurchaseOrder", params)

    async def get_sales_order(self, order_number: str) -> dict[str, Any]:
        params: dict[str, Any] = {
            "$filter": f"SalesOrder eq '{order_number}'",
            "$expand": "to_Item,to_Partner",
            "$format": "json",
        }
        return await self._get("/SD_SALESORDER_MANAGE_SRV/A_SalesOrder", params)

    async def get_stock(self, material: str, plant: str | None = None) -> dict[str, Any]:
        filter_str = f"Material eq '{material}'"
        if plant:
            filter_str += f" and Plant eq '{plant}'"
        params: dict[str, Any] = {"$filter": filter_str, "$format": "json"}
        return await self._get("/API_MATERIAL_STOCK_SRV/A_MatlStkInAcctMod", params)

    async def get_delivery(self, delivery_number: str) -> dict[str, Any]:
        params: dict[str, Any] = {
            "$filter": f"DeliveryDocument eq '{delivery_number}'",
            "$expand": "to_DeliveryDocumentItem",
            "$format": "json",
        }
        return await self._get("/SD_ORDER_DELIVER_SRV/A_OutbDeliveryHeader", params)

    async def get_billing_document(self, billing_number: str) -> dict[str, Any]:
        params: dict[str, Any] = {
            "$filter": f"BillingDocument eq '{billing_number}'",
            "$expand": "to_Item",
            "$format": "json",
        }
        return await self._get("/SD_BILLING_MANAGE_SRV/A_BillingDocument", params)

    async def health_check(self) -> bool:
        try:
            resp = await self._get_client().get(
                f"{self._base_url}/", params={"$format": "json"}, timeout=5.0
            )
            return resp.status_code < 500
        except Exception:
            return False

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
