"""
End-to-end scenario tests.
Each test represents a real-world SAP consulting workflow.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestMMScenario:
    """MM consultant workflow: blocked invoice → diagnosis → recommend → approve."""

    def test_blocked_invoice_price_variance_full_workflow(self, client: TestClient) -> None:
        # Step 1: Analyze blocked invoice
        analysis = client.post("/api/v1/analyze", json={
            "tcode": "MIRO",
            "module": "MM",
            "document_id": "51000321",
            "status": "BLOCKED",
            "company_code": "1000",
            "user": "mm_consultant",
        }).json()

        assert analysis["diagnosis"]["issue_type"] == "GRIR_MISMATCH"
        assert analysis["diagnosis"]["severity"] == "high"
        assert analysis["primary_action"]["tcode"] == "MR11"
        primary = analysis["primary_action"]
        assert "rollback_plan" in primary

        # Step 2: Simulate impact
        sim = client.post("/api/v1/simulate", json={
            "tcode": "MIRO",
            "module": "MM",
            "document_id": "51000321",
            "action_tcode": "MR11",
        }).json()

        assert sim["simulation"]["financial"]["posting_required"] is True
        assert sim["simulation"]["financial"]["amount"] == 3500.0
        assert sim["simulation"]["risk_score"] < 0.9

        # Step 3: Submit for approval
        submit = client.post("/api/v1/approval/submit", json={
            "tcode": "MIRO",
            "module": "MM",
            "document_id": "51000321",
            "status": "BLOCKED",
            "user": "mm_consultant",
        }).json()

        assert submit["status"] == "awaiting_approval"
        req_id = submit["request_id"]

        # Step 4: Approve
        approval = client.post(f"/api/v1/approval/{req_id}/approve", json={
            "request_id": req_id,
            "approver": "finance_controller",
        }).json()
        assert approval["status"] == "approved"

        # Step 5: Verify final state
        final = client.get(f"/api/v1/approval/{req_id}").json()
        assert final["status"] == "approved"
        assert final["approver"] == "finance_controller"
        assert final["recommended_action"]["tcode"] == "MR11"

    def test_missing_gr_scenario(self, client: TestClient) -> None:
        analysis = client.post("/api/v1/analyze", json={
            "tcode": "MIRO",
            "module": "MM",
            "document_id": "51000322",
            "status": "BLOCKED",
        }).json()

        assert analysis["diagnosis"]["issue_type"] == "MISSING_GR"
        assert analysis["primary_action"]["tcode"] == "MIGO"
        assert len(analysis["diagnosis"]["supporting_evidence"]) > 0
        # Evidence should mention no goods receipt
        evidence_text = " ".join(analysis["diagnosis"]["supporting_evidence"])
        assert "goods receipt" in evidence_text.lower() or "GR" in evidence_text


class TestSDScenario:
    """SD consultant workflow: credit block → release order."""

    def test_credit_blocked_order_full_workflow(self, client: TestClient) -> None:
        # Step 1: Analyze
        analysis = client.post("/api/v1/analyze", json={
            "tcode": "VA03",
            "module": "SD",
            "document_id": "1000081234",
            "status": "BLOCKED",
            "sales_org": "1000",
            "user": "sd_consultant",
        }).json()

        assert analysis["diagnosis"]["issue_type"] == "CREDIT_BLOCK"
        assert analysis["primary_action"]["tcode"] == "VKM1"

        # Evidence must mention credit exposure vs limit
        evidence_text = " ".join(analysis["diagnosis"]["supporting_evidence"])
        assert "275000" in evidence_text or "credit" in evidence_text.lower()

        # Step 2: Submit for approval
        submit = client.post("/api/v1/approval/submit", json={
            "tcode": "VA03",
            "module": "SD",
            "document_id": "1000081234",
            "status": "BLOCKED",
            "user": "sd_consultant",
        }).json()
        req_id = submit["request_id"]

        # Step 3: Reject (credit issue not resolved)
        reject = client.post(f"/api/v1/approval/{req_id}/reject", json={
            "request_id": req_id,
            "approver": "credit_manager",
            "reason": "Customer has overdue invoices — credit not yet cleared",
        }).json()
        assert reject["status"] == "rejected"

        # Step 4: Cannot re-approve a rejected request
        resp = client.post(f"/api/v1/approval/{req_id}/approve", json={
            "request_id": req_id,
            "approver": "credit_manager",
        })
        assert resp.status_code == 409

    def test_pricing_error_scenario(self, client: TestClient) -> None:
        analysis = client.post("/api/v1/analyze", json={
            "tcode": "VA03",
            "module": "SD",
            "document_id": "1000081235",
            "status": "OPEN",
        }).json()

        assert analysis["diagnosis"]["issue_type"] == "PRICING_ERROR"
        assert analysis["primary_action"]["tcode"] == "VA02"


class TestSafetyScenario:
    """Verify all safety contracts are enforced."""

    def test_execution_requires_approval(self, client: TestClient) -> None:
        resp = client.post("/api/v1/execute", json={
            "request_id": "nonexistent",
            "executor": "hacker",
        })
        assert resp.status_code in (403, 404)

    def test_all_actions_have_rollback_plan(self, client: TestClient) -> None:
        for payload in [
            {"tcode": "MIRO", "module": "MM", "document_id": "51000321", "status": "BLOCKED"},
            {"tcode": "VA03", "module": "SD", "document_id": "1000081234", "status": "BLOCKED"},
        ]:
            analysis = client.post("/api/v1/analyze", json=payload).json()
            for action in analysis["recommended_actions"]:
                assert action["rollback_plan"], f"Action {action['tcode']} missing rollback plan"

    def test_confidence_score_present_on_all_actions(self, client: TestClient) -> None:
        analysis = client.post("/api/v1/analyze", json={
            "tcode": "MIRO",
            "module": "MM",
            "document_id": "51000321",
            "status": "BLOCKED",
        }).json()
        for action in analysis["recommended_actions"]:
            assert 0.0 <= action["confidence"] <= 1.0
