"""Integration tests for /api/v1/auth/* routes.

Uses ``auth_client`` (no auth override) so real JWT logic runs.
The admin user is seeded by the app lifespan (admin@sap-copilot.local / changeme).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ── Login ─────────────────────────────────────────────────────────────────────


def test_login_correct_credentials(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/api/v1/auth/login",
        data={"username": "admin@sap-copilot.local", "password": "changeme"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/api/v1/auth/login",
        data={"username": "admin@sap-copilot.local", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_login_unknown_user(auth_client: TestClient) -> None:
    resp = auth_client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@nowhere.com", "password": "anything"},
    )
    assert resp.status_code == 401


# ── /me ───────────────────────────────────────────────────────────────────────


def _get_admin_token(client: TestClient) -> str:
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@sap-copilot.local", "password": "changeme"},
    )
    return resp.json()["access_token"]


def test_me_with_valid_token(auth_client: TestClient) -> None:
    token = _get_admin_token(auth_client)
    resp = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "admin@sap-copilot.local"
    assert data["role"] == "admin"


def test_me_without_token(auth_client: TestClient) -> None:
    resp = auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_expired_token(auth_client: TestClient) -> None:
    from jose import jwt
    from backend.app.core.config import settings
    import time

    expired_payload = {
        "sub": "some-id",
        "email": "x@x.com",
        "role": "admin",
        "exp": int(time.time()) - 3600,
        "type": "access",
    }
    expired_token = jwt.encode(
        expired_payload, settings.secret_key, algorithm=settings.algorithm
    )
    resp = auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401


# ── Token refresh ─────────────────────────────────────────────────────────────


def test_refresh_token(auth_client: TestClient) -> None:
    login = auth_client.post(
        "/api/v1/auth/login",
        data={"username": "admin@sap-copilot.local", "password": "changeme"},
    )
    refresh_token = login.json()["refresh_token"]

    resp = auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


# ── User management (ADMIN only) ──────────────────────────────────────────────


def test_create_user_as_admin(auth_client: TestClient) -> None:
    token = _get_admin_token(auth_client)
    resp = auth_client.post(
        "/api/v1/auth/users",
        json={
            "email": "consultant@example.com",
            "password": "secure1234",
            "full_name": "Test Consultant",
            "role": "consultant",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "consultant@example.com"
    assert data["role"] == "consultant"


def test_create_user_without_admin_role(auth_client: TestClient) -> None:
    """A CONSULTANT token cannot create users."""
    # First, create a consultant
    admin_token = _get_admin_token(auth_client)
    auth_client.post(
        "/api/v1/auth/users",
        json={
            "email": "consultant2@example.com",
            "password": "secure1234",
            "full_name": "Consultant 2",
            "role": "consultant",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # Login as consultant
    consultant_resp = auth_client.post(
        "/api/v1/auth/login",
        data={"username": "consultant2@example.com", "password": "secure1234"},
    )
    consultant_token = consultant_resp.json()["access_token"]

    # Try to create a user — should 403
    resp = auth_client.post(
        "/api/v1/auth/users",
        json={
            "email": "hacker@example.com",
            "password": "secure1234",
            "full_name": "Hacker",
            "role": "admin",
        },
        headers={"Authorization": f"Bearer {consultant_token}"},
    )
    assert resp.status_code == 403
