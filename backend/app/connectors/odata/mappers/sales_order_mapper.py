"""OData → sales order dict mapper (ECC + S/4HANA)."""
from __future__ import annotations

from typing import Any, Literal

from backend.app.connectors.odata.mappers import _warn_missing, sap_amount, sap_date, sap_string


def map_sales_order(
    payload: dict[str, Any],
    *,
    version: Literal["ecc", "s4hana"] = "s4hana",
) -> dict[str, Any]:
    if version == "ecc":
        return _map_ecc(payload)
    return _map_s4hana(payload)


def _map_ecc(d: dict[str, Any]) -> dict[str, Any]:
    if "SalesOrder" not in d:
        _warn_missing("SalesOrder", d)
    items = d.get("to_SalesOrderItem", {})
    items_list: list[dict[str, Any]] = (
        items.get("results", []) if isinstance(items, dict) else (items if isinstance(items, list) else [])
    )
    return {
        "order_number": sap_string(d.get("SalesOrder")) or "",
        "customer_id": sap_string(d.get("SoldToParty")),
        "status": sap_string(d.get("OverallSDProcessStatus")) or "OPEN",
        "sales_org": sap_string(d.get("SalesOrganization")),
        "currency": sap_string(d.get("TransactionCurrency")),
        "total_amount": sap_amount(d.get("TotalNetAmount")),
        "created_at": sap_date(d.get("CreationDate")),
        "items": [_map_item(i) for i in items_list],
    }


def _map_s4hana(d: dict[str, Any]) -> dict[str, Any]:
    if "SalesOrder" not in d:
        _warn_missing("SalesOrder", d)
    items = d.get("to_Item", {})
    items_list: list[dict[str, Any]] = (
        items.get("results", []) if isinstance(items, dict) else (items if isinstance(items, list) else [])
    )
    return {
        "order_number": sap_string(d.get("SalesOrder")) or "",
        "customer_id": sap_string(d.get("SoldToParty")),
        "status": sap_string(d.get("OverallSDProcessStatus")) or "OPEN",
        "sales_org": sap_string(d.get("SalesOrganization")),
        "currency": sap_string(d.get("TransactionCurrency")),
        "total_amount": sap_amount(d.get("TotalNetAmount")),
        "created_at": sap_date(d.get("CreationDate")),
        "items": [_map_item(i) for i in items_list],
    }


def _map_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_number": sap_string(item.get("SalesOrderItem")),
        "material": sap_string(item.get("Material")),
        "quantity": sap_amount(item.get("RequestedQuantity")),
        "unit": sap_string(item.get("RequestedQuantityUnit")),
        "net_amount": sap_amount(item.get("NetAmount")),
    }
