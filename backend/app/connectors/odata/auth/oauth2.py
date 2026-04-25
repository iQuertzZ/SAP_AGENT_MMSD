"""OAuth2 Client Credentials handler for SAP S/4HANA Cloud."""
from __future__ import annotations

import time
from typing import Any

import httpx

from backend.app.connectors.odata.exceptions import SAPAuthError


class OAuth2Handler:
    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: str = "",
    ) -> None:
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._token: str | None = None
        self._expires_at: float = 0.0

    def is_expired(self) -> bool:
        return time.monotonic() >= self._expires_at - 30

    async def fetch_token(self, client: httpx.AsyncClient) -> str:
        data: dict[str, Any] = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }
        if self._scope:
            data["scope"] = self._scope
        try:
            resp = await client.post(self._token_url, data=data)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise SAPAuthError(f"OAuth2 token fetch failed: {exc.response.status_code}") from exc
        payload: dict[str, Any] = resp.json()
        token: str = payload["access_token"]
        expires_in: float = float(payload.get("expires_in", 3600))
        self._token = token
        self._expires_at = time.monotonic() + expires_in
        return token

    async def get_token(self, client: httpx.AsyncClient) -> str:
        if self._token is None or self.is_expired():
            return await self.fetch_token(client)
        return self._token

    def auth_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}
