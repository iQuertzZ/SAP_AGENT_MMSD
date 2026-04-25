"""OData service for MM invoice documents (MIRO / MIR7)."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from backend.app.connectors.odata.mappers.invoice_mapper import map_invoice

if TYPE_CHECKING:
    from backend.app.connectors.odata.client import SAPODataClient

# ECC service paths
_ECC_SET = "/sap/opu/odata/sap/MM_IV_GDC_MIRO_SRV/InvoiceDocumentSet"
# S/4HANA service paths
_S4_DOC = "/sap/opu/odata/sap/API_SUPPLIER_INVOICE_SRV/A_SupplierInvoice"

SERVICE = "mm_invoice"


class InvoiceService:
    def __init__(self, client: "SAPODataClient") -> None:
        self._client = client

    async def get_invoice(
        self, document_id: str, fiscal_year: str | None = None
    ) -> dict[str, Any]:
        version = await self._client.detect_version()
        if version == "ecc":
            return await self._get_ecc(document_id, fiscal_year)
        return await self._get_s4hana(document_id)

    async def _get_ecc(self, document_id: str, fiscal_year: str | None) -> dict[str, Any]:
        if fiscal_year:
            path = f"{_ECC_SET}(FiscalYear='{fiscal_year}',DocumentNumber='{document_id}')"
            params: dict[str, Any] = {
                "$expand": "to_DocumentItem,to_AccountingDoc",
                "$format": "json",
            }
        else:
            path = _ECC_SET
            params = {
                "$filter": f"DocumentNumber eq '{document_id}'",
                "$expand": "to_DocumentItem,to_AccountingDoc",
                "$format": "json",
                "$top": "1",
            }
        data = await self._client.get(path, params=params, service=SERVICE)
        payload = _unwrap_results(data)
        return map_invoice(payload, version="ecc")

    async def _get_s4hana(self, document_id: str) -> dict[str, Any]:
        path = f"{_S4_DOC}('{document_id}')"
        params: dict[str, Any] = {
            "$expand": "to_SupplierInvoiceItemGLAcct,to_SuplrInvcItemPurOrdRef",
            "$format": "json",
        }
        data = await self._client.get(path, params=params, service=SERVICE)
        return map_invoice(data, version="s4hana")


def _unwrap_results(data: dict[str, Any]) -> dict[str, Any]:
    results = data.get("results", [])
    if isinstance(results, list) and results:
        return results[0]
    return data
