"""
Context Service — enriches the raw SAPContext with full document data
fetched from the SAP connector.
"""
from __future__ import annotations

from typing import Any

from backend.app.connectors.base import SAPConnectorBase
from backend.app.core.logging import get_logger
from backend.app.models.context import SAPContext, SAPModule

logger = get_logger(__name__)


class ContextService:
    def __init__(self, connector: SAPConnectorBase) -> None:
        self._connector = connector

    async def enrich(self, context: SAPContext) -> SAPContext:
        """Fetch full document payload and attach to context.raw_data."""
        try:
            raw = await self._fetch_document(context)
            return context.model_copy(update={"raw_data": raw})
        except Exception as exc:
            logger.warning("Could not enrich context", doc_id=context.document_id, error=str(exc))
            return context

    async def _fetch_document(self, context: SAPContext) -> dict[str, Any]:
        tcode = context.tcode.upper()
        doc_id = context.document_id

        # MM
        if context.module == SAPModule.MM:
            if tcode in {"MIRO", "MIR4", "MIR6"}:
                return await self._connector.get_invoice(doc_id, context.company_code)
            if tcode in {"ME21N", "ME22N", "ME23N", "ME2M", "ME2L"}:
                return await self._connector.get_purchase_order(doc_id)
            if tcode in {"MIGO", "MB51", "MB52", "MMBE"}:
                return await self._connector.get_stock(doc_id, context.plant)

        # SD
        if context.module == SAPModule.SD:
            if tcode in {"VA01", "VA02", "VA03", "VA05"}:
                return await self._connector.get_sales_order(doc_id)
            if tcode in {"VL01N", "VL02N", "VL03N", "VL10"}:
                return await self._connector.get_delivery(doc_id)
            if tcode in {"VF01", "VF02", "VF03", "VF04"}:
                return await self._connector.get_billing_document(doc_id)

        logger.info("No specific fetcher for tcode", tcode=tcode)
        return {}
