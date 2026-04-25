"""In-memory TTL cache for OData reads."""
from __future__ import annotations

import time
from threading import Lock
from typing import Any


class ODataCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            value, expires_at = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return value

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        with self._lock:
            self._store[key] = (value, time.monotonic() + ttl_seconds)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            total = self._hits + self._misses
            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / total, 3) if total else 0.0,
                "size": len(self._store),
            }
