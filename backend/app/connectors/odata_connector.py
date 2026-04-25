"""Re-export for backwards compatibility — real implementation is in odata/odata_connector.py."""
from backend.app.connectors.odata.odata_connector import ODataConnector

__all__ = ["ODataConnector"]
