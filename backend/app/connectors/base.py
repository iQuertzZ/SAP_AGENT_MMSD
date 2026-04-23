from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SAPConnectorBase(ABC):
    """
    Abstract interface for all SAP data connectors.

    Implementations: MockConnector, ODataConnector, RFCConnector.
    """

    @abstractmethod
    async def get_invoice(self, document_id: str, company_code: str | None = None) -> dict[str, Any]:
        """Fetch invoice header + items from RBKPF/RBDRSEG."""

    @abstractmethod
    async def get_purchase_order(self, po_number: str) -> dict[str, Any]:
        """Fetch PO header + items from EKKO/EKPO."""

    @abstractmethod
    async def get_sales_order(self, order_number: str) -> dict[str, Any]:
        """Fetch sales order header + items from VBAK/VBAP."""

    @abstractmethod
    async def get_stock(self, material: str, plant: str | None = None) -> dict[str, Any]:
        """Fetch stock overview from MARD/MCHB."""

    @abstractmethod
    async def get_delivery(self, delivery_number: str) -> dict[str, Any]:
        """Fetch delivery from LIKP/LIPS."""

    @abstractmethod
    async def get_billing_document(self, billing_number: str) -> dict[str, Any]:
        """Fetch billing document from VBRK/VBRP."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the SAP backend is reachable."""
