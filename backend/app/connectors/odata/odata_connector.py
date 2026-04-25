"""OData connector facade — implements BaseSAPConnector using the odata/ sub-package."""
from __future__ import annotations

from typing import Any

from backend.app.connectors.base import SAPConnectorBase
from backend.app.connectors.odata.cache import ODataCache
from backend.app.connectors.odata.client import SAPODataClient
from backend.app.connectors.odata.services.mm_invoice import InvoiceService
from backend.app.connectors.odata.services.mm_purchase_order import PurchaseOrderService
from backend.app.connectors.odata.services.mm_stock import StockService
from backend.app.connectors.odata.services.sd_sales_order import SalesOrderService

# TTLs (seconds)
_TTL_INVOICE = 60
_TTL_PO = 120
_TTL_SO = 60
_TTL_STOCK = 30


class ODataConnector(SAPConnectorBase):
    """Production SAP connector — wraps SAPODataClient with caching."""

    def __init__(self) -> None:
        self._client = SAPODataClient()
        self._cache = ODataCache()
        self._invoice_svc = InvoiceService(self._client)
        self._po_svc = PurchaseOrderService(self._client)
        self._so_svc = SalesOrderService(self._client)
        self._stock_svc = StockService(self._client)

    # Expose metrics + cache for the health endpoint
    @property
    def metrics(self) -> Any:
        return self._client.metrics

    @property
    def cache(self) -> ODataCache:
        return self._cache

    @property
    def circuit_breaker_state(self) -> str:
        return self._client.circuit_breaker_state

    # ── BaseSAPConnector implementation ────────────────────────────────────────

    async def get_invoice(
        self, document_id: str, company_code: str | None = None
    ) -> dict[str, Any]:
        key = f"invoice:{document_id}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        result = await self._invoice_svc.get_invoice(document_id)
        self._cache.set(key, result, _TTL_INVOICE)
        return result

    async def get_purchase_order(self, po_number: str) -> dict[str, Any]:
        key = f"po:{po_number}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        result = await self._po_svc.get_purchase_order(po_number)
        self._cache.set(key, result, _TTL_PO)
        return result

    async def get_sales_order(self, order_number: str) -> dict[str, Any]:
        key = f"so:{order_number}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        result = await self._so_svc.get_sales_order(order_number)
        self._cache.set(key, result, _TTL_SO)
        return result

    async def get_stock(self, material: str, plant: str | None = None) -> dict[str, Any]:
        key = f"stock:{material}:{plant or ''}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        result = await self._stock_svc.get_stock(material, plant)
        self._cache.set(key, result, _TTL_STOCK)
        return result

    async def get_delivery(self, delivery_number: str) -> dict[str, Any]:
        # Not cached — delivery state changes rapidly
        path = f"/sap/opu/odata/sap/SD_ORDER_DELIVER_SRV/A_OutbDeliveryHeader('{delivery_number}')"
        return await self._client.get(
            path,
            params={"$expand": "to_DeliveryDocumentItem", "$format": "json"},
            service="sd_delivery",
        )

    async def get_billing_document(self, billing_number: str) -> dict[str, Any]:
        path = f"/sap/opu/odata/sap/SD_BILLING_MANAGE_SRV/A_BillingDocument('{billing_number}')"
        return await self._client.get(
            path,
            params={"$expand": "to_Item", "$format": "json"},
            service="sd_billing",
        )

    async def health_check(self) -> bool:
        return await self._client.health_check()

    async def close(self) -> None:
        await self._client.close()
