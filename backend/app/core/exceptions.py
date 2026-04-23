from __future__ import annotations


class CopilotBaseError(Exception):
    """Base exception for all copilot errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class SAPConnectorError(CopilotBaseError):
    """SAP backend unreachable or returned an unexpected response."""


class DocumentNotFoundError(CopilotBaseError):
    """Requested SAP document does not exist."""

    def __init__(self, doc_id: str) -> None:
        super().__init__(f"Document {doc_id!r} not found", code="DOCUMENT_NOT_FOUND")


class DiagnosisError(CopilotBaseError):
    """Diagnostic engine failed."""


class ApprovalNotFoundError(CopilotBaseError):
    def __init__(self, request_id: str) -> None:
        super().__init__(
            f"Approval request {request_id!r} not found", code="APPROVAL_NOT_FOUND"
        )


class ApprovalStateError(CopilotBaseError):
    """Invalid state transition for an approval request."""


class ExecutionDisabledError(CopilotBaseError):
    def __init__(self) -> None:
        super().__init__(
            "Execution layer is disabled. Set EXECUTION_ENABLED=true to enable.",
            code="EXECUTION_DISABLED",
        )


class ExecutionError(CopilotBaseError):
    """SAP execution failed."""


class AIServiceError(CopilotBaseError):
    """Claude API call failed."""
