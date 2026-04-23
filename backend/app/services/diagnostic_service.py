"""
Diagnostic Service — maps SAP context to a DiagnosisResult.

Priority: AI analysis (if key present) → rule engine → unknown fallback.
"""
from __future__ import annotations

from backend.app.core.logging import get_logger
from backend.app.knowledge.mm_rules import find_matching_rule as find_mm_rule
from backend.app.knowledge.sd_rules import find_matching_sd_rule
from backend.app.models.context import SAPContext, SAPModule
from backend.app.models.diagnosis import DiagnosisResult, IssueSeverity, IssueType

logger = get_logger(__name__)


class DiagnosticService:
    def __init__(self, ai_service: "AIService | None" = None) -> None:  # noqa: F821
        self._ai = ai_service

    async def diagnose(self, context: SAPContext) -> DiagnosisResult:
        if self._ai is not None:
            try:
                result = await self._ai.diagnose(context)
                if result.confidence >= 0.70:
                    logger.info(
                        "AI diagnosis accepted",
                        issue=result.issue_type,
                        confidence=result.confidence,
                    )
                    return result
                logger.info(
                    "AI confidence too low, falling back to rules",
                    confidence=result.confidence,
                )
            except Exception as exc:
                logger.warning("AI diagnosis failed, using rule engine", error=str(exc))

        return self._rule_based_diagnosis(context)

    def _rule_based_diagnosis(self, context: SAPContext) -> DiagnosisResult:
        tcode = context.tcode.upper()
        status = context.status.value
        raw = context.raw_data

        if context.module == SAPModule.MM:
            rule = find_mm_rule(tcode, status, raw)
            if rule:
                return DiagnosisResult(
                    issue_type=rule.issue_type,
                    root_cause=rule.root_cause,
                    severity=rule.severity,
                    confidence=rule.base_confidence,
                    details=self._extract_mm_details(raw),
                    supporting_evidence=self._build_mm_evidence(raw, rule.condition_key),
                    affected_documents=self._extract_affected_docs(raw),
                    source="rule_engine",
                )

        if context.module == SAPModule.SD:
            rule = find_matching_sd_rule(tcode, status, raw)
            if rule:
                return DiagnosisResult(
                    issue_type=rule.issue_type,
                    root_cause=rule.root_cause,
                    severity=rule.severity,
                    confidence=rule.base_confidence,
                    details=self._extract_sd_details(raw),
                    supporting_evidence=self._build_sd_evidence(raw, rule.condition_key),
                    affected_documents=self._extract_affected_docs(raw),
                    source="rule_engine",
                )

        logger.info("No matching rule, returning UNKNOWN diagnosis", tcode=tcode, status=status)
        return DiagnosisResult(
            issue_type=IssueType.UNKNOWN,
            root_cause=f"No matching rule found for {tcode} in status {status}.",
            severity=IssueSeverity.LOW,
            confidence=0.30,
            source="rule_engine",
        )

    # ── Detail extractors ────────────────────────────────────────────────────

    def _extract_mm_details(self, raw: dict) -> dict:
        return {
            k: raw[k]
            for k in ("vendor", "po_number", "gr_amount", "invoice_amount",
                      "grir_diff", "block_reason", "currency")
            if k in raw
        }

    def _build_mm_evidence(self, raw: dict, condition_key: str | None) -> list[str]:
        evidence: list[str] = []
        if raw.get("grir_diff"):
            diff = raw["grir_diff"]
            evidence.append(f"GR/IR difference of {diff} {raw.get('currency', '')} detected")
        if raw.get("block_reason"):
            evidence.append(f"SAP block reason: {raw['block_reason']}")
        if raw.get("po_number"):
            evidence.append(f"Related PO: {raw['po_number']}")
        if raw.get("gr_amount") == 0.0:
            evidence.append("No goods receipt found for this PO")
        return evidence

    def _extract_sd_details(self, raw: dict) -> dict:
        return {
            k: raw[k]
            for k in ("customer", "credit_limit", "credit_exposure", "block_reason",
                      "pricing_incomplete", "missing_conditions", "currency")
            if k in raw
        }

    def _build_sd_evidence(self, raw: dict, condition_key: str | None) -> list[str]:
        evidence: list[str] = []
        if raw.get("credit_exposure") and raw.get("credit_limit"):
            excess = raw["credit_exposure"] - raw["credit_limit"]
            evidence.append(
                f"Credit exposure {raw['credit_exposure']} exceeds limit {raw['credit_limit']} "
                f"by {excess:.2f} {raw.get('currency', '')}"
            )
        if raw.get("pricing_incomplete"):
            evidence.append("Pricing conditions are incomplete")
        if raw.get("missing_conditions"):
            evidence.append(f"Missing condition types: {', '.join(raw['missing_conditions'])}")
        if raw.get("block_reason"):
            evidence.append(f"SAP block reason: {raw['block_reason']}")
        return evidence

    def _extract_affected_docs(self, raw: dict) -> list[str]:
        docs: list[str] = []
        for key in ("po_number", "order_number", "delivery_number", "billing_number"):
            if val := raw.get(key):
                docs.append(str(val))
        return docs
