"""OData → purchase order dict mapper (ECC + S/4HANA)."""
from __future__ import annotations

from typing import Any, Literal

from backend.app.connectors.odata.mappers import _warn_missing, sap_amount, sap_date, sap_string


def map_purchase_order(
    payload: dict[str, Any],
    *,
    version: Literal["ecc", "s4hana"] = "s4hana",
) -> dict[str, Any]:
    if version == "ecc":
        return _map_ecc(payload)
    return _map_s4hana(payload)


def _map_ecc(d: dict[str, Any]) -> dict[str, Any]:
    if "PurchaseOrder" not in d:
        _warn_missing("PurchaseOrder", d)
    items = d.get("to_PurchaseOrderItem", {})
    items_list: list[dict[str, Any]] = (
        items.get("results", []) if isinstance(items, dict) else (items if isinstance(items, list) else [])
    )
    return {
        "po_number": sap_string(d.get("PurchaseOrder")) or "",
        "vendor_id": sap_string(d.get("Vendor")),
        "status": sap_string(d.get("PurchaseOrderStatus")) or "OPEN",
        "company_code": sap_string(d.get("CompanyCode")),
        "plant": sap_string(d.get("Plant")),
        "currency": sap_string(d.get("DocumentCurrency")),
        "total_amount": sap_amount(d.get("NetPriceAmount")),
        "created_at": sap_date(d.get("CreationDate")),
        "items": [_map_item_ecc(i) for i in items_list],
    }


def _map_item_ecc(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_number": sap_string(item.get("PurchaseOrderItem")),
        "material": sap_string(item.get("Material")),
        "quantity": sap_amount(item.get("OrderQuantity")),
        "unit": sap_string(item.get("PurchaseOrderQuantityUnit")),
        "net_price": sap_amount(item.get("NetPriceAmount")),
        "delivery_date": sap_date(item.get("ScheduleLineDeliveryDate")),
    }


def _map_s4hana(d: dict[str, Any]) -> dict[str, Any]:
    if "PurchaseOrder" not in d:
        _warn_missing("PurchaseOrder", d)
    items = d.get("to_PurchaseOrderItem", {})
    items_list: list[dict[str, Any]] = (
        items.get("results", []) if isinstance(items, dict) else (items if isinstance(items, list) else [])
    )
    return {
        "po_number": sap_string(d.get("PurchaseOrder")) or "",
        "vendor_id": sap_string(d.get("Supplier")),
        "status": sap_string(d.get("PurchaseOrderStatus")) or "OPEN",
        "company_code": sap_string(d.get("CompanyCode")),
        "plant": sap_string(d.get("Plant")),
        "currency": sap_string(d.get("DocumentCurrency")),
        "total_amount": sap_amount(d.get("NetPriceAmount")),
        "created_at": sap_date(d.get("CreationDate")),
        "items": [_map_item_s4hana(i) for i in items_list],
    }


def _map_item_s4hana(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_number": sap_string(item.get("PurchaseOrderItem")),
        "material": sap_string(item.get("Material")),
        "quantity": sap_amount(item.get("OrderQuantity")),
        "unit": sap_string(item.get("PurchaseOrderQuantityUnit")),
        "net_price": sap_amount(item.get("NetPriceAmount")),
        "delivery_date": sap_date(item.get("ScheduleLineDeliveryDate")),
    }
