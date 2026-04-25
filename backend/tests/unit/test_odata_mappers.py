"""Unit tests for OData mappers and helper functions."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.app.connectors.odata.mappers import sap_amount, sap_bool, sap_date, sap_string
from backend.app.connectors.odata.mappers.invoice_mapper import map_invoice
from backend.app.connectors.odata.mappers.po_mapper import map_purchase_order
from backend.app.connectors.odata.mappers.sales_order_mapper import map_sales_order
from backend.app.connectors.odata.mappers.stock_mapper import map_stock

FIXTURES = Path(__file__).parent.parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


# ── Helper functions ───────────────────────────────────────────────────────────

class TestSapAmount:
    def test_valid_float(self):
        assert sap_amount("1234.56") == 1234.56

    def test_empty_string(self):
        assert sap_amount("") == 0.0

    def test_none(self):
        assert sap_amount(None) == 0.0

    def test_zero(self):
        assert sap_amount("0.00") == 0.0

    def test_invalid(self):
        assert sap_amount("N/A") == 0.0


class TestSapDate:
    def test_odata_timestamp(self):
        dt = sap_date("/Date(1704067200000)/")
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 1

    def test_odata_timestamp_with_offset(self):
        dt = sap_date("/Date(1704067200000+0100)/")
        assert dt is not None

    def test_none(self):
        assert sap_date(None) is None

    def test_empty_string(self):
        assert sap_date("") is None

    def test_invalid(self):
        assert sap_date("not-a-date") is None


class TestSapBool:
    def test_x_is_true(self):
        assert sap_bool("X") is True

    def test_empty_is_false(self):
        assert sap_bool("") is False

    def test_none_is_false(self):
        assert sap_bool(None) is False

    def test_true_string(self):
        assert sap_bool("TRUE") is True

    def test_one_string(self):
        assert sap_bool("1") is True

    def test_bool_true(self):
        assert sap_bool(True) is True  # type: ignore[arg-type]


class TestSapString:
    def test_normal(self):
        assert sap_string("hello") == "hello"

    def test_empty_returns_none(self):
        assert sap_string("") is None

    def test_none_returns_none(self):
        assert sap_string(None) is None


# ── Invoice mapper ─────────────────────────────────────────────────────────────

class TestInvoiceMapper:
    def test_ecc_basic(self):
        raw = load("odata_invoice_ecc.json")
        payload = raw["d"]["results"][0]
        result = map_invoice(payload, version="ecc")
        assert result["document_id"] == "5100032100"
        assert result["vendor_id"] == "1000234"
        assert result["amount"] == 12345.67
        assert result["currency"] == "EUR"
        assert result["status"] == "OPEN"
        assert result["purchase_order_id"] == "4500012345"
        assert len(result["items"]) == 1
        assert result["items"][0]["gl_account"] == "160000"

    def test_ecc_blocked(self):
        payload = {
            "DocumentNumber": "5100099999",
            "FiscalYear": "2024",
            "LifNr": "V001",
            "DmbtrSum": "1000.00",
            "Waers": "EUR",
            "PaymentBlockingReason": "R",
            "EBELN": "",
        }
        result = map_invoice(payload, version="ecc")
        assert result["status"] == "BLOCKED"
        assert result["block_reason"] == "R"

    def test_s4hana_basic(self):
        raw = load("odata_invoice_s4hana.json")
        payload = raw["d"]
        result = map_invoice(payload, version="s4hana")
        assert result["document_id"] == "5100032100"
        assert result["vendor_id"] == "1000234"
        assert result["amount"] == 12345.67
        assert result["status"] == "OPEN"

    def test_s4hana_blocked(self):
        payload = {
            "SupplierInvoice": "5100099999",
            "DocumentCurrency": "EUR",
            "Supplier": "V001",
            "DocumentAmount": "500.00",
            "PaymentBlockingReason": "B",
            "SupplierInvoiceStatus": "O",
        }
        result = map_invoice(payload, version="s4hana")
        assert result["status"] == "BLOCKED"

    def test_s4hana_null_amount(self):
        payload = {
            "SupplierInvoice": "5100099999",
            "DocumentCurrency": "EUR",
            "Supplier": "V001",
            "DocumentAmount": "",
            "PaymentBlockingReason": "",
            "SupplierInvoiceStatus": "O",
        }
        result = map_invoice(payload, version="s4hana")
        assert result["amount"] == 0.0

    def test_ecc_missing_items(self):
        payload = {
            "DocumentNumber": "5100032100",
            "FiscalYear": "2024",
            "LifNr": "V001",
            "DmbtrSum": "100.00",
            "Waers": "EUR",
            "PaymentBlockingReason": "",
        }
        result = map_invoice(payload, version="ecc")
        assert result["items"] == []


# ── PO mapper ─────────────────────────────────────────────────────────────────

class TestPOMapper:
    def test_ecc(self):
        raw = load("odata_po_ecc.json")
        result = map_purchase_order(raw["d"], version="ecc")
        assert result["po_number"] == "4500012345"
        assert result["vendor_id"] == "1000234"
        assert result["total_amount"] == 5000.0
        assert result["currency"] == "EUR"
        assert result["created_at"] is not None
        assert len(result["items"]) == 1
        assert result["items"][0]["material"] == "MAT-001"
        assert result["items"][0]["quantity"] == 10.0

    def test_s4hana(self):
        raw = load("odata_po_s4hana.json")
        result = map_purchase_order(raw["d"], version="s4hana")
        assert result["po_number"] == "4500012345"
        assert result["vendor_id"] == "1000234"

    def test_empty_items(self):
        payload = {
            "PurchaseOrder": "4500099999",
            "Vendor": "V001",
            "DocumentCurrency": "EUR",
            "NetPriceAmount": "",
        }
        result = map_purchase_order(payload, version="ecc")
        assert result["items"] == []
        assert result["total_amount"] == 0.0


# ── Sales order mapper ─────────────────────────────────────────────────────────

class TestSalesOrderMapper:
    def test_ecc(self):
        raw = load("odata_sales_order_ecc.json")
        result = map_sales_order(raw["d"], version="ecc")
        assert result["order_number"] == "0000012345"
        assert result["customer_id"] == "CUST-001"
        assert result["total_amount"] == 8750.0
        assert result["created_at"] is not None
        assert len(result["items"]) == 1

    def test_s4hana(self):
        raw = load("odata_sales_order_s4hana.json")
        result = map_sales_order(raw["d"], version="s4hana")
        assert result["order_number"] == "0000012345"
        assert len(result["items"]) == 1

    def test_missing_items(self):
        payload = {
            "SalesOrder": "0000000001",
            "SoldToParty": "CUST-001",
            "TransactionCurrency": "EUR",
            "TotalNetAmount": "0.00",
        }
        result = map_sales_order(payload, version="s4hana")
        assert result["items"] == []


# ── Stock mapper ───────────────────────────────────────────────────────────────

class TestStockMapper:
    def test_ecc(self):
        raw = load("odata_stock_ecc.json")
        result = map_stock(raw["d"], version="ecc")
        assert result["material"] == "MAT-001"
        assert result["plant"] == "1000"
        assert result["unrestricted_stock"] == 150.0
        assert result["blocked_stock"] == 5.0
        assert result["quality_stock"] == 10.0

    def test_s4hana(self):
        raw = load("odata_stock_ecc.json")
        result = map_stock(raw["d"], version="s4hana")
        assert result["material"] == "MAT-001"
        assert result["unrestricted_stock"] == 150.0

    def test_null_stock(self):
        payload = {
            "Material": "MAT-999",
            "Plant": "1000",
            "MatlWrhsStkQtyInMatBaseUnit": "",
            "MaterialBaseUnit": "EA",
        }
        result = map_stock(payload, version="s4hana")
        assert result["unrestricted_stock"] == 0.0
