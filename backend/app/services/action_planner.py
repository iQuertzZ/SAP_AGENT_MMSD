"""
Action Planner — maps a DiagnosisResult to a ranked list of RecommendedActions.
"""
from __future__ import annotations

import uuid
from typing import Any

from backend.app.core.logging import get_logger
from backend.app.knowledge.mm_rules import MM_RULES
from backend.app.knowledge.sd_rules import SD_RULES
from backend.app.models.action import RecommendedAction, RiskLevel
from backend.app.models.context import SAPContext
from backend.app.models.diagnosis import DiagnosisResult, IssueType

logger = get_logger(__name__)

# Maps issue_type → list of (action_tcode, description, risk, rollback, prerequisites, auth)
_ISSUE_ACTIONS: dict[str, list[dict[str, Any]]] = {
    # MM
    IssueType.GRIR_MISMATCH: [
        {
            "tcode": "MR11",
            "description": "Run GR/IR account maintenance to clear the open balance",
            "risk": "medium",
            "rollback": "Reverse MR11 posting with MR8M using the generated FI document.",
            "prerequisites": ["Fiscal period must be open", "GR document must exist"],
            "auth": ["M_RECH_WRK", "F_BKPF_BUK"],
            "duration": 10,
        },
    ],
    IssueType.MISSING_GR: [
        {
            "tcode": "MIGO",
            "description": "Post goods receipt (movement type 101) against the PO",
            "risk": "medium",
            "rollback": "Cancel GR with movement type 102 in MIGO.",
            "prerequisites": ["Physical goods must be on-site"],
            "auth": ["M_MSEG_WMB"],
            "duration": 5,
        },
    ],
    IssueType.PRICE_VARIANCE: [
        {
            "tcode": "MRBR",
            "description": "Release the price-variance-blocked invoice after approval",
            "risk": "medium",
            "rollback": "Re-block invoice via MIR4 or reverse with MR8M.",
            "prerequisites": ["Variance must be within approved tolerance"],
            "auth": ["M_RECH_WRK"],
            "duration": 5,
        },
        {
            "tcode": "ME22N",
            "description": "Update PO price to match vendor invoice if correct",
            "risk": "high",
            "rollback": "Revert PO price change in ME22N.",
            "prerequisites": ["Purchasing manager approval required"],
            "auth": ["M_EINK_EKG"],
            "duration": 15,
        },
    ],
    IssueType.QUANTITY_VARIANCE: [
        {
            "tcode": "MRBR",
            "description": "Release quantity-variance-blocked invoice after verification",
            "risk": "medium",
            "rollback": "Re-block in MIR4.",
            "prerequisites": ["Verify actual receipt quantity in MB51"],
            "auth": ["M_RECH_WRK"],
            "duration": 5,
        },
    ],
    IssueType.INVOICE_BLOCKED: [
        {
            "tcode": "MRBR",
            "description": "Release all blocked invoices matching selection criteria",
            "risk": "medium",
            "rollback": "Re-block invoices via MIR4.",
            "prerequisites": ["All blocking reasons must be resolved"],
            "auth": ["M_RECH_WRK"],
            "duration": 5,
        },
    ],
    IssueType.PO_NOT_RELEASED: [
        {
            "tcode": "ME28",
            "description": "Mass-release purchase orders via ME28",
            "risk": "low",
            "rollback": "Revoke release in ME28.",
            "prerequisites": ["Approver authorization required"],
            "auth": ["M_EINK_FRG"],
            "duration": 3,
        },
    ],
    IssueType.STOCK_INCONSISTENCY: [
        {
            "tcode": "MI07",
            "description": "Post inventory differences after physical count (MI07)",
            "risk": "high",
            "rollback": "Reverse MI07 document with MI08.",
            "prerequisites": ["Physical inventory document MI01 must exist"],
            "auth": ["M_MSEG_WMB", "M_IBED_BUK"],
            "duration": 20,
        },
    ],
    IssueType.VENDOR_BLOCKED: [
        {
            "tcode": "XK05",
            "description": "Remove vendor purchasing/payment block after review",
            "risk": "medium",
            "rollback": "Re-apply block in XK05.",
            "prerequisites": ["AP and Purchasing approval required"],
            "auth": ["F_LFA1_BUK"],
            "duration": 5,
        },
    ],
    IssueType.TOLERANCE_EXCEEDED: [
        {
            "tcode": "MRBR",
            "description": "Release invoice after tolerance exception approval",
            "risk": "high",
            "rollback": "Re-block invoice in MIR4.",
            "prerequisites": ["Exception approval required from management"],
            "auth": ["M_RECH_WRK"],
            "duration": 10,
        },
    ],
    # SD
    IssueType.CREDIT_BLOCK: [
        {
            "tcode": "VKM1",
            "description": "Release credit-blocked sales order after credit review",
            "risk": "medium",
            "rollback": "Re-block order in VKM1 or VA02.",
            "prerequisites": ["Review open items in FBL5N", "Credit controller approval"],
            "auth": ["V_VBAK_VKO", "F_KNKK_BED"],
            "duration": 10,
        },
        {
            "tcode": "FD32",
            "description": "Increase customer credit limit in FD32 (temporary if needed)",
            "risk": "high",
            "rollback": "Restore original credit limit in FD32.",
            "prerequisites": ["Credit manager approval required"],
            "auth": ["F_KNKK_BED"],
            "duration": 10,
        },
    ],
    IssueType.PRICING_ERROR: [
        {
            "tcode": "VA02",
            "description": "Update pricing conditions in VA02 — use 'Reprice' (G) function",
            "risk": "medium",
            "rollback": "Restore original pricing by selecting 'Copy pricing' from prior date.",
            "prerequisites": ["Valid condition records must exist in VK13"],
            "auth": ["V_VBAK_VKO"],
            "duration": 10,
        },
        {
            "tcode": "VK12",
            "description": "Update pricing condition record in VK12 if root price is wrong",
            "risk": "high",
            "rollback": "Restore condition record to previous validity period.",
            "prerequisites": ["Pricing analyst approval"],
            "auth": ["V_KONP_KNA"],
            "duration": 15,
        },
    ],
    IssueType.DELIVERY_BLOCK: [
        {
            "tcode": "VL02N",
            "description": "Remove delivery block and post goods issue",
            "risk": "medium",
            "rollback": "Cancel goods issue via VL09.",
            "prerequisites": ["Stock must be available", "Picking completed"],
            "auth": ["V_LIKP_VST"],
            "duration": 10,
        },
    ],
    IssueType.BILLING_BLOCK: [
        {
            "tcode": "VF02",
            "description": "Remove billing block and create billing document",
            "risk": "medium",
            "rollback": "Cancel billing document with VF11.",
            "prerequisites": ["All deliveries must be goods-issued", "Pricing complete"],
            "auth": ["V_VBRK_FKA"],
            "duration": 5,
        },
    ],
    IssueType.MATERIAL_NOT_AVAILABLE: [
        {
            "tcode": "MD04",
            "description": "Review stock/requirements list and expedite open POs",
            "risk": "low",
            "rollback": "Display-only — rescheduling reverts delivery date.",
            "prerequisites": ["Check MMBE for current unrestricted stock"],
            "auth": ["M_MSEG_WMB"],
            "duration": 10,
        },
    ],
    IssueType.INCOMPLETION_LOG: [
        {
            "tcode": "VA02",
            "description": "Complete mandatory fields shown in incompletion log",
            "risk": "low",
            "rollback": "Restore original field values in VA02.",
            "prerequisites": ["Edit > Incompletion Log in VA02"],
            "auth": ["V_VBAK_VKO"],
            "duration": 5,
        },
    ],
    IssueType.PARTNER_MISSING: [
        {
            "tcode": "VA02",
            "description": "Add missing partner function in VA02 > Partner tab",
            "risk": "low",
            "rollback": "Remove incorrect partner in VA02.",
            "prerequisites": ["Customer master data complete in XD03"],
            "auth": ["V_VBAK_VKO"],
            "duration": 5,
        },
    ],
    IssueType.OUTPUT_MISSING: [
        {
            "tcode": "VA02",
            "description": "Re-issue missing output (e.g. order confirmation) via VA02 > Output",
            "risk": "low",
            "rollback": "Cancel incorrectly sent output in NACE.",
            "prerequisites": [],
            "auth": ["V_VBAK_VKO"],
            "duration": 3,
        },
    ],
}


class ActionPlanner:
    def plan(self, context: SAPContext, diagnosis: DiagnosisResult) -> list[RecommendedAction]:
        templates = _ISSUE_ACTIONS.get(diagnosis.issue_type, [])
        if not templates:
            logger.info("No action templates for issue", issue=diagnosis.issue_type)
            return []

        actions: list[RecommendedAction] = []
        for tpl in templates:
            action_id = str(uuid.uuid4())
            action = RecommendedAction(
                action_id=action_id,
                tcode=tpl["tcode"],
                description=tpl["description"],
                risk=RiskLevel(tpl["risk"]),
                confidence=round(diagnosis.confidence * self._risk_confidence_factor(tpl["risk"]), 3),
                parameters=self._build_parameters(context, tpl["tcode"]),
                prerequisites=tpl.get("prerequisites", []),
                rollback_plan=tpl["rollback"],
                estimated_duration_minutes=tpl.get("duration", 5),
                requires_authorization=tpl.get("auth", []),
            )
            actions.append(action)

        return sorted(actions, key=lambda a: a.confidence, reverse=True)

    def _risk_confidence_factor(self, risk: str) -> float:
        return {"low": 1.0, "medium": 0.95, "high": 0.85}.get(risk, 1.0)

    def _build_parameters(self, context: SAPContext, tcode: str) -> dict[str, Any]:
        params: dict[str, Any] = {}
        raw = context.raw_data

        # Pre-fill common SAP parameters from context
        if context.company_code:
            params["BUKRS"] = context.company_code
        if context.plant:
            params["WERKS"] = context.plant
        if raw.get("po_number"):
            params["EBELN"] = raw["po_number"]
        if raw.get("vendor"):
            params["LIFNR"] = raw["vendor"]
        if raw.get("customer"):
            params["KUNNR"] = raw["customer"]
        if context.document_id:
            params["BELNR"] = context.document_id
        if context.fiscal_year:
            params["GJAHR"] = context.fiscal_year

        return params
