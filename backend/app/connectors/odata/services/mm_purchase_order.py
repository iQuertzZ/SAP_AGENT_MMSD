"""OData service for MM purchase orders (ME23N)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from backend.app.connectors.odata.mappers.po_mapper import map_purchase_order

if TYPE_CHECKING:
    from backend.app.connectors.odata.client import SAPODataClient

_ECC_SET = "/sap/opu/odata/sap/MM_PUR_PO_MAINT_SRV/PurchaseOrderSet"
_S4_DOC = "/sap/opu/odata/sap/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder"

SERVICE = "mm_purchase_order"


class PurchaseOrderService:
    def __init__(self, client: "SAPODataClient") -> None:
        self._client = client

    async def get_purchase_order(self, po_number: str) -> dict[str, Any]:
        version = await self._client.detect_version()
        if version == "ecc":
            return await self._get_ecc(po_number)
        return await self._get_s4hana(po_number)

    async def _get_ecc(self, po_number: str) -> dict[str, Any]:
        path = f"{_ECC_SET}('{po_number}')"
        params: dict[str, Any] = {
            "$expand": "to_PurchaseOrderItem",
            "$format": "json",
        }
        data = await self._client.get(path, params=params, service=SERVICE)
        return map_purchase_order(data, version="ecc")

    async def _get_s4hana(self, po_number: str) -> dict[str, Any]:
        path = f"{_S4_DOC}('{po_number}')"
        params: dict[str, Any] = {
            "$expand": "to_PurchaseOrderItem",
            "$format": "json",
        }
        data = await self._client.get(path, params=params, service=SERVICE)
        return map_purchase_order(data, version="s4hana")
