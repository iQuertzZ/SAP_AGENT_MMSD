"""OData service for SD sales orders (VA03)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from backend.app.connectors.odata.mappers.sales_order_mapper import map_sales_order

if TYPE_CHECKING:
    from backend.app.connectors.odata.client import SAPODataClient

_ECC_SET = "/sap/opu/odata/sap/SD_SALESORDER_SRV/SalesOrderSet"
_S4_DOC = "/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder"

SERVICE = "sd_sales_order"


class SalesOrderService:
    def __init__(self, client: "SAPODataClient") -> None:
        self._client = client

    async def get_sales_order(self, order_number: str) -> dict[str, Any]:
        version = await self._client.detect_version()
        if version == "ecc":
            return await self._get_ecc(order_number)
        return await self._get_s4hana(order_number)

    async def _get_ecc(self, order_number: str) -> dict[str, Any]:
        path = f"{_ECC_SET}('{order_number}')"
        params: dict[str, Any] = {
            "$expand": "to_SalesOrderItem",
            "$format": "json",
        }
        data = await self._client.get(path, params=params, service=SERVICE)
        return map_sales_order(data, version="ecc")

    async def _get_s4hana(self, order_number: str) -> dict[str, Any]:
        path = f"{_S4_DOC}('{order_number}')"
        params: dict[str, Any] = {
            "$expand": "to_Item,to_Partner",
            "$format": "json",
        }
        data = await self._client.get(path, params=params, service=SERVICE)
        return map_sales_order(data, version="s4hana")
