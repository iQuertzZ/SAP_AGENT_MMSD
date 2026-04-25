"""Basic Auth handler for SAP OData."""
from __future__ import annotations

import httpx


class BasicAuthHandler:
    def __init__(self, username: str, password: str) -> None:
        self._auth = httpx.BasicAuth(username, password)

    def apply(self, request: httpx.Request) -> httpx.Request:
        return self._auth.auth_flow(request).__next__()  # type: ignore[return-value]

    @property
    def httpx_auth(self) -> httpx.BasicAuth:
        return self._auth
