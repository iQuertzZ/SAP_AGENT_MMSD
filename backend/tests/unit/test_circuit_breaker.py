"""Unit tests for the circuit breaker in SAPODataClient."""
from __future__ import annotations

import time

import pytest

from backend.app.connectors.odata.client import CBState, CircuitBreaker


class TestCircuitBreaker:
    def _cb(self, threshold: int = 3, recovery: int = 60) -> CircuitBreaker:
        return CircuitBreaker(failure_threshold=threshold, recovery_timeout=recovery)

    def test_initial_state_closed(self):
        cb = self._cb()
        assert cb.state == CBState.CLOSED

    def test_allow_request_when_closed(self):
        cb = self._cb()
        assert cb.allow_request() is True

    def test_transitions_to_open_after_threshold(self):
        cb = self._cb(threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == CBState.OPEN

    def test_does_not_open_before_threshold(self):
        cb = self._cb(threshold=3)
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CBState.CLOSED

    def test_open_blocks_requests(self):
        cb = self._cb(threshold=1)
        cb.record_failure()
        assert cb.state == CBState.OPEN
        assert cb.allow_request() is False

    def test_transitions_to_half_open_after_recovery_timeout(self):
        # With recovery=3600, first check is OPEN; with recovery=0 it immediately
        # becomes HALF_OPEN on the next state access.
        cb = self._cb(threshold=1, recovery=3600)
        cb.record_failure()
        assert cb.state == CBState.OPEN
        # Simulate timeout by forcing _opened_at far in the past
        cb._opened_at = cb._opened_at - 3601
        assert cb.state == CBState.HALF_OPEN

    def test_half_open_allows_one_request(self):
        cb = self._cb(threshold=1, recovery=0)
        cb.record_failure()
        time.sleep(0.01)
        assert cb.allow_request() is True

    def test_half_open_success_closes(self):
        cb = self._cb(threshold=1, recovery=0)
        cb.record_failure()
        time.sleep(0.01)
        _ = cb.state  # trigger HALF_OPEN
        cb.record_success()
        assert cb.state == CBState.CLOSED

    def test_half_open_failure_reopens(self):
        cb = self._cb(threshold=1, recovery=3600)
        cb.record_failure()
        cb._opened_at = cb._opened_at - 3601  # fast-forward past timeout
        assert cb.state == CBState.HALF_OPEN
        cb.record_failure()
        # After failure in HALF_OPEN, back to OPEN (new opened_at is fresh)
        assert cb._state.value == "OPEN"

    def test_success_resets_failure_count(self):
        cb = self._cb(threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        cb.record_failure()
        # Only 1 failure after success — should still be CLOSED
        assert cb.state == CBState.CLOSED

    def test_allow_request_half_open(self):
        cb = self._cb(threshold=1, recovery=0)
        cb.record_failure()
        time.sleep(0.01)
        assert cb.allow_request() is True  # HALF_OPEN allows
