"""OData → Pydantic mapper helpers."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

_ODATA_DATE_RE = re.compile(r"/Date\((\d+)(?:[+-]\d+)?\)/")


def sap_amount(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning("sap_amount: cannot parse", value=value)
        return 0.0


def sap_date(value: str | None) -> datetime | None:
    if not value:
        return None
    m = _ODATA_DATE_RE.match(value)
    if m:
        ms = int(m.group(1))
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        logger.warning("sap_date: cannot parse", value=value)
        return None


def sap_bool(value: str | None) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().upper() in {"X", "TRUE", "1", "YES"}


def sap_string(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return value


def _warn_missing(field: str, payload: dict[str, Any]) -> None:
    logger.warning("sap_mapper: expected field missing", field=field, keys=list(payload.keys()))
