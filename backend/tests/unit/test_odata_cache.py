"""Unit tests for ODataCache."""
from __future__ import annotations

import time

import pytest

from backend.app.connectors.odata.cache import ODataCache


class TestODataCache:
    def test_set_and_get(self):
        cache = ODataCache()
        cache.set("k1", {"v": 1}, ttl_seconds=60)
        assert cache.get("k1") == {"v": 1}

    def test_miss_returns_none(self):
        cache = ODataCache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self):
        cache = ODataCache()
        cache.set("k1", {"v": 1}, ttl_seconds=0)
        # TTL=0 — already expired on next tick
        time.sleep(0.01)
        assert cache.get("k1") is None

    def test_invalidate(self):
        cache = ODataCache()
        cache.set("k1", {"v": 1}, ttl_seconds=60)
        cache.invalidate("k1")
        assert cache.get("k1") is None

    def test_invalidate_missing_key_no_error(self):
        cache = ODataCache()
        cache.invalidate("not-there")  # should not raise

    def test_clear(self):
        cache = ODataCache()
        cache.set("k1", {"v": 1}, ttl_seconds=60)
        cache.set("k2", {"v": 2}, ttl_seconds=60)
        cache.clear()
        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_stats_hits_misses(self):
        cache = ODataCache()
        cache.set("k1", {"v": 1}, ttl_seconds=60)
        cache.get("k1")  # hit
        cache.get("k1")  # hit
        cache.get("k2")  # miss
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(2 / 3, abs=0.01)

    def test_stats_initial_hit_rate_zero(self):
        cache = ODataCache()
        stats = cache.get_stats()
        assert stats["hit_rate"] == 0.0

    def test_expired_counts_as_miss(self):
        cache = ODataCache()
        cache.set("k1", {"v": 1}, ttl_seconds=0)
        time.sleep(0.01)
        cache.get("k1")
        stats = cache.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0

    def test_stats_size(self):
        cache = ODataCache()
        cache.set("k1", {"v": 1}, ttl_seconds=60)
        cache.set("k2", {"v": 2}, ttl_seconds=60)
        assert cache.get_stats()["size"] == 2
