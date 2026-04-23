"""
Mock SAP connector — returns realistic test data without a live SAP system.
Used for development, demos, and CI/CD tests.
"""
from __future__ import annotations

from typing import Any

from backend.app.connectors.base import SAPConnectorBase
from backend.app.core.exceptions import DocumentNotFoundError


_MOCK_INVOICES: dict[str, dict[str, Any]] = {
    "51000321": {
        "document_id": "51000321",
        "document_type": "RE",
        "company_code": "1000",
        "fiscal_year": "2026",
        "vendor": "V-100012",
        "vendor_name": "ACME Supplies GmbH",
        "status": "BLOCKED",
        "block_reason": "price_variance",
        "invoice_amount": 48500.00,
        "currency": "EUR",
        "po_number": "4500012345",
        "gr_amount": 45000.00,
        "grir_diff": 3500.00,
        "posting_date": "2026-04-20",
        "items": [
            {"item": "1", "material": "MAT-001", "qty_invoiced": 100, "qty_received": 100,
             "price_invoiced": 485.0, "price_po": 450.0, "variance_pct": 7.78},
        ],
    },
    "51000322": {
        "document_id": "51000322",
        "document_type": "RE",
        "company_code": "1000",
        "fiscal_year": "2026",
        "vendor": "V-200045",
        "vendor_name": "TechParts Ltd.",
        "status": "BLOCKED",
        "block_reason": "missing_gr",
        "invoice_amount": 12000.00,
        "currency": "EUR",
        "po_number": "4500012346",
        "gr_amount": 0.00,
        "grir_diff": 12000.00,
        "posting_date": "2026-04-21",
        "items": [
            {"item": "1", "material": "MAT-002", "qty_invoiced": 50, "qty_received": 0,
             "price_invoiced": 240.0, "price_po": 240.0, "variance_pct": 0.0},
        ],
    },
}

_MOCK_PURCHASE_ORDERS: dict[str, dict[str, Any]] = {
    "4500012345": {
        "po_number": "4500012345",
        "document_type": "NB",
        "status": "OPEN",
        "vendor": "V-100012",
        "company_code": "1000",
        "plant": "1000",
        "total_value": 45000.00,
        "currency": "EUR",
        "release_status": "RELEASED",
        "items": [
            {"item": "10", "material": "MAT-001", "qty_ordered": 100,
             "qty_delivered": 100, "qty_invoiced": 0, "price": 450.0},
        ],
    },
    "4500012346": {
        "po_number": "4500012346",
        "document_type": "NB",
        "status": "OPEN",
        "vendor": "V-200045",
        "company_code": "1000",
        "plant": "1000",
        "total_value": 12000.00,
        "currency": "EUR",
        "release_status": "RELEASED",
        "items": [
            {"item": "10", "material": "MAT-002", "qty_ordered": 50,
             "qty_delivered": 0, "qty_invoiced": 0, "price": 240.0},
        ],
    },
}

_MOCK_SALES_ORDERS: dict[str, dict[str, Any]] = {
    "1000081234": {
        "order_number": "1000081234",
        "order_type": "OR",
        "status": "BLOCKED",
        "block_reason": "credit_block",
        "customer": "C-10001",
        "customer_name": "Global Retail AG",
        "sales_org": "1000",
        "distribution_channel": "10",
        "division": "00",
        "total_value": 250000.00,
        "currency": "EUR",
        "credit_limit": 200000.00,
        "credit_exposure": 275000.00,
        "requested_delivery_date": "2026-05-10",
        "items": [
            {"item": "10", "material": "FG-001", "qty": 500, "price": 500.0},
        ],
    },
    "1000081235": {
        "order_number": "1000081235",
        "order_type": "OR",
        "status": "OPEN",
        "block_reason": "pricing_error",
        "customer": "C-10002",
        "customer_name": "RegionalMart BV",
        "sales_org": "1000",
        "total_value": 0.0,
        "currency": "EUR",
        "pricing_incomplete": True,
        "missing_conditions": ["PR00", "MWST"],
        "requested_delivery_date": "2026-05-15",
        "items": [
            {"item": "10", "material": "FG-002", "qty": 200, "price": 0.0},
        ],
    },
}

_MOCK_STOCK: dict[str, dict[str, Any]] = {
    "MAT-001": {
        "material": "MAT-001",
        "description": "Industrial Valve DN50",
        "plant": "1000",
        "unrestricted": 150.0,
        "in_quality": 10.0,
        "blocked": 0.0,
        "in_transit": 50.0,
        "unit": "PC",
    },
    "MAT-002": {
        "material": "MAT-002",
        "description": "Electronic Control Unit",
        "plant": "1000",
        "unrestricted": 0.0,
        "in_quality": 0.0,
        "blocked": 0.0,
        "in_transit": 0.0,
        "unit": "PC",
    },
}


class MockConnector(SAPConnectorBase):
    """Returns static mock data for development and testing."""

    async def get_invoice(self, document_id: str, company_code: str | None = None) -> dict[str, Any]:
        doc = _MOCK_INVOICES.get(document_id)
        if doc is None:
            raise DocumentNotFoundError(document_id)
        return doc

    async def get_purchase_order(self, po_number: str) -> dict[str, Any]:
        doc = _MOCK_PURCHASE_ORDERS.get(po_number)
        if doc is None:
            raise DocumentNotFoundError(po_number)
        return doc

    async def get_sales_order(self, order_number: str) -> dict[str, Any]:
        doc = _MOCK_SALES_ORDERS.get(order_number)
        if doc is None:
            raise DocumentNotFoundError(order_number)
        return doc

    async def get_stock(self, material: str, plant: str | None = None) -> dict[str, Any]:
        doc = _MOCK_STOCK.get(material)
        if doc is None:
            raise DocumentNotFoundError(material)
        return doc

    async def get_delivery(self, delivery_number: str) -> dict[str, Any]:
        return {
            "delivery_number": delivery_number,
            "status": "OPEN",
            "ship_to": "C-10001",
            "plant": "1000",
            "items": [],
        }

    async def get_billing_document(self, billing_number: str) -> dict[str, Any]:
        return {
            "billing_number": billing_number,
            "status": "OPEN",
            "billing_type": "F2",
            "customer": "C-10001",
            "net_value": 0.0,
            "currency": "EUR",
        }

    async def health_check(self) -> bool:
        return True
