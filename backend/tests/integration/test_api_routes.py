"""Integration tests for all API routes using TestClient."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert "connector" in data


def test_analyze_miro_blocked(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/analyze",
        json={
            "tcode": "MIRO",
            "module": "MM",
            "document_id": "51000321",
            "status": "BLOCKED",
            "company_code": "1000",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["diagnosis"]["issue_type"] == "GRIR_MISMATCH"
    assert len(data["recommended_actions"]) > 0
    assert data["primary_action"]["tcode"] == "MR11"
    assert data["primary_action"]["confidence"] > 0.7
    assert "processing_ms" in data


def test_analyze_va03_credit_block(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/analyze",
        json={
            "tcode": "VA03",
            "module": "SD",
            "document_id": "1000081234",
            "status": "BLOCKED",
            "sales_org": "1000",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["diagnosis"]["issue_type"] == "CREDIT_BLOCK"
    assert data["primary_action"]["tcode"] == "VKM1"


def test_analyze_missing_gr(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/analyze",
        json={
            "tcode": "MIRO",
            "module": "MM",
            "document_id": "51000322",
            "status": "BLOCKED",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["diagnosis"]["issue_type"] == "MISSING_GR"
    assert data["primary_action"]["tcode"] == "MIGO"


def test_simulate_endpoint(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/simulate",
        json={
            "tcode": "MIRO",
            "module": "MM",
            "document_id": "51000321",
            "action_tcode": "MR11",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["action_tcode"] == "MR11"
    assert 0.0 <= data["simulation"]["risk_score"] <= 1.0
    assert "financial" in data["simulation"]


def test_approval_submit_and_approve_flow(client: TestClient) -> None:
    # Submit for approval
    resp = client.post(
        "/api/v1/approval/submit",
        json={
            "tcode": "MIRO",
            "module": "MM",
            "document_id": "51000321",
            "status": "BLOCKED",
            "user": "consultant_01",
        },
    )
    assert resp.status_code == 200
    req_id = resp.json()["request_id"]
    assert resp.json()["status"] == "awaiting_approval"

    # Approve it
    resp2 = client.post(
        f"/api/v1/approval/{req_id}/approve",
        json={"request_id": req_id, "approver": "controller_01"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "approved"

    # Verify state
    resp3 = client.get(f"/api/v1/approval/{req_id}")
    assert resp3.status_code == 200
    assert resp3.json()["status"] == "approved"


def test_approval_reject_flow(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/approval/submit",
        json={
            "tcode": "VA03",
            "module": "SD",
            "document_id": "1000081234",
            "status": "BLOCKED",
        },
    )
    req_id = resp.json()["request_id"]

    resp2 = client.post(
        f"/api/v1/approval/{req_id}/reject",
        json={"request_id": req_id, "approver": "manager", "reason": "Not authorized"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "rejected"


def test_approval_not_found(client: TestClient) -> None:
    resp = client.get("/api/v1/approval/nonexistent-id")
    assert resp.status_code == 404


def test_execute_disabled_by_default(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/approval/submit",
        json={
            "tcode": "MIRO",
            "module": "MM",
            "document_id": "51000321",
            "status": "BLOCKED",
        },
    )
    req_id = resp.json()["request_id"]
    client.post(f"/api/v1/approval/{req_id}/approve", json={"request_id": req_id, "approver": "mgr"})

    resp2 = client.post("/api/v1/execute", json={"request_id": req_id, "executor": "consultant"})
    assert resp2.status_code == 403  # EXECUTION_DISABLED


def test_list_approvals(client: TestClient) -> None:
    resp = client.get("/api/v1/approval/")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "items" in data
