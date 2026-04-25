"""OData service for MM material stock."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from backend.app.connectors.odata.mappers.stock_mapper import map_stock

if TYPE_CHECKING:
    from backend.app.connectors.odata.client import SAPODataClient

_ECC_SET = "/sap/opu/odata/sap/MMIM_MATERIAL_STOCK_SRV/MaterialStockAvailability"
_S4_SET = "/sap/opu/odata/sap/API_MATERIAL_STOCK_SRV/A_MatlStkInAcctMod"

SERVICE = "mm_stock"


class StockService:
    def __init__(self, client: "SAPODataClient") -> None:
        self._client = client

    async def get_stock(self, material: str, plant: str | None = None) -> dict[str, Any]:
        version = await self._client.detect_version()
        if version == "ecc":
            return await self._get_ecc(material, plant)
        return await self._get_s4hana(material, plant)

    async def _get_ecc(self, material: str, plant: str | None) -> dict[str, Any]:
        if plant:
            path = f"{_ECC_SET}(Material='{material}',Plant='{plant}')"
            params: dict[str, Any] = {"$format": "json"}
        else:
            path = _ECC_SET
            params = {
                "$filter": f"Material eq '{material}'",
                "$format": "json",
                "$top": "1",
            }
        data = await self._client.get(path, params=params, service=SERVICE)
        return map_stock(data, version="ecc")

    async def _get_s4hana(self, material: str, plant: str | None) -> dict[str, Any]:
        if plant:
            path = f"{_S4_SET}(Material='{material}',Plant='{plant}')"
            params: dict[str, Any] = {"$format": "json"}
        else:
            path = _S4_SET
            params = {
                "$filter": f"Material eq '{material}'",
                "$format": "json",
                "$top": "1",
            }
        data = await self._client.get(path, params=params, service=SERVICE)
        return map_stock(data, version="s4hana")
