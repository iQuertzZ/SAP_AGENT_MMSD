from __future__ import annotations

from functools import lru_cache

from backend.app.connectors.base import SAPConnectorBase
from backend.app.connectors.mock_connector import MockConnector
from backend.app.connectors.odata_connector import ODataConnector
from backend.app.core.config import ConnectorType, settings


@lru_cache(maxsize=1)
def get_connector() -> SAPConnectorBase:
    if settings.sap_connector == ConnectorType.ODATA:
        return ODataConnector()
    return MockConnector()
