"""Integration tests verifying route-level RBAC enforcement.

Uses ``auth_client`` (real JWT auth) to test access control.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _ensure_user(client: TestClient, admin_token: str, email: str, role: str) -> str:
    """Create user if not already present; return access token."""
    create = client.post(
        "/api/v1/auth/users",
        json={"email": email, "password": "testpass1", "full_name": email, "role": role},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # 201 = created, 409 = already exists — both are fine
    assert create.status_code in (201, 409), create.text
    return _login(client, email, "testpass1")


@pytest.fixture()
def admin_token(auth_client: TestClient) -> str:
    return _login(auth_client, "admin@sap-copilot.local", "changeme")


@pytest.fixture()
def consultant_token(auth_client: TestClient, admin_token: str) -> str:
    return _ensure_user(auth_client, admin_token, "prot-consultant@example.com", "consultant")


@pytest.fixture()
def manager_token(auth_client: TestClient, admin_token: str) -> str:
    return _ensure_user(auth_client, admin_token, "prot-manager@example.com", "manager")


# ── No token → 401 ───────────────────────────────────────────────────────────


def test_analyze_without_token_is_401(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/api/v1/analyze",
        json={"tcode": "MIRO", "module": "MM", "document_id": "51000321", "status": "BLOCKED"},
    )
    assert resp.status_code == 401


# ── CONSULTANT can analyze ────────────────────────────────────────────────────


def test_analyze_with_consultant_token(
    auth_client: TestClient, consultant_token: str
) -> None:
    resp = auth_client.post(
        "/api/v1/analyze",
        json={"tcode": "MIRO", "module": "MM", "document_id": "51000321", "status": "BLOCKED"},
        headers={"Authorization": f"Bearer {consultant_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["diagnosis"]["issue_type"] == "GRIR_MISMATCH"


# ── CONSULTANT cannot approve ─────────────────────────────────────────────────


def test_approve_with_consultant_token_is_403(
    auth_client: TestClient, consultant_token: str, manager_token: str
) -> None:
    # Submit an approval first (as manager)
    submit = auth_client.post(
        "/api/v1/approval/submit",
        json={"tcode": "MIRO", "module": "MM", "document_id": "51000321", "status": "BLOCKED"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert submit.status_code == 200
    req_id = submit.json()["request_id"]

    # CONSULTANT tries to approve → 403
    resp = auth_client.post(
        f"/api/v1/approval/{req_id}/approve",
        json={"request_id": req_id, "approver": "mgr"},
        headers={"Authorization": f"Bearer {consultant_token}"},
    )
    assert resp.status_code == 403


# ── MANAGER can approve ───────────────────────────────────────────────────────


def test_approve_with_manager_token(
    auth_client: TestClient, manager_token: str
) -> None:
    submit = auth_client.post(
        "/api/v1/approval/submit",
        json={"tcode": "MIRO", "module": "MM", "document_id": "51000321", "status": "BLOCKED"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    req_id = submit.json()["request_id"]

    resp = auth_client.post(
        f"/api/v1/approval/{req_id}/approve",
        json={"request_id": req_id, "approver": "mgr"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


# ── MANAGER cannot execute ────────────────────────────────────────────────────


def test_execute_with_manager_token_is_403(
    auth_client: TestClient, manager_token: str
) -> None:
    resp = auth_client.post(
        "/api/v1/execute",
        json={"request_id": "any-id", "executor": "mgr"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    # 403 from RBAC (not allowed) or 403 from EXECUTION_DISABLED — both are correct
    assert resp.status_code == 403


# ── ADMIN can attempt execute (blocked by EXECUTION_ENABLED=false) ────────────


def test_execute_with_admin_token_blocked_by_disabled_flag(
    auth_client: TestClient, admin_token: str, manager_token: str
) -> None:
    submit = auth_client.post(
        "/api/v1/approval/submit",
        json={"tcode": "MIRO", "module": "MM", "document_id": "51000321", "status": "BLOCKED"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    req_id = submit.json()["request_id"]
    auth_client.post(
        f"/api/v1/approval/{req_id}/approve",
        json={"request_id": req_id, "approver": "mgr"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )

    resp = auth_client.post(
        "/api/v1/execute",
        json={"request_id": req_id, "executor": "admin"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # ADMIN passes RBAC; execution blocked by EXECUTION_ENABLED=false → 403
    assert resp.status_code == 403


# ── Health is public ──────────────────────────────────────────────────────────


def test_health_is_public(auth_client: TestClient) -> None:
    resp = auth_client.get("/api/v1/health")
    assert resp.status_code == 200
