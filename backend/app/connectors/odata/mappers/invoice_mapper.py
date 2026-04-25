"""OData → invoice dict mapper (ECC + S/4HANA)."""
from __future__ import annotations

from typing import Any, Literal

from backend.app.connectors.odata.mappers import (
    _warn_missing,
    sap_amount,
    sap_string,
)


def map_invoice(
    payload: dict[str, Any],
    *,
    version: Literal["ecc", "s4hana"] = "s4hana",
) -> dict[str, Any]:
    if version == "ecc":
        return _map_ecc(payload)
    return _map_s4hana(payload)


def _map_ecc(d: dict[str, Any]) -> dict[str, Any]:
    for field in ("DocumentNumber", "FiscalYear"):
        if field not in d:
            _warn_missing(field, d)
    items = d.get("to_DocumentItem", {})
    items_list: list[dict[str, Any]] = []
    if isinstance(items, dict):
        items_list = items.get("results", [])
    elif isinstance(items, list):
        items_list = items

    block_reason = sap_string(d.get("PaymentBlockingReason"))
    status = "BLOCKED" if block_reason else "OPEN"

    return {
        "document_id": sap_string(d.get("DocumentNumber")) or "",
        "fiscal_year": sap_string(d.get("FiscalYear")),
        "vendor_id": sap_string(d.get("LifNr")),
        "amount": sap_amount(d.get("DmbtrSum")),
        "currency": sap_string(d.get("Waers")),
        "status": status,
        "block_reason": block_reason,
        "purchase_order_id": sap_string(d.get("EBELN")),
        "items": [_map_item_ecc(i) for i in items_list],
    }


def _map_item_ecc(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_number": sap_string(item.get("Buzei")),
        "amount": sap_amount(item.get("Wrbtr")),
        "currency": sap_string(item.get("Waers")),
        "gl_account": sap_string(item.get("Hkont")),
        "cost_center": sap_string(item.get("Kostl")),
    }


def _map_s4hana(d: dict[str, Any]) -> dict[str, Any]:
    for field in ("SupplierInvoice", "DocumentCurrency"):
        if field not in d:
            _warn_missing(field, d)
    items = d.get("to_SupplierInvoiceItemGLAcct", {})
    items_list: list[dict[str, Any]] = []
    if isinstance(items, dict):
        items_list = items.get("results", [])
    elif isinstance(items, list):
        items_list = items

    inv_status = sap_string(d.get("SupplierInvoiceStatus")) or ""
    block_reason = sap_string(d.get("PaymentBlockingReason"))
    if block_reason:
        status = "BLOCKED"
    elif inv_status in {"C", "CLEARED"}:
        status = "POSTED"
    else:
        status = "OPEN"

    return {
        "document_id": sap_string(d.get("SupplierInvoice")) or "",
        "fiscal_year": sap_string(d.get("FiscalYear")),
        "vendor_id": sap_string(d.get("Supplier")),
        "amount": sap_amount(d.get("DocumentAmount") or d.get("DocumentAmountInCompanyCodeCurrency")),
        "currency": sap_string(d.get("DocumentCurrency")),
        "status": status,
        "block_reason": block_reason,
        "purchase_order_id": sap_string(d.get("PurchaseOrder")),
        "items": [_map_item_s4hana(i) for i in items_list],
    }


def _map_item_s4hana(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_number": sap_string(item.get("SupplierInvoiceItem")),
        "amount": sap_amount(item.get("DocumentItemAmount")),
        "currency": sap_string(item.get("DocumentCurrency")),
        "gl_account": sap_string(item.get("GLAccount")),
        "cost_center": sap_string(item.get("CostCenter")),
    }
