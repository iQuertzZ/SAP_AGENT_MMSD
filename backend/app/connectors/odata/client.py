"""SAP OData HTTP client: session, auth, CSRF, retry, circuit breaker, version detection."""
from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import Any, Literal

import httpx
import structlog

from backend.app.connectors.odata.auth.basic import BasicAuthHandler
from backend.app.connectors.odata.auth.oauth2 import OAuth2Handler
from backend.app.connectors.odata.exceptions import (
    SAPAuthError,
    SAPConnectionError,
    SAPDocumentNotFoundError,
    SAPServiceError,
)
from backend.app.connectors.odata.metrics import SAPMetrics
from backend.app.core.config import settings

logger = structlog.get_logger(__name__)


class CBState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    def __init__(self, failure_threshold: int, recovery_timeout: int) -> None:
        self._threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._state = CBState.CLOSED
        self._failures = 0
        self._opened_at: float = 0.0

    @property
    def state(self) -> CBState:
        if self._state == CBState.OPEN:
            if time.monotonic() - self._opened_at >= self._recovery_timeout:
                self._state = CBState.HALF_OPEN
        return self._state

    def record_success(self) -> None:
        self._state = CBState.CLOSED
        self._failures = 0

    def record_failure(self) -> None:
        self._failures += 1
        if self._state == CBState.HALF_OPEN or self._failures >= self._threshold:
            self._state = CBState.OPEN
            self._opened_at = time.monotonic()

    def allow_request(self) -> bool:
        s = self.state
        return s in (CBState.CLOSED, CBState.HALF_OPEN)


class SAPODataClient:
    """
    Async HTTP client for SAP OData services.

    Handles: Basic/OAuth2 auth, CSRF tokens, retry with backoff,
    circuit breaker, version detection, structured logging.
    """

    CATALOG_PATH = "/sap/opu/odata/IWFND/CATALOGSERVICE/ServiceCollection"

    def __init__(self) -> None:
        self._base_url = settings.sap_odata_base_url.rstrip("/")
        self._verify_ssl = settings.sap_verify_ssl
        self._timeout = httpx.Timeout(
            connect=settings.sap_timeout_connect,
            read=settings.sap_timeout_read,
            write=settings.sap_timeout_read,
            pool=settings.sap_timeout_connect,
        )
        self._max_retries = settings.sap_max_retries
        self._backoff = settings.sap_retry_backoff

        # Auth
        self._oauth: OAuth2Handler | None = None
        self._basic: BasicAuthHandler | None = None
        if settings.sap_use_oauth:
            self._oauth = OAuth2Handler(
                settings.sap_oauth_url,
                settings.sap_oauth_client_id,
                settings.sap_oauth_client_secret,
                settings.sap_oauth_scope,
            )
        else:
            self._basic = BasicAuthHandler(settings.sap_odata_user, settings.sap_odata_password)

        self._csrf_token: str | None = None
        self._sap_version: Literal["ecc", "s4hana"] | None = None

        self._cb = CircuitBreaker(
            settings.sap_cb_failure_threshold,
            settings.sap_cb_recovery_timeout,
        )
        self.metrics = SAPMetrics()
        self._client: httpx.AsyncClient | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def _build_client(self) -> httpx.AsyncClient:
        base_headers: dict[str, str] = {
            "Accept": "application/json",
            "DataServiceVersion": "2.0",
            "sap-client": settings.sap_client,
            "Accept-Language": settings.sap_language,
        }
        if settings.sap_sandbox and settings.sap_sandbox_api_key:
            base_headers["APIKey"] = settings.sap_sandbox_api_key

        kwargs: dict[str, Any] = {
            "headers": base_headers,
            "verify": self._verify_ssl,
            "follow_redirects": True,
        }
        if not settings.sap_sandbox:
            kwargs["timeout"] = self._timeout
        else:
            kwargs["timeout"] = httpx.Timeout(30.0)

        if self._basic:
            kwargs["auth"] = self._basic.httpx_auth
        return httpx.AsyncClient(**kwargs)

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ── SAP version detection ──────────────────────────────────────────────────

    async def detect_version(self) -> Literal["ecc", "s4hana"]:
        if settings.sap_version != "auto":
            self._sap_version = settings.sap_version  # type: ignore[assignment]
            return self._sap_version  # type: ignore[return-value]
        if self._sap_version:
            return self._sap_version
        try:
            client = self._get_client()
            resp = await client.get(
                f"{self._base_url}{self.CATALOG_PATH}",
                params={"$top": "1", "$format": "json"},
                timeout=httpx.Timeout(10.0),
            )
            text = resp.text
            if "S4HANA" in text or "s4hana" in text.lower() or "S/4" in text:
                self._sap_version = "s4hana"
            else:
                self._sap_version = "ecc"
        except Exception:
            logger.warning("SAP version detection failed — defaulting to ecc")
            self._sap_version = "ecc"
        return self._sap_version

    @property
    def sap_version(self) -> Literal["ecc", "s4hana"]:
        return self._sap_version or "ecc"

    # ── CSRF ───────────────────────────────────────────────────────────────────

    async def _fetch_csrf_token(self) -> str:
        client = self._get_client()
        resp = await client.get(
            f"{self._base_url}/sap/opu/odata/",
            headers={"x-csrf-token": "Fetch"},
        )
        token = resp.headers.get("x-csrf-token", "")
        if not token:
            logger.warning("CSRF token not returned by SAP")
        self._csrf_token = token
        return token

    async def _ensure_csrf(self) -> str:
        if not self._csrf_token:
            return await self._fetch_csrf_token()
        return self._csrf_token

    # ── Auth headers ───────────────────────────────────────────────────────────

    async def _auth_headers(self) -> dict[str, str]:
        if self._oauth:
            token = await self._oauth.get_token(self._get_client())
            return {"Authorization": f"Bearer {token}"}
        return {}

    # ── Core request ───────────────────────────────────────────────────────────

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        service: str = "unknown",
    ) -> dict[str, Any]:
        return await self._request("GET", path, params=params, service=service)

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        service: str = "unknown",
        _csrf_retried: bool = False,
    ) -> dict[str, Any]:
        if not self._cb.allow_request() and not settings.sap_sandbox:
            raise SAPConnectionError(
                f"Circuit breaker OPEN — SAP requests blocked (state: {self._cb.state})"
            )

        url = f"{self._base_url}{path}"
        extra_headers = await self._auth_headers()

        if method in ("POST", "PUT", "PATCH", "DELETE"):
            csrf = await self._ensure_csrf()
            extra_headers["x-csrf-token"] = csrf

        last_exc: Exception = RuntimeError("unreachable")
        for attempt in range(self._max_retries + 1):
            t0 = time.monotonic()
            try:
                client = self._get_client()
                resp = await client.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    headers=extra_headers,
                )
                duration_ms = (time.monotonic() - t0) * 1000
                logger.info(
                    "sap_request",
                    method=method,
                    url=url,
                    status=resp.status_code,
                    duration_ms=round(duration_ms, 1),
                    attempt=attempt,
                )

                # CSRF expired — refetch once
                if resp.status_code == 403 and not _csrf_retried:
                    self._csrf_token = None
                    return await self._request(
                        method, path, params=params, json=json,
                        service=service, _csrf_retried=True,
                    )

                error = self._parse_error(resp)
                if error:
                    self._cb.record_failure()
                    self.metrics.record_request(service, duration_ms, success=False, error_type=type(error).__name__)
                    raise error

                resp.raise_for_status()
                self._cb.record_success()
                self.metrics.record_request(service, duration_ms, success=True)
                data: dict[str, Any] = resp.json()
                return data.get("d", data)

            except (SAPAuthError, SAPDocumentNotFoundError, SAPServiceError):
                raise
            except SAPConnectionError:
                raise
            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                duration_ms = (time.monotonic() - t0) * 1000
                last_exc = exc
                self._cb.record_failure()
                self.metrics.record_request(service, duration_ms, success=False, error_type="timeout")
                logger.warning("sap_request_retry", attempt=attempt, error=str(exc))
                if attempt < self._max_retries:
                    await asyncio.sleep(self._backoff * (2 ** attempt))
            except httpx.HTTPStatusError as exc:
                duration_ms = (time.monotonic() - t0) * 1000
                if 500 <= exc.response.status_code < 600:
                    last_exc = exc
                    self._cb.record_failure()
                    self.metrics.record_request(service, duration_ms, success=False, error_type="server_error")
                    logger.warning("sap_5xx_retry", status=exc.response.status_code, attempt=attempt)
                    if attempt < self._max_retries:
                        await asyncio.sleep(self._backoff * (2 ** attempt))
                else:
                    # Non-5xx non-parsed error
                    self._cb.record_failure()
                    self.metrics.record_request(service, duration_ms, success=False, error_type="http_error")
                    raise SAPConnectionError(f"SAP HTTP {exc.response.status_code}") from exc

        self.metrics.record_request(service, 0, success=False, error_type="max_retries")
        raise SAPConnectionError(f"SAP unreachable after {self._max_retries} retries: {last_exc}") from last_exc

    # ── Error parsing ──────────────────────────────────────────────────────────

    def _parse_error(self, resp: httpx.Response) -> Exception | None:
        status = resp.status_code
        if status == 401:
            return SAPAuthError("SAP authentication failed (401)")
        if status == 404:
            return SAPDocumentNotFoundError(resp.url.path.split("/")[-1])
        if status == 403:
            # Could be CSRF (handled by caller) or auth
            body = ""
            try:
                body = resp.text
            except Exception:
                pass
            if "CSRF" not in body and "csrf" not in body.lower():
                return SAPAuthError("SAP authorization failed (403)")
            return None  # CSRF — let caller handle
        if 400 <= status < 500:
            try:
                payload = resp.json()
                err = payload.get("error", {})
                code = err.get("code", str(status))
                msg = ""
                inner = err.get("message", {})
                if isinstance(inner, dict):
                    msg = inner.get("value", "")
                elif isinstance(inner, str):
                    msg = inner
                if code or msg:
                    return SAPServiceError(code, msg)
            except Exception:
                pass
        return None

    # ── Health check ───────────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        try:
            client = self._get_client()
            resp = await client.get(
                f"{self._base_url}{self.CATALOG_PATH}",
                params={"$top": "1", "$format": "json"},
                timeout=httpx.Timeout(5.0),
            )
            return resp.status_code < 400
        except Exception:
            return False

    @property
    def circuit_breaker_state(self) -> str:
        return self._cb.state.value
