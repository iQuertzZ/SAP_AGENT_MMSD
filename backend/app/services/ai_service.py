"""
AI Service — Claude-powered analysis for SAP MM/SD issues.

Uses:
  - claude-sonnet-4-6 for analysis
  - Prompt caching on the system prompt (SAP knowledge base ~4 KB)
  - Tool use for structured JSON output
"""
from __future__ import annotations

import json
from typing import Any

import anthropic

from backend.app.core.config import settings
from backend.app.core.exceptions import AIServiceError
from backend.app.core.logging import get_logger
from backend.app.models.context import SAPContext
from backend.app.models.diagnosis import DiagnosisResult, IssueSeverity, IssueType

logger = get_logger(__name__)

_DIAGNOSIS_TOOL = {
    "name": "report_diagnosis",
    "description": "Report the structured diagnosis of the SAP issue",
    "input_schema": {
        "type": "object",
        "properties": {
            "issue_type": {
                "type": "string",
                "enum": [t.value for t in IssueType],
                "description": "Classified issue type",
            },
            "root_cause": {
                "type": "string",
                "description": "Plain-language root cause explanation (2-3 sentences)",
            },
            "severity": {
                "type": "string",
                "enum": [s.value for s in IssueSeverity],
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Confidence score 0-1",
            },
            "supporting_evidence": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of observed facts that support this diagnosis",
            },
            "affected_documents": {
                "type": "array",
                "items": {"type": "string"},
                "description": "SAP document numbers affected",
            },
        },
        "required": ["issue_type", "root_cause", "severity", "confidence"],
    },
}

_SAP_SYSTEM_PROMPT = """You are a Principal SAP MM/SD Expert AI assistant.

# Your Role
Diagnose SAP issues in Materials Management (MM) and Sales & Distribution (SD) modules.
Provide accurate, structured diagnoses based on document data and transaction context.

# SAP MM Knowledge

## Key Transactions
- MIRO: Incoming Invoice Verification — common issues: GR/IR mismatch, price/quantity variance, vendor block
- MIGO: Goods Movements — movement types: 101 (GR), 102 (GR reversal), 261 (GI to order)
- ME21N/22N/23N: Purchase Order maintenance
- MRBR: Release Blocked Invoices
- MR11: GR/IR Account Maintenance (clears open GR/IR balances)

## MM Issue Patterns
| Status | Tcode | Typical Cause |
|--------|-------|---------------|
| BLOCKED | MIRO | price_variance > tolerance, quantity_variance, missing_gr, vendor_blocked |
| ERROR | MIGO | movement not allowed, period closed, stock negative |
| PENDING | ME23N | release strategy not completed |

## Key MM Tables
- EKKO/EKPO: Purchase Order header/items
- RBKPF/RBDRSEG: Invoice document header/items
- MKPF/MSEG: Material document header/items
- MARD: Plant storage location stock
- LFA1/LFB1: Vendor master

# SAP SD Knowledge

## Key Transactions
- VA01/02/03: Sales Order create/change/display
- VL01N/02N: Outbound Delivery
- VF01/02: Billing document
- VKM1: Release credit-blocked orders
- FD32: Customer credit management

## SD Issue Patterns
| Status | Tcode | Typical Cause |
|--------|-------|---------------|
| BLOCKED | VA03 | credit_block (credit exposure > limit), pricing_error, incompletion_log |
| BLOCKED | VL03N | delivery_block, material_not_available, picking incomplete |
| BLOCKED | VF03 | billing_block, predecessor not goods-issued |

## Key SD Tables
- VBAK/VBAP: Sales Order header/items
- LIKP/LIPS: Delivery header/items
- VBRK/VBRP: Billing document header/items
- KNKK: Customer credit management data

# Diagnosis Rules
1. Confidence >= 0.90: Strong evidence, clear SAP status, known pattern
2. Confidence 0.70-0.89: Probable match, some ambiguity
3. Confidence < 0.70: Uncertain — flag for manual review

Always base your diagnosis on the provided document data, not assumptions.
Return UNKNOWN if the evidence is insufficient."""


class AIService:
    def __init__(self) -> None:
        if not settings.anthropic_api_key:
            raise AIServiceError("ANTHROPIC_API_KEY is not configured")
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    async def diagnose(self, context: SAPContext) -> DiagnosisResult:
        user_message = self._build_user_message(context)

        try:
            response = self._client.messages.create(
                model=settings.anthropic_model,
                max_tokens=1024,
                system=[
                    {
                        "type": "text",
                        "text": _SAP_SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                tools=[_DIAGNOSIS_TOOL],
                tool_choice={"type": "any"},
                messages=[{"role": "user", "content": user_message}],
            )
        except anthropic.APIError as exc:
            logger.error("Anthropic API error", error=str(exc))
            raise AIServiceError(f"Claude API call failed: {exc}") from exc

        return self._parse_response(response)

    def _build_user_message(self, context: SAPContext) -> str:
        raw = context.raw_data
        return (
            f"Diagnose the following SAP {context.module} issue:\n\n"
            f"Transaction: {context.tcode}\n"
            f"Document ID: {context.document_id}\n"
            f"Status: {context.status}\n"
            f"Company Code: {context.company_code or 'N/A'}\n"
            f"Plant: {context.plant or 'N/A'}\n\n"
            f"Document Data:\n```json\n{json.dumps(raw, indent=2, default=str)}\n```\n\n"
            "Use the report_diagnosis tool to provide your structured analysis."
        )

    def _parse_response(self, response: anthropic.types.Message) -> DiagnosisResult:
        for block in response.content:
            if block.type == "tool_use" and block.name == "report_diagnosis":
                inp: dict[str, Any] = block.input
                return DiagnosisResult(
                    issue_type=IssueType(inp["issue_type"]),
                    root_cause=inp["root_cause"],
                    severity=IssueSeverity(inp["severity"]),
                    confidence=float(inp["confidence"]),
                    supporting_evidence=inp.get("supporting_evidence", []),
                    affected_documents=inp.get("affected_documents", []),
                    source="ai",
                )

        raise AIServiceError("Claude did not return a diagnosis tool call")
