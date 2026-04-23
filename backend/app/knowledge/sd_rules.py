"""SD diagnostic and action rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.models.diagnosis import IssueSeverity, IssueType


@dataclass
class SDRule:
    rule_id: str
    tcode: str
    status_match: list[str]
    condition_key: str | None
    issue_type: IssueType
    root_cause: str
    severity: IssueSeverity
    base_confidence: float
    action_tcode: str
    action_description: str
    action_risk: str
    rollback_plan: str
    prerequisites: list[str] = field(default_factory=list)
    authorization_objects: list[str] = field(default_factory=list)


SD_RULES: list[SDRule] = [
    # ── Sales Orders – Credit Block ─────────────────────────────────────────
    SDRule(
        rule_id="SD-001",
        tcode="VA03",
        status_match=["BLOCKED"],
        condition_key="credit_block",
        issue_type=IssueType.CREDIT_BLOCK,
        root_cause=(
            "Sales order is blocked due to a credit management check failure. "
            "The customer has exceeded their credit limit or has overdue open items."
        ),
        severity=IssueSeverity.HIGH,
        base_confidence=0.94,
        action_tcode="VKM1",
        action_description="Release the credit-blocked sales order via VKM1 after credit review",
        action_risk="medium",
        rollback_plan="Re-block the sales order in VKM1 or VA02 if the credit situation has not improved.",
        prerequisites=["Credit controller must review open items in FBL5N", "Customer credit limit review in FD32"],
        authorization_objects=["V_VBAK_VKO", "F_KNKK_BED"],
    ),
    # ── Sales Orders – Pricing ──────────────────────────────────────────────
    SDRule(
        rule_id="SD-002",
        tcode="VA03",
        status_match=["OPEN", "BLOCKED", "ERROR"],
        condition_key="pricing_error",
        issue_type=IssueType.PRICING_ERROR,
        root_cause=(
            "Sales order pricing is incomplete or contains errors. "
            "A mandatory condition type is missing or a condition record is expired/invalid."
        ),
        severity=IssueSeverity.HIGH,
        base_confidence=0.89,
        action_tcode="VA02",
        action_description="Open order in VA02, go to condition screen, and run 'Reprice' (G) to refresh pricing",
        action_risk="medium",
        rollback_plan="Restore original pricing by selecting 'Copy pricing' from the last valid date.",
        prerequisites=["Valid condition records must exist in VK13", "Pricing date must be correct"],
        authorization_objects=["V_VBAK_VKO"],
    ),
    # ── Sales Orders – Incompletion ─────────────────────────────────────────
    SDRule(
        rule_id="SD-003",
        tcode="VA03",
        status_match=["OPEN", "BLOCKED"],
        condition_key="incompletion_log",
        issue_type=IssueType.INCOMPLETION_LOG,
        root_cause=(
            "The sales order has an incompletion log — mandatory fields are missing "
            "(e.g. shipping conditions, incoterms, payment terms)."
        ),
        severity=IssueSeverity.MEDIUM,
        base_confidence=0.91,
        action_tcode="VA02",
        action_description="Complete missing fields in VA02 (use Edit > Incompletion Log to view list)",
        action_risk="low",
        rollback_plan="No posting involved — changes can be reversed by restoring previous field values.",
        prerequisites=["Check incompletion log via VA02 > Edit > Incompletion Log"],
        authorization_objects=["V_VBAK_VKO"],
    ),
    # ── Delivery ────────────────────────────────────────────────────────────
    SDRule(
        rule_id="SD-004",
        tcode="VL03N",
        status_match=["BLOCKED"],
        condition_key="delivery_block",
        issue_type=IssueType.DELIVERY_BLOCK,
        root_cause=(
            "Outbound delivery is blocked. Possible reasons: goods issue not posted, "
            "picking not confirmed, warehouse transfer not complete, or manual delivery block."
        ),
        severity=IssueSeverity.HIGH,
        base_confidence=0.88,
        action_tcode="VL02N",
        action_description="Remove delivery block in VL02N (header > delivery block field) and complete goods issue",
        action_risk="medium",
        rollback_plan="Cancel goods issue (VL09) if posted incorrectly and reinstate the delivery block.",
        prerequisites=["Stock must be available at storage location", "Picking must be completed"],
        authorization_objects=["V_LIKP_VST"],
    ),
    # ── Delivery – Material Availability ────────────────────────────────────
    SDRule(
        rule_id="SD-005",
        tcode="VA03",
        status_match=["OPEN", "BLOCKED"],
        condition_key="material_not_available",
        issue_type=IssueType.MATERIAL_NOT_AVAILABLE,
        root_cause=(
            "Requested material quantity is not available for the confirmed delivery date. "
            "ATP (Available-to-Promise) check failed."
        ),
        severity=IssueSeverity.HIGH,
        base_confidence=0.86,
        action_tcode="MD04",
        action_description="Check stock/requirements in MD04, expedite purchase orders, or reschedule delivery date",
        action_risk="low",
        rollback_plan="No direct posting — rescheduling can be reverted by restoring the original delivery date.",
        prerequisites=["Check MMBE for current stock", "Verify open PO receipts in ME2M"],
        authorization_objects=["M_MSEG_WMB"],
    ),
    # ── Billing ─────────────────────────────────────────────────────────────
    SDRule(
        rule_id="SD-006",
        tcode="VF03",
        status_match=["BLOCKED"],
        condition_key="billing_block",
        issue_type=IssueType.BILLING_BLOCK,
        root_cause=(
            "Billing document or the underlying sales order/delivery has a billing block. "
            "This may be due to a pricing error, credit block, or manual hold."
        ),
        severity=IssueSeverity.HIGH,
        base_confidence=0.90,
        action_tcode="VF02",
        action_description="Remove billing block in VF02 and run billing via VF04 due list",
        action_risk="medium",
        rollback_plan="Cancel the billing document using VF11 if issued in error.",
        prerequisites=["All prerequisite deliveries must be goods-issued", "Pricing must be complete"],
        authorization_objects=["V_VBRK_FKA"],
    ),
    # ── Partner ─────────────────────────────────────────────────────────────
    SDRule(
        rule_id="SD-007",
        tcode="VA03",
        status_match=["OPEN", "ERROR"],
        condition_key="partner_missing",
        issue_type=IssueType.PARTNER_MISSING,
        root_cause=(
            "A mandatory partner function is missing in the sales order "
            "(e.g. Ship-To party, Bill-To party, or Payer)."
        ),
        severity=IssueSeverity.MEDIUM,
        base_confidence=0.93,
        action_tcode="VA02",
        action_description="Add the missing partner function in VA02 > Partner tab",
        action_risk="low",
        rollback_plan="Remove incorrect partner assignments via VA02.",
        prerequisites=["Customer master data must be complete in XD02/XD03"],
        authorization_objects=["V_VBAK_VKO"],
    ),
]


def get_sd_rules_for_tcode(tcode: str) -> list[SDRule]:
    return [r for r in SD_RULES if r.tcode == tcode.upper()]


def find_matching_sd_rule(tcode: str, status: str, context_data: dict[str, Any]) -> SDRule | None:
    candidates = get_sd_rules_for_tcode(tcode)
    for rule in candidates:
        if status.upper() in rule.status_match:
            if rule.condition_key is None or rule.condition_key in context_data:
                return rule
    for rule in candidates:
        if status.upper() in rule.status_match:
            return rule
    return None
