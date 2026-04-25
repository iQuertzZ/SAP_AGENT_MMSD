"""In-memory request metrics for the SAP OData connector."""
from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any


class SAPMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self._total_duration_ms = 0.0
        self.requests_by_service: dict[str, int] = {}
        self.errors_by_type: dict[str, int] = {}
        self.last_error: str | None = None
        self.last_success_at: datetime | None = None

    def record_request(
        self,
        service: str,
        duration_ms: float,
        *,
        success: bool,
        error_type: str | None = None,
    ) -> None:
        with self._lock:
            self.total_requests += 1
            self._total_duration_ms += duration_ms
            self.requests_by_service[service] = self.requests_by_service.get(service, 0) + 1
            if success:
                self.successful_requests += 1
                self.last_success_at = datetime.now(timezone.utc)
            else:
                self.failed_requests += 1
                if error_type:
                    self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
                    self.last_error = error_type

    def get_summary(self) -> dict[str, Any]:
        with self._lock:
            total = self.total_requests
            avg_ms = round(self._total_duration_ms / total, 1) if total else 0.0
            success_rate = round(self.successful_requests / total, 3) if total else 1.0
            return {
                "total_requests": total,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate": success_rate,
                "avg_duration_ms": avg_ms,
                "requests_by_service": dict(self.requests_by_service),
                "errors_by_type": dict(self.errors_by_type),
                "last_error": self.last_error,
                "last_success_at": (
                    self.last_success_at.isoformat() if self.last_success_at else None
                ),
            }
