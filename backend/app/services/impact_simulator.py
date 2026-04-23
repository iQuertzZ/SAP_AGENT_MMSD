"""
Impact Simulator — estimates the financial, workflow, and risk impact of an action
before any execution.  All logic is deterministic from the available data.
"""
from __future__ import annotations

from backend.app.core.logging import get_logger
from backend.app.models.action import RecommendedAction, RiskLevel
from backend.app.models.context import SAPContext, SAPModule
from backend.app.models.diagnosis import DiagnosisResult, IssueType
from backend.app.models.simulation import FinancialImpact, SimulationResult, WorkflowImpact

logger = get_logger(__name__)

_RISK_SCORE_MAP: dict[RiskLevel, float] = {
    RiskLevel.LOW: 0.15,
    RiskLevel.MEDIUM: 0.40,
    RiskLevel.HIGH: 0.75,
}

_NON_REVERSIBLE_TCODES = {"MR11", "MI07", "VF01", "MIRO"}
_FINANCIAL_POSTING_TCODES = {"MR11", "MIGO", "MI07", "VF01", "VF02", "MIRO", "MR8M"}


class ImpactSimulator:
    def simulate(
        self,
        context: SAPContext,
        diagnosis: DiagnosisResult,
        action: RecommendedAction,
    ) -> SimulationResult:
        raw = context.raw_data

        financial = self._simulate_financial(context, diagnosis, action)
        workflow = self._simulate_workflow(context, diagnosis, action)
        risk_score = self._calculate_risk_score(action, financial, workflow)
        documents_affected = self._count_affected_docs(raw, action)
        warnings = self._generate_warnings(context, diagnosis, action, financial)
        blockers = self._check_blockers(context, action)
        reversible = action.tcode not in _NON_REVERSIBLE_TCODES

        result = SimulationResult(
            documents_affected=documents_affected,
            financial=financial,
            workflow=workflow,
            risk_score=round(risk_score, 3),
            warnings=warnings,
            blockers=blockers,
            reversible=reversible,
            simulation_notes=self._build_notes(action, financial, reversible),
        )
        logger.info(
            "Simulation complete",
            tcode=action.tcode,
            risk_score=result.risk_score,
            documents_affected=documents_affected,
        )
        return result

    def _simulate_financial(
        self, context: SAPContext, diagnosis: DiagnosisResult, action: RecommendedAction
    ) -> FinancialImpact:
        raw = context.raw_data
        posting = action.tcode in _FINANCIAL_POSTING_TCODES

        amount: float | None = None
        currency = raw.get("currency")
        gl_accounts: list[str] = []
        cost_centers: list[str] = []

        if diagnosis.issue_type == IssueType.GRIR_MISMATCH and action.tcode == "MR11":
            amount = raw.get("grir_diff")
            gl_accounts = ["WRX", "GR/IR Clearing"]
        elif diagnosis.issue_type == IssueType.MISSING_GR and action.tcode == "MIGO":
            amount = raw.get("invoice_amount")
            gl_accounts = ["GR/IR Clearing", "Stock Account"]
        elif diagnosis.issue_type == IssueType.CREDIT_BLOCK and action.tcode == "VKM1":
            amount = raw.get("total_value")
            gl_accounts = ["Revenue", "Customer Receivables"]
        elif diagnosis.issue_type in {IssueType.PRICE_VARIANCE, IssueType.QUANTITY_VARIANCE}:
            amount = raw.get("grir_diff") or raw.get("invoice_amount")
            gl_accounts = ["Price Difference Account", "GR/IR Clearing"]

        if raw.get("cost_center"):
            cost_centers = [raw["cost_center"]]

        return FinancialImpact(
            posting_required=posting and amount is not None,
            amount=amount,
            currency=currency,
            gl_accounts_affected=gl_accounts,
            cost_centers_affected=cost_centers,
        )

    def _simulate_workflow(
        self, context: SAPContext, diagnosis: DiagnosisResult, action: RecommendedAction
    ) -> WorkflowImpact:
        steps: list[str] = []
        approvals: list[str] = []
        notifications: list[str] = []

        if action.risk == RiskLevel.HIGH:
            approvals.append("Senior Controller or Finance Manager approval required")
        if action.risk in {RiskLevel.MEDIUM, RiskLevel.HIGH}:
            approvals.append("Supervisor sign-off required in approval workflow")

        if action.tcode in {"MR11", "MI07"}:
            steps.append("FI posting will be created")
            notifications.append("Finance team notified via workflow")
        if action.tcode == "MRBR":
            steps.append("Invoice will move to 'Released' status")
            steps.append("Automatic payment run scheduling triggered")
            notifications.append("AP team notified of released invoice")
        if action.tcode == "VKM1":
            steps.append("Order credit block removed")
            steps.append("Order moves to delivery scheduling")
            notifications.append("Sales team notified of order release")
        if action.tcode == "MIGO":
            steps.append("Material document created")
            steps.append("Stock updated in MARD/MCHB")
            steps.append("GR/IR clearing account updated")

        return WorkflowImpact(
            steps_triggered=steps,
            approvals_required=approvals,
            notifications_sent=notifications,
        )

    def _calculate_risk_score(
        self,
        action: RecommendedAction,
        financial: FinancialImpact,
        workflow: WorkflowImpact,
    ) -> float:
        base = _RISK_SCORE_MAP.get(action.risk, 0.40)

        # Adjust for financial magnitude
        if financial.amount is not None:
            if financial.amount > 100_000:
                base = min(base + 0.15, 0.99)
            elif financial.amount > 10_000:
                base = min(base + 0.07, 0.99)

        # Adjust for approval count
        if len(workflow.approvals_required) >= 2:
            base = min(base + 0.05, 0.99)

        return base

    def _count_affected_docs(self, raw: dict, action: RecommendedAction) -> int:
        count = 1  # the primary document
        if raw.get("items"):
            count += len(raw["items"])
        return count

    def _generate_warnings(
        self,
        context: SAPContext,
        diagnosis: DiagnosisResult,
        action: RecommendedAction,
        financial: FinancialImpact,
    ) -> list[str]:
        warnings: list[str] = []
        raw = context.raw_data

        if action.tcode not in _NON_REVERSIBLE_TCODES is False:
            warnings.append(
                f"Transaction {action.tcode} creates postings that are difficult to reverse."
            )
        if financial.amount and financial.amount > 50_000:
            warnings.append(
                f"High financial impact: {financial.amount:,.2f} {financial.currency or ''}. "
                "Ensure proper authorization."
            )
        if raw.get("block_reason") == "vendor_blocked":
            warnings.append("Vendor is currently blocked — verify block removal authorization.")
        if diagnosis.confidence < 0.75:
            warnings.append(
                f"Diagnosis confidence is {diagnosis.confidence:.0%}. "
                "Manual verification recommended before executing."
            )
        return warnings

    def _check_blockers(self, context: SAPContext, action: RecommendedAction) -> list[str]:
        blockers: list[str] = []
        raw = context.raw_data

        if action.tcode in _FINANCIAL_POSTING_TCODES:
            if not raw.get("fiscal_year") and not context.fiscal_year:
                blockers.append("Fiscal year not determined — verify posting period is open.")

        if action.tcode == "MIGO" and raw.get("po_number") is None:
            blockers.append("No Purchase Order number found — cannot post GR without PO reference.")

        return blockers

    def _build_notes(
        self, action: RecommendedAction, financial: FinancialImpact, reversible: bool
    ) -> str:
        parts = [f"Action: {action.tcode} — {action.description}"]
        if financial.posting_required and financial.amount:
            parts.append(
                f"Financial posting: {financial.amount:,.2f} {financial.currency or '?'} "
                f"affecting {', '.join(financial.gl_accounts_affected)}"
            )
        parts.append("Reversible: " + ("Yes — rollback plan available." if reversible else "No — permanent posting."))
        return " | ".join(parts)
