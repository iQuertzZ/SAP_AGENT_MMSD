"""
MM diagnostic and action rules.

Each rule maps a (tcode, status, condition) tuple to:
  - issue_type
  - root_cause
  - severity
  - base_confidence
  - recommended_action (tcode)
  - rollback_plan
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.models.diagnosis import IssueSeverity, IssueType


@dataclass
class MMRule:
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


MM_RULES: list[MMRule] = [
    # ── Invoice Verification ────────────────────────────────────────────────
    MMRule(
        rule_id="MM-001",
        tcode="MIRO",
        status_match=["BLOCKED"],
        condition_key="grir_diff",
        issue_type=IssueType.GRIR_MISMATCH,
        root_cause=(
            "Invoice is blocked because the invoiced quantity or amount does not match "
            "the goods receipt posting. The GR/IR clearing account has an open balance."
        ),
        severity=IssueSeverity.HIGH,
        base_confidence=0.92,
        action_tcode="MR11",
        action_description="Run GR/IR account maintenance (MR11) to reconcile the open GR/IR difference",
        action_risk="medium",
        rollback_plan="Reverse the MR11 posting using MR8M with the generated FI document number.",
        prerequisites=["Goods Receipt must exist for the PO item", "Fiscal period must be open"],
        authorization_objects=["M_RECH_WRK", "F_BKPF_BUK"],
    ),
    MMRule(
        rule_id="MM-002",
        tcode="MIRO",
        status_match=["BLOCKED"],
        condition_key="missing_gr",   # matched via block_reason priority
        issue_type=IssueType.MISSING_GR,
        root_cause=(
            "Invoice is blocked because no goods receipt has been posted for this purchase "
            "order item. The system cannot match the invoice to a delivery."
        ),
        severity=IssueSeverity.HIGH,
        base_confidence=0.95,
        action_tcode="MIGO",
        action_description="Post goods receipt (MIGO – mvt type 101) against the PO before reprocessing the invoice",
        action_risk="medium",
        rollback_plan="Cancel the GR posting in MIGO using movement type 102, then re-block the invoice in MIRO.",
        prerequisites=["Physical goods must have been received"],
        authorization_objects=["M_MSEG_WMB"],
    ),
    MMRule(
        rule_id="MM-003",
        tcode="MIRO",
        status_match=["BLOCKED"],
        condition_key=None,   # fallback only — caught by MM-001 first when grir_diff present
        issue_type=IssueType.PRICE_VARIANCE,
        root_cause=(
            "Invoice price exceeds the configured tolerance limits relative to the PO price. "
            "The variance may result from vendor surcharges, freight, or price updates."
        ),
        severity=IssueSeverity.MEDIUM,
        base_confidence=0.88,
        action_tcode="MRBR",
        action_description="Release the blocked invoice via MRBR after verifying the price variance is acceptable",
        action_risk="medium",
        rollback_plan="Re-block the invoice in MIR4 or reverse via MR8M if released incorrectly.",
        prerequisites=["Price variance must be within company-approved limits"],
        authorization_objects=["M_RECH_WRK"],
    ),
    MMRule(
        rule_id="MM-004",
        tcode="MIRO",
        status_match=["BLOCKED"],
        condition_key=None,   # fallback only
        issue_type=IssueType.QUANTITY_VARIANCE,
        root_cause=(
            "Invoiced quantity differs from the received quantity beyond tolerance limits."
        ),
        severity=IssueSeverity.MEDIUM,
        base_confidence=0.87,
        action_tcode="MRBR",
        action_description="Release invoice after quantity variance review, or adjust GR via MIGO",
        action_risk="medium",
        rollback_plan="Reverse the release and coordinate with warehouse for correct GR quantity.",
        prerequisites=["Verify actual goods receipt quantity in MMBE or MB52"],
        authorization_objects=["M_RECH_WRK"],
    ),
    # ── Purchase Orders ─────────────────────────────────────────────────────
    MMRule(
        rule_id="MM-005",
        tcode="ME23N",
        status_match=["BLOCKED", "PENDING"],
        condition_key="po_not_released",
        issue_type=IssueType.PO_NOT_RELEASED,
        root_cause=(
            "Purchase Order has not completed the release (approval) strategy. "
            "One or more release levels are pending approval."
        ),
        severity=IssueSeverity.MEDIUM,
        base_confidence=0.90,
        action_tcode="ME28",
        action_description="Release the purchase order via ME28 (mass release) or ME29N (single)",
        action_risk="low",
        rollback_plan="Revoke release in ME28 and return PO to previous release level.",
        prerequisites=["Approver must have ME28 authorization"],
        authorization_objects=["M_EINK_FRG"],
    ),
    # ── Goods Movements ─────────────────────────────────────────────────────
    MMRule(
        rule_id="MM-006",
        tcode="MIGO",
        status_match=["ERROR", "BLOCKED"],
        condition_key="stock_inconsistency",
        issue_type=IssueType.STOCK_INCONSISTENCY,
        root_cause=(
            "Stock quantity or value is inconsistent between the material document "
            "and the stock management segments (MARD/MCHB tables)."
        ),
        severity=IssueSeverity.CRITICAL,
        base_confidence=0.82,
        action_tcode="MI07",
        action_description="Run inventory difference posting (MI07) after physical inventory count",
        action_risk="high",
        rollback_plan="Reverse the MI07 posting using MI08 if posted incorrectly.",
        prerequisites=["Physical inventory document must exist (MI01/MI04)", "Fiscal period open"],
        authorization_objects=["M_MSEG_WMB", "M_IBED_BUK"],
    ),
    # ── Vendor ──────────────────────────────────────────────────────────────
    MMRule(
        rule_id="MM-007",
        tcode="MIRO",
        status_match=["BLOCKED"],
        condition_key="vendor_blocked",
        issue_type=IssueType.VENDOR_BLOCKED,
        root_cause=(
            "The vendor account is blocked for posting (purchasing or payment block). "
            "All new transactions for this vendor are halted."
        ),
        severity=IssueSeverity.HIGH,
        base_confidence=0.93,
        action_tcode="XK05",
        action_description="Review and remove vendor block in XK05 after verifying the reason for blocking",
        action_risk="medium",
        rollback_plan="Re-apply the block in XK05 if the vendor issue is not resolved.",
        prerequisites=["Vendor master data review required", "AP/Purchasing approval"],
        authorization_objects=["F_LFA1_BUK", "M_LFA1_APP"],
    ),
]


def get_mm_rules_for_tcode(tcode: str) -> list[MMRule]:
    return [r for r in MM_RULES if r.tcode == tcode.upper()]


def find_matching_rule(tcode: str, status: str, context_data: dict[str, Any]) -> MMRule | None:
    """Return the best-matching MM rule for the given context.

    Priority:
      1. Exact match on block_reason == condition_key (most specific)
      2. condition_key present as a data key in context_data
      3. First rule that matches status (catch-all fallback)
    """
    candidates = get_mm_rules_for_tcode(tcode)
    block_reason = context_data.get("block_reason", "")

    # Priority 1: block_reason matches condition_key exactly
    if block_reason:
        for rule in candidates:
            if status.upper() in rule.status_match and rule.condition_key == block_reason:
                return rule

    # Priority 2: condition_key is a key present in context_data
    for rule in candidates:
        if status.upper() in rule.status_match:
            if rule.condition_key is None or rule.condition_key in context_data:
                return rule

    # Priority 3: fallback — first status match
    for rule in candidates:
        if status.upper() in rule.status_match:
            return rule

    return None
