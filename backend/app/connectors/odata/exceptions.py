"""SAP OData connector exceptions."""
from __future__ import annotations


class SAPConnectionError(Exception):
    """SAP Gateway unreachable (network / 5xx / timeout)."""


class SAPAuthError(Exception):
    """SAP authentication failed (401 / 403 non-CSRF)."""


class SAPDocumentNotFoundError(Exception):
    """SAP document not found (404)."""

    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(f"SAP document not found: {document_id}")


class SAPServiceError(Exception):
    """Business error returned in OData error body."""

    def __init__(self, sap_error_code: str, sap_error_message: str) -> None:
        self.sap_error_code = sap_error_code
        self.sap_error_message = sap_error_message
        super().__init__(f"SAP error [{sap_error_code}]: {sap_error_message}")
