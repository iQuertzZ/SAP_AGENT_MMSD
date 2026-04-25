"""OData → stock dict mapper (ECC + S/4HANA)."""
from __future__ import annotations

from typing import Any, Literal

from backend.app.connectors.odata.mappers import _warn_missing, sap_amount, sap_string


def map_stock(
    payload: dict[str, Any],
    *,
    version: Literal["ecc", "s4hana"] = "s4hana",
) -> dict[str, Any]:
    if version == "ecc":
        return _map_ecc(payload)
    return _map_s4hana(payload)


def _map_ecc(d: dict[str, Any]) -> dict[str, Any]:
    if "Material" not in d:
        _warn_missing("Material", d)
    return {
        "material": sap_string(d.get("Material")) or "",
        "plant": sap_string(d.get("Plant")),
        "storage_location": sap_string(d.get("StorageLocation")),
        "unrestricted_stock": sap_amount(d.get("MatlWrhsStkQtyInMatBaseUnit") or d.get("UnrestrictedStockQty")),
        "unit": sap_string(d.get("MaterialBaseUnit")),
        "blocked_stock": sap_amount(d.get("BlockedStockQty")),
        "quality_stock": sap_amount(d.get("QualityInspectionStockQty")),
    }


def _map_s4hana(d: dict[str, Any]) -> dict[str, Any]:
    if "Material" not in d:
        _warn_missing("Material", d)
    return {
        "material": sap_string(d.get("Material")) or "",
        "plant": sap_string(d.get("Plant")),
        "storage_location": sap_string(d.get("StorageLocation")),
        "unrestricted_stock": sap_amount(d.get("MatlWrhsStkQtyInMatBaseUnit")),
        "unit": sap_string(d.get("MaterialBaseUnit")),
        "blocked_stock": sap_amount(d.get("BlockedStockQty")),
        "quality_stock": sap_amount(d.get("QualityInspectionStockQty")),
    }
