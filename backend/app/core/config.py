from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConnectorType(str, Enum):
    MOCK = "mock"
    ODATA = "odata"
    RFC = "rfc"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # SAP
    sap_connector: ConnectorType = ConnectorType.MOCK
    sap_odata_base_url: str = "https://localhost/sap/opu/odata/sap"
    sap_odata_user: str = ""
    sap_odata_password: str = ""
    sap_rfc_host: str = ""
    sap_rfc_sysnr: str = "00"
    sap_rfc_client: str = "100"
    sap_rfc_user: str = ""
    sap_rfc_password: str = ""

    # App
    app_env: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    secret_key: str = "dev-secret-change-in-production"
    execution_enabled: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("anthropic_api_key")
    @classmethod
    def warn_missing_key(cls, v: str) -> str:
        if not v:
            import warnings
            warnings.warn(
                "ANTHROPIC_API_KEY not set — AI analysis will use rule-based fallback",
                stacklevel=2,
            )
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == Environment.PRODUCTION

    @property
    def ai_enabled(self) -> bool:
        return bool(self.anthropic_api_key)


settings = Settings()
